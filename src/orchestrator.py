from src.perplexity_targets import get_company_targets
from src.company_ranker import rank_companies
from src.apollo_client import find_contacts
from src.claude_email_generator import generate_email_variants
from src.slack_notifier import send_to_slack


def run():
    print("🔍 Finding target companies...")
    companies = get_company_targets()

    print("📊 Ranking companies...")
    ranked = rank_companies(companies)

    for entry in ranked:
        name = entry["company_name"]
        website = entry["company_website"]

        print(f"🔗 Finding contacts for {name}...")
        contacts = find_contacts(domain=website)

        print(f"✉️ Generating outreach emails for {name}...")
        emails = generate_email_variants(name, contacts)

        print(f"📨 Sending summary to Slack for {name}...")
        send_to_slack(name, website, entry["score"], entry["rationale"], contacts, emails)


if __name__ == "__main__":
    run()
