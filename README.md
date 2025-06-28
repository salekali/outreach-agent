content = """

# Outreach AI Agent

## 📚 Overview

This project automates the discovery, qualification, and outreach to potential DevOps consulting clients using AI-powered agents. It combines Perplexity (for target company research), Claude (for lead scoring and cold email generation), and Apollo.io (for contact enrichment), while posting results and email drafts to Slack for your review.

---

## 🚀 Features

✅ **Target Discovery:**
Uses Perplexity's `sonar-deep-research` model to find 15 new companies daily hiring for cloud/DevOps roles or with prior consulting history.

✅ **Lead Scoring:**
Uses Claude Sonnet to rank companies 0–100 based on hiring signals, consulting history, funding, and more. Produces rationale and signal summary.

✅ **Contact Enrichment:**
Fetches verified contacts (CTO, VP Eng, Platform Leads) using Apollo.io's API by company domain or name.

✅ **Cold Email Generation:**
Uses Claude Opus + your CV to generate 3 short, friendly outreach emails tailored to the target company and contact profile.

✅ **Slack Notification:**
Posts company summary, score, contacts, and email variants to a Slack channel via Incoming Webhooks.

✅ **Secrets Management:**
Uses SOPS + age to encrypt and manage API keys and secrets safely in `config/.env.enc`.

---

## 🛠️ Setup

### 1️⃣ Install Dependencies

```bash
brew install sops age
make install
```

### 2️⃣ Generate Age Key

```bash
mkdir -p ~/.config/sops/age
age-keygen -o ~/.config/sops/age/keys.txt
```

Copy the generated public key (age1...) into your ~/.sops.yaml:

```yaml
creation_rules:
  - path_regex: '.*'
    age:
      - age1yourpublickeyhere
```

### 3️⃣ Create Secrets

Add:

```bash
CLAUDE_API_KEY=your_key
PERPLEXITY_API_KEY=your_key
APOLLO_API_KEY=your_key
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```


To your `config/.env` file. This file will be encrypted with SOPS.

```bash
make encrypt
```

## ▶️ Running the Agent

Run manually with decrypted env vars:

```bash
make decrypt
make run
```

## 🔥 Notes

rankings.csv is the canonical source of leads scored and processed.

Slack messages include score, rationale, contacts, and 3 outreach email variants.

Uses Perplexity's sonar-deep-research model by default (configured in config/settings.yaml).
## 🔒 Security

Secrets are encrypted with SOPS using your local age key.

Do not commit decrypted .env files to git.

Add this to .gitignore:
```gitignore
.env
*.env
__pycache__/
*.

pyc
venv/
```
## 📬 Future Enhancements

Schedule as daily cron or systemd job

Auto-send first email via SMTP or Mailgun

Deduplicate contacts using CRM integration

Interactive Slack buttons to mark leads as contacted
## 📝 License

MIT

For help, improvements, or custom flows — drop your notes in issues or contact Salek directly.
