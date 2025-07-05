import json
import boto3
import requests
from anthropic import Anthropic

# AWS clients
secrets_client = boto3.client("secretsmanager")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("devops-outreach-db")

# Load secrets
def get_secret(secret_name="app/ai/agent/devops-outreach"):
    secret = secrets_client.get_secret_value(SecretId=secret_name)
    return json.loads(secret["SecretString"])

secrets = get_secret()
CLAUDE_API_KEY = secrets["CLAUDE_API_KEY"]
SLACK_WEBHOOK_URL = secrets["SLACK_WEBHOOK_URL"]
client = Anthropic(api_key=CLAUDE_API_KEY)

def generate_email_variants(company_name, company_info, contacts, model="claude-sonnet-4-20250514"):
    if not contacts:
        return ["No contacts found."]

    is_consultancy = any(kw in company_info.lower() for kw in ["consulting", "solutions", "services", "agency", "systems", "group"])

    if is_consultancy:
        use_case = (
            "You're reaching out to a DevOps consulting company that may be open to partnering on projects, subcontracting overflow work, or collaborating on complex cloud transformations. "
            "They already understand DevOps, so focus on how you can complement or extend their delivery capacity, bring in niche AWS or Kubernetes expertise, or help with white-labeled engagements."
        )
    else:
        use_case = (
            "You're reaching out to a company that may benefit from DevOps consulting. Focus on how you can help them scale cloud infrastructure, improve developer workflows, or reduce ops overhead."
        )

    consultant_bio = (
        "You are a results-oriented DevOps consultant named Salek Ali, with over 8 years of experience helping companies modernize "
        "and scale their cloud infrastructure. You specialize in AWS, Kubernetes, Terraform, and CI/CD automation, "
        "and have deep technical expertise backed by a PhD in distributed systems. You've led high-impact projects "
        "for both startups and government agencies—building secure AWS landing zones, optimizing EKS deployments, and "
        "implementing developer workflows that reduce costs and accelerate time to value. You're known for delivering "
        "real business outcomes with clear communication, strategic thinking, and technical precision."
    )

    summary = ", ".join(f"{c['name']} ({c['title']})" for c in contacts[:3])
    prompt = (
        f"{consultant_bio}\n\n"
        f"You're reaching out to: {company_name}\n"
        f"Relevant contacts: {summary}\n\n"
        f"{use_case}\n\n"
        "Write 3 short cold email variants in Australian English (80–120 words). Each should:\n"
        "- Be friendly, confident, and human\n"
        "- Briefly introduce yourself and what you offer\n"
        "- Mention how you can help companies like this\n"
        "- End with a soft call to action like 'Would it make sense to connect?'\n\n"
        "Avoid buzzwords. Use plain English. No markdown or bullet points."
    )

    msg = client.messages.create(
        model=model,
        max_tokens=1000,
        temperature=0.7,
        messages=[{"role": "user", "content": prompt}]
    )

    content = msg.content[0].text.strip()
    print(content)
    return content

def send_to_slack(company_name, website, company_info, score, rationale, contacts, emails):
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*🚀 New Lead Scored: {company_name}*\n<{website}|Visit Site>\n*Score:* {score}\n*Why:* {rationale}\n*Company Info:* {company_info}"
            }
        },
        {"type": "divider"},
    ]

    for contact in contacts:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{contact.get('name')}* — {contact.get('title')}\n:e-mail: {contact.get('email')}\n:male-technologist:{contact.get('linkedin_url')}"
            }
        })

    blocks.append({"type": "divider"})

    blocks.append({
        "type": "section",
        "text": {"type": "mrkdwn", "text": emails}
    })

    payload = {"blocks": blocks}
    resp = requests.post(SLACK_WEBHOOK_URL, json=payload)

    if resp.status_code != 200:
        print(f"❌ Slack failed: {resp.status_code} {resp.text}")
    else:
        print(f"✅ Slack sent for {company_name}")

def lambda_handler(event, context):
    websites = event.get("websites", [])
    if not websites:
        return {"statusCode": 400, "body": "No websites provided."}

    for website in websites:
        try:
            result = table.scan(
                FilterExpression="company_website = :w",
                ExpressionAttributeValues={":w": website}
            )
            for item in result.get("Items", []):
                name = item["company_name"]
                info = item.get("company_info", "")
                score = item.get("score", "N/A")
                rationale = item.get("rationale", "N/A")
                contacts = item.get("contacts", [])
                emails = generate_email_variants(name, info, contacts)
                emails = emails.replace("**", "*")
                send_to_slack(name, website, info, score, rationale, contacts, emails)
        except Exception as e:
            print(f"❌ Failed for {website}: {e}")

    return {"statusCode": 200, "body": "Slack notifications sent."}
