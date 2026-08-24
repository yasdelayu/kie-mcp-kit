#!/usr/bin/env node
/**
 * KIE MCP connector (Node) — a port of server/kie_server.py.
 *
 *   kie_post(path, body)            POST any KIE endpoint (usually createTask)
 *   kie_get(path)                   GET any KIE endpoint (usually recordInfo poll)
 *   kie_upload_file(localPath, …)   local media file -> KIE-hosted URL (~3d TTL)
 *   kie_download(url, destPath)     result URL -> local disk (+ inline image preview)
 *   kie_fetch_model_docs(path|url)  a model's live docs (cached ~3 days)
 *   kie_workflows(workflow?)        list / load a bundled SKILL.md
 *   kie_workflow_file(workflow,path) read a workflow reference file
 *
 * The API key is read from KIE_API_KEY in the server's environment and never
 * crosses the tool boundary. Run:  node kie_server.mjs
 */
import { readFile, writeFile, mkdir, stat } from "node:fs/promises";
import { createWriteStream, statSync } from "node:fs";
import { Readable } from "node:stream";
import { pipeline } from "node:stream/promises";
import { homedir } from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

// --- config ----------------------------------------------------------------
const API_KEY = process.env.KIE_API_KEY ?? "";
const BASE_URL = (process.env.KIE_BASE_URL ?? "https://api.kie.ai").replace(/\/+$/, "");
const UPLOAD_URL = process.env.KIE_UPLOAD_URL ?? "https://kieai.redpandaai.co/api/file-stream-upload";
const DOCS_BASE = (process.env.KIE_DOCS_BASE ?? "https://docs.kie.ai").replace(/\/+$/, "");
const ws = () => (process.env.KIE_WORKSPACE_DIR ?? "").trim();   // read live (selftest mutates it)
const CACHE_DIR = path.join(homedir(), ".cache", "kie-mcp-kit", "docs");
const DOCS_TTL_MS = 3 * 24 * 3600 * 1000;
const SKILL_ROOT = (() => {                      // repo (../skill) or bundled/npm (./skill)
  const here = path.dirname(fileURLToPath(import.meta.url));
  for (const c of [path.resolve(here, "..", "skill"), path.resolve(here, "skill")]) {
    try { if (statSync(c).isDirectory()) return c; } catch {}
  }
  return path.resolve(here, "..", "skill");
})();

const originOf = (u) => { const p = new URL(u); return `${p.protocol}//${p.host}`; };

// Hosts the Bearer key may reach — the SSRF boundary (the agent controls `path`).
const API_ORIGINS = new Set([originOf(BASE_URL), originOf(UPLOAD_URL)]);
const DOCS_ORIGIN = originOf(DOCS_BASE);

// The only file types that cross the boundary — an allowlist, so a script or
// executable destination is never reachable.
const IMAGE_EXTS = new Set([".png", ".jpg", ".jpeg", ".webp", ".gif", ".avif"]);
const MEDIA_EXTS = new Set([...IMAGE_EXTS,
  ".mp4", ".mov", ".webm", ".mkv", ".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".opus"]);
const PREVIEW_MAX_PX = 1024;
const PREVIEW_MAX_BYTES = 400_000;

const WORKFLOWS = {
  "generate-anything": "A single image / video / music / speech asset on command.",
  "content-factory": "Bulk UGC product ads — 5 stages: research → plan → generate → schedule → cost report.",
  "youtube-factory": "Faceless YouTube videos — research → script → visuals → voiceover → assembly.",
};

// --- helpers ---------------------------------------------------------------
class Blocked extends Error {}
const require_ = (cond, msg) => { if (!cond) throw new Blocked(msg); };

const absUrl = (p) => /^https?:\/\//.test(p) ? p : `${BASE_URL}/${p.replace(/^\/+/, "")}`;

function workspaceRoot() {
  const w = ws();
  const root = path.resolve(w ? w.replace(/^~/, homedir()) : process.cwd());
  require_(root !== path.parse(root).root && root !== path.resolve(homedir()),
    `Refusing ${root} as the workspace — set KIE_WORKSPACE_DIR to a project folder.`);
  return root;
}
const isInside = (root, p) => root === p || p.startsWith(root + path.sep);

function resolveInWorkspace(p, what) {           // WRITE (download) — confined
  const root = workspaceRoot();
  const abs = path.resolve(root, p.replace(/^~/, homedir()));
  require_(isInside(root, abs), `Blocked: ${what} path escapes the workspace ${root}.`);
  return abs;
}
function resolveReadable(p, what) {              // READ (upload) — home-tree ok
  const abs = path.resolve(workspaceRoot(), p.replace(/^~/, homedir()));
  const roots = [path.resolve(homedir())];
  if (ws()) roots.push(path.resolve(ws().replace(/^~/, homedir())));
  require_(roots.some((r) => isInside(r, abs)),
    `Blocked: ${what} may only read from your home folder or KIE_WORKSPACE_DIR — got ${abs}.`);
  return abs;
}

function assertMediaName(name, what) {
  const eff = name.replace(/[. ]+$/, "");   // Windows strips trailing dots/spaces at write time
  require_(eff === name, `Blocked: ${what} name has trailing dots/spaces (${JSON.stringify(name)}).`);
  require_(eff && !eff.startsWith("."), `Blocked: ${what} refuses dotfiles (${JSON.stringify(name)}).`);
  const ext = path.extname(eff).toLowerCase();
  require_(MEDIA_EXTS.has(ext), `Blocked: ${ext || "extension-less"} is not a media type — ${what} handles media only.`);
}

const bodyOf = async (r) => { const t = await r.text(); try { return JSON.parse(t); } catch { return t; } };

async function thumbnail(buf) {                  // small jpeg preview, or null
  try {
    const { Jimp } = await import("jimp");
    const img = await Jimp.read(buf);
    if (img.bitmap.width > PREVIEW_MAX_PX || img.bitmap.height > PREVIEW_MAX_PX)
      img.scaleToFit({ w: PREVIEW_MAX_PX, h: PREVIEW_MAX_PX });
    let out = await img.getBuffer("image/jpeg", { quality: 78 });
    if (out.length > PREVIEW_MAX_BYTES) {
      img.scaleToFit({ w: 768, h: 768 });
      out = await img.getBuffer("image/jpeg", { quality: 62 });
    }
    return out.length <= PREVIEW_MAX_BYTES ? out : null;
  } catch { return null; }
}

const text = (obj) => ({ content: [{ type: "text", text: typeof obj === "string" ? obj : JSON.stringify(obj) }] });

// --- tool implementations (pure of MCP wiring, so selftest can hit helpers) --
async function kiePost(p, body) {
  const url = absUrl(p);
  require_(API_ORIGINS.has(originOf(url)), `Blocked: kie_post may only reach ${[...API_ORIGINS].join(", ")}.`);
  const r = await fetch(url, { method: "POST", headers: { Authorization: `Bearer ${API_KEY}`, "Content-Type": "application/json" }, body: JSON.stringify(body), signal: AbortSignal.timeout(120_000) });
  return { status: r.status, ok: r.ok, body: await bodyOf(r) };
}
async function kieGet(p) {
  const url = absUrl(p);
  require_(API_ORIGINS.has(originOf(url)), `Blocked: kie_get may only reach ${[...API_ORIGINS].join(", ")}.`);
  const r = await fetch(url, { headers: { Authorization: `Bearer ${API_KEY}` }, signal: AbortSignal.timeout(120_000) });
  return { status: r.status, ok: r.ok, body: await bodyOf(r) };
}
async function kieUpload(localPath, uploadPath) {
  const abs = resolveReadable(localPath, "kie_upload_file");
  require_(statSync(abs).isFile(), `Not a file: ${abs}`);
  assertMediaName(path.basename(abs), "kie_upload_file");
  const buf = await readFile(abs);
  const fd = new FormData();
  fd.append("file", new Blob([buf]), path.basename(abs));
  if (uploadPath) fd.append("uploadPath", uploadPath);
  const r = await fetch(UPLOAD_URL, { method: "POST", headers: { Authorization: `Bearer ${API_KEY}` }, body: fd, signal: AbortSignal.timeout(300_000) });
  const parsed = await bodyOf(r);
  const uurl = parsed?.data?.downloadUrl ?? parsed?.data?.url ?? null;
  const out = { ok: r.ok && Boolean(uurl), status: r.status, url: uurl, localPath: abs, bytes: buf.length };
  if (!out.ok) out.response = parsed;
  return out;
}
async function kieDownload(url, destPath, preview = true) {
  const dest = resolveInWorkspace(destPath, "kie_download");
  assertMediaName(path.basename(dest), "kie_download");
  const wantPreview = preview && IMAGE_EXTS.has(path.extname(dest).toLowerCase());
  let r;
  try {
    r = await fetch(url, { signal: AbortSignal.timeout(60_000) });
  } catch (e) {
    return { ok: false, status: 0, destPath: dest, bytes: 0, error: `${e.name}: ${e.message}`, url,
      hint: "Origin was slow or unreachable. Result URLs stay valid ~24h — retry, or fetch the URL directly." };
  }
  if (!r.ok) return { ok: false, status: r.status, destPath: dest, bytes: 0, error: (await r.text()).slice(0, 500), url };
  await mkdir(path.dirname(dest), { recursive: true });
  let n = 0, thumb = null;
  if (wantPreview) {
    const buf = Buffer.from(await r.arrayBuffer());
    await writeFile(dest, buf); n = buf.length; thumb = await thumbnail(buf);
  } else {
    await pipeline(Readable.fromWeb(r.body), createWriteStream(dest));
    n = (await stat(dest)).size;
  }
  const meta = { ok: true, status: r.status, destPath: dest, bytes: n };
  if (thumb) return { content: [{ type: "image", data: thumb.toString("base64"), mimeType: "image/jpeg" }, { type: "text", text: JSON.stringify(meta) }] };
  return meta;
}
function docsUrl(p, url) {
  let raw;
  if (url) raw = url;
  else if (p) { const s = p.replace(/^\/+/, ""); raw = (s.startsWith("market/") || s.includes("-api/")) ? `${DOCS_BASE}/${s}` : `${DOCS_BASE}/market/${s}`; }
  else throw new Blocked("kie_fetch_model_docs needs { path } (e.g. 'gpt/gpt-image-2-text-to-image') or { url }.");
  require_(originOf(raw) === DOCS_ORIGIN, `Blocked: docs may only come from ${DOCS_ORIGIN}.`);
  const u = new URL(raw);
  if (u.host === new URL(DOCS_BASE).host && !u.pathname.endsWith(".md") && !u.search) raw += ".md";
  return raw;
}
async function kieFetchDocs(p, url, force = false) {
  const resolved = docsUrl(p, url);
  const cache = path.join(CACHE_DIR, new URL(resolved).pathname.replace(/^\/+|\/+$/g, "").replace(/\//g, "_"));
  if (!force) { try { const st = await stat(cache); if (Date.now() - st.mtimeMs < DOCS_TTL_MS) return { ok: true, url: resolved, cached: true, content: await readFile(cache, "utf8") }; } catch {} }
  const r = await fetch(resolved, { signal: AbortSignal.timeout(60_000) });
  if (!r.ok) return { ok: false, url: resolved, status: r.status, content: (await r.text()).slice(0, 2000) };
  const body = await r.text();
  await mkdir(CACHE_DIR, { recursive: true }); await writeFile(cache, body, "utf8");
  return { ok: true, url: resolved, cached: false, content: body };
}
async function modelsIndex() {
  try { const r = await fetch(`${DOCS_BASE}/market/quickstart.md`, { signal: AbortSignal.timeout(60_000) }); if (r.ok) return await r.text(); } catch {}
  return "Browse https://docs.kie.ai/market/quickstart for the model list.";
}
async function kieWorkflows(workflow) {
  if (!workflow) return ["KIE workflows — call kie_workflows('<name>') to load one:",
    ...Object.entries(WORKFLOWS).map(([n, d]) => `- ${n}: ${d}`)].join("\n");
  const name = workflow.trim().replace(/^\/+|\/+$/g, "");
  require_(name in WORKFLOWS, `Unknown workflow ${JSON.stringify(name)}. Options: ${Object.keys(WORKFLOWS).join(", ")}.`);
  return await readFile(path.join(SKILL_ROOT, name, "SKILL.md"), "utf8");
}
async function kieWorkflowFile(workflow, p) {
  const name = workflow.trim().replace(/^\/+|\/+$/g, "");
  require_(name in WORKFLOWS, `Unknown workflow ${JSON.stringify(name)}. Options: ${Object.keys(WORKFLOWS).join(", ")}.`);
  const root = path.resolve(SKILL_ROOT, name);
  const target = path.resolve(root, p);
  require_(isInside(root, target), "Blocked: path escapes the workflow folder.");
  require_([".md", ".txt"].includes(path.extname(target).toLowerCase()), "Only .md / .txt reference files can be read.");
  return await readFile(target, "utf8");
}

// --- self-check (no network): node kie_server.mjs --selftest -----------------
function rejects(fn, ...args) { try { fn(...args); } catch (e) { if (e instanceof Blocked) return; } throw new Error(`guard missed: ${fn.name}(${args})`); }
async function rejectsAsync(fn) { try { await fn(); } catch (e) { if (e instanceof Blocked) return; } throw new Error("async guard missed"); }
async function selftest() {
  const assert = (c, m) => { if (!c) throw new Error("assert: " + m); };
  assert(absUrl("/api/v1/jobs/createTask") === `${BASE_URL}/api/v1/jobs/createTask`, "absUrl rel");
  assert(absUrl("https://api.kie.ai/x") === "https://api.kie.ai/x", "absUrl abs");
  assert(originOf("https://api.kie.ai/a/b") === "https://api.kie.ai", "origin");
  assert(docsUrl("gpt/gpt-image-2-text-to-image", null).endsWith("/market/gpt/gpt-image-2-text-to-image.md"), "docs path");
  assert(docsUrl("suno-api/generate-music", null).endsWith("/suno-api/generate-music.md"), "docs api path");
  rejects(docsUrl, null, "https://evil.com/x");
  for (const g of ["clip.mp4", "shot-001.png", "voice.mp3"]) assertMediaName(g, "t");
  for (const b of ["evil.js.", "evil.py ", "shell.sh", ".env", "run.py.", "notes.txt", "noext"]) rejects(assertMediaName, b, "t");
  const saved = process.env.KIE_WORKSPACE_DIR;
  try {
    process.env.KIE_WORKSPACE_DIR = "/"; rejects(workspaceRoot);
    process.env.KIE_WORKSPACE_DIR = homedir(); rejects(workspaceRoot);
  } finally { if (saved === undefined) delete process.env.KIE_WORKSPACE_DIR; else process.env.KIE_WORKSPACE_DIR = saved; }
  assert((await kieWorkflows()).includes("content-factory"), "workflow listing");
  for (const n of Object.keys(WORKFLOWS)) assert((await kieWorkflows(n)).trimStart().startsWith("---"), `${n} frontmatter`);
  await rejectsAsync(() => kieWorkflows("nope"));
  assert((await kieWorkflowFile("generate-anything", "references/models.md")).includes("reference_image_urls"), "models.md");
  console.log("selftest ok");
}

// --- MCP wiring --------------------------------------------------------------
async function serve() {
  const { McpServer } = await import("@modelcontextprotocol/sdk/server/mcp.js");
  const { StdioServerTransport } = await import("@modelcontextprotocol/sdk/server/stdio.js");
  const { z } = await import("zod");
  const server = new McpServer({ name: "kie", version: "1.0.0" });
  const guard = (fn) => async (a) => { try { return await fn(a); } catch (e) { if (e instanceof Blocked) return text({ ok: false, error: e.message }); throw e; } };

  server.tool("kie_post", "POST to any KIE.ai endpoint — submit a generation task (usually '/api/v1/jobs/createTask'). Returns { status, ok, body }.",
    { path: z.string(), body: z.record(z.any()) }, guard(async ({ path: p, body }) => text(await kiePost(p, body))));
  server.tool("kie_get", "GET from any KIE.ai endpoint — poll task status (usually '/api/v1/jobs/recordInfo?taskId=...'). Returns { status, ok, body }.",
    { path: z.string() }, guard(async ({ path: p }) => text(await kieGet(p))));
  server.tool("kie_upload_file", "Upload a local media file to KIE storage. Returns a hosted URL (~3-day TTL) for @Image/@Video references.",
    { localPath: z.string(), uploadPath: z.string().optional() }, guard(async ({ localPath, uploadPath }) => text(await kieUpload(localPath, uploadPath))));
  server.tool("kie_download", "Download a result URL to local disk. For an image, preview=true (default) also returns a small inline thumbnail; set false for batches. video/audio never preview.",
    { url: z.string(), destPath: z.string(), preview: z.boolean().optional() },
    guard(async ({ url, destPath, preview }) => { const r = await kieDownload(url, destPath, preview ?? true); return r.content ? r : text(r); }));
  server.tool("kie_fetch_model_docs", "Fetch a KIE model's live docs (docs.kie.ai/market/...), cached ~3 days. Use before calling a model whose payload you don't know.",
    { path: z.string().optional(), url: z.string().optional(), force: z.boolean().optional() },
    guard(async ({ path: p, url, force }) => text(await kieFetchDocs(p, url, force ?? false))));
  server.tool("kie_workflows", "Load a bundled KIE workflow (a SKILL.md that orchestrates the kie_* tools). MUST USE before bulk/multi-step content — a campaign, a batch of UGC ads, a faceless YouTube video, 'content factory'/'контент-завод'. No arg = list; a name = load it.",
    { workflow: z.string().optional() }, guard(async ({ workflow }) => text(await kieWorkflows(workflow))));
  server.tool("kie_workflow_file", "Read a reference file a workflow's SKILL.md points to (e.g. 'references/models.md'). Text only, confined to the workflow folder.",
    { workflow: z.string(), path: z.string() }, guard(async ({ workflow, path: p }) => text(await kieWorkflowFile(workflow, p))));

  server.resource("kie-models", "kie://models", async (uri) => ({ contents: [{ uri: uri.href, text: await modelsIndex() }] }));
  server.resource("kie-models-index", "kie://models/_index", async (uri) => ({ contents: [{ uri: uri.href, text: await modelsIndex() }] }));

  await server.connect(new StdioServerTransport());
}

if (process.argv.includes("--selftest")) selftest().catch((e) => { console.error(e); process.exit(1); });
else serve().catch((e) => { console.error(e); process.exit(1); });
