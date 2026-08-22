#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["fastmcp>=2.0", "requests>=2.28", "pillow>=10.0"]
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

import io
import json
import mimetypes
import os
import time
from pathlib import Path
from urllib.parse import urlparse

import requests
from fastmcp import FastMCP
from fastmcp.utilities.types import Image

# --- config ----------------------------------------------------------------
API_KEY = os.environ.get("KIE_API_KEY", "")
BASE_URL = os.environ.get("KIE_BASE_URL", "https://api.kie.ai").rstrip("/")
UPLOAD_URL = os.environ.get("KIE_UPLOAD_URL", "https://kieai.redpandaai.co/api/file-stream-upload")
DOCS_BASE = os.environ.get("KIE_DOCS_BASE", "https://docs.kie.ai").rstrip("/")
WORKSPACE = os.environ.get("KIE_WORKSPACE_DIR", "").strip()
CACHE_DIR = Path.home() / ".cache" / "kie-mcp-kit" / "docs"
DOCS_TTL = 3 * 24 * 3600  # seconds

def _origin_of(url: str) -> str:
    p = urlparse(url)
    return f"{p.scheme}://{p.netloc}"


# Hosts the Bearer key is allowed to reach. The agent controls `path`, so this
# is the SSRF boundary — never send credentials anywhere else.
_API_ORIGINS = {_origin_of(BASE_URL), _origin_of(UPLOAD_URL)}
_DOCS_ORIGIN = _origin_of(DOCS_BASE)

# The only file types that cross the boundary, in either direction. An allowlist
# (not a denylist) — anything unlisted is refused, so a script or executable
# destination can never be reached by an extension this set doesn't name.
_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".avif"}
_MEDIA_EXTS = _IMAGE_EXTS | {
    ".mp4", ".mov", ".webm", ".mkv",
    ".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".opus",
}
# An inline preview stays a thumbnail: a client renders an image block as a
# handful of vision tokens, but the raw bytes as base64 text would blow up the
# context. Keep the webp small and bounded.
_PREVIEW_MAX_PX = 1024
_PREVIEW_MAX_BYTES = 400_000

# One session for connection pooling — a factory run fires dozens of calls.
# Auth headers stay per-call so docs fetches never carry credentials.
_http = requests.Session()

mcp = FastMCP("kie")


# --- helpers ---------------------------------------------------------------
def _abs_url(path: str) -> str:
    """A relative path resolves against BASE_URL; an absolute URL passes through."""
    return path if path.startswith(("http://", "https://")) else f"{BASE_URL}/{path.lstrip('/')}"


def _require(cond: bool, msg: str) -> None:
    if not cond:
        raise ValueError(msg)


def _workspace_root() -> Path:
    """The directory file tools are confined to: KIE_WORKSPACE_DIR, else the cwd.

    '/' and a bare home directory are refused either way — a sandbox that wide
    is not a sandbox. A host-launched server can inherit an arbitrary cwd, so
    point KIE_WORKSPACE_DIR at the project folder.
    """
    root = (Path(WORKSPACE).expanduser() if WORKSPACE else Path.cwd()).resolve()
    _require(str(root) != root.anchor and root != Path.home().resolve(),
             f"Refusing {root} as the workspace — set KIE_WORKSPACE_DIR to a project folder.")
    return root


def _resolve_in_workspace(path: str, what: str) -> Path:
    """Resolve a local path and confine it (symlinks included) to the workspace."""
    root = _workspace_root()
    p = Path(path).expanduser()
    p = (p if p.is_absolute() else root / p).resolve()
    _require(root == p or root in p.parents, f"Blocked: {what} path escapes the workspace {root}.")
    return p


def _body(resp: requests.Response):
    try:
        return resp.json()
    except ValueError:
        return resp.text


def _thumbnail(raw: bytes) -> bytes | None:
    """A small webp preview of an image, or None if it can't be made cheaply.

    Downscale to fit _PREVIEW_MAX_PX and, if still over budget, once more at
    lower quality. Anything that won't decode or won't shrink returns None —
    the download still succeeds, just without an inline preview.
    """
    try:
        from PIL import Image as _PILImage

        im = _PILImage.open(io.BytesIO(raw))
        im.thumbnail((_PREVIEW_MAX_PX, _PREVIEW_MAX_PX))
        if im.mode not in ("RGB", "RGBA"):
            im = im.convert("RGB")
        buf = io.BytesIO()
        im.save(buf, "WEBP", quality=80)
        if buf.tell() > _PREVIEW_MAX_BYTES:
            im.thumbnail((768, 768))
            buf = io.BytesIO()
            im.save(buf, "WEBP", quality=65)
        return buf.getvalue() if buf.tell() <= _PREVIEW_MAX_BYTES else None
    except Exception:
        return None


def _assert_media_name(name: str, what: str) -> None:
    """Allow only a plain media filename — the name the filesystem will really create.

    Windows strips trailing dots and spaces at write time, so "evil.js." lands on
    disk as "evil.js"; validate the stripped form, not the string as given.
    """
    eff = name.rstrip(". ")
    _require(eff == name, f"Blocked: {what} name has trailing dots/spaces ({name!r}).")
    _require(bool(eff) and not eff.startswith("."), f"Blocked: {what} refuses dotfiles ({name!r}).")
    ext = os.path.splitext(eff)[1].lower()
    _require(ext in _MEDIA_EXTS,
             f"Blocked: {ext or 'extension-less'} is not a media type — {what} handles media only.")


# --- tools -----------------------------------------------------------------
@mcp.tool()
def kie_post(path: str, body: dict) -> dict:
    """POST to any KIE.ai endpoint — submit a generation task (usually
    '/api/v1/jobs/createTask'). Returns { status, ok, body }."""
    url = _abs_url(path)
    _require(_origin_of(url) in _API_ORIGINS,
             f"Blocked: kie_post may only reach {', '.join(sorted(_API_ORIGINS))}.")
    r = _http.post(url, json=body, headers={"Authorization": f"Bearer {API_KEY}"}, timeout=120)
    return {"status": r.status_code, "ok": r.ok, "body": _body(r)}


@mcp.tool()
def kie_get(path: str) -> dict:
    """GET from any KIE.ai endpoint — poll task status (usually
    '/api/v1/jobs/recordInfo?taskId=...'). Returns { status, ok, body }."""
    url = _abs_url(path)
    _require(_origin_of(url) in _API_ORIGINS,
             f"Blocked: kie_get may only reach {', '.join(sorted(_API_ORIGINS))}.")
    r = _http.get(url, headers={"Authorization": f"Bearer {API_KEY}"}, timeout=120)
    return {"status": r.status_code, "ok": r.ok, "body": _body(r)}


@mcp.tool()
def kie_upload_file(localPath: str, uploadPath: str | None = None) -> dict:
    """Upload a local media file to KIE storage. Returns a hosted URL (~3-day
    TTL) to use as an @Image/@Video reference in a job payload."""
    p = _resolve_in_workspace(localPath, "kie_upload_file")
    _require(p.is_file(), f"Not a file: {p}")
    _assert_media_name(p.name, "kie_upload_file")
    ctype = mimetypes.types_map.get(p.suffix.lower()) or "application/octet-stream"
    with p.open("rb") as fh:
        files = {"file": (p.name, fh, ctype)}
        data = {"uploadPath": uploadPath} if uploadPath else {}
        r = _http.post(UPLOAD_URL, files=files, data=data,
                       headers={"Authorization": f"Bearer {API_KEY}"}, timeout=300)
    parsed = _body(r)
    url = None
    if isinstance(parsed, dict) and isinstance(parsed.get("data"), dict):
        url = parsed["data"].get("downloadUrl") or parsed["data"].get("url")
    out = {"ok": r.ok and bool(url), "status": r.status_code, "url": url,
           "localPath": str(p), "bytes": p.stat().st_size, "contentType": ctype}
    if not out["ok"]:  # only surface the raw body when something went wrong
        out["response"] = parsed
    return out


@mcp.tool()
def kie_download(url: str, destPath: str, preview: bool = True):
    """Download a result URL (image/video/audio) to local disk. Creates parent
    folders; refuses non-media destinations.

    For an image destination, `preview=True` (default) also returns a small
    inline thumbnail so the result shows in the chat — the full-resolution file
    still lands at destPath. Set `preview=False` for batch downloads (dozens of
    files) so thumbnails don't flood the context; video/audio never preview.
    """
    dest = _resolve_in_workspace(destPath, "kie_download")
    _assert_media_name(dest.name, "kie_download")
    want_preview = preview and dest.suffix.lower() in _IMAGE_EXTS

    # An image we may preview is read whole (they're small); everything else streams.
    with _http.get(url, stream=not want_preview, timeout=300) as r:
        if not r.ok:  # same shape as kie_post/kie_get — report, don't raise
            return {"ok": False, "status": r.status_code, "destPath": str(dest),
                    "bytes": 0, "error": r.text[:500]}
        dest.parent.mkdir(parents=True, exist_ok=True)
        if want_preview:
            raw = r.content
            dest.write_bytes(raw)
            n = len(raw)
        else:
            n = 0
            with dest.open("wb") as fh:
                for chunk in r.iter_content(65536):
                    fh.write(chunk)
                    n += len(chunk)
            raw = None

    meta = {"ok": True, "status": r.status_code, "destPath": str(dest), "bytes": n}
    thumb = _thumbnail(raw) if raw is not None else None
    if thumb:
        return [Image(data=thumb, format="webp"), json.dumps(meta)]
    return meta


def _docs_url(path: str | None, url: str | None) -> str:
    if url:
        raw = url
    elif path:
        p = path.lstrip("/")
        raw = f"{DOCS_BASE}/{p}" if (p.startswith("market/") or "-api/" in p) else f"{DOCS_BASE}/market/{p}"
    else:
        raise ValueError("kie_fetch_model_docs needs { path } (e.g. 'gpt/gpt-image-2-text-to-image') or { url }.")
    _require(_origin_of(raw) == _DOCS_ORIGIN, f"Blocked: docs may only come from {_DOCS_ORIGIN}.")
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
    r = _http.get(resolved, timeout=60)
    if not r.ok:
        return {"ok": False, "url": resolved, "status": r.status_code, "content": r.text[:2000]}
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache.write_text(r.text, "utf-8")
    return {"ok": True, "url": resolved, "cached": False, "content": r.text}


# --- workflows: ship the skills inside the server, Higgsfield-style ----------
# Skills live as files under skill/, which only Claude Code (and agent mode)
# loads. Exposing them as a tool makes the same instructions reachable from ANY
# MCP client — a plain Desktop chat, claude.ai, Cursor — via a tool call.
_SKILL_ROOT = Path(__file__).resolve().parent.parent / "skill"
_WORKFLOWS = {
    "generate-anything": "A single image / video / music / speech asset on command.",
    "content-factory": "Bulk UGC product ads — 5 stages: research → plan → generate → schedule → cost report.",
    "youtube-factory": "Faceless YouTube videos — research → script → visuals → voiceover → assembly.",
}


@mcp.tool()
def kie_workflows(workflow: str | None = None) -> str:
    """Load a bundled KIE workflow — a SKILL.md that orchestrates the kie_* tools.

    MUST USE before building any multi-step or bulk content: a content campaign,
    a batch of UGC ads / reels, a faceless YouTube video, an image asset pack —
    or when the user says "content factory" / "контент-завод". Call with NO
    argument to list the workflows; call with a name to load its full
    instructions, then follow them. A single one-off asset doesn't need this —
    use kie_post / kie_get directly.
    """
    if not workflow:
        lines = ["KIE workflows — call kie_workflows('<name>') to load one:"]
        lines += [f"- {n}: {d}" for n, d in _WORKFLOWS.items()]
        return "\n".join(lines)
    name = workflow.strip().strip("/")
    _require(name in _WORKFLOWS, f"Unknown workflow {name!r}. Options: {', '.join(_WORKFLOWS)}.")
    md = _SKILL_ROOT / name / "SKILL.md"
    _require(md.is_file(), f"Workflow {name!r} has no SKILL.md next to the server.")
    return md.read_text("utf-8")


@mcp.tool()
def kie_workflow_file(workflow: str, path: str) -> str:
    """Read a reference file a workflow's SKILL.md points to (e.g. content-factory's
    'references/prompt-library.md'). Text only, confined to the workflow folder."""
    name = workflow.strip().strip("/")
    _require(name in _WORKFLOWS, f"Unknown workflow {name!r}. Options: {', '.join(_WORKFLOWS)}.")
    root = (_SKILL_ROOT / name).resolve()
    target = (root / path).resolve()
    _require(root == target or root in target.parents, "Blocked: path escapes the workflow folder.")
    _require(target.is_file() and target.suffix.lower() in {".md", ".txt"},
             "Only .md / .txt reference files can be read.")
    return target.read_text("utf-8")


@mcp.resource("kie://models")
def models_index() -> str:
    """Live catalog of KIE.ai models, fetched from docs.kie.ai — the starting
    point when the job isn't a tuned default. Pick a model, then read its
    payload shape with kie_fetch_model_docs."""
    r = _http.get(f"{DOCS_BASE}/market/quickstart.md", timeout=60)
    return r.text if r.ok else "Browse https://docs.kie.ai/market/quickstart for the model list."


@mcp.resource("kie://models/_index")
def models_index_alias() -> str:
    """Alias of kie://models for skills that reference the older _index path."""
    return models_index()


# --- self-check (no network): `uv run kie_server.py --selftest` -------------
def _rejects(fn, *args) -> None:
    try:
        fn(*args)
    except ValueError:
        return
    raise AssertionError(f"guard missed: {fn.__name__}{args!r}")


def _selftest() -> None:
    # URL resolution + origin pinning
    assert _abs_url("/api/v1/jobs/createTask") == f"{BASE_URL}/api/v1/jobs/createTask"
    assert _abs_url("https://api.kie.ai/x") == "https://api.kie.ai/x"
    assert _origin_of("https://api.kie.ai/a/b") == "https://api.kie.ai"
    assert _docs_url("gpt/gpt-image-2-text-to-image", None).endswith("/market/gpt/gpt-image-2-text-to-image.md")
    assert _docs_url("suno-api/generate-music", None).endswith("/suno-api/generate-music.md")
    _rejects(_docs_url, None, "https://evil.com/x")

    # Media-name allowlist: the filesystem's effective name decides
    for good in ("clip.mp4", "shot-001.png", "voice.mp3"):
        _assert_media_name(good, "test")
    for bad in ("evil.js.", "evil.py ", "shell.sh", ".env", "run.py.", "notes.txt", "noext"):
        _rejects(_assert_media_name, bad, "test")

    # Workspace confinement — the boundary that keeps writes inside the project
    import tempfile
    global WORKSPACE
    saved = WORKSPACE
    try:
        with tempfile.TemporaryDirectory() as tmp:
            WORKSPACE = tmp
            root = Path(tmp).resolve()
            assert _resolve_in_workspace("out/clip.mp4", "t") == root / "out" / "clip.mp4"
            _rejects(_resolve_in_workspace, "../escape.mp4", "t")
            _rejects(_resolve_in_workspace, "/etc/passwd", "t")
        WORKSPACE = "/"
        _rejects(_workspace_root)
        WORKSPACE = str(Path.home())
        _rejects(_workspace_root)
    finally:
        WORKSPACE = saved

    # Inline preview: a real image downscales to a bounded webp; junk returns None
    from PIL import Image as _PILImage
    big = io.BytesIO()
    _PILImage.new("RGB", (4000, 3000), (30, 90, 90)).save(big, "PNG")
    thumb = _thumbnail(big.getvalue())
    assert thumb and thumb[:4] == b"RIFF" and len(thumb) <= _PREVIEW_MAX_BYTES, "preview budget"
    assert _thumbnail(b"not an image") is None

    # Embedded workflows: listing names them; each loads; junk and traversal are refused
    listing = kie_workflows()
    assert all(n in listing for n in _WORKFLOWS), "workflow listing"
    for name in _WORKFLOWS:
        assert kie_workflows(name).lstrip().startswith("---"), f"{name} SKILL.md frontmatter"
    _rejects(kie_workflows, "nope")
    assert "concept seeds" in kie_workflow_file("content-factory", "references/prompt-library.md").lower()
    _rejects(kie_workflow_file, "content-factory", "../../server/kie_server.py")
    _rejects(kie_workflow_file, "content-factory", "SKILL.md/../../../etc/hosts")
    print("selftest ok")


if __name__ == "__main__":
    import sys
    if "--selftest" in sys.argv:
        _selftest()
    else:
        mcp.run()
