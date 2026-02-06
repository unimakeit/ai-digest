#!/usr/bin/env python3
"""
AI Digest - Generate Substack article markdown
"""

import json
import sys
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = Path(__file__).parent
SKILL_DIR = SCRIPT_DIR.parent
OUTPUT_DIR = SKILL_DIR / "output"

CATEGORY_META = {
    'ai_news': {'name': 'AI News', 'emoji': '📰', 'tagline': 'What happened today'},
    'ai_discourse': {'name': 'AI Discourse', 'emoji': '💬', 'tagline': 'What people are debating'},
    'model_releases': {'name': 'Model Release', 'emoji': '🤖', 'tagline': 'What you can try'},
    'ai_tools': {'name': 'AI Tool', 'emoji': '🛠️', 'tagline': 'What you can use'},
    'product_hunt': {'name': 'Product Hunt', 'emoji': '🚀', 'tagline': "What's launching"},
    'ai_papers': {'name': 'AI Paper', 'emoji': '📄', 'tagline': "What's being discovered"},
    'ai_funding': {'name': 'AI Funding', 'emoji': '💰', 'tagline': 'Where money flows'},
    'github_repos': {'name': 'GitHub Repo', 'emoji': '🔥', 'tagline': 'What to explore'},
}

CATEGORY_ORDER = ['ai_news', 'ai_discourse', 'model_releases', 'ai_tools', 
                  'product_hunt', 'ai_papers', 'ai_funding', 'github_repos']


def format_date(date_str):
    """Format date for display."""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return dt.strftime("%B %d, %Y")


def generate_article(date_str=None):
    """Generate Substack article markdown."""
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")
    
    data_file = OUTPUT_DIR / date_str / "data.json"
    if not data_file.exists():
        print(f"Error: No data file found for {date_str}")
        sys.exit(1)
    
    with open(data_file) as f:
        data = json.load(f)
    
    selected = data.get('selected', {})
    categories = data.get('categories', {})
    
    formatted_date = format_date(date_str)
    
    # Build article
    lines = []
    
    # Title
    lines.append(f"# AI Digest: {formatted_date}")
    lines.append("")
    lines.append("*The 8 things you need to know in AI today.*")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Each category
    num = 1
    for cat in CATEGORY_ORDER:
        if cat not in selected:
            continue
        
        item = selected[cat]
        meta = CATEGORY_META.get(cat, {'name': cat, 'emoji': '📌', 'tagline': ''})
        
        lines.append(f"## {num}. {meta['emoji']} {meta['name']}")
        lines.append(f"*{meta['tagline']}*")
        lines.append("")
        lines.append(f"### [{item['title']}]({item['url']})")
        lines.append("")
        
        if item.get('description'):
            lines.append(item['description'])
            lines.append("")
        
        # Add runner-ups if available
        cat_items = categories.get(cat, [])
        if len(cat_items) > 1:
            lines.append("**Also trending:**")
            for runner in cat_items[1:4]:  # Next 3
                lines.append(f"- [{runner['title']}]({runner['url']})")
            lines.append("")
        
        lines.append("---")
        lines.append("")
        num += 1
    
    # Footer
    lines.append("## 📬 Stay Updated")
    lines.append("")
    lines.append("Subscribe to get daily AI insights delivered to your inbox.")
    lines.append("")
    lines.append("*Curated by AI Digest — your daily radar on what matters in AI.*")
    
    article = "\n".join(lines)
    
    # Save
    output_file = OUTPUT_DIR / date_str / "substack.md"
    with open(output_file, 'w') as f:
        f.write(article)
    
    print(f"✅ Substack article saved to {output_file}")
    print(f"\nPreview:\n{'='*60}")
    print(article[:2000])
    if len(article) > 2000:
        print("\n... [truncated]")
    
    return article


if __name__ == "__main__":
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    generate_article(date_arg)
