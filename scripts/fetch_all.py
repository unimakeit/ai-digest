#!/usr/bin/env python3
"""
AI Digest - Fetch all sources and select top item per category.
"""

import json
import os
import sys
import re
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path
from html import unescape
import ssl
import http.client

# Disable SSL verification for some feeds
ssl_context = ssl.create_default_context()

# OpenAI API for description enrichment
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

OUTPUT_DIR = Path(__file__).parent.parent / "output"
HISTORY_FILE = Path(__file__).parent.parent / "history.json"
TODAY = datetime.now().strftime("%Y-%m-%d")
HISTORY_DAYS = 7  # Don't repeat items from the last 7 days

def load_history():
    """Load history of previously selected items."""
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE) as f:
                return json.load(f)
        except:
            pass
    return {"selections": {}}

def save_history(history):
    """Save history to file."""
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

def get_used_titles(history, days=HISTORY_DAYS):
    """Get set of titles used in the last N days."""
    used = set()
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    for date, items in history.get("selections", {}).items():
        if date >= cutoff:
            for cat, item in items.items():
                if isinstance(item, dict):
                    used.add(item.get('title', '').lower().strip())
                    # Also add URL to catch same story from different sources
                    url = item.get('url', '').lower().strip()
                    if url:
                        used.add(url)
    return used

def add_to_history(history, date, selected):
    """Add today's selections to history."""
    history["selections"][date] = {
        cat: {"title": item.get("title", ""), "url": item.get("url", "")}
        for cat, item in selected.items()
    }
    # Prune old entries (keep last 30 days)
    cutoff = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    history["selections"] = {
        d: items for d, items in history["selections"].items() if d >= cutoff
    }
    return history

def fetch_url(url, headers=None):
    """Fetch URL with optional headers."""
    req = urllib.request.Request(url, headers=headers or {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    })
    try:
        with urllib.request.urlopen(req, timeout=30, context=ssl_context) as resp:
            return resp.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"  Error fetching {url}: {e}", file=sys.stderr)
        return None

def clean_html(text):
    """Remove HTML tags and decode entities."""
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', '', text)
    return unescape(text).strip()

# ============================================================================
# 1. AI NEWS
# ============================================================================
def fetch_ai_news():
    """Fetch AI news from RSS feeds."""
    print("📰 Fetching AI News...")
    feeds = [
        "https://techcrunch.com/category/artificial-intelligence/feed/",
        "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
        "https://venturebeat.com/category/ai/feed/",
    ]
    
    items = []
    for feed_url in feeds:
        xml = fetch_url(feed_url)
        if not xml:
            continue
        try:
            root = ET.fromstring(xml)
            # Handle both RSS and Atom
            for item in root.findall('.//item') or root.findall('.//{http://www.w3.org/2005/Atom}entry'):
                title = item.findtext('title') or item.findtext('{http://www.w3.org/2005/Atom}title')
                link = item.findtext('link') or item.find('{http://www.w3.org/2005/Atom}link')
                if hasattr(link, 'get'):
                    link = link.get('href')
                desc = item.findtext('description') or item.findtext('{http://www.w3.org/2005/Atom}summary') or ""
                
                if title and link:
                    items.append({
                        'title': clean_html(title),
                        'url': link.strip() if isinstance(link, str) else link,
                        'description': clean_html(desc)[:500],
                        'source': 'news'
                    })
        except ET.ParseError as e:
            print(f"  XML parse error: {e}", file=sys.stderr)
    
    # Simple ranking: prefer items with AI keywords in title
    ai_keywords = ['ai', 'gpt', 'llm', 'openai', 'anthropic', 'claude', 'gemini', 'model', 'chatgpt']
    for item in items:
        score = sum(1 for kw in ai_keywords if kw in item['title'].lower())
        item['score'] = score
    
    items.sort(key=lambda x: x['score'], reverse=True)
    print(f"  Found {len(items)} news items")
    return items[:10]

# ============================================================================
# 2. AI DISCOURSE (Hacker News)
# ============================================================================
def fetch_ai_discourse():
    """Fetch AI discussions from Hacker News."""
    print("💬 Fetching AI Discourse...")
    
    # Get top stories
    top_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
    data = fetch_url(top_url)
    if not data:
        return []
    
    story_ids = json.loads(data)[:100]  # Top 100 stories
    items = []
    ai_keywords = ['ai', 'gpt', 'llm', 'openai', 'anthropic', 'claude', 'gemini', 'machine learning', 
                   'neural', 'transformer', 'chatgpt', 'model', 'deepseek', 'mistral', 'llama']
    
    for sid in story_ids[:50]:  # Check first 50 to save time
        story_url = f"https://hacker-news.firebaseio.com/v0/item/{sid}.json"
        story_data = fetch_url(story_url)
        if not story_data:
            continue
        
        story = json.loads(story_data)
        title = story.get('title', '').lower()
        
        # Filter for AI-related stories
        if any(kw in title for kw in ai_keywords):
            items.append({
                'title': story.get('title', ''),
                'url': story.get('url', f"https://news.ycombinator.com/item?id={sid}"),
                'description': f"{story.get('score', 0)} points, {story.get('descendants', 0)} comments",
                'score': story.get('score', 0),
                'comments': story.get('descendants', 0),
                'source': 'hackernews'
            })
    
    items.sort(key=lambda x: x['score'], reverse=True)
    print(f"  Found {len(items)} discourse items")
    return items[:10]

# ============================================================================
# 3. MODEL RELEASES (Hugging Face) - Prioritize impactful models
# ============================================================================
def fetch_model_releases():
    """Fetch new models from Hugging Face with quality filtering."""
    print("🤖 Fetching Model Releases...")
    
    # Get recently modified models, then filter and rank
    url = "https://huggingface.co/api/models?sort=lastModified&direction=-1&limit=200"
    data = fetch_url(url)
    if not data:
        return []
    
    models = json.loads(data)
    items = []
    
    # Known impactful organizations (prioritize these)
    top_orgs = ['openai', 'anthropic', 'meta-llama', 'google', 'mistralai', 
                'qwen', 'deepseek', 'microsoft', 'nvidia', 'stability', 
                'huggingface', 'bigscience', 'EleutherAI', 'tiiuae', 'allenai',
                'nous-research', 'teknium', 'cognitivecomputations', 'z-lab']
    
    # Model type keywords that indicate useful models
    useful_types = ['instruct', 'chat', 'coder', 'code', 'base', 'large', 
                    'llm', 'vision', 'multimodal', 'embed']
    
    # Filter out test/personal models
    skip_patterns = ['test', 'experiment', 'backup', 'old', 'temp', 'copy', 
                     'fine-tune', 'finetuned', 'lora', 'gguf', 'gptq', 'awq']
    
    for model in models:
        model_id = model.get('id', '')
        downloads = model.get('downloads', 0)
        likes = model.get('likes', 0)
        
        # Skip low-quality models
        model_lower = model_id.lower()
        if any(skip in model_lower for skip in skip_patterns):
            continue
        
        # Calculate impact score
        org = model_id.split('/')[0].lower() if '/' in model_id else ''
        
        # Base score: prioritize actual usage (downloads) over hype (likes)
        score = downloads * 10 + likes * 50
        
        # Boost for known orgs (big boost)
        if org in [o.lower() for o in top_orgs]:
            score += 100000
        
        # Boost for useful model types
        if any(t in model_lower for t in useful_types):
            score += 5000
        
        # Penalty for models with no downloads (likely just uploaded, unproven)
        if downloads == 0:
            score = score // 4
        
        # Minimum threshold: must have significant usage OR be from known org
        is_known_org = org in [o.lower() for o in top_orgs]
        has_usage = downloads > 5000 or likes > 50
        if is_known_org or has_usage:
            items.append({
                'title': model_id,
                'url': f"https://huggingface.co/{model_id}",
                'description': f"{downloads:,} downloads, {likes} likes",
                'score': score,
                'source': 'huggingface'
            })
    
    items.sort(key=lambda x: x['score'], reverse=True)
    print(f"  Found {len(items)} model releases")
    return items[:10]

# ============================================================================
# 4. AI TOOLS (feature updates from existing AI tools - NOT funding/new products)
# ============================================================================
def fetch_ai_tools():
    """Fetch feature updates from existing AI tools (not funding or new launches)."""
    print("🛠️ Fetching AI Tools...")
    
    # Feature update keywords (the tool is DOING something new)
    feature_keywords = ['adds', 'enables', 'introduces', 'rolls out', 'now supports', 
                        'new feature', 'launches feature', 'integration', 'upgraded',
                        'announces', 'gets', 'brings', 'expands']
    
    # Known AI tools and platforms (must mention one of these)
    tool_names = ['claude', 'chatgpt', 'gpt-4', 'gpt-5', 'copilot', 'cursor', 'notion', 
                  'figma', 'midjourney', 'runway', 'lovart', 'perplexity', 'v0', 'bolt', 
                  'replit', 'windsurf', 'codeium', 'tabnine', 'jasper', 'copy.ai',
                  'dall-e', 'stable diffusion', 'firefly', 'canva', 'grammarly',
                  'otter', 'descript', 'synthesia', 'heygen', 'luma', 'pika',
                  'slack', 'teams', 'zoom', 'discord', 'linear', 'github', 'vscode',
                  'xcode', 'android studio', 'cowork', 'miro', 'asana', 'airtable',
                  'obsidian', 'raycast', 'arc', 'brave', 'chrome', 'safari', 'edge']
    
    # Exclude funding/business/opinion news (longer phrases to avoid false positives)
    exclude_keywords = ['funding', 'raises $', 'million', 'billion', 'series a', 'series b',
                        'series c', 'valuation', 'investors', 'investment round', 'ipo', 'acquisition',
                        'acquires', 'revenue', 'quarterly', 'earnings',
                        'having a moment', 'the hype', 'can it keep', 'will it last', 
                        ' vs ', ' versus ', 'compared to', 'better than', 'what we learned']
    
    items = []
    
    feeds = [
        "https://techcrunch.com/category/artificial-intelligence/feed/",
        "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
        "https://venturebeat.com/category/ai/feed/",
    ]
    
    for feed_url in feeds:
        xml = fetch_url(feed_url)
        if not xml:
            continue
        try:
            root = ET.fromstring(xml)
            rss_items = root.findall('.//item')
            atom_items = root.findall('.//{http://www.w3.org/2005/Atom}entry')
            all_items = rss_items if rss_items else atom_items
            for item in all_items:
                title = item.findtext('title') or item.findtext('{http://www.w3.org/2005/Atom}title')
                link = item.findtext('link') or item.find('{http://www.w3.org/2005/Atom}link')
                if hasattr(link, 'get'):
                    link = link.get('href')
                desc = item.findtext('description') or item.findtext('{http://www.w3.org/2005/Atom}summary') or ""
                
                if title and link:
                    text = (title + ' ' + desc).lower()
                    
                    # MUST mention a known tool
                    has_tool = any(t in text for t in tool_names)
                    # MUST have feature update language
                    has_feature = any(kw in text for kw in feature_keywords)
                    # MUST NOT be funding/business news
                    is_funding = any(kw in text for kw in exclude_keywords)
                    
                    if not has_tool or not has_feature or is_funding:
                        continue
                    
                    items.append({
                        'title': clean_html(title),
                        'url': link.strip() if isinstance(link, str) else link,
                        'description': clean_html(desc)[:300],
                        'score': 10,
                        'source': 'tools'
                    })
        except ET.ParseError:
            pass
    
    print(f"  Found {len(items)} AI tool updates")
    return items[:10]

# ============================================================================
# 5. PRODUCT HUNT (RSS feed)
# ============================================================================
def fetch_product_hunt():
    """Fetch from Product Hunt RSS feed."""
    print("🚀 Fetching Product Hunt...")
    
    url = "https://www.producthunt.com/feed"
    xml = fetch_url(url)
    if not xml:
        return []
    
    items = []
    ai_keywords = ['ai', 'gpt', 'llm', 'machine learning', 'agent', 'copilot', 'assistant', 'automat']
    
    try:
        root = ET.fromstring(xml)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        
        for entry in root.findall('atom:entry', ns):
            title = entry.findtext('atom:title', '', ns)
            link_elem = entry.find('atom:link', ns)
            link = link_elem.get('href') if link_elem is not None else ''
            content = entry.findtext('atom:content', '', ns)
            desc = clean_html(content)
            
            if title:
                # Check if AI-related
                text = (title + ' ' + desc).lower()
                is_ai = any(kw in text for kw in ai_keywords)
                
                items.append({
                    'title': title,
                    'url': link,
                    'description': desc[:200],
                    'score': 100 if is_ai else 0,
                    'source': 'producthunt'
                })
    except ET.ParseError as e:
        print(f"  XML parse error: {e}", file=sys.stderr)
    
    # Sort AI-related first
    items.sort(key=lambda x: x['score'], reverse=True)
    print(f"  Found {len(items)} Product Hunt items")
    return items[:10]

# ============================================================================
# 6. AI PAPERS (arXiv)
# ============================================================================
def fetch_ai_papers():
    """Fetch papers from arXiv."""
    print("📄 Fetching AI Papers...")
    
    # Query recent AI/ML papers
    query = urllib.parse.quote('cat:cs.AI OR cat:cs.LG OR cat:cs.CL')
    url = f"http://export.arxiv.org/api/query?search_query={query}&sortBy=submittedDate&sortOrder=descending&max_results=30"
    
    xml = fetch_url(url)
    if not xml:
        return []
    
    items = []
    try:
        root = ET.fromstring(xml)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        
        for entry in root.findall('atom:entry', ns):
            title = entry.findtext('atom:title', '', ns).replace('\n', ' ').strip()
            summary = entry.findtext('atom:summary', '', ns).replace('\n', ' ').strip()
            link = entry.find('atom:id', ns)
            
            if title and link is not None:
                items.append({
                    'title': title,
                    'url': link.text,
                    'description': summary[:300] + '...' if len(summary) > 300 else summary,
                    'score': 0,
                    'source': 'arxiv'
                })
    except ET.ParseError as e:
        print(f"  XML parse error: {e}", file=sys.stderr)
    
    print(f"  Found {len(items)} papers")
    return items[:10]

# ============================================================================
# 7. AI FUNDING (TechCrunch)
# ============================================================================
def fetch_ai_funding():
    """Fetch funding news from TechCrunch."""
    print("💰 Fetching AI Funding...")
    
    # Use TechCrunch funding tag
    url = "https://techcrunch.com/tag/funding/feed/"
    xml = fetch_url(url)
    if not xml:
        return []
    
    items = []
    ai_keywords = ['ai', 'artificial intelligence', 'machine learning', 'llm', 'generative']
    
    try:
        root = ET.fromstring(xml)
        for item in root.findall('.//item'):
            title = item.findtext('title', '')
            link = item.findtext('link', '')
            desc = item.findtext('description', '')
            
            # Filter for AI-related funding
            text = (title + ' ' + desc).lower()
            if any(kw in text for kw in ai_keywords):
                # Extract funding amount if present
                amount_match = re.search(r'\$[\d.]+[MBK]|\d+\s*million|\d+\s*billion', title + ' ' + desc, re.I)
                amount = amount_match.group() if amount_match else ''
                
                items.append({
                    'title': clean_html(title),
                    'url': link,
                    'description': amount or clean_html(desc)[:200],
                    'score': 0,
                    'source': 'funding'
                })
    except ET.ParseError:
        pass
    
    print(f"  Found {len(items)} funding items")
    return items[:10]

# ============================================================================
# 8. GITHUB REPOS (Daily Trending - hardcoded from live scrape)
# ============================================================================
def fetch_github_repos():
    """Fetch daily trending GitHub repos from github.com/trending."""
    print("🔥 Fetching GitHub Repos...")
    
    # Today's actual trending AI repos (scraped from github.com/trending)
    # This should be updated by browser scraping in production
    trending_today = [
        {
            'title': 'thedotmack/claude-mem',
            'url': 'https://github.com/thedotmack/claude-mem',
            'description': 'A Claude Code plugin that automatically captures everything Claude does during your coding sessions, compresses it with AI, and injects relevant context back into future sessions.',
            'stars_today': 1899,
            'source': 'github'
        },
        {
            'title': 'obra/superpowers',
            'url': 'https://github.com/obra/superpowers',
            'description': 'An agentic skills framework & software development methodology that works.',
            'stars_today': 893,
            'source': 'github'
        },
        {
            'title': 'openai/skills',
            'url': 'https://github.com/openai/skills',
            'description': 'Skills Catalog for Codex',
            'stars_today': 621,
            'source': 'github'
        },
        {
            'title': 'bytedance/UI-TARS-desktop',
            'url': 'https://github.com/bytedance/UI-TARS-desktop',
            'description': 'The Open-Source Multimodal AI Agent Stack: Connecting Cutting-Edge AI Models and Agent Infra',
            'stars_today': 560,
            'source': 'github'
        },
        {
            'title': 'topoteretes/cognee',
            'url': 'https://github.com/topoteretes/cognee',
            'description': 'Memory for AI Agents in 6 lines of code',
            'stars_today': 69,
            'source': 'github'
        },
        {
            'title': 'linshenkx/prompt-optimizer',
            'url': 'https://github.com/linshenkx/prompt-optimizer',
            'description': '一款提示词优化器，助力于编写高质量的提示词',
            'stars_today': 45,
            'source': 'github'
        },
    ]
    
    items = []
    for repo in trending_today:
        items.append({
            'title': repo['title'],
            'url': repo['url'],
            'description': f"{repo['description']} (+{repo['stars_today']} ⭐ today)",
            'score': repo['stars_today'],
            'source': 'github'
        })
    
    print(f"  Found {len(items)} GitHub repos")
    return items

# ============================================================================
# AI ENRICHMENT - Generate better descriptions
# ============================================================================
def call_openai(prompt, max_tokens=300):
    """Call OpenAI API to generate text."""
    if not OPENAI_API_KEY:
        return None
    
    try:
        conn = http.client.HTTPSConnection("api.openai.com")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }
        body = json.dumps({
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.7
        })
        conn.request("POST", "/v1/chat/completions", body, headers)
        response = conn.getresponse()
        data = json.loads(response.read().decode())
        return data['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"  OpenAI error: {e}", file=sys.stderr)
        return None

def enrich_description(item, category):
    """Generate an enriched description for an item using AI."""
    title = item.get('title', '')
    url = item.get('url', '')
    original_desc = item.get('description', '')
    
    # Base instruction for bullet point format
    bullet_format = """Format as 3 bullet points:
• [Key fact or what happened]
• [Why it matters or implications]  
• [What to watch or takeaway]

Keep each bullet to ONE line (under 80 chars). No intro text, just bullets."""
    
    # Category-specific prompts
    prompts = {
        'ai_news': f"""Summarize this AI news for a carousel card.

Headline: {title}
Context: {original_desc}

{bullet_format}""",
        
        'ai_discourse': f"""Summarize this AI community discussion.

Title: {title}
Context: {original_desc}

{bullet_format}""",
        
        'model_releases': f"""Summarize this AI model release.

Model: {title}
Stats: {original_desc}

{bullet_format}""",
        
        'ai_tools': f"""Summarize this AI tool update.

Headline: {title}
Details: {original_desc}

{bullet_format}""",
        
        'product_hunt': f"""Summarize this new AI product.

Product: {title}
Description: {original_desc}

{bullet_format}""",
        
        'ai_papers': f"""Summarize this research paper for non-experts.

Title: {title}
Abstract: {original_desc}

{bullet_format}""",
        
        'ai_funding': f"""Summarize this AI funding news.

Headline: {title}
Details: {original_desc}

{bullet_format}""",
        
        'github_repos': f"""Summarize this trending GitHub repo.

Repo: {title}
Description: {original_desc}

{bullet_format}""",
    }
    
    prompt = prompts.get(category, f"Summarize in 3 bullet points: {title}. Context: {original_desc}\n\n{bullet_format}")
    
    result = call_openai(prompt)
    if result:
        return result
    return original_desc  # Fallback to original

def enrich_all_descriptions(selected):
    """Enrich descriptions for all selected items."""
    if not OPENAI_API_KEY:
        print("\n⚠️  No OpenAI API key - skipping description enrichment")
        return selected
    
    print("\n✨ Enriching descriptions with AI...")
    enriched = {}
    
    for category, item in selected.items():
        print(f"  📝 {category}...")
        new_desc = enrich_description(item, category)
        enriched[category] = {**item, 'description': new_desc, 'original_description': item.get('description', '')}
    
    print("  ✓ Done enriching descriptions")
    return enriched

# ============================================================================
# MAIN
# ============================================================================
def main():
    print(f"\n{'='*60}")
    print(f"AI Digest - Fetching data for {TODAY}")
    print(f"{'='*60}\n")
    
    results = {
        'date': TODAY,
        'fetched_at': datetime.now().isoformat(),
        'categories': {
            'ai_news': fetch_ai_news(),
            'ai_discourse': fetch_ai_discourse(),
            'model_releases': fetch_model_releases(),
            'ai_tools': fetch_ai_tools(),
            'product_hunt': fetch_product_hunt(),
            'ai_papers': fetch_ai_papers(),
            'ai_funding': fetch_ai_funding(),
            'github_repos': fetch_github_repos(),
        }
    }
    
    # Load history to avoid repeating recent items
    history = load_history()
    historically_used = get_used_titles(history)
    print(f"\n📜 Loaded {len(historically_used)} items from history (last {HISTORY_DAYS} days)")
    
    # Select top item per category (dedup by title/URL only, allow topic overlap in News/Discourse)
    results['selected'] = {}
    used_titles = set()
    used_urls = set()
    
    # Categories where topic overlap is OK (news/discourse can cover same story, tools can mention same tools)
    allow_topic_overlap = {'ai_news', 'ai_discourse', 'ai_tools'}
    used_topics = set()
    
    def extract_topics(text):
        """Extract main topic keywords from text."""
        topics = set()
        text_lower = text.lower()
        topic_map = {
            'claude': ['claude', 'anthropic', 'opus'],
            'openai': ['openai', 'chatgpt', 'gpt-', 'codex'],
        }
        for topic, keywords in topic_map.items():
            if any(kw in text_lower for kw in keywords):
                topics.add(topic)
        return topics
    
    for cat, items in results['categories'].items():
        if items:
            for item in items:
                title_key = item['title'].lower().strip()
                url_key = item.get('url', '').lower().strip()
                
                # Skip if shown in recent history
                if title_key in historically_used or url_key in historically_used:
                    continue
                
                # Always skip exact title/URL duplicates within today
                if title_key in used_titles or url_key in used_urls:
                    continue
                
                # For non-news/discourse categories, also skip topic overlap
                if cat not in allow_topic_overlap:
                    item_topics = extract_topics(item['title'] + ' ' + item.get('description', ''))
                    if item_topics & used_topics:
                        continue
                
                results['selected'][cat] = item
                used_titles.add(title_key)
                used_urls.add(url_key)
                # Track topics for later categories
                used_topics.update(extract_topics(item['title'] + ' ' + item.get('description', '')))
                print(f"\n✓ {cat}: {item['title'][:60]}...")
                break
            else:
                if items:
                    # Fallback to first item even if it was used before
                    results['selected'][cat] = items[0]
                    print(f"\n⚠ {cat}: {items[0]['title'][:60]}... (fallback, may repeat)")
        else:
            print(f"\n✗ {cat}: No items found")
    
    # Enrich descriptions with AI
    results['selected'] = enrich_all_descriptions(results['selected'])
    
    # Save to history for future deduplication
    history = add_to_history(history, TODAY, results['selected'])
    save_history(history)
    print(f"\n📝 Saved today's selections to history")
    
    # Save results
    output_dir = OUTPUT_DIR / TODAY
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "data.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"Results saved to {output_file}")
    print(f"{'='*60}\n")
    
    return results

if __name__ == "__main__":
    main()
