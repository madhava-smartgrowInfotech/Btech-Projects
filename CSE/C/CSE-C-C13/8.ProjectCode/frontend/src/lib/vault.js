// File operations that combine the API with browser-side cryptography.
// The server only ever receives ciphertext and RSA-wrapped file keys.
import { api, ApiError } from './api'
import * as C from './vaultCrypto'

export async function uploadFile(file, me, onStage = () => {}) {
  const cfg = await api.config()
  if (file.size > cfg.max_upload_mb * 1024 * 1024) throw new Error(`${file.name} exceeds the ${cfg.max_upload_mb} MB limit.`)
  if (file.size === 0) throw new Error(`${file.name} is empty.`)
  onStage('Encrypting in your browser')
  const buf = await file.arrayBuffer()
  const sha = await C.calculateSHA256(buf)
  const fek = await C.generateFileEncryptionKey()
  const enc = await C.encryptFile(buf, fek)
  const wrapped = await C.wrapFileKey(fek, await C.importPublicKey(me.public_key))
  const form = new FormData()
  form.append('ciphertext', new Blob([enc.ciphertext], { type: 'application/octet-stream' }), 'ciphertext.bin')
  form.append('original_filename', file.name)
  form.append('mime_type', file.type || 'application/octet-stream')
  form.append('original_size', String(file.size))
  form.append('iv', enc.ivB64)
  form.append('wrapped_fek', wrapped)
  form.append('plaintext_sha256', sha)
  onStage('Uploading ciphertext')
  return api.upload(form)
}

// Re-encrypt new content with the file's existing key, so every existing share keeps working.
export async function replaceFileContent(fileId, file, privateKey, onStage = () => {}) {
  const meta = await api.file(fileId)
  if (!meta.wrapped_fek) throw new Error('You do not hold a key for this file.')
  onStage('Encrypting in your browser')
  const fek = await C.unwrapFileKey(meta.wrapped_fek, privateKey)
  const buf = await file.arrayBuffer()
  const sha = await C.calculateSHA256(buf)
  const enc = await C.encryptFile(buf, fek)
  const form = new FormData()
  form.append('ciphertext', new Blob([enc.ciphertext], { type: 'application/octet-stream' }), 'ciphertext.bin')
  form.append('iv', enc.ivB64)
  form.append('plaintext_sha256', sha)
  form.append('original_size', String(file.size))
  onStage('Uploading ciphertext')
  return api.updateFile(fileId, form)
}

// Download ciphertext, decrypt locally, verify AES-GCM tag and SHA-256. Resolves to { blob, name, meta }.
export async function fetchAndDecrypt(fileId, privateKey) {
  const meta = await api.file(fileId)
  const res = await api.download(fileId)
  const ct = await res.arrayBuffer()
  if (!meta.wrapped_fek) throw new Error('You do not hold a key for this file.')
  const fek = await C.unwrapFileKey(meta.wrapped_fek, privateKey)
  let pt
  try {
    pt = await C.decryptFile(ct, fek, meta.iv)
  } catch {
    throw new Error('Decryption failed: the file is corrupted or the key does not match (AES-GCM authentication failed).')
  }
  if (!(await C.verifySHA256(pt, meta.plaintext_sha256))) {
    throw new Error('Integrity check failed: SHA-256 mismatch. The file was not saved.')
  }
  return { blob: new Blob([pt], { type: meta.mime_type || 'application/octet-stream' }), name: meta.original_filename, meta }
}

export function saveBlob(blob, name) {
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = name
  document.body.appendChild(a)
  a.click()
  a.remove()
  setTimeout(() => URL.revokeObjectURL(a.href), 5000)
}

// Re-wrap the file key for a recipient (done locally) and grant access.
export async function shareWith(fileId, email, role, privateKey) {
  const q = email.trim()
  const users = await api.users(q)
  const target = users.find((u) => u.email.toLowerCase() === q.toLowerCase())
  if (!target) throw new ApiError('No registered user with that email address.', 404)
  if (!target.public_key) throw new ApiError('That user has no public key on record.', 400)
  const meta = await api.file(fileId)
  const fek = await C.unwrapFileKey(meta.wrapped_fek, privateKey)
  const wrapped = await C.wrapFileKey(fek, await C.importPublicKey(target.public_key))
  await api.share(fileId, { user_id: target.id, role, wrapped_fek: wrapped })
  return target
}
