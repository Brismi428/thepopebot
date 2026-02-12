Create a comprehensive Firecrawl skill at `.claude/skills/firecrawl/SKILL.md` that teaches the factory when and how to use Firecrawl for web scraping tasks. The skill should include:

1. **Decision Framework**: When to use Firecrawl vs requests/BeautifulSoup (always prefer Firecrawl for web scraping)
2. **API Endpoints**: Document all 7 endpoints (/scrape, /crawl, /map, /search, /extract, /agent, /batch)
3. **Python SDK Setup**: Usage with `from firecrawl import Firecrawl` and API key access via `os.environ.get("FIRECRAWL_API_KEY")`
4. **Common Patterns**: Include code examples for:
   - Single page to markdown: `app.scrape(url, formats=["markdown"])`
   - Structured extraction with schema: `app.scrape(url, formats=[{"type": "json", "schema": schema}])`
   - Web search + scrape: `app.search(query, limit=5, scrape_options={"formats": ["markdown"]})`
   - Agent endpoint: POST /v2/agent with prompt (no URL needed)
   - Full site crawl: `app.crawl(url, limit=100)`
   - URL discovery: `app.map(url)`
5. **Requirements Integration**: Note that tools using Firecrawl must add `firecrawl` to requirements.txt
6. **FIRE-1 Agent**: Document the agent's capabilities for complex navigation (clicking, scrolling, pagination)

After creating the skill file, commit the change, push to main, and trigger the Docker rebuild by updating a relevant file that will cause the docker-build.yml workflow to run.