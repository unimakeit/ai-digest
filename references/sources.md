# Data Sources

## 1. AI News

**Primary:** RSS feeds
- TechCrunch AI: `https://techcrunch.com/category/artificial-intelligence/feed/`
- The Verge AI: `https://www.theverge.com/rss/ai-artificial-intelligence/index.xml`
- VentureBeat AI: `https://venturebeat.com/category/ai/feed/`
- Ars Technica AI: `https://feeds.arstechnica.com/arstechnica/technology-lab`

**Ranking:** Recency + social shares + keyword density for major announcements

## 2. AI Discourse

**Primary:** Hacker News API
- Endpoint: `https://hacker-news.firebaseio.com/v0/`
- Filter: Stories with AI/ML/LLM keywords, sort by score

**Secondary:** Reddit
- r/MachineLearning hot posts
- r/LocalLLaMA hot posts
- r/artificial hot posts

**Tertiary:** Twitter/X (if available via bird skill)
- Search: AI OR LLM OR "machine learning" filter:popular

**Ranking:** Comment count + upvotes, controversy signal (high comments relative to score)

## 3. Model Releases

**Primary:** Hugging Face
- New models: `https://huggingface.co/api/models?sort=lastModified&direction=-1`
- Filter: Last 24h, significant likes/downloads

**Secondary:** GitHub releases from major labs
- OpenAI, Anthropic, Google, Meta, Mistral repos

**Tertiary:** News mentions of model releases

**Ranking:** Downloads/likes + organization reputation + capability claims

## 4. AI Tools

**Primary:** There's An AI For That
- Scrape: `https://theresanaiforthat.com/new/`

**Secondary:** FutureTools
- Scrape: `https://www.futuretools.io/`

**Tertiary:** Product Hunt AI category (handled separately)

**Ranking:** User ratings + feature uniqueness + practical utility signal

## 5. Product Hunt

**Primary:** Product Hunt API
- Endpoint: `https://api.producthunt.com/v2/api/graphql`
- Auth: Bearer token required
- Query: Posts from today, filter by AI/ML topics

**Fallback:** Scrape `https://www.producthunt.com/topics/artificial-intelligence`

**Ranking:** Upvotes + comment count + maker reputation

## 6. AI Papers

**Primary:** arXiv API
- Endpoint: `http://export.arxiv.org/api/query`
- Categories: cs.AI, cs.LG, cs.CL, cs.CV
- Filter: Last 24-48h submissions

**Secondary:** Papers With Code trending
- Scrape: `https://paperswithcode.com/`

**Tertiary:** Hugging Face Daily Papers
- `https://huggingface.co/papers`

**Ranking:** Citation velocity + GitHub stars on implementations + Twitter mentions

## 7. AI Funding

**Primary:** Crunchbase (limited without API key)
- Fallback: TechCrunch funding tag RSS

**Secondary:** News scraping
- Filter funding announcements from AI News sources

**Tertiary:** Twitter/LinkedIn announcements from VCs

**Ranking:** Deal size + company stage + investor reputation

## 8. GitHub Repos

**Primary:** GitHub Trending
- Scrape: `https://github.com/trending?since=daily`
- Filter: Repos with AI/ML/LLM in description or topics

**Secondary:** GitHub Search API
- Query: `stars:>100 pushed:>YYYY-MM-DD` with AI keywords

**Ranking:** Star velocity (stars gained today) + fork ratio + recent activity

---

## Rate Limits & Keys

| Source | Rate Limit | Auth Required |
|--------|-----------|---------------|
| Hacker News | None | No |
| Reddit | 60/min | Optional (OAuth) |
| arXiv | 1/3s | No |
| Hugging Face | 1000/day | Optional |
| Product Hunt | 450/day | Yes (OAuth) |
| GitHub | 60/hr (unauth), 5000/hr (auth) | Optional |

## Fallback Strategy

If primary source fails:
1. Try secondary source
2. Try cached data from yesterday
3. Skip category with note in output
