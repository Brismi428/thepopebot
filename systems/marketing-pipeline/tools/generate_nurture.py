"""
Generate Nurture — Creates a 5-email nurture drip sequence for Warm leads
using Claude API. Focuses on education, case studies, and soft CTAs.

Inputs:
    - warm_leads (list[dict]): Warm tier leads from segment_leads.py

Outputs:
    - dict with:
        - sequence (list[dict]): The 5-email nurture sequence
        - file_written (str): Path to the nurture sequence markdown file

Usage:
    python generate_nurture.py --input output/segmented_leads.json --output-dir output/nurture

Environment Variables:
    - ANTHROPIC_API_KEY: Claude API key (required)
"""

import argparse
import json
import logging
import os
import sys
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

NURTURE_SYSTEM_PROMPT = """You are an expert B2B email marketing strategist specializing in nurture sequences.
You write emails that are:
- Educational first, promotional second
- Genuinely useful — readers should learn something even if they never buy
- Written at a conversational but professional level
- Focused on building trust and authority over time
- Each email under 200 words

The sequence builds progressively from awareness to consideration."""

NURTURE_PROMPT_TEMPLATE = """Create a 5-email nurture drip sequence for warm B2B leads in the automation/operations space.

## Context
These are companies that show some interest signals but aren't ready for direct outreach yet. Common characteristics:
- Company sizes: {size_range}
- Industries: {industries}
- Common tech stacks: {tech_stacks}
- Common pain signals: {pain_signals}
- Average score: {avg_score}

## Sequence Structure

### Email 1 — Welcome/Education (Send Day 1)
Introduce the problem space. Share an industry insight about operational inefficiency or the cost of manual processes. No selling.

### Email 2 — Case Study (Send Day 5)
Real-world example of a company solving their automation problem. Specific numbers and outcomes. Make it relatable.

### Email 3 — How-To (Send Day 10)
Practical tips for improving operations or evaluating automation tools. Actionable advice they can use immediately.

### Email 4 — Social Proof (Send Day 16)
Testimonials, metrics, or success stories. Let results speak. Multiple short examples better than one long one.

### Email 5 — Soft CTA (Send Day 22)
Invitation to learn more — webinar, guide, or brief call. Low pressure. Make it feel like a natural next step, not a sales push.

## Output Format
Return ONLY valid JSON:
{{
    "sequence": [
        {{
            "email_number": 1,
            "send_day": 1,
            "theme": "Welcome/Education",
            "subject": "Subject line here",
            "body": "Email body here"
        }},
        {{
            "email_number": 2,
            "send_day": 5,
            "theme": "Case Study",
            "subject": "Subject line here",
            "body": "Email body here"
        }},
        {{
            "email_number": 3,
            "send_day": 10,
            "theme": "How-To",
            "subject": "Subject line here",
            "body": "Email body here"
        }},
        {{
            "email_number": 4,
            "send_day": 16,
            "theme": "Social Proof",
            "subject": "Subject line here",
            "body": "Email body here"
        }},
        {{
            "email_number": 5,
            "send_day": 22,
            "theme": "Soft CTA",
            "subject": "Subject line here",
            "body": "Email body here"
        }}
    ]
}}"""


def summarize_warm_leads(warm_leads: list[dict]) -> dict:
    """Summarize warm lead characteristics for the prompt."""
    sizes = set()
    industries = set()
    tech_stacks = set()
    pain_signals = set()
    scores = []

    for lead in warm_leads:
        size = lead.get("company_size", "")
        if size and size != "unknown":
            sizes.add(str(size))

        industry = lead.get("industry", "")
        if industry and industry != "unknown":
            industries.add(industry)

        for tech in lead.get("tech_stack", [])[:5]:
            tech_stacks.add(tech)

        for signal in lead.get("pain_signals", [])[:3]:
            pain_signals.add(signal)

        scores.append(lead.get("total_score", 0))

    return {
        "size_range": ", ".join(list(sizes)[:5]) or "Various",
        "industries": ", ".join(list(industries)[:5]) or "Various",
        "tech_stacks": ", ".join(list(tech_stacks)[:10]) or "Various",
        "pain_signals": "; ".join(list(pain_signals)[:5]) or "General operational inefficiency",
        "avg_score": round(sum(scores) / len(scores), 1) if scores else 0,
    }


def generate_nurture_sequence(warm_leads: list[dict]) -> dict | None:
    """Generate a 5-email nurture sequence using Claude."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return None

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        summary = summarize_warm_leads(warm_leads)
        prompt = NURTURE_PROMPT_TEMPLATE.format(**summary)

        msg = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=3000,
            temperature=0.7,
            system=NURTURE_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        raw = msg.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

        return json.loads(raw)

    except ImportError:
        logger.error("anthropic package not installed")
        return None
    except json.JSONDecodeError as e:
        logger.warning("Failed to parse nurture sequence JSON: %s", e)
        return None
    except Exception as e:
        logger.error("Nurture generation failed: %s", e)
        return None


def write_nurture_markdown(sequence_data: dict, output_dir: str) -> str | None:
    """Write the nurture sequence to a Markdown file."""
    filepath = os.path.join(output_dir, "sequence.md")

    try:
        lines = ["# Nurture Email Sequence\n"]
        lines.append("A 5-email drip sequence for warm leads. Focused on education, trust-building, and soft conversion.\n")
        lines.append("---\n")

        for email in sequence_data.get("sequence", []):
            num = email.get("email_number", "?")
            day = email.get("send_day", "?")
            theme = email.get("theme", "")
            subject = email.get("subject", "")
            body = email.get("body", "")

            lines.append(f"## Email {num}: {theme} (Send Day {day})\n")
            lines.append(f"**Subject:** {subject}\n")
            lines.append(f"{body}\n")
            lines.append("---\n")

        os.makedirs(output_dir, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return filepath

    except OSError as e:
        logger.error("Failed to write nurture file %s: %s", filepath, e)
        return None


def main() -> dict[str, Any]:
    """
    Main entry point. Generates a nurture email sequence for warm leads.

    Returns:
        dict: Generated nurture sequence and file path.
    """
    parser = argparse.ArgumentParser(description="Generate nurture email sequence")
    parser.add_argument("--input", required=True, help="Path to segmented leads JSON")
    parser.add_argument("--output-dir", default="output/nurture", help="Directory for sequence file")
    parser.add_argument("--output", default="output/nurture_results.json", help="Summary output file")
    args = parser.parse_args()

    logger.info("Starting nurture sequence generation")

    try:
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            msg = "ANTHROPIC_API_KEY not set. Required for email generation."
            logger.error(msg)
            return {"status": "error", "data": None, "message": msg}

        with open(args.input, "r", encoding="utf-8") as f:
            segmented = json.load(f)

        warm_leads = segmented.get("data", {}).get("warm", [])
        if not warm_leads:
            logger.info("No warm leads to generate nurture for")
            return {"status": "success", "data": {"sequence": None, "file_written": None},
                    "message": "No warm leads for nurture sequence"}

        logger.info("Generating nurture sequence informed by %d warm leads", len(warm_leads))

        sequence_data = generate_nurture_sequence(warm_leads)
        if not sequence_data:
            msg = "Failed to generate nurture sequence"
            logger.error(msg)
            return {"status": "error", "data": None, "message": msg}

        filepath = write_nurture_markdown(sequence_data, args.output_dir)

        result = {
            "status": "success",
            "data": {
                "sequence": sequence_data,
                "file_written": filepath,
                "email_count": len(sequence_data.get("sequence", [])),
                "warm_leads_analyzed": len(warm_leads),
            },
            "message": f"Generated {len(sequence_data.get('sequence', []))}-email nurture sequence",
        }

        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

        logger.info("Nurture results written to %s", args.output)
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
