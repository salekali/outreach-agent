# src/perplexity_targets.py
import csv
import os
import json
import re
from pathlib import Path
import requests

SEEN_PATH = Path("data/rankings.csv")
PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"

REQUIRED_KEYS = {"company_name", "company_website", "company_info"}


def load_seen_companies():
    if not SEEN_PATH.exists():
        return set()
    with open(SEEN_PATH, "r") as f:
        reader = csv.DictReader(f)
        return set(row["company_name"] for row in reader)

def extract_json(text):
    match = re.search(r'(\[\s*{.*?}\s*\])', text, re.DOTALL)
    if not match:
        raise ValueError("No valid JSON block found in the response.")
    return json.loads(match.group(1))

def validate_company_list(company_data):
    if not isinstance(company_data, list):
        raise ValueError("Expected a list of company objects.")
    for entry in company_data:
        if not REQUIRED_KEYS <= entry.keys():
            raise ValueError(f"Entry missing required keys: {entry}")

def fetch_target_companies(limit=15, model="sonar-deep-research", num_companies=15):
    seen = load_seen_companies()
    exclude_clause = "".join(f"- {name}\n" for name in sorted(seen)) if seen else ""

    headers = {
        "Authorization": f"Bearer {os.getenv('PERPLEXITY_API_KEY')}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a market intelligence assistant for a DevOps consultant. Your job is to identify companies that have either worked with consultants in the past or are currently hiring for DevOps, Platform Engineering, or Cloud Infrastructure roles. "
                    "Only include companies with credible public signals (LinkedIn, Crunchbase, GitHub, blogs, job listings, etc). Output only valid JSON with objects containing 'company_name' and 'company_website'."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Give me a list of {num_companies} companies (with website) that either (a) have hired DevOps consultants recently, "
                    "or (b) are advertising for platform/cloud/infrastructure engineers. Aim for companies that are growing, "
                    "scaling, or cloud-mature enough to benefit from external help. "
                    "Only include if verifiable via public signals like LinkedIn jobs, hiring pages, Crunchbase, GitHub or blog activity. "
                    "Do not include any of the following companies:\n" + exclude_clause +
                    "Return in valid JSON format as a list of objects with keys: 'company_name', 'company_website' and 'company_info'."
                )
            }
        ]
    }

    response = requests.post(PERPLEXITY_API_URL, headers=headers, json=payload)
    response.raise_for_status()
    data = response.json()

    try:
        content = data["choices"][0]["message"]["content"]
        company_data = extract_json(content)
        validate_company_list(company_data)
    except Exception as e:
        raise ValueError(f"Failed to parse or validate Perplexity response: {e}")

    raw_companies = [
        (entry["company_name"], entry["company_website"], entry["company_info"])
        for entry in company_data
    ]

    new_companies = [(n, u) for n, u in raw_companies if n not in seen][:limit]
    return new_companies
