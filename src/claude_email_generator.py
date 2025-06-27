# src/claude_email_generator.py
import os
import anthropic

CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")

client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)


def generate_email_variants(company_name, contacts):
    if not contacts:
        return ["No contacts found."]

    consultant_bio = (
        "You are a results-oriented DevOps consultant with over 8 years of experience helping companies modernize "
        "and scale their cloud infrastructure. You specialize in AWS, Kubernetes, Terraform, and CI/CD automation, "
        "and have deep technical expertise backed by a PhD in distributed systems. You've led high-impact projects "
        "for both startups and government agencies—building secure landing zones, optimizing EKS deployments, and "
        "implementing developer workflows that reduce costs and accelerate time to value. You're known for delivering "
        "real business outcomes with clear communication, strategic thinking, and technical precision."
    )

    contact_names_titles = [
        f"{c.get('full_name')} ({c.get('title')})" for c in contacts if c.get("full_name") and c.get("title")
    ]
    recipient_summary = ", ".join(contact_names_titles[:3])

    prompt = (
        f"{consultant_bio}\n\n"
        f"You're reaching out to: {company_name}\n"
        f"Relevant contacts: {recipient_summary}\n\n"
        "Write 3 short cold email variants in Australian English (80–120 words). Each should:\n"
        "- Be friendly, confident, and human\n"
        "- Briefly introduce yourself and what you offer\n"
        "- Mention how you can help companies like this\n"
        "- End with a soft call to action like 'Would it make sense to connect?'\n\n"
        "Avoid buzzwords. Use plain English. No markdown or bullet points."
    )

    message = client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=1000,
        temperature=0.7,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    outputs = message.content[0].text.strip().split("\n\n")
    variants = [o.strip() for o in outputs if len(o.strip()) > 20]
    return variants[:3]
