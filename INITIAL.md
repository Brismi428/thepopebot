# WAT System Request

Fill out the sections below. Keep it simple -- write in plain language. The factory will expand this into a full technical specification (PRP) for review before building.

---

## What problem are you solving?

[Describe the problem in plain language. What manual work are you automating? What information do you need gathered, processed, or delivered? Example: "I need to monitor competitor websites weekly and get a summary of changes."]

## What goes in?

[What does the system need to start working? Examples: a company name, a URL, a list of keywords, a CSV file, a webhook payload. Be specific about format if it matters.]

## What comes out?

[What should the system produce? Examples: a JSON report, a CSV file, a Slack message, an email, a GitHub PR with results. Where should the output go?]

## How often should it run?

[Pick one or describe your own schedule.]

- [ ] On demand (I trigger it manually)
- [ ] Daily
- [ ] Weekly
- [ ] Monthly
- [ ] When triggered by an external event (webhook)
- [ ] Other: _______________

## Where should results go?

[Pick one or more.]

- [ ] Committed back to the GitHub repo
- [ ] Sent to Slack
- [ ] Sent via email
- [ ] Posted to a webhook URL
- [ ] Written to a file/database
- [ ] Other: _______________

## Anything else?

[Optional. Mention any APIs you already have access to, services you prefer, constraints, or things you have tried before that did not work. If you have an n8n workflow JSON that does something similar, mention that here.]

---

**Next step**: Run `/generate-prp INITIAL.md` to turn this into a full PRP for review.
