import json
import boto3
from anthropic import Anthropic
from botocore.exceptions import ClientError

# AWS Clients
dynamodb = boto3.resource("dynamodb")
secrets_client = boto3.client("secretsmanager")

# DynamoDB Table
table = dynamodb.Table("devops-outreach-db")

# Load secret from Secrets Manager
def get_anthropic_api_key(secret_name="app/ai/agent/devops-outreach"):
    try:
        secret_response = secrets_client.get_secret_value(SecretId=secret_name)
        secret_data = json.loads(secret_response["SecretString"])
        return secret_data["CLAUDE_API_KEY"]
    except ClientError as e:
        raise ValueError(f"❌ Failed to fetch API key from Secrets Manager: {e}")

# Claude Client
ANTHROPIC_API_KEY = get_anthropic_api_key()
client = Anthropic(api_key=ANTHROPIC_API_KEY)

# Function to rank a company based on public signals
def rank_company(company_name, company_website, model):
    prompt = (
        f"Company: {company_name}\n"
        f"Website: {company_website}\n\n"
        "Evaluate whether this company is a good lead for DevOps consulting based on its public signals.\n"
        "Consider factors like recent hiring for DevOps roles, history of using consultants, product complexity, and any recent funding or growth signals.\n"
        "Provide a score from 0 to 100, a brief rationale, and the date ranked.\n\n"
        "Format your response as a JSON object with the following keys:\n"
        "signal_summary: A brief summary of the signals considered\n"
        "score: The score from 0 to 100\n"
        "rationale: A one-line explanation of the score\n"
        "date_ranked: The date the company was ranked in YYYY-MM-DD format\n\n"
        "Example response:\n"
        '{"signal_summary": "Hiring DevOps engineers on LinkedIn, raised Series A funding", '
        '"score": 85, "rationale": "Strong hiring signals and recent funding",'
        '"date_ranked": "2023-10-01"}\n\n'
        "Only return the JSON object. Do not include any explanatory text, markdown formatting, or commentary."
    )

    system_prompt = (
        "You are a highly skilled DevOps market analyst. Your task is to evaluate whether a company is a good lead for DevOps consulting services. "
        "You analyze public signals such as recent hiring trends, history of using external consultants, product complexity, and growth or funding signals. "
        "You are precise, objective, and only return valid JSON with exactly the following keys: signal_summary, score, rationale, date_ranked. "
        "You never include commentary, explanations, or text outside the JSON object. If uncertain, make the best possible estimate. "
        "The score must be between 0 and 100, and the date_ranked must be in YYYY-MM-DD format (use today's date). "
        "Only return a single JSON object in your response."
    )

    response = client.messages.create(
        model=model,
        max_tokens=1024,
        temperature=0.5,
        system=system_prompt,
        messages=[
            {"role": "user", "content": prompt}
        ],
    )

    content = response.content[0].text
    try:
        data = json.loads(content)
        assert set(data.keys()) >= {
            "signal_summary", "score", "rationale", "date_ranked"
        }, "Missing required fields in Claude response"
        return data
    except Exception as e:
        raise ValueError(f"Invalid JSON from Claude or parsing failed: {e}")


def lambda_handler(event, context):
    try:
        websites = event.get("websites", [])
    except Exception as e:
        print(f"❌ Error parsing event detail: {e}")
        return {"statusCode": 400, "body": "Invalid event format"}

    if not websites:
        return {"statusCode": 200, "body": json.dumps({"message": "No websites provided."})}

    results = []

    for website in websites:
        try:
            response = table.get_item(Key={"company_website": website})
            item = response.get("Item")
            if not item:
                print(f"⚠️ No item found for website: {website}")
                continue

            name = item["company_name"]

            result = rank_company(name, website, model="claude-sonnet-4-20250514")

            table.update_item(
                Key={"company_website": website},
                UpdateExpression="""
                    SET score = :s, rationale = :r, signal_summary = :ss, date_ranked = :d
                """,
                ExpressionAttributeValues={
                    ":s": int(result["score"]),
                    ":r": result["rationale"],
                    ":ss": result["signal_summary"],
                    ":d": result["date_ranked"],
                }
            )

            results.append({"company_name": name, "score": result["score"]})
            print(f"✅ Ranked company: {name}")

        except ClientError as e:
            print(f"❌ Error accessing/updating DynamoDB for {website}: {e}")

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Ranked companies updated.",
            "count": len(results),
            "results": results,
            "websites": websites
        })
    }
