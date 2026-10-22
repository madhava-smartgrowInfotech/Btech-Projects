// One-click demo: makes sure three fictional accounts exist, fills the owner's vault with synthetic files,
// shares some of them (viewer / editor), and exercises RBAC so the audit log has real events.
// Everything runs through the normal API and the normal browser-side encryption.
import { api, ApiError, setToken } from './api'
import * as C from './vaultCrypto'
import { replaceFileContent, shareWith, uploadFile } from './vault'

export const DEMO_ACCOUNTS = {
  owner: { name: 'Olivia Owner', email: 'owner@example.com', password: 'Demo-Owner-123', label: 'Owner' },
  editor: { name: 'Eddie Editor', email: 'editor@example.com', password: 'Demo-Editor-123', label: 'Editor' },
  viewer: { name: 'Vera Viewer', email: 'viewer@example.com', password: 'Demo-Viewer-123', label: 'Viewer' },
}

const text = (name, body) => new File([body], name, { type: 'text/plain' })

function syntheticFiles() {
  const stamp = new Date().toISOString().slice(0, 10)
  const csv = ['quarter,region,revenue_usd,headcount', 'Q1,EMEA,1204500,42', 'Q1,APAC,998200,31', 'Q2,EMEA,1311900,44', 'Q2,APAC,1102300,35'].join('\n')
  return [
    {
      file: text('Q3-board-memo.txt', `CONFIDENTIAL - BOARD MEMO (${stamp})\n\nSynthetic demo document.\nProject Lighthouse enters pilot in October. Budget approved: 240,000 USD.\nOwner: Olivia Owner. Reviewers: Eddie Editor (edit), Vera Viewer (read only).\n`),
      share: [['editor', 'editor'], ['viewer', 'viewer']],
    },
    { file: new File([csv], 'regional-revenue.csv', { type: 'text/csv' }), share: [['viewer', 'viewer']] },
    {
      file: new File([JSON.stringify({ service: 'billing-api', rotated: stamp, note: 'synthetic demo credentials - not real', keys: ['demo-key-a1', 'demo-key-b2'] }, null, 2)], 'api-credentials.json', {
        type: 'application/json',
      }),
      share: [],
    },
    { file: text('employee-handbook-draft.md', '# Employee handbook (draft)\n\n1. Remote work policy\n2. Security basics: encrypt everything, share least privilege.\n3. Incident response contacts\n'), share: [['editor', 'editor']] },
    { file: text('design-review-notes.txt', 'Design review notes\n- Move audit view into the security area\n- Add dark mode toggle\n- Hash-chain verification on a schedule\n'), share: [] },
  ]
}

async function ensureAccounts(onStep) {
  for (const a of Object.values(DEMO_ACCOUNTS)) {
    onStep(`Creating ${a.label.toLowerCase()} account (generating RSA-2048 keys)`)
    try {
      const keys = await C.createAccountKeys(a.password)
      await api.register({ name: a.name, email: a.email, password: a.password, ...keys })
    } catch (err) {
      if (!(err instanceof ApiError && err.status === 400)) throw err // 400 = already exists
    }
  }
}

async function loginAs(key, withKey = false) {
  const a = DEMO_ACCOUNTS[key]
  const { access_token } = await api.login(a.email, a.password)
  setToken(access_token)
  const me = await api.me()
  let privateKey = null
  if (withKey) {
    const { bundle } = await api.keyBundle()
    privateKey = await C.importPrivateKey(await C.restorePrivateKey(bundle, a.password))
  }
  return { me, privateKey, token: access_token }
}

async function seed(onStep) {
  const owner = await loginAs('owner', true)
  const created = []
  const plan = syntheticFiles()
  for (const item of plan) {
    onStep(`Encrypting and uploading ${item.file.name}`)
    const rec = await uploadFile(item.file, owner.me)
    created.push({ rec, item })
  }
  for (const { rec, item } of created) {
    for (const [who, role] of item.share) {
      onStep(`Sharing ${rec.original_filename} with the ${who}`)
      await shareWith(rec.id, DEMO_ACCOUNTS[who].email, role, owner.privateKey)
    }
  }
  const memo = created[0].rec

  onStep('Editor updates the board memo (allowed)')
  const ed = await loginAs('editor', true)
  await replaceFileContent(memo.id, text('Q3-board-memo.txt', `CONFIDENTIAL - BOARD MEMO (revised)\n\nSynthetic demo document, edited by Eddie Editor.\nProject Lighthouse pilot confirmed. Budget: 240,000 USD. Legal review pending.\n`), ed.privateKey)

  onStep('Viewer tries to delete a file (denied and audited)')
  await loginAs('viewer')
  try {
    await api.remove(memo.id)
  } catch {
    /* expected: 403 */
  }
  try {
    await api.fileAudit(memo.id)
  } catch {
    /* expected: 403 */
  }
  setToken(null)
}

// Ensure demo data exists. Safe to call repeatedly; only seeds an empty owner vault.
export async function prepareDemo(onStep = () => {}) {
  onStep('Checking demo accounts')
  let needsSeed = false
  try {
    const { me } = await loginAs('owner')
    void me
    needsSeed = (await api.files()).length === 0
  } catch (err) {
    if (!(err instanceof ApiError) || err.status !== 401) throw err
    await ensureAccounts(onStep)
    needsSeed = true
  } finally {
    setToken(null)
  }
  if (needsSeed) await seed(onStep)
}
