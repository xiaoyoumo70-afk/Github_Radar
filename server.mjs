#!/usr/bin/env node
/**
 * github-radar-ui — API server (zero dependencies, Node.js built-ins only)
 *
 * REST API:
 *   GET  /api/projects               — list analyzed projects
 *   GET  /api/projects/:safe_name     — project detail (markdown from Obsidian)
 *   POST /api/search                  — natural language search via LLM
 *   GET  /api/settings                — read settings
 *   PUT  /api/settings                — update settings
 *   GET  /api/models                  — available models from LLM endpoint
 */

import { createServer } from 'node:http';
import { spawn } from 'node:child_process';
import { readFileSync, writeFileSync, appendFileSync, existsSync, mkdirSync, readdirSync, statSync, rmSync } from 'node:fs';
import { join, dirname, extname } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const PORT        = parseInt(process.env.PORT || '4420', 10);
const __dirname   = dirname(fileURLToPath(import.meta.url));
const DATA_DIR    = process.env.GITHUB_RADAR_DATA_DIR || __dirname;
const ARTIFACTS   = process.env.ARTIFACTS_DIR
  ? (process.env.ARTIFACTS_DIR.startsWith('/') ? process.env.ARTIFACTS_DIR : join(DATA_DIR, process.env.ARTIFACTS_DIR))
  : join(DATA_DIR, 'artifacts');
const SETTINGS_PATH = join(DATA_DIR, '.ui-settings.json');
const ENV_PATH     = join(DATA_DIR, '.env');
const PUBLIC_DIR   = join(__dirname, 'public');
const LOG_DIR      = join(DATA_DIR, 'logs');
const SEARCH_ERROR_LOG = join(LOG_DIR, 'search-errors.log');
mkdirSync(DATA_DIR, { recursive: true });
mkdirSync(ARTIFACTS, { recursive: true });
mkdirSync(LOG_DIR, { recursive: true });

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
};

const PROVIDER_PRESETS = {
  local:    { base_url: 'http://localhost:8000/v1', needs_key: false },
  openai:   { base_url: 'https://api.openai.com/v1', needs_key: true },
  deepseek: { base_url: 'https://api.deepseek.com/v1', needs_key: true },
  custom:   { base_url: 'http://localhost:8000/v1', needs_key: true },
};

function resolveBaseUrl(settings) {
  const preset = PROVIDER_PRESETS[settings.llm_provider] || PROVIDER_PRESETS.local;
  return settings.llm_base_url || preset.base_url;
}

const DEFAULT_SETTINGS = {
  llm_provider: 'local',
  llm_base_url: '',
  llm_model: 'qwen3.7',
  llm_api_key: '',
  github_token: '',
  obsidian_vault: 'AI-Vault',
  theme: 'system',
};

// ── Helpers ──────────────────────────────────────────────────────────
function json(res, data, status = 200) {
  const body = JSON.stringify(data);
  res.writeHead(status, { 'Content-Type': 'application/json; charset=utf-8' });
  res.end(body);
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    let body = '';
    req.on('data', c => { body += c; if (body.length > 1_000_000) req.destroy(); });
    req.on('end', () => { try { resolve(body ? JSON.parse(body) : {}); } catch (e) { reject(e); } });
    req.on('error', reject);
  });
}

function loadSettings() {
  try {
    if (existsSync(SETTINGS_PATH)) {
      return { ...DEFAULT_SETTINGS, ...JSON.parse(readFileSync(SETTINGS_PATH, 'utf-8')) };
    }
  } catch {}
  return { ...DEFAULT_SETTINGS };
}

function saveSettingsFile(data) {
  writeFileSync(SETTINGS_PATH, JSON.stringify(data, null, 2));
}

function loadEnv() {
  const s = { ...DEFAULT_SETTINGS };
  try {
    if (existsSync(ENV_PATH)) {
      const lines = readFileSync(ENV_PATH, 'utf-8').split('\n');
      for (const line of lines) {
        const m = line.match(/^(\w+)\s*=\s*(.+)/);
        if (m) {
          const k = m[1].toLowerCase();
          if (k === 'llm_provider') s.llm_provider = m[2].trim();
          if (k === 'llm_base_url') s.llm_base_url = m[2].trim();
          if (k === 'llm_model') s.llm_model = m[2].trim();
          if (k === 'llm_api_key') s.llm_api_key = m[2].trim();
          if (k === 'github_token') s.github_token = m[2].trim();
          if (k === 'obsidian_vault') s.obsidian_vault = m[2].trim();
        }
      }
    }
  } catch {}
  return s;
}

function loadEffectiveSettings() {
  let fileSettings = {};
  try {
    if (existsSync(SETTINGS_PATH)) fileSettings = JSON.parse(readFileSync(SETTINGS_PATH, 'utf-8'));
  } catch {}
  return { ...loadEnv(), ...fileSettings };
}

function runSidecar(args, timeoutMs = 30 * 60 * 1000) {
  const sidecar = process.env.GITHUB_RADAR_SIDECAR_PATH;
  if (!sidecar || !existsSync(sidecar)) {
    return Promise.reject(new Error('Python sidecar not found. Build it with packaging/build-python-sidecar-* first.'));
  }
  const settings = loadEffectiveSettings();
  const env = {
    ...process.env,
    GITHUB_TOKEN: settings.github_token || '',
    LLM_PROVIDER: settings.llm_provider || DEFAULT_SETTINGS.llm_provider,
    LLM_BASE_URL: resolveBaseUrl(settings),
    LLM_MODEL: settings.llm_model || DEFAULT_SETTINGS.llm_model,
    LLM_API_KEY: settings.llm_api_key || DEFAULT_SETTINGS.llm_api_key,
    OBSIDIAN_VAULT: settings.obsidian_vault || DEFAULT_SETTINGS.obsidian_vault,
    ARTIFACTS_DIR: ARTIFACTS,
    GITHUB_RADAR_DATA_DIR: DATA_DIR,
  };

  return new Promise((resolve, reject) => {
    const child = spawn(sidecar, args, { cwd: DATA_DIR, env });
    let stdout = '';
    let stderr = '';
    const timer = setTimeout(() => {
      child.kill('SIGTERM');
      reject(new Error(`Sidecar timeout after ${timeoutMs}ms`));
    }, timeoutMs);
    child.stdout.on('data', (chunk) => { stdout += chunk.toString(); });
    child.stderr.on('data', (chunk) => { stderr += chunk.toString(); });
    child.on('error', (err) => {
      clearTimeout(timer);
      reject(err);
    });
    child.on('close', (code) => {
      clearTimeout(timer);
      if (code === 0) resolve({ code, stdout, stderr });
      else reject(new Error(`Sidecar exited ${code}\n${stdout}\n${stderr}`));
    });
  });
}

function makeErrorLogId() {
  return `search-${new Date().toISOString().replace(/[:.]/g, '-')}-${Math.random().toString(36).slice(2, 8)}`;
}

function serializeError(err) {
  return {
    name: err?.name || 'Error',
    message: err?.message || String(err),
    stack: err?.stack || '',
    cause: err?.cause ? serializeError(err.cause) : undefined,
  };
}

function safeText(value, max = 12000) {
  const s = typeof value === 'string' ? value : JSON.stringify(value, null, 2);
  return s.length > max ? `${s.slice(0, max)}\n...[truncated ${s.length - max} chars]` : s;
}

function buildSearchFailureLog({ id, query, settings, projects, prompt, responseStatus, responseText, raw, error }) {
  const now = new Date().toISOString();
  const safeSettings = {
    llm_provider: settings.llm_provider,
    llm_base_url: resolveBaseUrl(settings),
    llm_model: settings.llm_model,
    llm_api_key_present: !!settings.llm_api_key,
    github_token_present: !!settings.github_token,
    obsidian_vault: settings.obsidian_vault,
  };
  return [
    `# GitHub Radar Search Failure`,
    `id: ${id}`,
    `time: ${now}`,
    `query: ${query}`,
    `data_dir: ${DATA_DIR}`,
    `artifacts_dir: ${ARTIFACTS}`,
    `settings: ${JSON.stringify(safeSettings)}`,
    `project_count: ${projects.length}`,
    `response_status: ${responseStatus || 'n/a'}`,
    '',
    `## Error`,
    safeText(serializeError(error)),
    '',
    `## LLM Raw Message`,
    safeText(raw || ''),
    '',
    `## HTTP Response Text`,
    safeText(responseText || ''),
    '',
    `## Prompt`,
    safeText(prompt || ''),
    '',
    `---`,
    '',
  ].join('\n');
}

function writeSearchFailureLog(payload) {
  const logText = buildSearchFailureLog(payload);
  appendFileSync(SEARCH_ERROR_LOG, logText, 'utf-8');
  return logText;
}

async function summarizeSearchFailure({ settings, query, logText, error }) {
  const compactLog = safeText(logText, 10000);
  const prompt = `你是 GitHub Radar 的故障诊断助手。请根据失败日志总结搜索失败原因。\n\n要求：\n1. 用中文。\n2. 先给一句最可能原因。\n3. 再列出 2-4 个证据。\n4. 最后给 1-3 个修复建议。\n5. 不要泄露 token 或密钥。\n\n用户搜索：${query}\n\n错误：${error?.message || String(error)}\n\n完整日志摘录：\n${compactLog}`;

  const baseUrl = resolveBaseUrl(settings);
  const headers = { 'Content-Type': 'application/json' };
  if (settings.llm_api_key) {
    headers['Authorization'] = `Bearer ${settings.llm_api_key}`;
  }
  try {
    const resp = await fetch(`${baseUrl}/chat/completions`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        model: settings.llm_model,
        messages: [
          { role: 'system', content: '你是严谨的应用故障诊断助手，输出中文短报告。' },
          { role: 'user', content: prompt },
        ],
        temperature: 0.2,
        max_tokens: 800,
      }),
      signal: AbortSignal.timeout(30000),
    });
    if (!resp.ok) throw new Error(`summary LLM HTTP ${resp.status}`);
    const data = await resp.json();
    const text = data.choices?.[0]?.message?.content || data.choices?.[0]?.message?.reasoning_content || '';
    if (!text.trim()) throw new Error('summary LLM returned empty message');
    return { ok: true, text: text.trim() };
  } catch (summaryError) {
    return {
      ok: false,
      text: `AI 总结失败：${summaryError.message}\n基础判断：搜索失败发生在 LLM 搜索链路，原始错误为「${error?.message || String(error)}」。请优先检查模型 API 地址、模型名、服务可用性，以及返回内容是否为合法 JSON。`,
      error: summaryError.message,
    };
  }
}

// ── Project helpers ──────────────────────────────────────────────────
function listProjects() {
  const projects = [];
  if (!existsSync(ARTIFACTS)) return projects;

  for (const dir of readdirSync(ARTIFACTS)) {
    const d = join(ARTIFACTS, dir);
    if (!statSync(d).isDirectory()) continue;
    if (dir === 'repos' || dir === 'tasks' || dir === 'topics' || dir === 'topics_cache') continue;

    const metaFile = join(d, 'metadata.json');
    const synFile  = join(d, 'analyses', 'final_synthesis.json');
    const taskFile = join(d, 'checkpoints', 'task_state.json');

    if (!existsSync(metaFile)) continue;

    try {
      const meta = JSON.parse(readFileSync(metaFile, 'utf-8'));
      const syn  = existsSync(synFile) ? JSON.parse(readFileSync(synFile, 'utf-8')) : null;
      const task = existsSync(taskFile) ? JSON.parse(readFileSync(taskFile, 'utf-8')) : {};

      projects.push({
        safe_name: dir,
        full_name: meta.repo || dir.replace(/__/g, '/'),
        url: meta.url || '',
        description: meta.description || '',
        language: meta.language || '',
        topics: meta.topics || [],
        stars: meta.stars || 0,
        forks: meta.forks || 0,
        license: meta.license || '',
        pushed_at: meta.pushed_at || '',
        fetched_at: meta.fetched_at || '',
        status: task.status || 'unknown',
        takeaway: syn?.one_sentence_takeaway || '',
        action: syn?.recommended_action || '',
        tags: syn?.obsidian_tags || [],
        innovations: syn?.key_innovations || [],
      });
    } catch (e) {
      console.error(`Error reading ${dir}:`, e.message);
    }
  }

  projects.sort((a, b) => b.stars - a.stars);
  return projects;
}

function getProjectMarkdown(safeName) {
  const settings = loadSettings();
  const vaultName = settings.obsidian_vault || 'AI-Vault';
  const vaultBase = process.env.OBSIDIAN_VAULT_PATH
    || join(DATA_DIR, 'vaults', vaultName);
  const mdPath = join(vaultBase, 'Projects', 'GitHub Radar', 'Repos', `${safeName}.md`);
  if (existsSync(mdPath)) {
    return readFileSync(mdPath, 'utf-8');
  }
  return null;
}

async function fetchModels(baseUrl, apiKey) {
  const headers = {};
  if (apiKey) headers['Authorization'] = `Bearer ${apiKey}`;
  try {
    const resp = await fetch(`${baseUrl}/models`, {
      headers,
      signal: AbortSignal.timeout(5000),
    });
    if (!resp.ok) return [];
    const data = await resp.json();
    return (data.data || data.models || data || []).map(m => ({
      id: m.id || m.name || m.model || 'unknown',
      name: m.name || m.model || m.id || 'unknown',
    }));
  } catch {
    return [];
  }
}

// ── Static file server ──────────────────────────────────────────────
function serveStatic(res, pathname) {
  let filePath = join(PUBLIC_DIR, pathname === '/' ? 'index.html' : pathname);
  if (!existsSync(filePath)) {
    // SPA fallback
    filePath = join(PUBLIC_DIR, 'index.html');
  }
  const ext = extname(filePath);
  const ct = MIME[ext] || 'application/octet-stream';
  try {
    const data = readFileSync(filePath);
    res.writeHead(200, { 'Content-Type': ct, 'Content-Length': data.length });
    res.end(data);
  } catch {
    res.writeHead(404);
    res.end('Not Found');
  }
}

// ── Router ──────────────────────────────────────────────────────────
async function handleRequest(req, res) {
  const url = new URL(req.url, `http://${req.headers.host}`);
  const method = req.method.toUpperCase();
  const pathname = url.pathname;

  // Static files
  if (method === 'GET' && !pathname.startsWith('/api/')) {
    return serveStatic(res, pathname);
  }

  // CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (method === 'OPTIONS') {
    res.writeHead(204);
    return res.end();
  }

  try {
    // GET /api/projects
    if (method === 'GET' && pathname === '/api/projects') {
      return json(res, listProjects());
    }

    // GET /api/projects/:safe_name
    const projMatch = pathname.match(/^\/api\/projects\/([^/]+)$/);
    if (method === 'GET' && projMatch) {
      const safeName = projMatch[1];
      const projects = listProjects();
      const proj = projects.find(p => p.safe_name === safeName);
      if (!proj) return json(res, { error: 'Not found' }, 404);
      const md = getProjectMarkdown(safeName);
      return json(res, { ...proj, markdown: md });
    }

    // DELETE /api/projects/:safe_name
    if (method === 'DELETE' && projMatch) {
      const safeName = projMatch[1];
      if (safeName.includes('..') || safeName.includes('/')) {
        return json(res, { error: 'Invalid project name' }, 400);
      }
      const dir = join(ARTIFACTS, safeName);
      if (!existsSync(dir)) return json(res, { error: 'Not found' }, 404);
      rmSync(dir, { recursive: true, force: true });
      return json(res, { ok: true, deleted: safeName });
    }

    // POST /api/search
    if (method === 'POST' && pathname === '/api/search') {
      const { query } = await readBody(req);
      if (!query || !query.trim()) {
        const projects = listProjects();
        return json(res, { results: projects, interpreted: '', total: projects.length });
      }

      const settings = loadSettings();
      const projects = listProjects();
      if (projects.length === 0) return json(res, { results: [], interpreted: '暂无已分析项目' });

      const summaries = projects.map((p, i) =>
        `${i}. ${p.full_name} | ⭐${p.stars} | ${p.language || '?'} | ${p.description || ''} | topics: ${(p.topics||[]).join(', ')} | 总结: ${p.takeaway || ''}`
      ).join('\n');

      const llmPrompt = `你是一个GitHub项目搜索引擎。用户输入自然语言查询，需要从项目列表中找出最匹配的项目。

查询："${query.trim()}"

项目列表：
${summaries}

请严格返回 JSON：
{
  "interpreted": "理解用户想找什么（≤40字）",
  "matched_indices": [0],
  "reasoning": "匹配理由（≤100字）"
}

只返回匹配的项目索引（数字），不返回不相关的。如果没有匹配的，返回空数组。`;

        let responseStatus = null;
        let responseText = '';
        let raw = '';
        const baseUrl = resolveBaseUrl(settings);
        const headers = { 'Content-Type': 'application/json' };
        if (settings.llm_api_key) {
          headers['Authorization'] = `Bearer ${settings.llm_api_key}`;
        }
        try {
          const resp = await fetch(`${baseUrl}/chat/completions`, {
          method: 'POST',
          headers,
          body: JSON.stringify({
            model: settings.llm_model,
            messages: [
              { role: 'system', content: '你是GitHub项目搜索助手，严格返回JSON。' },
              { role: 'user', content: llmPrompt },
            ],
            temperature: 0.1,
            max_tokens: 1024,
          }),
          signal: AbortSignal.timeout(60000),
          });

          responseStatus = resp.status;
          responseText = await resp.text();
          if (!resp.ok) throw new Error(`LLM HTTP ${resp.status}: ${responseText.slice(0, 500)}`);
          let data;
          try {
            data = JSON.parse(responseText);
          } catch (parseError) {
            throw new Error(`LLM response is not valid JSON: ${parseError.message}`);
          }
          raw = data.choices?.[0]?.message?.content
               || data.choices?.[0]?.message?.reasoning_content
               || '';

        // Extract valid JSON from reasoning model output (may have thinking text mixed in)
        let parsed = null;
        const jsonMatches = [...raw.matchAll(/\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}/g)];
        // Try each match from last to first (JSON is usually at the end)
        for (let i = jsonMatches.length - 1; i >= 0; i--) {
          try {
            parsed = JSON.parse(jsonMatches[i][0]);
            if (parsed && typeof parsed.matched_indices !== 'undefined') break;
            parsed = null;
          } catch {}
        }
        if (!parsed) throw new Error('No valid JSON found in response');
        const results = (parsed.matched_indices || []).map(i => projects[i]).filter(Boolean);

        return json(res, {
          results,
          interpreted: parsed.interpreted || '',
          reasoning: parsed.reasoning || '',
          total: projects.length,
        });
      } catch (e) {
        console.error('[search] LLM failed:', e.message);
        const failureId = makeErrorLogId();
        const logText = writeSearchFailureLog({
          id: failureId,
          query,
          settings,
          projects,
          prompt: llmPrompt,
          responseStatus,
          responseText,
          raw,
          error: e,
        });
        const summary = await summarizeSearchFailure({ settings, query, logText, error: e });
        return json(res, {
          ok: false,
          error: 'search_failed',
          message: e.message,
          failure_id: failureId,
          log_path: SEARCH_ERROR_LOG,
          log: logText,
          ai_summary: summary.text,
          ai_summary_ok: summary.ok,
          ai_summary_error: summary.error || '',
          results: [],
          interpreted: `搜索失败: "${query}"`,
          reasoning: summary.text,
          total: projects.length,
        }, 500);
      }
    }

    // GET /api/settings
    if (method === 'GET' && pathname === '/api/settings') {
      const file = loadSettings();
      const env  = loadEnv();
      const activeSettings = { ...env, ...file };
      return json(res, {
        file,
        providers: Object.keys(PROVIDER_PRESETS).map(k => ({
          key: k,
          base_url: PROVIDER_PRESETS[k].base_url,
          needs_key: PROVIDER_PRESETS[k].needs_key,
        })),
        env: {
          llm_provider: activeSettings.llm_provider,
          llm_base_url: resolveBaseUrl(activeSettings),
          llm_model: activeSettings.llm_model,
          llm_api_key_present: !!activeSettings.llm_api_key,
        },
      });
    }

    // PUT /api/settings
    if (method === 'PUT' && pathname === '/api/settings') {
      const body = await readBody(req);
      const current = loadSettings();
      const updated = { ...current, ...body };
      saveSettingsFile(updated);
      return json(res, { ok: true, settings: updated });
    }

    // GET /api/models
    if (method === 'GET' && pathname === '/api/models') {
      const settings = loadSettings();
      const baseUrl = url.searchParams.get('base_url') || resolveBaseUrl(settings);
      try {
        const models = await fetchModels(baseUrl, settings.llm_api_key);
        return json(res, { models, base_url: baseUrl });
      } catch (e) {
        return json(res, { models: [], base_url: baseUrl, error: e.message }, 500);
      }
    }

    // POST /api/analyze-repo
    if (method === 'POST' && pathname === '/api/analyze-repo') {
      const body = await readBody(req);
      const repo = String(body.repo || '').trim();
      if (!repo) return json(res, { error: 'repo is required' }, 400);
      const args = ['analyze-repo', repo];
      if (body.force) args.push('--force');
      if (body.no_llm) args.push('--no-llm');
      try {
        const result = await runSidecar(args);
        return json(res, { ok: true, ...result });
      } catch (e) {
        return json(res, { ok: false, error: e.message }, 500);
      }
    }

    // GET /api/runtime
    if (method === 'GET' && pathname === '/api/runtime') {
      const sidecar = process.env.GITHUB_RADAR_SIDECAR_PATH || '';
      return json(res, {
        data_dir: DATA_DIR,
        artifacts_dir: ARTIFACTS,
        sidecar_path: sidecar,
        sidecar_found: !!(sidecar && existsSync(sidecar)),
      });
    }

    // 404
    res.writeHead(404);
    res.end('Not Found');
  } catch (e) {
    console.error('[error]', e);
    res.writeHead(500);
    res.end(JSON.stringify({ error: e.message }));
  }
}

// ── Start ────────────────────────────────────────────────────────────
export function startServer(options = {}) {
  const port = parseInt(options.port || PORT, 10);
  const host = options.host || process.env.HOST || '0.0.0.0';
  const server = createServer(handleRequest);
  return new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(port, host, () => {
      server.off('error', reject);
      console.log(`[github-radar-ui] http://${host}:${port}`);
      console.log(`[github-radar-ui] data dir: ${DATA_DIR}`);
      console.log(`[github-radar-ui] artifacts: ${ARTIFACTS}`);
      console.log(`[github-radar-ui] projects: ${listProjects().length}`);
      resolve(server);
    });
  });
}

const isCli = process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href;
if (isCli) {
  startServer().catch((e) => {
    console.error('[github-radar-ui] failed to start:', e);
    process.exit(1);
  });
}
