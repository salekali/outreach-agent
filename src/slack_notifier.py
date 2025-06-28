import os
import json
import requests

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")


def send_to_slack(company_name, website, company_info, score, rationale, contacts, emails):
    if not SLACK_WEBHOOK_URL:
        print("⚠️ SLACK_WEBHOOK_URL not set.")
        return

    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*🚀 New Lead Scored: {company_name}*\n<{website}|Visit Site>\n*Score:* {score}\n*Why:* {rationale}\n*Info:* {company_info}"
            }
        },
        {"type": "divider"},
    ]

    for contact in contacts:
        block = {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{contact.get('full_name')}* — {contact.get('title')}\n📧 {contact.get('email')}"
            }
        }
        blocks.append(block)

    blocks.append({"type": "divider"})

    for i, variant in enumerate(emails):
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Email Variant {i+1}:*\n{variant}"
            }
        })

    payload = {"blocks": blocks}

    response = requests.post(
        SLACK_WEBHOOK_URL,
        data=json.dumps(payload),
        headers={"Content-Type": "application/json"}
    )

    if response.status_code != 200:
        print(f"❌ Failed to send Slack message: {response.status_code} — {response.text}")
    else:
        print(f"✅ Slack message sent for {company_name}")
