Generate a complete PRP (Product Requirements Prompt) for building a site intelligence system called "site-intelligence-pack".

SYSTEM OVERVIEW:
Build a comprehensive website analysis system with three specialist components that produces evidence-backed business intelligence reports while respecting robots.txt and rate limits.

DETAILED REQUIREMENTS:

**Input/Output:**
- Single domain via workflow_dispatch input OR batch processing from inputs/targets.csv
- Outputs: JSON files (inventory, rankings, extractions, final pack) + README committed to repo under outputs/{domain}/{timestamp}/
- GitHub Issues created on major failures

**Triggering:**
- On-demand via workflow_dispatch 
- Optional nightly scheduled batch run

**Scale & Constraints:**
- 200 pages max per site by default
- Rate limiting: 1-2 req/sec with politeness controls
- MUST respect robots.txt (fetch first, check disallowed paths)
- No authentication bypass (mark login/paywall pages as inaccessible)

**Three Specialist Components:**

1. **relevance-ranker-specialist**: 
   - Ranks pages using path keywords (pricing/faq/terms/etc)
   - Lightweight semantic scoring on titles/headings/first N chars
   - Priority categories: offers/pricing/how-it-works/policies/testimonials → about/faq/contact → blog/other

2. **deep-extract-specialist**: 
   - Deep-scrapes top K pages
   - Extracts structured fields: offers, pricing, guarantees, process steps, FAQs, contact methods, policies, testimonials
   - All extractions must include quoted evidence with URL + excerpt

3. **synthesis-validator-specialist**: 
   - Builds final JSON pack with evidence mapping
   - Every "important claim" must have evidence entries (url + excerpt + extracted_at + page_title)
   - Schema validation of final output

**Core Technical Requirements:**

- **Evidence Tracking**: Every key claim in synthesized_findings must map to evidence_index entries
- **De-duplication**: Canonicalize URLs, cluster near-identical pages, avoid header/footer boilerplate
- **Page Discovery**: Explicitly attempt to find: home, about, offers, pricing, faq, contact, policies, privacy, terms, blog
- **Failure Handling**: If Firecrawl fails, fall back to direct HTTP; if <5 pages extracted successfully, open GitHub Issue but still commit partial outputs

**JSON Schema (Site Intelligence Pack):**
```
{
  "site": {
    "target_url": string,
    "domain": string, 
    "crawled_at_iso": string,
    "robots": {
      "fetched_url": string,
      "allowed_summary": string,
      "disallowed_summary": string,
      "raw_excerpt": string?
    }
  },
  "inventory": [
    {
      "url": string,
      "canonical_url": string,
      "title": string?,
      "discovered_from": string?,
      "http_status": number?,
      "content_hash": string?,
      "dedup_cluster_id": string,
      "notes": string?
    }
  ],
  "ranked_pages": [
    {
      "url": string,
      "canonical_url": string,
      "rank": number,
      "reasons": [string],
      "category": string
    }
  ],
  "deep_extract_notes": {
    "pages": [
      {
        "url": string,
        "canonical_url": string,
        "title": string?,
        "summary": string,
        "extracted_entities": {
          "company_name": string?,
          "product_names": [string]?,
          "audience": string?,
          "locations": [string]?,
          "contact_points": [string]?
        },
        "offers": [
          {
            "name": string?,
            "description": string?,
            "price": string?,
            "billing_terms": string?,
            "guarantees": string?,
            "evidence": [string]
          }
        ],
        "pricing": {
          "model": string?,
          "tiers": [object]?,
          "add_ons": [object]?,
          "evidence": [string]
        },
        "how_it_works": {
          "steps": [string]?,
          "evidence": [string]
        },
        "faq": [
          {
            "q": string,
            "a": string,
            "evidence": [string]
          }
        ],
        "testimonials": [
          {
            "quote": string?,
            "name": string?,
            "source_context": string?,
            "evidence": [string]
          }
        ],
        "policies": {
          "privacy": string?,
          "terms": string?,
          "refunds": string?,
          "shipping": string?,
          "cancellations": string?,
          "evidence": [string]
        },
        "constraints": {
          "requires_login": boolean?,
          "blocked_by_robots": boolean?
        }
      }
    ]
  },
  "synthesized_findings": {
    "positioning": {
      "claims": [
        {
          "id": string,
          "claim": string,
          "evidence": [string]
        }
      ]
    },
    "offers_and_pricing": {
      "claims": [...]
    },
    "customer_journey": {
      "claims": [...]
    },
    "trust_signals": {
      "claims": [...]
    },
    "compliance_and_policies": {
      "claims": [...]
    },
    "unknowns_and_gaps": [
      {
        "issue": string,
        "affected_urls": [string],
        "notes": string
      }
    ]
  },
  "evidence_index": {
    "evidence_id": {
      "url": string,
      "excerpt": string,
      "page_title": string?,
      "extracted_at_iso": string
    }
  },
  "run_metadata": {
    "max_pages": number,
    "pages_crawled": number,
    "pages_extracted": number,
    "dedup_clusters": number,
    "blocked_count": number,
    "inaccessible_count": number,
    "errors": [string]
  }
}
```

**Integration Requirements:**
- Use Firecrawl API for crawling/extraction
- GitHub API for commits and issue creation
- Write outputs to: inventory.json, ranked_pages.json, deep_extract.json, site_intelligence_pack.json, README.md
- Commit with message: "Add Site Intelligence Pack for {domain} (YYYY-MM-DD)"

Generate the complete PRP following the WAT factory patterns and save it to PRPs/site-intelligence-pack.md. Include confidence score in final commit message.