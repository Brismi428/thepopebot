const express = require('express');
const helmet = require('helmet');
const fs = require('fs');
const path = require('path');
require('dotenv').config();

const { createJob } = require('./tools/create-job');
const { loadCrons } = require('./cron');
const { loadTriggers } = require('./triggers');
const { setWebhook, sendMessage, mdToTelegramHtml, formatJobNotification, downloadFile, reactToMessage, startTypingIndicator } = require('./tools/telegram');
const { isWhisperEnabled, transcribeAudio } = require('./tools/openai');
const { chat } = require('./claude');
const { toolDefinitions, toolExecutors } = require('./claude/tools');
const { getHistory, updateHistory, clearHistory, getConversationCount } = require('./claude/conversation');
const { githubApi, getJobStatus, getSystemsCatalog } = require('./tools/github');
const { getApiKey } = require('./claude');
const { render_md } = require('./utils/render-md');
const { retry } = require('./utils/retry');
const { webhookJobSchema, telegramRegisterSchema, githubWebhookSchema, chatMessageSchema, sanitizeUserInput, validate } = require('./utils/validation');
const { verifyHmac, isHmacSignature } = require('./utils/hmac');
const rateLimit = require('express-rate-limit');
const log = require('./utils/logger');

const app = express();

// Trust first proxy (Caddy) so rate limiter reads X-Forwarded-For correctly
app.set('trust proxy', 1);

app.use(helmet());
app.use(express.json({
  verify: (req, _res, buf) => {
    if (req.url === '/github/webhook') req.rawBody = buf;
  },
}));

// Rate limiters per endpoint type
const telegramLimiter = rateLimit({
  windowMs: 60 * 1000,
  max: 30,
  standardHeaders: true,
  legacyHeaders: false,
  message: { error: 'Too many requests' },
});

const webhookLimiter = rateLimit({
  windowMs: 60 * 1000,
  max: 10,
  standardHeaders: true,
  legacyHeaders: false,
  message: { error: 'Too many requests' },
});

const jobLimiter = rateLimit({
  windowMs: 60 * 1000,
  max: 5,
  standardHeaders: true,
  legacyHeaders: false,
  message: { error: 'Too many job creation requests' },
});

const chatLimiter = rateLimit({
  windowMs: 60 * 1000,
  max: 10,
  standardHeaders: true,
  legacyHeaders: false,
  message: { error: 'Too many chat requests' },
});

const { API_KEY, TELEGRAM_WEBHOOK_SECRET, TELEGRAM_BOT_TOKEN, GH_WEBHOOK_SECRET, GH_OWNER, GH_REPO, TELEGRAM_CHAT_ID, TELEGRAM_VERIFICATION } = process.env;

// Bot token from env, can be overridden by /telegram/register
let telegramBotToken = TELEGRAM_BOT_TOKEN || null;

// Routes that have their own authentication
const PUBLIC_ROUTES = ['/telegram/webhook', '/github/webhook'];

// Global x-api-key auth (skip for routes with their own auth)
app.use((req, res, next) => {
  if (PUBLIC_ROUTES.includes(req.path)) {
    return next();
  }
  if (req.headers['x-api-key'] !== API_KEY) {
    return res.status(401).json({ error: 'Unauthorized' });
  }
  next();
});

app.use(loadTriggers());

// Track server start time for uptime calculation
const startedAt = Date.now();

// GET /ping - simple health check
app.get('/ping', (req, res) => {
  res.json({ message: 'Pong!' });
});

// GET /health - detailed health check with diagnostics
app.get('/health', async (req, res) => {
  const checks = {};
  let healthy = true;

  // Uptime
  const uptimeMs = Date.now() - startedAt;
  checks.uptime = {
    status: 'ok',
    seconds: Math.floor(uptimeMs / 1000),
  };

  // Conversation store
  checks.conversations = {
    status: 'ok',
    count: getConversationCount(),
  };

  // GitHub API connectivity
  try {
    await githubApi(`/repos/${GH_OWNER}/${GH_REPO}`);
    checks.github = { status: 'ok' };
  } catch (err) {
    checks.github = { status: 'error', message: err.message };
    healthy = false;
  }

  // Claude API key validity (lightweight check via a minimal request)
  try {
    const apiKey = getApiKey();
    checks.claude = { status: apiKey ? 'ok' : 'missing', configured: !!apiKey };
  } catch (err) {
    checks.claude = { status: 'error', message: err.message };
    healthy = false;
  }

  // NCA Toolkit connectivity (no /health endpoint — a 404 still proves it's reachable)
  try {
    const ncaUrl = process.env.NCA_TOOLKIT_URL || 'http://nca-toolkit:8080';
    const ncaRes = await fetch(`${ncaUrl}/`, { signal: AbortSignal.timeout(3000) });
    checks.nca_toolkit = { status: ncaRes.status === 404 || ncaRes.ok ? 'ok' : 'error', statusCode: ncaRes.status };
  } catch (err) {
    checks.nca_toolkit = { status: 'unreachable', message: err.message };
  }

  // Telegram bot configuration
  checks.telegram = {
    status: telegramBotToken ? 'ok' : 'not_configured',
    chatConfigured: !!TELEGRAM_CHAT_ID,
  };

  res.status(healthy ? 200 : 503).json({
    status: healthy ? 'healthy' : 'degraded',
    checks,
    timestamp: new Date().toISOString(),
  });
});

// GET /jobs/status - get running job status
app.get('/jobs/status', async (req, res) => {
  try {
    const result = await getJobStatus(req.query.job_id);
    res.json(result);
  } catch (err) {
    log.error({ err }, 'Failed to get job status');
    res.status(500).json({ error: 'Failed to get job status' });
  }
});

// GET /systems - list all systems in the catalog
app.get('/systems', async (req, res) => {
  try {
    const systems = await getSystemsCatalog();
    res.json({ systems, count: systems.length });
  } catch (err) {
    log.error({ err }, 'Failed to get systems catalog');
    res.status(500).json({ error: 'Failed to get systems catalog' });
  }
});

// GET /chat/history - retrieve web dashboard chat history
app.get('/chat/history', (req, res) => {
  const history = getHistory('web-dashboard');
  res.json({ messages: history });
});

// DELETE /chat/history - clear web dashboard chat history
app.delete('/chat/history', (req, res) => {
  clearHistory('web-dashboard');
  res.json({ ok: true });
});

// POST /chat - web dashboard chat with Claude
app.post('/chat', chatLimiter, async (req, res) => {
  try {
    const { message } = validate(chatMessageSchema, req.body);
    const sanitized = sanitizeUserInput(message);

    const history = getHistory('web-dashboard');
    const { response, history: newHistory } = await chat(
      sanitized,
      history,
      toolDefinitions,
      toolExecutors
    );
    updateHistory('web-dashboard', newHistory);

    res.json({ response });
  } catch (err) {
    if (err.status === 400) return res.status(400).json({ error: err.message });
    log.error({ err }, 'Failed to process chat message');
    res.status(500).json({ error: 'Failed to process chat message' });
  }
});

// POST /webhook - create a new job
app.post('/webhook', jobLimiter, async (req, res) => {
  try {
    const { job } = validate(webhookJobSchema, req.body);
    const result = await createJob(job);
    res.json(result);
  } catch (err) {
    if (err.status === 400) return res.status(400).json({ error: err.message });
    log.error({ err }, 'Failed to create job');
    res.status(500).json({ error: 'Failed to create job' });
  }
});

// POST /telegram/register - register a Telegram webhook
app.post('/telegram/register', async (req, res) => {
  try {
    const { bot_token, webhook_url } = validate(telegramRegisterSchema, req.body);
    const result = await setWebhook(bot_token, webhook_url, TELEGRAM_WEBHOOK_SECRET);
    telegramBotToken = bot_token;
    res.json({ success: true, result });
  } catch (err) {
    if (err.status === 400) return res.status(400).json({ error: err.message });
    log.error({ err }, 'Failed to register webhook');
    res.status(500).json({ error: 'Failed to register webhook' });
  }
});

// POST /telegram/webhook - receive Telegram updates
app.post('/telegram/webhook', telegramLimiter, async (req, res) => {
  // Validate secret token if configured
  // Always return 200 to prevent Telegram retry loops on mismatch
  if (TELEGRAM_WEBHOOK_SECRET) {
    const headerSecret = req.headers['x-telegram-bot-api-secret-token'];
    if (headerSecret !== TELEGRAM_WEBHOOK_SECRET) {
      return res.status(200).json({ ok: true });
    }
  }

  const update = req.body;
  const message = update.message || update.edited_message;

  if (message && message.chat && telegramBotToken) {
    const chatId = String(message.chat.id);

    let messageText = null;

    if (message.text) {
      messageText = message.text;
    }

    // Check for verification code - this works even before TELEGRAM_CHAT_ID is set
    if (TELEGRAM_VERIFICATION && messageText === TELEGRAM_VERIFICATION) {
      await sendMessage(telegramBotToken, chatId, `Your chat ID:\n<code>${chatId}</code>`);
      return res.status(200).json({ ok: true });
    }

    // Security: if no TELEGRAM_CHAT_ID configured, ignore all messages (except verification above)
    if (!TELEGRAM_CHAT_ID) {
      return res.status(200).json({ ok: true });
    }

    // Security: only accept messages from configured chat
    if (chatId !== TELEGRAM_CHAT_ID) {
      return res.status(200).json({ ok: true });
    }

    // Acknowledge receipt with a thumbs up (await so it completes before typing indicator starts)
    await reactToMessage(telegramBotToken, chatId, message.message_id).catch(() => {});

    if (message.voice) {
      // Handle voice messages
      if (!isWhisperEnabled()) {
        await sendMessage(telegramBotToken, chatId, 'Voice messages are not supported. Please set OPENAI_API_KEY to enable transcription.');
        return res.status(200).json({ ok: true });
      }

      try {
        const { buffer, filename } = await downloadFile(telegramBotToken, message.voice.file_id);
        messageText = await transcribeAudio(buffer, filename);
      } catch (err) {
        log.error({ err }, 'Failed to transcribe voice');
        await sendMessage(telegramBotToken, chatId, 'Sorry, I could not transcribe your voice message.');
        return res.status(200).json({ ok: true });
      }
    }

    // Acknowledge receipt immediately so Telegram doesn't wait/retry
    res.status(200).json({ ok: true });

    // /status command — bypass Claude, respond directly with system status
    if (messageText && messageText.trim().toLowerCase().startsWith('/status')) {
      try {
        const jobResult = await getJobStatus();
        const convCount = getConversationCount();
        const uptimeSec = Math.floor((Date.now() - startedAt) / 1000);

        const formatUptime = (s) => {
          const d = Math.floor(s / 86400);
          const h = Math.floor((s % 86400) / 3600);
          const m = Math.floor((s % 3600) / 60);
          return [d && `${d}d`, h && `${h}h`, m && `${m}m`, `${s % 60}s`].filter(Boolean).join(' ');
        };

        const runningJobs = jobResult.jobs.filter(j => j.status === 'in_progress');
        const queuedJobs = jobResult.jobs.filter(j => j.status === 'queued');

        let jobLines = '';
        if (runningJobs.length === 0 && queuedJobs.length === 0) {
          jobLines = '  No active jobs';
        } else {
          for (const j of runningJobs) {
            jobLines += `  ▶ <code>${j.job_id.slice(0, 8)}</code> — running ${j.duration_minutes}m`;
            if (j.current_step) jobLines += ` (${j.current_step})`;
            jobLines += '\n';
          }
          for (const j of queuedJobs) {
            jobLines += `  ⏳ <code>${j.job_id.slice(0, 8)}</code> — queued\n`;
          }
        }

        const statusMsg = [
          '<b>System Status</b>',
          '',
          `⏱ Uptime: ${formatUptime(uptimeSec)}`,
          `💬 Active conversations: ${convCount}`,
          `🔧 Running jobs: ${runningJobs.length}`,
          `📋 Queued jobs: ${queuedJobs.length}`,
          '',
          '<b>Jobs:</b>',
          jobLines.trimEnd(),
        ].join('\n');

        await sendMessage(telegramBotToken, chatId, statusMsg);
      } catch (err) {
        log.error({ err }, 'Failed to get system status');
        await sendMessage(telegramBotToken, chatId, 'Failed to retrieve system status.').catch(() => {});
      }
      return;
    }

    if (messageText) {
      messageText = sanitizeUserInput(messageText);
      const stopTyping = startTypingIndicator(telegramBotToken, chatId);
      try {
        // Get conversation history and process with Claude
        const history = getHistory(chatId);
        const { response, history: newHistory } = await chat(
          messageText,
          history,
          toolDefinitions,
          toolExecutors
        );
        updateHistory(chatId, newHistory);

        // Send response (convert markdown → Telegram HTML, auto-splits if needed)
        await sendMessage(telegramBotToken, chatId, mdToTelegramHtml(response));
      } catch (err) {
        log.error({ err, chatId }, 'Failed to process message with Claude');
        await sendMessage(telegramBotToken, chatId, 'Sorry, I encountered an error processing your message.').catch(() => {});
      } finally {
        stopTyping();
      }
    }
  } else {
    // No message to process — still acknowledge
    res.status(200).json({ ok: true });
  }
});

/**
 * Extract job ID from branch name (e.g., "job/abc123" -> "abc123")
 */
function extractJobId(branchName) {
  if (!branchName || !branchName.startsWith('job/')) return null;
  return branchName.slice(4);
}

/**
 * Summarize a completed job using Claude — returns the raw message to send
 * @param {Object} results - Job results from webhook payload
 * @param {string} results.job - Original task (job.md)
 * @param {string} results.commit_message - Final commit message
 * @param {string[]} results.changed_files - List of changed file paths
 * @param {string} results.pr_status - PR state (open, closed, merged)
 * @param {string} results.log - Agent session log (JSONL)
 * @param {string} results.pr_url - PR URL
 * @returns {Promise<string>} The message to send to Telegram
 */
async function summarizeJob(results) {
  try {
    const apiKey = getApiKey();

    // System prompt from JOB_SUMMARY.md (supports {{includes}})
    const systemPrompt = render_md(
      path.join(__dirname, '..', 'operating_system', 'JOB_SUMMARY.md')
    );

    // User message: structured job results
    const userMessage = [
      results.job ? `## Task\n${results.job}` : '',
      results.commit_message ? `## Commit Message\n${results.commit_message}` : '',
      results.changed_files?.length ? `## Changed Files\n${results.changed_files.join('\n')}` : '',
      results.pr_status ? `## PR Status\n${results.pr_status}` : '',
      results.merge_result ? `## Merge Result\n${results.merge_result}` : '',
      results.pr_url ? `## PR URL\n${results.pr_url}` : '',
      results.log ? `## Agent Log\n${results.log}` : '',
    ].filter(Boolean).join('\n\n');

    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': apiKey,
        'anthropic-version': '2023-06-01',
      },
      body: JSON.stringify({
        model: process.env.EVENT_HANDLER_MODEL || 'claude-sonnet-4-20250514',
        max_tokens: 1024,
        system: systemPrompt,
        messages: [{ role: 'user', content: userMessage }],
      }),
    });

    if (!response.ok) throw new Error(`Claude API error: ${response.status}`);

    const result = await response.json();
    return (result.content?.[0]?.text || '').trim() || 'Job completed.';
  } catch (err) {
    log.error({ err }, 'Failed to summarize job');
    return 'Job completed.';
  }
}

/**
 * Detect if a completed job generated a PRP.
 * Returns PRP info for the webhook handler to deliver to the user for review.
 */
async function detectPrp(results) {
  const changedFiles = results.changed_files || [];

  // Find a PRP file (exclude templates/)
  const prpFile = changedFiles.find(f =>
    f.startsWith('PRPs/') && f.endsWith('.md') && !f.includes('templates/')
  );
  if (!prpFile) return null;

  const systemName = path.basename(prpFile, '.md');

  // Fetch PRP file content
  let prpContent = '';
  try {
    const prpData = await githubApi(`/repos/${GH_OWNER}/${GH_REPO}/contents/${prpFile}?ref=main`);
    prpContent = Buffer.from(prpData.content, 'base64').toString('utf8');
  } catch (err) {
    log.warn({ err: err.message, prpFile }, 'Could not fetch PRP content');
  }

  // Search for the confidence score
  const searchText = [results.commit_message, results.log, results.job, prpContent].filter(Boolean).join('\n');
  const match = searchText.match(/(?:CONFIDENCE_SCORE|Confidence\s+Score)[:\s]*(\d+)\s*\/\s*10/i);
  const confidence = match ? parseInt(match[1], 10) : null;

  log.info({ systemName, confidence, prpFile }, 'PRP detected');

  return { systemName, confidence, prpFile, prpContent };
}

/**
 * Summarize a PRP for Telegram delivery using Claude.
 * Returns a concise review with key sections, ready for user approval.
 */
async function summarizePrp(systemName, prpContent, confidence) {
  try {
    const apiKey = getApiKey();

    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': apiKey,
        'anthropic-version': '2023-06-01',
      },
      body: JSON.stringify({
        model: process.env.EVENT_HANDLER_MODEL || 'claude-sonnet-4-20250514',
        max_tokens: 2048,
        system: [
          'You are summarizing a Product Requirements Prompt (PRP) for a user to review on Telegram.',
          'Format your response in Telegram HTML (<b>, <i>, <code>).',
          'Include these sections:',
          '1. One-line description of what this system does',
          '2. Architecture overview (subagents, key tools)',
          '3. Key capabilities (bulleted list)',
          '4. Ambiguity flags or risks (if any)',
          '5. Confidence score rationale (brief)',
          '',
          'Keep it concise but complete enough for an informed approval decision.',
          'Do NOT use markdown — only Telegram HTML tags.',
        ].join('\n'),
        messages: [{ role: 'user', content: prpContent }],
      }),
    });

    if (!response.ok) throw new Error(`Claude API error: ${response.status}`);

    const result = await response.json();
    return (result.content?.[0]?.text || '').trim();
  } catch (err) {
    log.error({ err, systemName }, 'Failed to summarize PRP');
    return null;
  }
}

// POST /github/webhook - receive GitHub PR notifications
app.post('/github/webhook', webhookLimiter, async (req, res) => {
  // Validate webhook secret via GitHub's X-Hub-Signature-256 header (HMAC-SHA256)
  // Falls back to custom x-github-webhook-secret-token for workflow-initiated webhooks
  if (GH_WEBHOOK_SECRET) {
    const hubSignature = req.headers['x-hub-signature-256'];
    const customHeader = req.headers['x-github-webhook-secret-token'];
    const headerSecret = hubSignature || customHeader;

    if (!headerSecret) {
      log.warn({ ip: req.ip, event: req.headers['x-github-event'] }, 'GitHub webhook auth missing');
      return res.status(401).json({ error: 'Unauthorized' });
    }

    if (isHmacSignature(headerSecret)) {
      // HMAC path: verify signature against raw body
      if (!req.rawBody || !verifyHmac(GH_WEBHOOK_SECRET, req.rawBody, headerSecret)) {
        log.warn({ ip: req.ip, event: req.headers['x-github-event'] }, 'GitHub webhook HMAC verification failed');
        return res.status(401).json({ error: 'Unauthorized' });
      }
    } else {
      // Legacy path: plain string comparison (remove once workflow is updated)
      if (headerSecret !== GH_WEBHOOK_SECRET) {
        log.warn({ ip: req.ip, event: req.headers['x-github-event'] }, 'GitHub webhook auth failed');
        return res.status(401).json({ error: 'Unauthorized' });
      }
    }
  }

  const event = req.headers['x-github-event'];

  if (event !== 'pull_request') {
    return res.status(200).json({ ok: true, skipped: true });
  }

  let payload;
  try {
    payload = validate(githubWebhookSchema, req.body);
  } catch (err) {
    log.warn({ err: err.message }, 'GitHub webhook validation failed');
    return res.status(400).json({ error: err.message });
  }

  const pr = payload.pull_request;
  if (!pr) return res.status(200).json({ ok: true, skipped: true });

  const branchName = pr.head?.ref;
  const jobId = extractJobId(branchName);
  if (!jobId) return res.status(200).json({ ok: true, skipped: true, reason: 'not a job branch' });

  if (!TELEGRAM_CHAT_ID || !telegramBotToken) {
    log.info({ jobId }, 'Job completed but no chat ID to notify');
    return res.status(200).json({ ok: true, skipped: true, reason: 'no chat to notify' });
  }

  try {
    // All job data comes from the webhook payload — no GitHub API calls needed
    const results = payload.job_results || {};
    results.pr_url = pr.html_url;

    const message = await retry(() => summarizeJob(results), {
      label: `summarize-job-${jobId.slice(0, 8)}`,
    });

    await retry(() => sendMessage(telegramBotToken, TELEGRAM_CHAT_ID, mdToTelegramHtml(message)), {
      label: `notify-telegram-${jobId.slice(0, 8)}`,
    });

    // Add the summary to chat memory so Claude has context in future conversations
    const history = getHistory(TELEGRAM_CHAT_ID);
    history.push({ role: 'assistant', content: message });

    // If this job generated a PRP, summarize it and send for user approval
    const prpInfo = await detectPrp(results);
    if (prpInfo) {
      const prpSummary = await retry(() => summarizePrp(prpInfo.systemName, prpInfo.prpContent, prpInfo.confidence), {
        label: `summarize-prp-${jobId.slice(0, 8)}`,
      });

      const prpUrl = `https://github.com/${GH_OWNER}/${GH_REPO}/blob/main/${prpInfo.prpFile}`;
      const confidenceText = prpInfo.confidence !== null
        ? `Confidence: <b>${prpInfo.confidence}/10</b>`
        : 'Confidence: <b>unknown</b>';

      const reviewMsg = [
        `<b>PRP Ready for Review</b>`,
        '',
        `System: <b>${prpInfo.systemName}</b>`,
        confidenceText,
        `<a href="${prpUrl}">View full PRP on GitHub</a>`,
        '',
        prpSummary || 'Could not generate summary.',
        '',
        '<b>Options:</b>',
        '• Say "build it" to kick off the build',
        '• Reply with feedback to refine the PRP',
      ].join('\n');

      await retry(() => sendMessage(telegramBotToken, TELEGRAM_CHAT_ID, reviewMsg), {
        label: `notify-prp-review-${jobId.slice(0, 8)}`,
      });
      history.push({ role: 'assistant', content: reviewMsg });
    }

    updateHistory(TELEGRAM_CHAT_ID, history);

    log.info({ chatId: TELEGRAM_CHAT_ID, jobId: jobId.slice(0, 8) }, 'Notified chat about job');

    // Auto-pull repo when a job is merged
    if (results.merge_result === 'merged') {
      try {
        const { stdout } = await execAsync('git pull', { cwd: '/repo' });
        log.info({ jobId: jobId.slice(0, 8), output: stdout.trim() }, 'Auto-pulled repo after merge');
      } catch (err) {
        log.warn({ err: err.message, jobId: jobId.slice(0, 8) }, 'Auto-pull failed');
      }
    }

    res.status(200).json({ ok: true, notified: true, prpDetected: !!prpInfo });
  } catch (err) {
    log.error({ err }, 'Failed to process GitHub webhook');
    res.status(500).json({ error: 'Failed to process webhook' });
  }
});

// Error handler - don't leak stack traces
app.use((err, req, res, next) => {
  log.error({ err, path: req.path }, 'Unhandled error');
  res.status(500).json({ error: 'Internal server error' });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  log.info({ port: PORT }, 'Server started');
  loadCrons();
});
