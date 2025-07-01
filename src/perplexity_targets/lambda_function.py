# src/perplexity_targets.py

import json
import boto3
import requests
from pydantic import BaseModel
from botocore.exceptions import ClientError

# AWS clients
dynamodb = boto3.resource("dynamodb")
secrets_client = boto3.client("secretsmanager")
eventbridge = boto3.client("events")

# DynamoDB table
table = dynamodb.Table("devops-outreach-db")

# Secrets Manager
def get_perplexity_api_key(secret_name="app/ai/agent/devops-outreach"):
    try:
        secret_response = secrets_client.get_secret_value(SecretId=secret_name)
        secret_data = json.loads(secret_response["SecretString"])
        return secret_data["PERPLEXITY_API_KEY"]
    except ClientError as e:
        print(f"❌ Failed to fetch API key from Secrets Manager: {e}")
        raise

# Perplexity API
PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"
PERPLEXITY_API_KEY = get_perplexity_api_key()

class AnswerFormat(BaseModel):
    company_name: str
    company_website: str
    company_info: str

def load_seen_websites():
    seen = set()
    try:
        response = table.scan(ProjectionExpression="company_website")
        for item in response.get('Items', []):
            seen.add(item["company_website"].strip())
    except ClientError as e:
        print(f"⚠️ Error reading from DynamoDB: {e}")
    return seen

def fetch_target_companies(model="sonar-medium-online", num_companies=15):
    seen = load_seen_websites()
    exclude_clause = "".join(f"- {url}\n" for url in sorted(seen)) if seen else ""

    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a market intelligence assistant for a DevOps consultant. Your job is to identify companies that have either worked with consultants in the past or are currently hiring for DevOps, Platform Engineering, or Cloud Infrastructure roles. "
                    "Only include companies with credible public signals (LinkedIn, Crunchbase, GitHub, blogs, job listings, etc). "
                    "Focus on companies under 1000 employees and only in USA, UK, EU, Canada, Australia, or New Zealand. Never include companies from India. "
                    "Return only valid JSON list of objects with keys: 'company_name', 'company_website', and 'company_info'."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Give me a list of {num_companies} companies (with website) that either (a) have hired DevOps consultants recently, "
                    "or (b) are advertising for platform/cloud/infrastructure engineers. Aim for companies that are growing, "
                    "scaling, or cloud-mature enough to benefit from external help. "
                    "Only include if verifiable via public signals like LinkedIn jobs, hiring pages, Crunchbase, GitHub or blog activity. "
                    "Do not include companies that are too small (less than 10 employees) or too large (over 1000 employees). "
                    "For example, do not include companies like Docker, RedHat, IBM, Atlassian, or any large well-known companies."
                    "Restrict results to companies headquartered in the USA, UK, EU, Canada, Australia, or New Zealand. "
                    "Never include companies from India."
                    "Do not include any of the following websites:\n" + exclude_clause +
                    "Return in valid JSON format as a list of objects with keys: 'company_name', 'company_website' and 'company_info'."
                )
            }
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {"schema": AnswerFormat.model_json_schema()},
        },
    }

    response = requests.post(PERPLEXITY_API_URL, headers=headers, json=payload)
    response.raise_for_status()
    data = response.json()

    try:
        content = data["choices"][0]["message"]["content"]
        company_data = json.loads(content)
    except Exception as e:
        raise ValueError(f"❌ Failed to parse Perplexity response: {e}")

    new_companies = []
    for entry in company_data:
        if entry["company_website"] not in seen:
            try:
                table.put_item(
                    Item={
                        "company_website": entry["company_website"],
                        "company_name": entry["company_name"],
                        "company_info": entry["company_info"]
                    },
                    ConditionExpression="attribute_not_exists(company_website)"
                )
                print(f"✅ Added company: {entry['company_name']}")
                new_companies.append(entry)
            except ClientError as e:
                if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                    print(f"⚠️ Duplicate website detected: {entry['company_website']}")
                else:
                    print(f"❌ Error writing to DynamoDB: {e}")

    return new_companies

def lambda_handler(event, context):
    new_companies = fetch_target_companies()

    websites = [c["company_website"] for c in new_companies]

    return {
        "statusCode": 200,
        "websites": websites,
        "body": json.dumps({
            "message": "Perplexity targets fetched and stored.",
            "new_companies_count": len(new_companies),
            "websites": websites
        })
    }
