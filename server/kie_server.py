#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["fastmcp>=2.0", "requests>=2.28"]
# ///
"""
KIE MCP connector — 5 generic tools that let an agent drive any model on KIE.ai.

    kie_post(path, body)            POST any KIE endpoint (usually createTask)
    kie_get(path)                   GET any KIE endpoint (usually recordInfo poll)
    kie_upload_file(localPath, …)   local file -> KIE-hosted URL (~3d TTL)
    kie_download(url, destPath)     result URL -> local disk
    kie_fetch_model_docs(path|url)  a model's live docs (cached ~3 days)

The API key is read from KIE_API_KEY in the server's environment and never
crosses the tool boundary. Run:  uv run kie_server.py
"""
from __future__ import annotations

import json
import mimetypes
import os
import time
from pathlib import Path
from urllib.parse import urlparse

import requests
from fastmcp import FastMCP

# --- config ----------------------------------------------------------------
API_KEY = os.environ.get("KIE_API_KEY", "")
BASE_URL = os.environ.get("KIE_BASE_URL", "https://api.kie.ai").rstrip("/")
UPLOAD_URL = os.environ.get("KIE_UPLOAD_URL", "https://kieai.redpandaai.co/api/file-stream-upload")
DOCS_BASE = os.environ.get("KIE_DOCS_BASE", "https://docs.kie.ai").rstrip("/")
WORKSPACE = os.environ.get("KIE_WORKSPACE_DIR", "").strip()
CACHE_DIR = Path.home() / ".cache" / "kie-mcp-kit" / "docs"
DOCS_TTL = 3 * 24 * 3600  # seconds

# Hosts the Bearer key is allowed to reach. The agent controls `path`, so this
# is the SSRF boundary — never send credentials anywhere else.
_API_ORIGINS = {_o for _o in (
    f"{urlparse(BASE_URL).scheme}://{urlparse(BASE_URL).netloc}",
    f"{urlparse(UPLOAD_URL).scheme}://{urlparse(UPLOAD_URL).netloc}",
)}
_DOCS_ORIGIN = f"{urlparse(DOCS_BASE).scheme}://{urlparse(DOCS_BASE).netloc}"

# Media we accept for upload (KIE only references these).
_UPLOAD_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".mp4", ".mov", ".webm", ".mp3", ".wav", ".m4a"}
# Never write these to disk — they land where something later executes them.
_DENIED_DL_EXTS = {
    ".sh", ".bash", ".zsh", ".command", ".ps1", ".bat", ".cmd", ".exe", ".dll",
    ".so", ".dylib", ".msi", ".app", ".vbs", ".js", ".mjs", ".ts", ".py", ".rb",
    ".pl", ".php", ".jar", ".html", ".htm", ".svg", ".webloc", ".url", ".desktop",
    ".plist", ".scpt",
}

mcp = FastMCP("kie")


# --- helpers ---------------------------------------------------------------
def _origin(url: str) -> str:
    p = urlparse(url)
    return f"{p.scheme}://{p.netloc}"


def _abs_url(path: str) -> str:
    """A relative path resolves against BASE_URL; an absolute URL passes through."""
    return path if path.startswith(("http://", "https://")) else f"{BASE_URL}/{path.lstrip('/')}"


def _require(cond: bool, msg: str) -> None:
    if not cond:
        raise ValueError(msg)


def _resolve_in_workspace(path: str, what: str) -> Path:
    """Resolve a local path; if KIE_WORKSPACE_DIR is set, confine to it."""
    if WORKSPACE:
        root = Path(WORKSPACE).expanduser().resolve()
        _require(root != root.anchor and root != Path.home().resolve(),
                 f"KIE_WORKSPACE_DIR must not be '/' or your bare home directory.")
        p = (root / path).resolve() if not os.path.isabs(path) else Path(path).resolve()
        _require(root == p or root in p.parents, f"Blocked: {what} path escapes the workspace {root}.")
        return p
    return Path(path).expanduser().resolve()


def _body(resp: requests.Response):
    try:
        return resp.json()
    except ValueError:
        return resp.text


def _assert_downloadable(name: str) -> None:
    """Reject a destination the filesystem would turn into a script/executable/dotfile.

    Windows strips trailing dots and spaces at write time, so "evil.js." lands on
    disk as "evil.js" — validate the name the filesystem will actually create.
    """
    eff = name.rstrip(". ")
    _require(eff == name, f"Blocked: destination has trailing dots/spaces ({name!r}).")
    _require(bool(eff) and not eff.startswith("."), f"Blocked: refusing to write dotfile ({name!r}).")
    ext = os.path.splitext(eff)[1].lower()
    _require(ext not in _DENIED_DL_EXTS,
             f"Blocked: refusing to write a {ext or 'extension-less'} file — media destinations only.")


# --- tools -----------------------------------------------------------------
@mcp.tool()
def kie_post(path: str, body: dict) -> dict:
    """POST to any KIE.ai endpoint — submit a generation task (usually
    '/api/v1/jobs/createTask'). Returns { status, ok, body }."""
    url = _abs_url(path)
    _require(_origin(url) in _API_ORIGINS, f"Blocked: kie_post may only reach {_API_ORIGINS}.")
    r = requests.post(url, json=body, headers={"Authorization": f"Bearer {API_KEY}"}, timeout=120)
    return {"status": r.status_code, "ok": r.ok, "body": _body(r)}


@mcp.tool()
def kie_get(path: str) -> dict:
    """GET from any KIE.ai endpoint — poll task status (usually
    '/api/v1/jobs/recordInfo?taskId=...'). Returns { status, ok, body }."""
    url = _abs_url(path)
    _require(_origin(url) in _API_ORIGINS, f"Blocked: kie_get may only reach {_API_ORIGINS}.")
    r = requests.get(url, headers={"Authorization": f"Bearer {API_KEY}"}, timeout=120)
    return {"status": r.status_code, "ok": r.ok, "body": _body(r)}


@mcp.tool()
def kie_upload_file(localPath: str, uploadPath: str | None = None) -> dict:
    """Upload a local media file to KIE storage. Returns a hosted URL (~3-day
    TTL) to use as an @Image/@Video reference in a job payload."""
    p = _resolve_in_workspace(localPath, "kie_upload_file")
    _require(p.is_file(), f"Not a file: {p}")
    ext = p.suffix.lower()
    _require(ext in _UPLOAD_EXTS, f"Blocked: {ext or 'extension-less'} is not an uploadable media type.")
    ctype = mimetypes.types_map.get(ext) or "application/octet-stream"
    with p.open("rb") as fh:
        files = {"file": (p.name, fh, ctype)}
        data = {"uploadPath": uploadPath} if uploadPath else {}
        r = requests.post(UPLOAD_URL, files=files, data=data,
                          headers={"Authorization": f"Bearer {API_KEY}"}, timeout=300)
    parsed = _body(r)
    url = None
    if isinstance(parsed, dict) and isinstance(parsed.get("data"), dict):
        url = parsed["data"].get("downloadUrl") or parsed["data"].get("url")
    return {"ok": r.ok and bool(url), "status": r.status_code, "url": url,
            "localPath": str(p), "bytes": p.stat().st_size, "contentType": ctype, "response": parsed}


@mcp.tool()
def kie_download(url: str, destPath: str) -> dict:
    """Download a result URL (image/video/audio) to local disk. Creates parent
    folders. Refuses executable/script destinations."""
    dest = _resolve_in_workspace(destPath, "kie_download")
    _assert_downloadable(Path(destPath).name)
    dest.parent.mkdir(parents=True, exist_ok=True)
    r = requests.get(url, stream=True, timeout=300)
    r.raise_for_status()
    n = 0
    with dest.open("wb") as fh:
        for chunk in r.iter_content(65536):
            fh.write(chunk)
            n += len(chunk)
    return {"ok": True, "status": r.status_code, "destPath": str(dest), "bytes": n}


def _docs_url(path: str | None, url: str | None) -> str:
    if url:
        raw = url
    elif path:
        p = path.lstrip("/")
        raw = f"{DOCS_BASE}/{p}" if (p.startswith("market/") or "-api/" in p) else f"{DOCS_BASE}/market/{p}"
    else:
        raise ValueError("kie_fetch_model_docs needs { path } (e.g. 'gpt/gpt-image-2-text-to-image') or { url }.")
    _require(_origin(raw) == _DOCS_ORIGIN, f"Blocked: docs may only come from {_DOCS_ORIGIN}.")
    u = urlparse(raw)
    if u.netloc == urlparse(DOCS_BASE).netloc and not u.path.endswith(".md") and not u.query:
        raw = raw + ".md"  # docs.kie.ai serves compact markdown at the .md path
    return raw


@mcp.tool()
def kie_fetch_model_docs(path: str | None = None, url: str | None = None, force: bool = False) -> dict:
    """Fetch a KIE model's live docs (from docs.kie.ai/market/...), cached ~3
    days. Use before calling a model whose payload shape you don't know."""
    resolved = _docs_url(path, url)
    cache = CACHE_DIR / (urlparse(resolved).path.strip("/").replace("/", "_"))
    if not force and cache.is_file() and (time.time() - cache.stat().st_mtime) < DOCS_TTL:
        return {"ok": True, "url": resolved, "cached": True, "content": cache.read_text("utf-8")}
    r = requests.get(resolved, timeout=60)
    if not r.ok:
        return {"ok": False, "url": resolved, "status": r.status_code, "content": r.text[:2000]}
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache.write_text(r.text, "utf-8")
    return {"ok": True, "url": resolved, "cached": False, "content": r.text}


@mcp.resource("kie://models")
def models_index() -> str:
    """Live catalog of KIE.ai models, fetched from docs.kie.ai — the starting
    point when the job isn't a tuned default. Pick a model, then read its
    payload shape with kie_fetch_model_docs."""
    r = requests.get(f"{DOCS_BASE}/market/quickstart.md", timeout=60)
    return r.text if r.ok else "Browse https://docs.kie.ai/market/quickstart for the model list."


# --- self-check (no network): `uv run kie_server.py --selftest` -------------
def _selftest() -> None:
    assert _abs_url("/api/v1/jobs/createTask") == f"{BASE_URL}/api/v1/jobs/createTask"
    assert _abs_url("https://api.kie.ai/x") == "https://api.kie.ai/x"
    assert _origin("https://api.kie.ai/a/b") == "https://api.kie.ai"
    assert _docs_url("gpt/gpt-image-2-text-to-image", None).endswith("/market/gpt/gpt-image-2-text-to-image.md")
    assert _docs_url("suno-api/generate-music", None).endswith("/suno-api/generate-music.md")
    for bad in (None, ""):
        try:
            _docs_url(bad, "https://evil.com/x"); raise AssertionError("origin guard failed")
        except ValueError:
            pass
    _assert_downloadable("clip.mp4")  # allowed
    for bad in ("evil.js.", "evil.py ", "shell.sh", ".env", "run.py."):
        try:
            _assert_downloadable(bad); raise AssertionError(f"download guard missed {bad!r}")
        except ValueError:
            pass
    print("selftest ok")


if __name__ == "__main__":
    import sys
    if "--selftest" in sys.argv:
        _selftest()
    else:
        mcp.run()
