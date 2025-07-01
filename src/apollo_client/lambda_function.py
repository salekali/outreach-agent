import json
import boto3
import requests
from botocore.exceptions import ClientError

# DynamoDB and Secrets Manager clients
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("devops-outreach-db")
secrets_client = boto3.client("secretsmanager")

# Fetch Apollo API key from AWS Secrets Manager
def get_apollo_api_key(secret_name="app/ai/agent/devops-outreach"):
    try:
        secret_response = secrets_client.get_secret_value(SecretId=secret_name)
        secret_data = json.loads(secret_response["SecretString"])
        return secret_data["APOLLO_API_KEY"]
    except ClientError as e:
        print(f"❌ Failed to fetch Apollo API key: {e}")
        raise

# Apollo configuration
APOLLO_ENDPOINT = "https://api.apollo.io/v1/mixed_people/search"
APOLLO_API_KEY = get_apollo_api_key()

def search_contacts(company_name=None, company_website=None, titles=None, limit=4):
    headers = {
        "Cache-Control": "no-cache",
        "Content-Type": "application/json",
        "x-api-key": APOLLO_API_KEY,
    }

    params = {
        "person_titles": titles or [
            "CTO", "VP Engineering", "Director of DevOps",
            "Head of Platform", "Infrastructure Manager"
        ],
        "person_titles_include_variants": True,
        "page": 1,
        "per_page": limit,
    }

    if company_website:
        params["q_organization_domains"] = company_website
    elif company_name:
        params["q_organization_names"] = company_name
    else:
        raise ValueError("You must provide either company_name or company_website")

    try:
        res = requests.get(APOLLO_ENDPOINT, headers=headers, params=params)
        res.raise_for_status()
        data = res.json()
        people = data.get("people", [])

        contacts = []
        for person in people:
            email = person.get("email") if person.get("email_status") == "verified" else ""
            contacts.append({
                "name": f"{person.get('first_name', '')} {person.get('last_name', '')}".strip(),
                "title": person.get("title", ""),
                "email": email,
            })

        return contacts

    except Exception as e:
        print(f"[Apollo] ❌ Failed to fetch contacts for {company_name or company_website}: {e}")
        return []

def lambda_handler(event, context):
    try:
        websites = event.get("websites", [])
    except Exception as e:
        print(f"❌ Error parsing event detail: {e}")
        return {"statusCode": 400, "body": "Invalid event format"}

    if not websites:
        return {"statusCode": 200, "body": json.dumps({"message": "No websites provided."})}

    updated = []
    for website in websites:
        try:
            response = table.get_item(Key={"company_website": website})
            item = response.get("Item")

            if not item:
                print(f"⚠️ No record found in DynamoDB for {website}")
                continue

            contacts = search_contacts(company_website=website)

            if contacts:
                table.update_item(
                    Key={"company_website": website},
                    UpdateExpression="SET contacts = :c",
                    ExpressionAttributeValues={":c": contacts}
                )
                updated.append({"company": website, "contact_count": len(contacts)})
                print(f"✅ Added {len(contacts)} contacts to {website}")

        except ClientError as e:
            print(f"❌ DynamoDB error for {website}: {e}")

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Contact discovery complete.",
            "updated_companies": updated
        })
    }
