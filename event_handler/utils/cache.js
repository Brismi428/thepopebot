/**
 * Simple in-memory TTL cache.
 * @param {number} defaultTtlMs - Default TTL in milliseconds
 */
class TtlCache {
  constructor(defaultTtlMs = 30000) {
    this.defaultTtlMs = defaultTtlMs;
    this.store = new Map();
  }

  /**
   * Get a cached value by key. Returns undefined if expired or missing.
   * @param {string} key
   * @returns {*|undefined}
   */
  get(key) {
    const entry = this.store.get(key);
    if (!entry) return undefined;
    if (Date.now() > entry.expiresAt) {
      this.store.delete(key);
      return undefined;
    }
    return entry.value;
  }

  /**
   * Set a cached value with optional TTL override.
   * @param {string} key
   * @param {*} value
   * @param {number} [ttlMs] - TTL in milliseconds (uses default if omitted)
   */
  set(key, value, ttlMs) {
    this.store.set(key, {
      value,
      expiresAt: Date.now() + (ttlMs || this.defaultTtlMs),
    });
  }

  /**
   * Get a value from cache, or compute and cache it if missing/expired.
   * @param {string} key
   * @param {Function} fn - Async function to compute the value
   * @param {number} [ttlMs] - TTL in milliseconds
   * @returns {Promise<*>}
   */
  async getOrSet(key, fn, ttlMs) {
    const cached = this.get(key);
    if (cached !== undefined) return cached;
    const value = await fn();
    this.set(key, value, ttlMs);
    return value;
  }

  /**
   * Get the number of entries (for diagnostics).
   * @returns {number}
   */
  get size() {
    return this.store.size;
  }
}

module.exports = { TtlCache };
