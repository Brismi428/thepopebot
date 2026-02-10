"""
Generate Outreach — Creates personalized 3-email cold outreach sequences for Hot leads
using Claude API. Each email references something specific about the company.

Inputs:
    - hot_leads (list[dict]): Hot tier leads from segment_leads.py

Outputs:
    - dict with:
        - sequences (list[dict]): Generated email sequences per company
        - files_written (list[str]): Paths to individual sequence files

Usage:
    python generate_outreach.py --input output/segmented_leads.json --output-dir output/outreach

Environment Variables:
    - ANTHROPIC_API_KEY: Claude API key (required)
"""

import argparse
import json
import logging
import os
import re
import sys
import time
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

OUTREACH_SYSTEM_PROMPT = """You are an expert B2B cold email copywriter. You write emails that are:
- Personalized and specific — never generic
- Concise — under 150 words per email
- Value-first — lead with insight, not a pitch
- Professional but human — no corporate jargon
- Clear CTA — one ask per email

You never use:
- "I hope this finds you well"
- "I wanted to reach out"
- Excessive exclamation marks
- Generic compliments
- Aggressive urgency tactics

Write in a direct, helpful tone. Every sentence must earn its place."""

OUTREACH_PROMPT_TEMPLATE = """Write a 3-email cold outreach sequence for this company. Each email must reference specific details from the company data provided.

## Company Data
- Company: {company_name}
- Industry: {industry}
- Size: {company_size} employees
- Tech Stack: {tech_stack}
- Decision Makers: {decision_makers}
- Recent Blog Posts: {blog_posts}
- Job Listings: {job_listings}
- Pain Signals: {pain_signals}
- Score Breakdown: {score_breakdown}

## Sequence Structure

### Email 1 — Intro (Send Day 1)
- Reference something SPECIFIC about the company (a recent blog post, job listing, or tech stack choice)
- Introduce the value proposition in 1-2 sentences
- Personalized subject line (under 50 chars, no clickbait)
- No ask in this email — just establish relevance

### Email 2 — Value Add (Send Day 4)
- Share a relevant insight or mini case study
- Connect their specific pain signal to a solution
- Still no hard ask — build credibility

### Email 3 — Soft Close (Send Day 8)
- Reference the previous emails briefly
- Clear but gentle CTA: suggest a 15-minute call or share a relevant resource
- Create mild interest without pressure

## Output Format
Return ONLY valid JSON with this structure:
{{
    "company": "{company_name}",
    "sequence": [
        {{
            "email_number": 1,
            "send_day": 1,
            "subject": "Subject line here",
            "body": "Email body here"
        }},
        {{
            "email_number": 2,
            "send_day": 4,
            "subject": "Subject line here",
            "body": "Email body here"
        }},
        {{
            "email_number": 3,
            "send_day": 8,
            "subject": "Subject line here",
            "body": "Email body here"
        }}
    ]
}}"""


def slugify(text: str) -> str:
    """Convert text to a URL-safe slug."""
    slug = re.sub(r'[^\w\s-]', '', text.lower())
    slug = re.sub(r'[-\s]+', '-', slug).strip('-')
    return slug[:80]


def format_list(items: list, max_items: int = 5) -> str:
    """Format a list for the prompt, truncating if needed."""
    if not items:
        return "None available"
    if isinstance(items[0], dict):
        formatted = []
        for item in items[:max_items]:
            parts = [f"{k}: {v}" for k, v in item.items() if v]
            formatted.append(", ".join(parts[:3]))
        return "; ".join(formatted)
    return ", ".join(str(i) for i in items[:max_items])


def generate_sequence(lead: dict) -> dict | None:
    """Generate a 3-email outreach sequence for a single hot lead."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return None

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        company_name = lead.get("company_name", "Unknown")
        prompt = OUTREACH_PROMPT_TEMPLATE.format(
            company_name=company_name,
            industry=lead.get("industry", "unknown"),
            company_size=lead.get("company_size", "unknown"),
            tech_stack=format_list(lead.get("tech_stack", [])),
            decision_makers=format_list(lead.get("decision_makers", [])),
            blog_posts=format_list(lead.get("blog_posts", [])),
            job_listings=format_list(lead.get("job_listings", [])),
            pain_signals=format_list(lead.get("pain_signals", [])),
            score_breakdown=json.dumps(lead.get("score_breakdown", {})),
        )

        msg = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            temperature=0.7,
            system=OUTREACH_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        raw = msg.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

        sequence = json.loads(raw)
        return sequence

    except ImportError:
        logger.error("anthropic package not installed")
        return None
    except json.JSONDecodeError as e:
        logger.warning("Failed to parse outreach sequence JSON for %s: %s",
                       lead.get("company_name", "?"), e)
        return None
    except Exception as e:
        logger.error("Outreach generation failed for %s: %s",
                     lead.get("company_name", "?"), e)
        return None


def write_sequence_markdown(sequence: dict, output_dir: str) -> str | None:
    """Write a sequence to a Markdown file."""
    company = sequence.get("company", "unknown")
    slug = slugify(company)
    filepath = os.path.join(output_dir, f"emails_{slug}.md")

    try:
        lines = [f"# Outreach Sequence: {company}\n"]

        for email in sequence.get("sequence", []):
            num = email.get("email_number", "?")
            day = email.get("send_day", "?")
            subject = email.get("subject", "")
            body = email.get("body", "")

            lines.append(f"## Email {num} (Send Day {day})\n")
            lines.append(f"**Subject:** {subject}\n")
            lines.append(f"{body}\n")
            lines.append("---\n")

        os.makedirs(output_dir, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return filepath

    except OSError as e:
        logger.error("Failed to write sequence file %s: %s", filepath, e)
        return None


def main() -> dict[str, Any]:
    """
    Main entry point. Generates personalized outreach sequences for hot leads.

    Returns:
        dict: Generated sequences and file paths.
    """
    parser = argparse.ArgumentParser(description="Generate cold outreach email sequences")
    parser.add_argument("--input", required=True, help="Path to segmented leads JSON")
    parser.add_argument("--output-dir", default="output/outreach", help="Directory for sequence files")
    parser.add_argument("--output", default="output/outreach_results.json", help="Summary output file")
    args = parser.parse_args()

    logger.info("Starting outreach generation")

    try:
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            msg = "ANTHROPIC_API_KEY not set. Required for email generation."
            logger.error(msg)
            return {"status": "error", "data": None, "message": msg}

        with open(args.input, "r", encoding="utf-8") as f:
            segmented = json.load(f)

        hot_leads = segmented.get("data", {}).get("hot", [])
        if not hot_leads:
            logger.info("No hot leads to generate outreach for")
            return {"status": "success", "data": {"sequences": [], "files_written": []},
                    "message": "No hot leads for outreach"}

        logger.info("Generating outreach for %d hot leads", len(hot_leads))

        sequences = []
        files_written = []
        failed = []

        for i, lead in enumerate(hot_leads):
            company = lead.get("company_name", "unknown")
            logger.info("Generating outreach %d/%d: %s", i + 1, len(hot_leads), company)

            sequence = generate_sequence(lead)
            if sequence:
                sequences.append(sequence)
                filepath = write_sequence_markdown(sequence, args.output_dir)
                if filepath:
                    files_written.append(filepath)
                    logger.info("  Written to %s", filepath)
            else:
                failed.append(company)
                logger.warning("  Failed to generate outreach for %s", company)

            # Rate limit between Claude API calls
            if i < len(hot_leads) - 1:
                time.sleep(1)

        result = {
            "status": "success",
            "data": {
                "sequences": sequences,
                "files_written": files_written,
                "generated_count": len(sequences),
                "failed": failed,
                "failed_count": len(failed),
            },
            "message": f"Generated {len(sequences)} outreach sequences, {len(failed)} failed",
        }

        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

        logger.info("Outreach results written to %s", args.output)
        return result

    except FileNotFoundError as e:
        logger.error("Input file not found: %s", e)
        return {"status": "error", "data": None, "message": str(e)}
    except json.JSONDecodeError as e:
        logger.error("JSON parsing error: %s", e)
        return {"status": "error", "data": None, "message": f"Invalid JSON: {e}"}
    except Exception as e:
        logger.error("Unexpected error: %s", e)
        return {"status": "error", "data": None, "message": str(e)}


if __name__ == "__main__":
    result = main()
    if result["status"] != "success":
        sys.exit(1)
