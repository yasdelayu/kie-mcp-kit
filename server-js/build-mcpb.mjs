#!/usr/bin/env node
// Build kie-mcp-kit.mcpb — a single drag-onto-Claude-Desktop bundle.
// Bundles kie_server.mjs (+ deps) into one file, drops the skills beside it,
// writes the DXT manifest, and zips it. Requires the system `zip` (macOS/Linux).
import { build } from "esbuild";
import { cpSync, writeFileSync, rmSync, mkdirSync, readFileSync } from "node:fs";
import { execFileSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const stage = path.join(here, "build", "kie-mcp");
const version = JSON.parse(readFileSync(path.join(here, "package.json"), "utf8")).version;

rmSync(path.join(here, "build"), { recursive: true, force: true });
mkdirSync(path.join(stage, "dist"), { recursive: true });

await build({
  entryPoints: [path.join(here, "kie_server.mjs")],
  bundle: true, platform: "node", format: "esm",
  outfile: path.join(stage, "dist", "index.js"),
  banner: { js: "import{createRequire as _cr}from'module';const require=_cr(import.meta.url);" },
});

cpSync(path.join(here, "..", "skill"), path.join(stage, "skill"), { recursive: true });

const TOOLS = [
  ["kie_post", "Submit a generation task to any KIE.ai endpoint."],
  ["kie_get", "Poll a KIE.ai task or read the balance."],
  ["kie_upload_file", "Upload a local media file → KIE-hosted URL."],
  ["kie_download", "Download a result to disk (+ inline image preview)."],
  ["kie_fetch_model_docs", "Fetch a model's live docs (cached)."],
  ["kie_workflows", "List / load a bundled content workflow."],
  ["kie_workflow_file", "Read a workflow reference file."],
];
writeFileSync(path.join(stage, "manifest.json"), JSON.stringify({
  dxt_version: "0.1",
  name: "kie-mcp-kit",
  display_name: "KIE MCP Kit — image, video, music, speech",
  version,
  description: "Generate images, video, music and speech on the latest models via KIE.ai, plus content-factory workflows.",
  author: { name: "yasdelayu", url: "https://github.com/yasdelayu" },
  homepage: "https://github.com/yasdelayu/kie-mcp-kit",
  documentation: "https://github.com/yasdelayu/kie-mcp-kit#readme",
  license: "MIT",
  keywords: ["kie", "kie.ai", "image-generation", "video-generation", "music-generation", "mcp"],
  server: {
    type: "node",
    entry_point: "dist/index.js",
    mcp_config: {
      command: "node",
      args: ["${__dirname}/dist/index.js"],
      env: { KIE_API_KEY: "${user_config.kie_api_key}", KIE_WORKSPACE_DIR: "${user_config.kie_workspace_dir}" },
    },
  },
  user_config: {
    kie_api_key: { type: "string", title: "KIE.ai API Key", description: "Get one at https://kie.ai → Dashboard → API Keys", sensitive: true, required: true },
    kie_workspace_dir: { type: "directory", title: "Workspace folder (recommended)", description: "Confines file reads/writes to this folder. Leave empty to use the working directory.", required: false },
  },
  tools: TOOLS.map(([name, description]) => ({ name, description })),
  compatibility: { platforms: ["darwin", "win32", "linux"], runtimes: { node: ">=18.0.0" } },
}, null, 2) + "\n");

execFileSync("zip", ["-r", "-q", "-X", path.join(here, "kie-mcp-kit.mcpb"), "."], { cwd: stage });
const bytes = readFileSync(path.join(here, "kie-mcp-kit.mcpb")).length;
console.log(`built kie-mcp-kit.mcpb (${(bytes / 1e6).toFixed(1)} MB) — drag it onto Claude Desktop.`);
