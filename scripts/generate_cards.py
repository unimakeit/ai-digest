#!/usr/bin/env python3
"""
AI Digest - Generate carousel cards using HTML templates + Chrome headless
Outputs: 1080x1350 PNG cards (4:5 ratio for Instagram/social)
"""

import json
import os
import sys
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse
import html

# Paths
SCRIPT_DIR = Path(__file__).parent
SKILL_DIR = SCRIPT_DIR.parent
OUTPUT_DIR = SKILL_DIR / "output"
TEMPLATES_DIR = SKILL_DIR / "templates"

# Card dimensions (4:5 ratio)
WIDTH = 1080
HEIGHT = 1350

# Chrome path (macOS)
CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# Category config
CATEGORIES = {
    'ai_news': {'name': 'AI NEWS', 'emoji': '📰', 'name_v2': 'AI News'},
    'ai_discourse': {'name': 'AI DISCOURSE', 'emoji': '💬', 'name_v2': 'AI Discourse'},
    'model_releases': {'name': 'MODEL RELEASE', 'emoji': '🤖', 'name_v2': 'Model Release'},
    'ai_tools': {'name': 'AI TOOL', 'emoji': '🛠️', 'name_v2': 'AI Tools'},
    'product_hunt': {'name': 'PRODUCT HUNT', 'emoji': '🚀', 'name_v2': 'Product Hunt'},
    'ai_papers': {'name': 'AI PAPER', 'emoji': '📄', 'name_v2': 'AI Papers'},
    'ai_funding': {'name': 'AI FUNDING', 'emoji': '💰', 'name_v2': 'AI Funding'},
    'github_repos': {'name': 'GITHUB REPO', 'emoji': '🔥', 'name_v2': 'GitHub Repos'},
}

# Template version (v1 = original, v2 = tech-noir, v3 = swiss, v4 = content-first, v5 = dark-editorial)
TEMPLATE_VERSION = 'v5'

# Category order
CATEGORY_ORDER = [
    'ai_news', 'ai_discourse', 'model_releases', 'ai_tools',
    'product_hunt', 'ai_papers', 'ai_funding', 'github_repos'
]


def render_html_to_png(html_content: str, output_path: Path) -> bool:
    """Render HTML to PNG using Chrome headless."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
        f.write(html_content)
        html_path = f.name
    
    try:
        cmd = [
            CHROME_PATH,
            '--headless=new',
            '--disable-gpu',
            '--disable-software-rasterizer',
            f'--screenshot={output_path}',
            f'--window-size={WIDTH},{HEIGHT}',
            '--hide-scrollbars',
            '--default-background-color=00000000',
            f'file://{html_path}'
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        return output_path.exists()
    except Exception as e:
        print(f"  ⚠️  Chrome render error: {e}")
        return False
    finally:
        os.unlink(html_path)


def load_template(name: str) -> str:
    """Load an HTML template."""
    template_path = TEMPLATES_DIR / f"{name}.html"
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")
    return template_path.read_text()


def escape_html(text: str, preserve_newlines: bool = False) -> str:
    """Escape HTML special characters, optionally preserving newlines as <br>."""
    if not text:
        return ''
    escaped = html.escape(text)
    if preserve_newlines:
        escaped = escaped.replace('\n', '<br>')
    return escaped


def truncate(text: str, max_len: int) -> str:
    """Truncate text with ellipsis."""
    if not text:
        return ''
    if len(text) <= max_len:
        return text
    return text[:max_len-3].rsplit(' ', 1)[0] + '...'


def create_content_card(category: str, item: dict, date_str: str, card_num: int, version: str = None) -> str:
    """Create HTML for a content card."""
    ver = version or TEMPLATE_VERSION
    template_map = {'v1': 'card', 'v2': 'card_v2', 'v3': 'card_v3', 'v4': 'card_v4', 'v5': 'card_v5'}
    template_name = template_map.get(ver, 'card_v5')
    template = load_template(template_name)
    config = CATEGORIES.get(category, {'name': category.upper(), 'emoji': '📌', 'name_v2': category.title()})
    
    # Extract domain from URL
    url = item.get('url', '')
    try:
        domain = urlparse(url).netloc.replace('www.', '')
    except:
        domain = url[:40] if url else 'unknown'
    
    # Prepare content - allow longer descriptions
    title = truncate(item.get('title', 'Unknown'), 150)
    description = item.get('description', '')  # Don't truncate bullet points
    
    # Category name based on version
    cat_name = config['name'] if ver == 'v1' else config.get('name_v2', config['name'])
    
    # Replace placeholders
    html_content = template.replace('{{CATEGORY}}', category)
    html_content = html_content.replace('{{NUMBER}}', str(card_num))
    html_content = html_content.replace('{{EMOJI}}', config['emoji'])
    html_content = html_content.replace('{{CATEGORY_NAME}}', cat_name)
    html_content = html_content.replace('{{TITLE}}', escape_html(title))
    html_content = html_content.replace('{{DESCRIPTION}}', escape_html(description, preserve_newlines=True))
    html_content = html_content.replace('{{DOMAIN}}', escape_html(domain))
    html_content = html_content.replace('{{DATE}}', date_str)
    
    return html_content


def create_intro_card(date_str: str, version: str = None) -> str:
    """Create HTML for the intro card."""
    ver = version or TEMPLATE_VERSION
    template_map = {'v1': 'intro', 'v2': 'intro_v2', 'v3': 'intro_v3', 'v4': 'intro_v4', 'v5': 'intro_v5'}
    template_name = template_map.get(ver, 'intro_v5')
    template = load_template(template_name)
    
    # Format date nicely
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        formatted_date = dt.strftime('%B %d, %Y')
    except:
        formatted_date = date_str
    
    return template.replace('{{DATE}}', formatted_date)


def create_cta_card(substack_url: str = "ai-digest.substack.com", version: str = None) -> str:
    """Create HTML for the CTA card."""
    ver = version or TEMPLATE_VERSION
    template_map = {'v1': 'cta', 'v2': 'cta_v2', 'v3': 'cta_v3', 'v4': 'cta_v4', 'v5': 'cta_v5'}
    template_name = template_map.get(ver, 'cta_v5')
    template = load_template(template_name)
    return template.replace('{{SUBSTACK_URL}}', substack_url)


def generate_all_cards(date_str: str = None, include_intro: bool = True, include_cta: bool = True, version: str = None):
    """Generate all carousel cards for a given date."""
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")
    
    ver = version or TEMPLATE_VERSION
    print(f"📐 Using template version: {ver}")
    
    data_file = OUTPUT_DIR / date_str / "data.json"
    if not data_file.exists():
        print(f"Error: No data file found for {date_str}")
        print(f"Run fetch_all.py first")
        sys.exit(1)
    
    with open(data_file) as f:
        data = json.load(f)
    
    selected = data.get('selected', {})
    if not selected:
        print("Error: No selected items in data")
        sys.exit(1)
    
    # Output directory for cards
    cards_dir = OUTPUT_DIR / date_str / "carousel"
    cards_dir.mkdir(parents=True, exist_ok=True)
    
    created = []
    card_num = 0
    
    # Intro card
    if include_intro:
        card_num += 1
        print(f"🎨 Creating card {card_num}: intro")
        html_content = create_intro_card(date_str, ver)
        card_path = cards_dir / f"{card_num:02d}_intro.png"
        if render_html_to_png(html_content, card_path):
            created.append(str(card_path))
            print(f"  ✓ Saved {card_path.name}")
        else:
            print(f"  ✗ Failed to render intro card")
    
    # Content cards
    for category in CATEGORY_ORDER:
        if category not in selected:
            print(f"⚠️  Skipping {category} (no data)")
            continue
        
        card_num += 1
        item = selected[category]
        print(f"🎨 Creating card {card_num}: {category}")
        
        # For content cards, number shows position (after intro if present)
        display_num = card_num if not include_intro else card_num - 1
        html_content = create_content_card(category, item, date_str, display_num, ver)
        card_path = cards_dir / f"{card_num:02d}_{category}.png"
        
        if render_html_to_png(html_content, card_path):
            created.append(str(card_path))
            print(f"  ✓ Saved {card_path.name}")
        else:
            print(f"  ✗ Failed to render {category} card")
    
    # CTA card
    if include_cta:
        card_num += 1
        print(f"🎨 Creating card {card_num}: cta")
        html_content = create_cta_card(version=ver)
        card_path = cards_dir / f"{card_num:02d}_cta.png"
        if render_html_to_png(html_content, card_path):
            created.append(str(card_path))
            print(f"  ✓ Saved {card_path.name}")
        else:
            print(f"  ✗ Failed to render CTA card")
    
    print(f"\n✅ Created {len(created)} cards in {cards_dir}")
    return created


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate AI Digest carousel cards')
    parser.add_argument('date', nargs='?', help='Date (YYYY-MM-DD), default: today')
    parser.add_argument('--no-intro', action='store_true', help='Skip intro card')
    parser.add_argument('--no-cta', action='store_true', help='Skip CTA card')
    parser.add_argument('--version', '-v', choices=['v1', 'v2', 'v3', 'v4', 'v5'], default=None,
                        help='Template version (v1=original, v2=tech-noir, v3=swiss, v4=content-first, v5=dark-editorial). Default: v5')
    
    args = parser.parse_args()
    
    generate_all_cards(
        date_str=args.date,
        include_intro=not args.no_intro,
        include_cta=not args.no_cta,
        version=args.version
    )
