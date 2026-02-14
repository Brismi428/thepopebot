/**
 * Persistent conversation history management per Telegram chat.
 * - Keyed by chat_id
 * - 30-minute TTL per conversation
 * - Max 20 messages per conversation
 * - Backed by a JSON file for persistence across restarts
 * - In-memory cache with periodic flush to disk
 */

const fs = require('fs');
const path = require('path');
const log = require('../utils/logger');

const MAX_MESSAGES = 20;
const TTL_MS = 30 * 60 * 1000; // 30 minutes
const CLEANUP_INTERVAL_MS = 5 * 60 * 1000; // 5 minutes
const FLUSH_INTERVAL_MS = 30 * 1000; // 30 seconds

// Storage path — uses /data volume in Docker, falls back to local dir
const DATA_DIR = process.env.CONVERSATION_STORE_PATH || path.join(__dirname, '..', 'data');
const STORE_FILE = path.join(DATA_DIR, 'conversations.json');

// In-memory cache (hot path), periodically flushed to disk
let conversations = new Map();
let dirty = false;

/**
 * Load conversations from disk on startup
 */
function loadFromDisk() {
  try {
    if (fs.existsSync(STORE_FILE)) {
      const data = JSON.parse(fs.readFileSync(STORE_FILE, 'utf8'));
      conversations = new Map(Object.entries(data));
      log.info({ count: conversations.size }, 'Loaded conversations from disk');
    }
  } catch (err) {
    log.error({ err: err.message }, 'Failed to load conversations from disk');
    conversations = new Map();
  }
}

/**
 * Flush conversations to disk
 */
function flushToDisk() {
  if (!dirty) return;

  try {
    if (!fs.existsSync(DATA_DIR)) {
      fs.mkdirSync(DATA_DIR, { recursive: true });
    }
    const data = Object.fromEntries(conversations);
    fs.writeFileSync(STORE_FILE, JSON.stringify(data), 'utf8');
    dirty = false;
  } catch (err) {
    log.error({ err: err.message }, 'Failed to flush conversations to disk');
  }
}

/**
 * Sanitize message history before sending to Claude API.
 * Strips orphaned tool_result blocks (those without a preceding tool_use with matching ID).
 * @param {Array} messages - Message history
 * @returns {Array} - Cleaned message history
 */
function sanitizeHistory(messages) {
  // Collect all tool_use IDs from assistant messages
  const toolUseIds = new Set();
  for (const msg of messages) {
    if (msg.role === 'assistant' && Array.isArray(msg.content)) {
      for (const block of msg.content) {
        if (block.type === 'tool_use') {
          toolUseIds.add(block.id);
        }
      }
    }
  }

  // Filter out user messages that only contain orphaned tool_results
  return messages.filter(msg => {
    if (msg.role !== 'user' || !Array.isArray(msg.content)) return true;

    const validBlocks = msg.content.filter(block => {
      if (block.type !== 'tool_result') return true;
      return toolUseIds.has(block.tool_use_id);
    });

    if (validBlocks.length === 0) return false;
    msg.content = validBlocks;
    return true;
  });
}

/**
 * Get conversation history for a chat
 * @param {string} chatId - Telegram chat ID
 * @returns {Array} - Message history array
 */
function getHistory(chatId) {
  const entry = conversations.get(chatId);
  if (!entry) return [];

  // Check if expired
  if (Date.now() - entry.lastAccess > TTL_MS) {
    conversations.delete(chatId);
    dirty = true;
    return [];
  }

  entry.lastAccess = Date.now();
  dirty = true;
  return sanitizeHistory(entry.messages);
}

/**
 * Update conversation history for a chat
 * @param {string} chatId - Telegram chat ID
 * @param {Array} messages - New message history
 */
function updateHistory(chatId, messages) {
  // Trim to max messages (keep most recent)
  const trimmed = messages.slice(-MAX_MESSAGES);

  conversations.set(chatId, {
    messages: trimmed,
    lastAccess: Date.now(),
  });
  dirty = true;
}

/**
 * Clear conversation history for a chat
 * @param {string} chatId - Telegram chat ID
 */
function clearHistory(chatId) {
  conversations.delete(chatId);
  dirty = true;
}

/**
 * Get the number of active conversations (for health checks)
 * @returns {number}
 */
function getConversationCount() {
  return conversations.size;
}

/**
 * Clean up expired conversations
 */
function cleanupExpired() {
  const now = Date.now();
  for (const [chatId, entry] of conversations) {
    if (now - entry.lastAccess > TTL_MS) {
      conversations.delete(chatId);
      dirty = true;
    }
  }
}

// Initialize: load from disk, start cleanup and flush intervals
loadFromDisk();
setInterval(cleanupExpired, CLEANUP_INTERVAL_MS);
setInterval(flushToDisk, FLUSH_INTERVAL_MS);

// Flush on process exit
process.on('SIGTERM', () => { flushToDisk(); process.exit(0); });
process.on('SIGINT', () => { flushToDisk(); process.exit(0); });

module.exports = {
  getHistory,
  updateHistory,
  clearHistory,
  getConversationCount,
};
