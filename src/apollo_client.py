import os
import requests

APOLLO_API_KEY = os.getenv("APOLLO_API_KEY")
APOLLO_ENDPOINT = "https://api.apollo.io/v1/mixed_people/search"

def search_contacts(company_name=None, company_website=None, titles=None, limit=3):
    """
    Search for decision-makers at a given company using Apollo.io
    """

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

        results = []
        for person in people:
            results.append({
                "name": f"{person.get('first_name', '')} {person.get('last_name', '')}".strip(),
                "email": person.get("email_status") == "verified" and person.get("email") or "",
                "title": person.get("title", ""),
                "linkedin_url": person.get("linkedin_url", "")
            })

        return results

    except Exception as e:
        print(f"[Apollo] Failed to fetch contacts for {company_name}: {e}")
        return []
