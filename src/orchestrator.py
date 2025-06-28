from src.perplexity_targets import fetch_target_companies
from src.company_ranker import rank_companies
from src.apollo_client import search_contacts
from src.claude_email_generator import generate_email_variants
from src.slack_notifier import send_to_slack
from src.utils import load_settings


def run_outreach_cycle(logger):
    logger.info("🔧 Loading settings...")
    settings = load_settings()

    logger.info("🔍 Finding target companies...")
    perplexity_model = settings["perplexity"]["model"]
    num_companies = settings["perplexity"]["num_companies"]
    companies = fetch_target_companies(model=perplexity_model, num_companies=num_companies)

    logger.info("📊 Ranking companies...")
    company_ranker_model = settings["company_ranker"]["model"]
    ranked = rank_companies(companies, model=company_ranker_model)

    for entry in ranked:
        company_name = entry["company_name"]
        website = entry["company_website"]
        company_info = entry.get("company_info", "No additional info available")

        logger.info(f"🔗 Finding contacts for {company_name}...")
        titles = settings["apollo"]["titles"]
        limit = settings["apollo"]["limit"]
        contacts = search_contacts(company_name, website, titles, limit)

        logger.info(f"✉️ Generating outreach emails for {company_name}...")
        email_model = settings["email_generator"]["model"]
        emails = generate_email_variants(company_name, contacts, model=email_model)

        logger.info(f"📨 Sending summary to Slack for {company_name}...")
        send_to_slack(company_name, website, company_info, entry["score"], entry["rationale"], contacts, emails)
