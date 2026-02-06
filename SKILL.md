---
name: ai-digest
description: Daily AI digest system. Fetches trending content from 8 categories (AI News, AI Discourse, Model Releases, AI Tools, Product Hunt, AI Papers, AI Funding, GitHub Repos), selects the top item per category, enriches descriptions with AI, generates 4:5 carousel cards and a Substack article. Use for daily AI news curation, carousel generation, or Substack publishing.
---

# AI Digest

Daily curation system that surfaces the one thing you need to know across 8 AI categories.

## Quick Start

```bash
cd skills/ai-digest
source .venv/bin/activate

# Full pipeline
python scripts/run_daily.py

# Or step by step:
python scripts/fetch_all.py          # Fetch + enrich
python scripts/generate_cards.py     # Generate PNGs
python scripts/generate_substack.py  # Generate article
```

## Categories (in order)

1. 📰 **AI News** — Major announcements and developments
2. 💬 **AI Discourse** — Hot debates on HN, Reddit
3. 🤖 **Model Release** — New models on HuggingFace
4. 🛠️ **AI Tools** — Feature updates from AI tools
5. 🚀 **Product Hunt** — New AI product launches
6. 📄 **AI Papers** — Research from arXiv
7. 💰 **AI Funding** — Investment rounds
8. 🔥 **GitHub Repos** — Trending repositories

## Pipeline

### 1. Fetch & Enrich (`fetch_all.py`)

- Fetches from RSS feeds, APIs, and scraped sources
- Selects top item per category (dedup by title/URL)
- **Enriches descriptions with GPT-4o-mini**:
  - Generates 3 bullet points per item
  - Format: What happened → Why it matters → Takeaway
  - Requires `OPENAI_API_KEY` env var

### 2. Generate Cards (`generate_cards.py`)

- Renders HTML templates to PNG via Chrome headless
- Template version: **v5 (dark-editorial)**
  - Playfair Display serif headlines
  - JetBrains Mono for bullet points
  - Neon accent colors per category
  - 1080x1350 (4:5 ratio)

Options:
```bash
python scripts/generate_cards.py 2026-02-06         # Specific date
python scripts/generate_cards.py --no-intro         # Skip intro card
python scripts/generate_cards.py --version v4       # Use different template
```

### 3. Generate Substack (`generate_substack.py`)

Creates a markdown article with all 8 items expanded.

## Output Structure

```
output/YYYY-MM-DD/
├── data.json              # Raw + enriched data
├── carousel/
│   ├── 01_intro.png
│   ├── 02_ai_news.png
│   ├── ...
│   └── 10_cta.png
└── substack.md            # Article draft
```

## Templates

Located in `templates/`:
- `card_v5.html` — Dark editorial style (current)
- `intro_v5.html` — Cover card
- `cta_v5.html` — Subscribe call-to-action

Template versions:
- v1: Original Pillow-based
- v2: Tech-noir (first HTML)
- v3: Swiss International
- v4: Content-first (white)
- v5: **Dark editorial** (current default)

## Environment

Requires:
- Python 3.10+ with venv at `.venv/`
- Google Chrome (for headless rendering)
- `OPENAI_API_KEY` for description enrichment

## Cron

Scheduled daily at 8am CST (job: `ai-digest-daily`).

To run manually:
```bash
cd /Users/agent/.openclaw/workspace/skills/ai-digest
source .venv/bin/activate
python scripts/run_daily.py
```
