const log = require('./logger');

/**
 * Retry a function with exponential backoff.
 * @param {Function} fn - Async function to retry
 * @param {Object} [options]
 * @param {number} [options.attempts=3] - Maximum number of attempts
 * @param {number} [options.baseDelay=1000] - Base delay in ms (doubled each retry)
 * @param {string} [options.label='operation'] - Label for log messages
 * @returns {Promise<*>} Result of the function
 */
async function retry(fn, { attempts = 3, baseDelay = 1000, label = 'operation' } = {}) {
  let lastError;

  for (let i = 1; i <= attempts; i++) {
    try {
      return await fn();
    } catch (err) {
      lastError = err;
      if (i < attempts) {
        const delay = baseDelay * Math.pow(2, i - 1);
        log.warn({ label, attempt: i, attempts, delay, err: err.message }, 'Retrying after failure');
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }

  log.error({ label, attempts, err: lastError.message }, 'All retry attempts exhausted');
  throw lastError;
}

module.exports = { retry };
