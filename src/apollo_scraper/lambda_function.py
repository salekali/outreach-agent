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
APOLLO_PEOPLE_SEARCH_ENDPOINT = "https://api.apollo.io/v1/mixed_people/search"
APOLLO_PEOPLE_ENRICHMENT_ENDPOINT = "https://api.apollo.io/api/v1/people/match"
APOLLO_API_KEY = get_apollo_api_key()

def search_contacts(company_website=None, limit=4):
    headers = {
        "Cache-Control": "no-cache",
        "Content-Type": "application/json",
        "x-api-key": APOLLO_API_KEY,
    }

    # get company domain from website
    if company_website:
        if company_website.startswith("https://"):
            company_website = company_website.split("https://")[-1]
        elif company_website.startswith("http://"):
            company_website = company_website.split("http://")[-1]
        if "/" in company_website:
            company_website = company_website.split("/")[0]
        if "www." in company_website:
            company_website = company_website.replace("www.", "")
    else:
        print("[Apollo] ❌ No company website provided.")
        return []

    params = {
        "person_seniorities[]": [ "c_suite", "partner", "vp", "head", "director" ],
        "person_titles_include_variants": True,
        "page": 1,
        "per_page": limit,
        "q_organization_domains_list[]": [company_website]
    }

    try:
        res = requests.get(APOLLO_PEOPLE_SEARCH_ENDPOINT, headers=headers, params=params)
        res.raise_for_status()
        data = res.json()
        people = data.get("people", [])

        contacts = []
        for person in people:
            contact = {
                "name": person.get("name", ""),
                "title": person.get("title", ""),
                "linkedin_url": person.get("linkedin_url", ""),
                "seniority": person.get("seniority", ""),
            }

            res_contact = requests.get(
                APOLLO_PEOPLE_ENRICHMENT_ENDPOINT,
                headers=headers,
                params={"person_id": person.get("id")}
            )
            res_contact.raise_for_status()
            res_contact = res_contact.json()
            email = res_contact.get("person").get("email", None)
            contact["email"] = email if email else "No email found"

            contacts.append(contact)
        return contacts

    except Exception as e:
        print(f"[Apollo] ❌ Failed to fetch contacts for {company_website}: {e}")
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
            "updated_companies": updated,
            "websites": websites
        })
    }
