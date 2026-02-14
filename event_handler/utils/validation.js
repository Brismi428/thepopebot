const { z } = require('zod');

/**
 * Schema for POST /webhook (create job)
 */
const webhookJobSchema = z.object({
  job: z.string().min(1).max(50000),
});

/**
 * Schema for POST /telegram/register
 */
const telegramRegisterSchema = z.object({
  bot_token: z.string().min(10).max(200),
  webhook_url: z.string().url().max(500),
});

/**
 * Schema for POST /chat (web dashboard chat)
 */
const chatMessageSchema = z.object({
  message: z.string().min(1).max(10000),
});

/**
 * Schema for GitHub webhook payload (loose — we only validate what we use)
 */
const githubWebhookSchema = z.object({
  pull_request: z.object({
    head: z.object({
      ref: z.string(),
    }).optional(),
    html_url: z.string().url().optional(),
  }).optional(),
  job_results: z.object({
    job: z.string().optional(),
    commit_message: z.string().optional(),
    changed_files: z.array(z.string()).optional(),
    pr_status: z.string().optional(),
    merge_result: z.string().optional(),
    pr_url: z.string().optional(),
    log: z.string().optional(),
  }).optional(),
}).passthrough();

/**
 * Sanitize user input for safe inclusion in LLM prompts.
 * Strips control characters (except newline/tab) and trims excessive whitespace.
 * @param {string} text - Raw user input
 * @param {number} [maxLength=10000] - Maximum allowed length
 * @returns {string} Sanitized text
 */
function sanitizeUserInput(text, maxLength = 10000) {
  if (typeof text !== 'string') return '';
  return text
    // Remove control chars except \n and \t
    .replace(/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/g, '')
    // Collapse excessive newlines (more than 3 consecutive)
    .replace(/\n{4,}/g, '\n\n\n')
    .trim()
    .slice(0, maxLength);
}

/**
 * Validate and return parsed data, or throw with a user-friendly message.
 * @param {z.ZodSchema} schema
 * @param {*} data
 * @returns {*} Parsed data
 */
function validate(schema, data) {
  const result = schema.safeParse(data);
  if (!result.success) {
    const issues = result.error.issues.map(i => `${i.path.join('.')}: ${i.message}`).join('; ');
    const err = new Error(`Validation failed: ${issues}`);
    err.status = 400;
    throw err;
  }
  return result.data;
}

module.exports = {
  webhookJobSchema,
  telegramRegisterSchema,
  githubWebhookSchema,
  chatMessageSchema,
  sanitizeUserInput,
  validate,
};
