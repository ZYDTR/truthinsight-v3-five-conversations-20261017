// Audit the official scorer's HTTP calls without modifying requests or responses.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
const originalFetch = globalThis.fetch;
const root = process.env.JUDGE_AUDIT_DIR;
const endpoint = process.env.JUDGE_ENDPOINT;
const redact = text => process.env.JUDGE_API_KEY ? text.split(process.env.JUDGE_API_KEY).join('[REDACTED]') : text;
if (root) fs.mkdirSync(root, {recursive: true});
globalThis.fetch = async (url, options = {}) => {
  if (String(url) !== endpoint || !root) return originalFetch(url, options);
  const id = `${Date.now()}-${crypto.randomUUID()}`;
  const prefix = path.join(root, id);
  const payload = JSON.parse(options.body);
  if (payload.model !== 'qwen3.8-max' || payload.enable_thinking !== false || payload.chat_template_kwargs?.enable_thinking !== false) throw new Error('Unexpected judge model or thinking parameters');
  const started = Date.now();
  fs.writeFileSync(prefix + '.request.json', redact(JSON.stringify({at: new Date().toISOString(), endpoint, payload}, null, 2)));
  try {
    const response = await originalFetch(url, options);
    const body = await response.clone().text();
    fs.writeFileSync(prefix + '.response.txt', redact(body));
    fs.writeFileSync(prefix + '.meta.json', JSON.stringify({status: response.status, elapsed_ms: Date.now() - started}, null, 2));
    return response;
  } catch (error) {
    fs.writeFileSync(prefix + '.meta.json', redact(JSON.stringify({error: String(error), elapsed_ms: Date.now() - started}, null, 2)));
    throw error;
  }
};
