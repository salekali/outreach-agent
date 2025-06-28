import os
import json
import csv
from anthropic import Anthropic

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
client = Anthropic(api_key=ANTHROPIC_API_KEY)

RANKINGS_PATH = "data/rankings.json"

def rank_company(company_name, company_website, company_info, model):
    prompt = (
        f"Company: {company_name}\n"
        f"Website: {company_website}\n\n"
        "Evaluate whether this company is a good lead for DevOps consulting based on its public signals.\n"
        "Consider factors like recent hiring for DevOps roles, history of using consultants, product complexity, and any recent funding or growth signals.\n"
        "Provide a score from 0 to 100, a brief rationale, and the date ranked.\n\n"
        "Format your response as a JSON object with the following keys:\n"
        f"company_name: {company_name}\n"
        f"company_website: {company_website}\n"
        f"company_info: {company_info}\n"
        "signal_summary: A brief summary of the signals considered\n"
        "score: The score from 0 to 100\n"
        "rationale: A one-line explanation of the score\n"
        "date_ranked: The date the company was ranked in YYYY-MM-DD format\n\n"
        "Example response:\n"
        '{"company_name": "Example Corp", "company_website": "https://example.com", '
        '"company_info": "Example Corp is a leading provider of cloud solutions with a focus on DevOps and automation.", '
        '"signal_summary": "Hiring DevOps engineers on LinkedIn, raised Series A funding", '
        '"score": 85, "rationale": "Strong hiring signals and recent funding",'
        '"date_ranked": "2023-10-01"}\n\n'
        "Only return the JSON object. Do not include any explanatory text, markdown formatting, or commentary."
    )

    response = client.messages.create(
        model=model,
        max_tokens=1024,
        temperature=0.5,
        system="You are a DevOps market analyst.",
        messages=[
            {"role": "user", "content": prompt}
        ],
    )

    content = response.content[0].text
    try:
        data = json.loads(content)
        assert set(data.keys()) >= {
            "company_name",
            "company_website",
            "company_info",
            "signal_summary",
            "score",
            "rationale",
            "date_ranked",
        }, "Missing required fields in response"
    except Exception as e:
        raise ValueError(f"Invalid JSON from Claude or parsing failed: {e}")

    return data



def save_rankings_csv(rankings):
    if not rankings:
        return
    os.makedirs(os.path.dirname(RANKINGS_PATH), exist_ok=True)
    with open(RANKINGS_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rankings[0].keys())
        writer.writeheader()
        writer.writerows(rankings)


def rank_companies(companies, model="claude-3-sonnet-20240229"):
    results = []
    for name, url, info in companies:
        result = rank_company(name, url, info, model)
        results.append(result)
    save_rankings_csv(rankings=results)
    return results
