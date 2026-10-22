/* CipherVault browser cryptography (Web Crypto API).
 * AES-256-GCM for files, RSA-2048 OAEP/SHA-256 for key wrapping,
 * PBKDF2-HMAC-SHA-256 for private-key protection.
 * Ported unchanged from the original frontend/crypto.js so existing accounts and files keep working.
 */
const te = new TextEncoder()

export function b64encode(buf) {
  const bytes = new Uint8Array(buf)
  let s = ''
  for (let i = 0; i < bytes.length; i++) s += String.fromCharCode(bytes[i])
  return btoa(s)
}

export function b64decode(b64) {
  const s = atob(b64)
  const out = new Uint8Array(s.length)
  for (let i = 0; i < s.length; i++) out[i] = s.charCodeAt(i)
  return out.buffer
}

export const generateUserKeyPair = () =>
  crypto.subtle.generateKey(
    { name: 'RSA-OAEP', modulusLength: 2048, publicExponent: new Uint8Array([1, 0, 1]), hash: 'SHA-256' },
    true,
    ['wrapKey', 'unwrapKey'],
  )

export async function exportPublicKey(pairOrKey) {
  return b64encode(await crypto.subtle.exportKey('spki', pairOrKey.publicKey || pairOrKey))
}

export async function exportPrivateKey(pairOrKey) {
  return b64encode(await crypto.subtle.exportKey('pkcs8', pairOrKey.privateKey || pairOrKey))
}

export const importPublicKey = (b64) =>
  crypto.subtle.importKey('spki', b64decode(b64), { name: 'RSA-OAEP', hash: 'SHA-256' }, true, ['wrapKey'])

export const importPrivateKey = (b64) =>
  crypto.subtle.importKey('pkcs8', b64decode(b64), { name: 'RSA-OAEP', hash: 'SHA-256' }, true, ['unwrapKey'])

export async function deriveKeyFromPassword(password, saltB64, iterations = 120000) {
  const salt = Uint8Array.from(atob(saltB64), (c) => c.charCodeAt(0))
  const base = await crypto.subtle.importKey('raw', te.encode(password), 'PBKDF2', false, ['deriveKey'])
  return crypto.subtle.deriveKey({ name: 'PBKDF2', salt, iterations, hash: 'SHA-256' }, base, { name: 'AES-GCM', length: 256 }, false, [
    'encrypt',
    'decrypt',
  ])
}

const newSaltB64 = () => b64encode(crypto.getRandomValues(new Uint8Array(16)).buffer)

/* Encrypt exported PKCS#8 with a password-derived AES-GCM key. Returns a JSON string bundle. */
export async function protectPrivateKey(privateKeyB64, password) {
  const salt = newSaltB64()
  const kek = await deriveKeyFromPassword(password, salt)
  const iv = crypto.getRandomValues(new Uint8Array(12))
  const raw = Uint8Array.from(atob(privateKeyB64), (c) => c.charCodeAt(0))
  const ct = await crypto.subtle.encrypt({ name: 'AES-GCM', iv }, kek, raw)
  return JSON.stringify({ salt, iv: b64encode(iv.buffer), data: b64encode(ct), iterations: 120000 })
}

export async function restorePrivateKey(bundleJson, password) {
  const bundle = JSON.parse(bundleJson)
  const kek = await deriveKeyFromPassword(password, bundle.salt, bundle.iterations || 120000)
  const pt = await crypto.subtle.decrypt({ name: 'AES-GCM', iv: new Uint8Array(b64decode(bundle.iv)) }, kek, b64decode(bundle.data))
  return b64encode(pt)
}

export const generateFileEncryptionKey = () => crypto.subtle.generateKey({ name: 'AES-GCM', length: 256 }, true, ['encrypt', 'decrypt'])

/* Encrypt an ArrayBuffer with the FEK. Returns { ciphertext, ivB64 }. */
export async function encryptFile(plaintextBuffer, fek) {
  const iv = crypto.getRandomValues(new Uint8Array(12))
  const ct = await crypto.subtle.encrypt({ name: 'AES-GCM', iv }, fek, plaintextBuffer)
  return { ciphertext: ct, ivB64: b64encode(iv.buffer) }
}

export const decryptFile = (ciphertextBuffer, fek, ivB64) =>
  crypto.subtle.decrypt({ name: 'AES-GCM', iv: new Uint8Array(b64decode(ivB64)) }, fek, ciphertextBuffer)

export async function wrapFileKey(fek, recipientPublicKey) {
  return b64encode(await crypto.subtle.wrapKey('raw', fek, recipientPublicKey, { name: 'RSA-OAEP' }))
}

export const unwrapFileKey = (wrappedB64, ownerPrivateKey) =>
  crypto.subtle.unwrapKey('raw', b64decode(wrappedB64), ownerPrivateKey, { name: 'RSA-OAEP' }, { name: 'AES-GCM', length: 256 }, true, [
    'encrypt',
    'decrypt',
  ])

export async function calculateSHA256(buffer) {
  const digest = await crypto.subtle.digest('SHA-256', buffer)
  return [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, '0')).join('')
}

export async function verifySHA256(buffer, expectedHex) {
  return (await calculateSHA256(buffer)).toLowerCase() === String(expectedHex).toLowerCase()
}

/* Generate the key material for a new account. */
export async function createAccountKeys(password) {
  const pair = await generateUserKeyPair()
  const public_key = await exportPublicKey(pair)
  const bundle = await protectPrivateKey(await exportPrivateKey(pair), password)
  return { public_key, encrypted_private_key: bundle, private_key_salt: JSON.parse(bundle).salt }
}
