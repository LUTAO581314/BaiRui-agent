import { dispatchSocialMessage } from './src/social/dispatch.js'

function write(payload) {
  process.stdout.write(`${JSON.stringify(payload)}\n`)
}

async function readStdinJson() {
  const chunks = []
  for await (const chunk of process.stdin) chunks.push(chunk)
  const raw = Buffer.concat(chunks).toString('utf-8').trim()
  if (!raw) return {}
  return JSON.parse(raw)
}

async function main() {
  try {
    const input = await readStdinJson()
    if (input.action !== 'dispatch') {
      write({ ok: false, error: 'unsupported_action' })
      process.exitCode = 2
      return
    }
    const result = await dispatchSocialMessage(String(input.targetId || ''), input.payload || {})
    if (!result) {
      write({ ok: false, error: 'target_not_supported' })
      process.exitCode = 3
      return
    }
    write({ ok: true, result })
  } catch (error) {
    write({ ok: false, error: error?.message || String(error) })
    process.exitCode = 1
  }
}

await main()
