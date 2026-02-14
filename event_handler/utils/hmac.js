const crypto = require('crypto');

/**
 * Verify an HMAC-SHA256 signature against a payload.
 * @param {string} secret - The shared secret key
 * @param {Buffer|string} payload - The raw request body
 * @param {string} signature - The hex-encoded HMAC signature (with or without "sha256=" prefix)
 * @returns {boolean} - Whether the signature is valid
 */
function verifyHmac(secret, payload, signature) {
  if (!secret || !payload || !signature) return false;

  // Strip optional "sha256=" prefix
  const sig = signature.startsWith('sha256=') ? signature.slice(7) : signature;

  const expected = crypto
    .createHmac('sha256', secret)
    .update(payload)
    .digest('hex');

  // Use timing-safe comparison to prevent timing attacks
  try {
    const sigBuf = Buffer.from(sig, 'hex');
    const expectedBuf = Buffer.from(expected, 'hex');
    if (sigBuf.length !== expectedBuf.length) return false;
    return crypto.timingSafeEqual(sigBuf, expectedBuf);
  } catch {
    return false;
  }
}

/**
 * Check if a signature string looks like an HMAC (64-char hex string, optionally prefixed).
 * @param {string} signature - The signature to check
 * @returns {boolean}
 */
function isHmacSignature(signature) {
  if (!signature) return false;
  const sig = signature.startsWith('sha256=') ? signature.slice(7) : signature;
  return /^[0-9a-f]{64}$/i.test(sig);
}

module.exports = { verifyHmac, isHmacSignature };
