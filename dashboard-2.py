"""
Agent Memory Layer — Dashboard

Warm editorial gallery UI (Notion-style) backed by the always-on memory agent.
"""

import html as _html
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
import streamlit as st

AGENT_URL = "http://localhost:8888"
INBOX_DIR = Path("./inbox")

UPLOAD_EXTENSIONS = [
    "txt", "md", "json", "csv", "log", "xml", "yaml", "yml",
    "png", "jpg", "jpeg", "gif", "webp", "bmp", "svg",
    "mp3", "wav", "ogg", "flac", "m4a", "aac",
    "mp4", "webm", "mov", "avi", "mkv",
    "pdf",
]

SAMPLE_TEXTS = [
    {
        "title": "AI Agents in Production",
        "text": (
            "Anthropic released a report showing that 62% of Claude usage is now "
            "code-related, with AI agents being the fastest growing category. "
            "Companies are deploying agents for customer support, code review, "
            "and data analysis. The key challenge remains reliability: agents "
            "fail silently and need human oversight loops."
        ),
    },
    {
        "title": "Meeting Notes: Q1 Planning",
        "text": (
            "Discussed Q1 priorities: 1) Ship the new API by March 15, "
            "2) Hire two backend engineers, 3) Reduce inference costs by 40% "
            "by switching to smaller models for routing tasks. Sarah will lead "
            "the API project. Budget approved for $50k in cloud compute."
        ),
    },
    {
        "title": "Research: Memory in LLM Systems",
        "text": (
            "Current approaches to LLM memory: 1) Vector databases with RAG: "
            "good for retrieval but no active processing. 2) Conversation "
            "summarization: loses detail over time. 3) Knowledge graphs: "
            "expensive to maintain. The gap: no system actively consolidates "
            "and connects information like human memory does."
        ),
    },
    {
        "title": "Product Idea: Smart Inbox",
        "text": (
            "What if email had an AI layer that continuously reads, categorizes, "
            "and summarizes incoming mail? Not just filtering: actually understanding "
            "context across conversations. Competitors: Superhuman (fast UI, no AI "
            "summary), Shortwave (some AI, limited memory)."
        ),
    },
]


def api_get(path: str) -> dict | None:
    try:
        r = requests.get(f"{AGENT_URL}{path}", timeout=30)
        return r.json()
    except Exception:
        return None


def api_post(path: str, data: dict) -> dict | None:
    try:
        r = requests.post(f"{AGENT_URL}{path}", json=data, timeout=60)
        return r.json()
    except Exception as e:
        st.error(f"Agent not reachable: {e}")
        return None


def transform_memory(m: dict, idx: int) -> dict:
    summary = m.get("summary", "") or ""
    period = summary.find(".")
    if 0 < period < 80:
        title = summary[: period + 1]
    elif len(summary) > 77:
        title = summary[:77] + "…"
    else:
        title = summary

    source = m.get("source") or ""
    if source and "." in source:
        ext = Path(source).suffix.lower().lstrip(".")
        ext_upper = ext.upper()
    else:
        ext_upper = "TXT"

    kind = (
        "pdf"
        if ext_upper == "PDF"
        else "image"
        if ext_upper in ("PNG", "JPG", "JPEG", "GIF", "WEBP")
        else "text"
    )

    topics_str = " ".join(m.get("topics", []) or []).lower()
    entities_str = " ".join(m.get("entities", []) or []).lower()
    combined = topics_str + " " + entities_str

    if any(w in combined for w in ("invoice", "billing", "payment")):
        cover = "invoice"
    elif any(w in combined for w in ("map", "geography", "location", "paris", "museum", "orangerie")):
        cover = "map"
    elif kind == "image":
        cover = "slide"
    elif any(w in combined for w in ("philosophical", "biography", "literature", "history", "camus")):
        cover = "doc"
    else:
        cover = ["doc", "slide", "doc", "map"][idx % 4]

    tags = list(m.get("topics", []) or []) + list(m.get("entities", []) or [])[:3]

    return {
        "id": m["id"],
        "title": title,
        "description": summary,
        "source": source or "unknown",
        "kind": kind,
        "ext": ext_upper,
        "date": (m.get("created_at") or "")[:16],
        "tags": tags[:8],
        "cover": cover,
    }


# ---------- Gallery card helpers (native Streamlit, no iframe) ----------

_COVER_PALETTE = {
    "slide":   {"bg": "#E8E0CC", "ink": "#5A4A2C", "stripe": "#D9CEB2", "accent": "#9C5B3C"},
    "invoice": {"bg": "#DDE5D8", "ink": "#3D4E36", "stripe": "#CDD7C6", "accent": "#587044"},
    "doc":     {"bg": "#E2DDE8", "ink": "#403957", "stripe": "#D2CCDB", "accent": "#5C4F86"},
    "map":     {"bg": "#D6DEE2", "ink": "#34464F", "stripe": "#C6CFD4", "accent": "#436173"},
}


def _tag_hue(tag: str) -> int:
    h = 0
    for c in tag.lower():
        h = (h * 31 + ord(c)) & 0xFFFFFFFF
    return h % 360


def _tag_color(tag: str) -> str:
    return f"oklch(0.65 0.08 {_tag_hue(tag)})"


def _rel_date(iso: str) -> str:
    if not iso:
        return ""
    try:
        d = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        days = (datetime.now(timezone.utc) - d).days
        if days == 0:
            return "today"
        if days == 1:
            return "yesterday"
        if days < 7:
            return f"{days}d ago"
        if days < 30:
            return f"{days // 7}w ago"
        return d.strftime("%b %-d, %Y")
    except Exception:
        return iso[:10]


def _striped_bg(p: dict, uid: int) -> str:
    pid = f"sp-{uid}"
    return (
        f'<svg class="cover-pattern" preserveAspectRatio="none" viewBox="0 0 400 225" aria-hidden="true">'
        f'<defs><pattern id="{pid}" width="14" height="14" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
        f'<rect width="14" height="14" fill="{p["bg"]}"/>'
        f'<line x1="0" y1="0" x2="0" y2="14" stroke="{p["stripe"]}" stroke-width="6"/>'
        f'</pattern></defs>'
        f'<rect width="400" height="225" fill="url(#{pid})"/></svg>'
    )


def _cover_art(kind: str, p: dict) -> str:
    bg, ink, accent = p["bg"], p["ink"], p["accent"]
    if kind == "slide":
        return (
            f'<div class="cover-art"><svg viewBox="0 0 320 180" width="62%" aria-hidden="true">'
            f'<rect x="0" y="0" width="320" height="180" rx="8" fill="{bg}" stroke="{ink}" stroke-opacity="0.15"/>'
            f'<rect x="22" y="26" width="120" height="10" rx="2" fill="{ink}" opacity="0.85"/>'
            f'<rect x="22" y="44" width="80" height="6" rx="2" fill="{ink}" opacity="0.35"/>'
            f'<rect x="22" y="78" width="200" height="6" rx="2" fill="{ink}" opacity="0.55"/>'
            f'<rect x="22" y="92" width="240" height="6" rx="2" fill="{ink}" opacity="0.55"/>'
            f'<rect x="22" y="106" width="170" height="6" rx="2" fill="{ink}" opacity="0.55"/>'
            f'<circle cx="270" cy="140" r="14" fill="{accent}" opacity="0.85"/>'
            f'<rect x="22" y="138" width="60" height="8" rx="2" fill="{ink}" opacity="0.45"/>'
            f'</svg></div>'
        )
    if kind == "invoice":
        rows = "".join(
            f'<rect x="16" y="{94 + i * 18}" width="120" height="4" rx="1" fill="{ink}" opacity="0.45"/>'
            f'<rect x="180" y="{94 + i * 18}" width="44" height="4" rx="1" fill="{ink}" opacity="0.55"/>'
            for i in range(4)
        )
        return (
            f'<div class="cover-art"><svg viewBox="0 0 240 200" width="46%" aria-hidden="true">'
            f'<rect x="0" y="0" width="240" height="200" rx="6" fill="#FCFAF3" stroke="{ink}" stroke-opacity="0.18"/>'
            f'<rect x="0" y="0" width="240" height="36" fill="{accent}" opacity="0.9"/>'
            f'<rect x="16" y="14" width="86" height="8" rx="1.5" fill="#FCFAF3" opacity="0.95"/>'
            f'<rect x="16" y="58" width="60" height="5" rx="1" fill="{ink}" opacity="0.5"/>'
            f'<rect x="16" y="68" width="100" height="5" rx="1" fill="{ink}" opacity="0.3"/>'
            f'{rows}'
            f'<line x1="16" y1="172" x2="224" y2="172" stroke="{ink}" stroke-opacity="0.25"/>'
            f'<rect x="150" y="180" width="74" height="8" rx="1.5" fill="{ink}" opacity="0.85"/>'
            f'</svg></div>'
        )
    if kind == "map":
        v_lines = "".join(f'<line x1="{40 + i * 40}" y1="0" x2="{40 + i * 40}" y2="180"/>' for i in range(7))
        h_lines = "".join(f'<line x1="0" y1="{30 + i * 30}" x2="320" y2="{30 + i * 30}"/>' for i in range(5))
        return (
            f'<div class="cover-art"><svg viewBox="0 0 320 180" width="78%" aria-hidden="true">'
            f'<rect x="0" y="0" width="320" height="180" fill="{bg}"/>'
            f'<g stroke="{ink}" stroke-opacity="0.18" stroke-width="1">{v_lines}{h_lines}</g>'
            f'<rect x="120" y="60" width="120" height="40" fill="{accent}" opacity="0.18" stroke="{accent}" stroke-opacity="0.5" stroke-dasharray="3 3"/>'
            f'<path d="M -10 130 Q 80 110 160 132 T 330 124" fill="none" stroke="#7AA4B8" stroke-width="10" opacity="0.55" stroke-linecap="round"/>'
            f'<path d="M -10 130 Q 80 110 160 132 T 330 124" fill="none" stroke="#A8C3D2" stroke-width="2" opacity="0.7"/>'
            f'<g transform="translate(178 78)"><circle r="10" fill="{accent}" opacity="0.25"/>'
            f'<circle r="5" fill="{accent}"/><circle r="2" fill="#FCFAF3"/></g>'
            f'</svg></div>'
        )
    # doc (default)
    widths = [180, 166, 184, 172, 176, 160, 182, 150, 140]
    rows = "".join(
        f'<rect x="18" y="{64 + i * 14}" width="{w}" height="5" rx="1" fill="{ink}" opacity="0.45"/>'
        for i, w in enumerate(widths)
    )
    return (
        f'<div class="cover-art"><svg viewBox="0 0 220 200" width="42%" aria-hidden="true">'
        f'<rect x="0" y="0" width="220" height="200" rx="6" fill="#FCFAF3" stroke="{ink}" stroke-opacity="0.18"/>'
        f'<rect x="18" y="22" width="120" height="11" rx="2" fill="{ink}" opacity="0.85"/>'
        f'<rect x="18" y="40" width="60" height="5" rx="1" fill="{ink}" opacity="0.4"/>'
        f'{rows}</svg></div>'
    )


def _card_html(m: dict) -> str:
    p = _COVER_PALETTE.get(m["cover"], _COVER_PALETTE["doc"])
    uid = m["id"]
    title = _html.escape(m["title"])
    desc = _html.escape(m["description"])
    source = _html.escape(m["source"])
    tags_html = "".join(
        f'<span class="gc-tag"><span class="gc-swatch" style="background:{_tag_color(t)}"></span>{_html.escape(t)}</span>'
        for t in m["tags"]
    )
    return (
        f'<article class="gc-card">'
        f'<div class="gc-cover" style="--cover-bg:{p["bg"]};--cover-ink:{p["ink"]}">'
        f'{_striped_bg(p, uid)}'
        f'{_cover_art(m["cover"], p)}'
        f'<div class="gc-cover-meta"><span class="gc-pill">{m["ext"]}</span></div>'
        f'<div class="gc-cover-corner"><span class="gc-src" title="{source}">{source}</span></div>'
        f'</div>'
        f'<div class="gc-body">'
        f'<div class="gc-meta"><span class="gc-id">#{str(uid).zfill(2)}</span><span class="gc-date">{_rel_date(m["date"])}</span></div>'
        f'<h3 class="gc-title">{title}</h3>'
        f'<p class="gc-desc">{desc}</p>'
        f'<div class="gc-tags">{tags_html}</div>'
        f'</div></article>'
    )


# ---------- Streamlit theme CSS ----------

_THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter+Tight:wght@400;500;600;700&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;1,6..72,400&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
  --bg: #F4F1EB;
  --bg-2: #EBE7DD;
  --panel: #FFFFFF;
  --ink: #1C1B17;
  --ink-2: #57544C;
  --ink-3: #8C8779;
  --line: #E5E0D2;
  --accent: #9B4F2C;
}

/* App shell */
.stApp { background: var(--bg) !important; }

/* Sidebar */
section[data-testid="stSidebar"] {
  background: var(--bg-2) !important;
  border-right: 1px solid var(--line) !important;
}
section[data-testid="stSidebar"] * { color: var(--ink) !important; }

/* Main font */
html, body, .stApp, .stMarkdown, .stTextInput, .stTextArea, button {
  font-family: "Inter Tight", -apple-system, BlinkMacSystemFont, sans-serif !important;
}

/* Tabs styling */
.stTabs [data-baseweb="tab-list"] {
  background: transparent !important;
  border-bottom: 1px solid var(--line) !important;
  gap: 2px !important;
}
.stTabs [data-baseweb="tab"] {
  background: transparent !important;
  border: none !important;
  color: var(--ink-3) !important;
  font-family: "Inter Tight", sans-serif !important;
  font-size: 13px !important;
  font-weight: 500 !important;
  padding: 8px 14px !important;
  border-radius: 8px !important;
}
.stTabs [aria-selected="true"] {
  background: rgba(28,27,23,0.06) !important;
  color: var(--ink) !important;
}
.stTabs [data-baseweb="tab-highlight"] { background: transparent !important; }
.stTabs [data-baseweb="tab-border"] { display: none !important; }

/* Inputs */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
  background: var(--panel) !important;
  color: var(--ink) !important;
  border-color: var(--line) !important;
  font-family: "Inter Tight", sans-serif !important;
  border-radius: 8px !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
  border-color: #D9D2BF !important;
  box-shadow: 0 0 0 4px rgba(155,79,44,0.08) !important;
}

/* Buttons */
.stButton > button {
  background: var(--panel) !important;
  color: var(--ink) !important;
  border: 1px solid var(--line) !important;
  border-radius: 8px !important;
  font-family: "Inter Tight", sans-serif !important;
  font-size: 13px !important;
  font-weight: 500 !important;
  transition: all .15s !important;
}
.stButton > button:hover {
  background: var(--bg-2) !important;
  border-color: #D9D2BF !important;
}
.stButton > button[kind="primary"] {
  background: var(--ink) !important;
  color: var(--bg) !important;
  border-color: var(--ink) !important;
}
.stButton > button[kind="primary"]:hover {
  background: #2F1B10 !important;
  border-color: #2F1B10 !important;
}

/* Markdown text */
.stMarkdown p, .stMarkdown li { color: var(--ink-2) !important; }
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3 { color: var(--ink) !important; }

/* File uploader */
[data-testid="stFileUploader"] {
  background: var(--panel) !important;
  border: 1px dashed var(--line) !important;
  border-radius: 12px !important;
}

/* Alerts */
.stAlert { border-radius: 8px !important; }

/* Spinner */
.stSpinner > div { border-top-color: var(--accent) !important; }

/* Caption */
.stCaption { color: var(--ink-3) !important; }

/* Code blocks */
code { background: var(--bg-2) !important; color: var(--ink) !important; }

/* Info/success/warning/error boxes */
div[data-testid="stNotification"] { border-radius: 8px !important; }

/* Hide streamlit chrome */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stToolbar"] { background: transparent !important; }
[data-testid="stToolbarActions"] { display: none !important; }

/* Sidebar stat tiles */
.st-stat-tile {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 18px 12px 14px;
  text-align: center;
  transition: border-color .15s, transform .15s;
  margin-bottom: 0;
}
.st-stat-tile:hover { border-color: #D9D2BF; transform: translateY(-1px); }
.st-stat-tile .v {
  font-family: "Newsreader", Georgia, serif !important;
  font-weight: 500;
  font-size: 38px;
  line-height: 1;
  letter-spacing: -0.02em;
  color: var(--ink) !important;
}
.st-stat-tile.zero .v { color: var(--ink-3) !important; }
.st-stat-tile .l {
  margin-top: 8px;
  font-family: "JetBrains Mono", monospace !important;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  font-size: 10px;
  color: var(--ink-3) !important;
}
.st-stat-tile .delta { margin-top: 5px; font-size: 10.5px; color: var(--ink-3) !important; font-family: "JetBrains Mono", monospace !important; }
.st-stat-tile .delta.up { color: #4FA37A !important; }
.st-stats-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.st-stats-grid .wide { grid-column: span 2; }

/* Sidebar section header */
.st-side-h4 {
  font-family: "Newsreader", Georgia, serif !important;
  font-weight: 500;
  font-size: 18px;
  letter-spacing: -0.005em;
  color: var(--ink) !important;
  margin: 0 0 12px;
  display: flex;
  align-items: center;
  gap: 9px;
}

/* Status card */
.st-status-card {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: 26px 18px 22px;
  text-align: center;
  margin-bottom: 20px;
}
.st-status-label {
  font-family: "JetBrains Mono", monospace !important;
  text-transform: uppercase;
  letter-spacing: 0.14em;
  font-size: 11px;
  color: var(--ink) !important;
  font-weight: 500;
}
.st-status-sub {
  margin-top: 6px;
  font-size: 11px;
  color: var(--ink-3) !important;
  font-family: "JetBrains Mono", monospace !important;
}
.st-pulse-wrap { position: relative; width: 14px; height: 14px; margin: 0 auto 14px; }
.st-pulse-dot {
  width: 14px; height: 14px; border-radius: 50%; background: #4FA37A;
  box-shadow: 0 0 0 5px rgba(79,163,122,0.16); position: relative; z-index: 2;
}
.st-pulse-dot.offline { background: #ef4444; box-shadow: 0 0 0 5px rgba(239,68,68,0.16); }
.st-pulse-ring {
  position: absolute; inset: 0; border-radius: 50%;
  border: 1.5px solid rgba(79,163,122,0.6); animation: st-pulse 2.2s ease-out infinite;
}
@keyframes st-pulse {
  0% { transform: scale(1); opacity: 0.8; }
  100% { transform: scale(2.6); opacity: 0; }
}
.st-crumb {
  font-family: "JetBrains Mono", monospace !important;
  font-size: 11px; letter-spacing: 0.08em; color: var(--ink-3) !important;
  text-transform: uppercase; margin-bottom: 14px;
  display: flex; align-items: center; gap: 8px;
}
.st-crumb-pulse {
  position: relative; width: 7px; height: 7px; border-radius: 50%;
  background: #4FA37A; box-shadow: 0 0 0 3px rgba(79,163,122,0.18); display: inline-block;
}
.st-crumb-pulse::after {
  content: ""; position: absolute; inset: 0; border-radius: 50%;
  border: 1.2px solid rgba(79,163,122,0.6); animation: st-pulse 2.2s ease-out infinite;
}
.st-title {
  font-family: "Newsreader", Georgia, serif !important;
  font-weight: 500; font-size: 52px; line-height: 1.02; letter-spacing: -0.02em;
  color: var(--ink) !important; margin: 0 0 12px;
}
.st-title em { font-style: italic; color: var(--ink-3) !important; font-weight: 400; }
.st-subtitle { color: var(--ink-2) !important; font-size: 15px; max-width: 56ch; line-height: 1.5; margin: 0; }

/* Divider */
hr { border-color: var(--line) !important; margin: 16px 0 !important; }

/* Gallery cards */
.gc-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-top: 16px;
}
.gc-card {
  background: var(--panel); border: 1px solid var(--line); border-radius: 14px;
  overflow: hidden; display: flex; flex-direction: column;
  box-shadow: 0 1px 0 rgba(28,27,23,0.04), 0 1px 2px rgba(28,27,23,0.04);
  transition: transform .2s cubic-bezier(.2,.7,.2,1), box-shadow .2s, border-color .15s;
}
.gc-card:hover { transform: translateY(-2px); border-color: #D9D2BF;
  box-shadow: 0 12px 32px -12px rgba(28,27,23,0.18), 0 4px 12px -4px rgba(28,27,23,0.08); }
.gc-cover {
  position: relative; aspect-ratio: 3/1;
  background: var(--cover-bg, #EFEBDF); overflow: hidden; border-bottom: 1px solid var(--line);
}
.cover-pattern { position: absolute; inset: 0; opacity: 0.55; }
.cover-art { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; }
.gc-cover-meta { position: absolute; inset: 12px 12px auto 12px; display: flex; justify-content: flex-end; z-index: 2; }
.gc-pill {
  background: rgba(28,27,23,0.78); color: #F6F1E4;
  font-family: "JetBrains Mono", monospace; font-size: 9px; letter-spacing: 0.1em;
  padding: 2px 6px; border-radius: 4px;
}
.gc-cover-corner { position: absolute; left: 12px; bottom: 10px; right: 12px; z-index: 2; }
.gc-src {
  font-family: "JetBrains Mono", monospace; font-size: 9.5px;
  color: var(--cover-ink, #4A4538); background: rgba(255,253,247,0.7);
  padding: 2px 6px; border-radius: 4px; display: inline-block;
  max-width: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.gc-body { padding: 14px 16px 16px; display: flex; flex-direction: column; gap: 8px; flex: 1; }
.gc-meta {
  display: flex; align-items: center; justify-content: space-between;
  font-family: "JetBrains Mono", monospace; font-size: 9.5px; letter-spacing: 0.06em;
  color: var(--ink-3); text-transform: uppercase;
}
.gc-id { color: var(--ink-2); font-weight: 500; }
.gc-title {
  margin: 0; font-family: "Newsreader", Georgia, serif; font-weight: 500;
  font-size: 10px; line-height: 1.25; letter-spacing: -0.01em; color: var(--ink);
}
.gc-desc {
  margin: 0; font-size: 10px; line-height: 1.5; color: var(--ink-2);
  display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden;
}
.gc-tags { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 2px; }
.gc-tag {
  display: inline-flex; align-items: center; gap: 5px;
  background: #F0EBDD; color: var(--ink-2); border-radius: 999px;
  padding: 2px 8px 2px 7px; font-size: 11px; white-space: nowrap;
}
.gc-swatch { width: 5px; height: 5px; border-radius: 50%; flex-shrink: 0; }
.gc-tag-more { color: var(--ink-3); font-size: 11px; padding: 2px 4px; }
.gc-empty {
  text-align: center; padding: 80px 20px; border: 1px dashed #D9D2BF;
  border-radius: 16px; background: rgba(255,255,255,0.4); margin-top: 32px;
}
.gc-empty h4 {
  font-family: "Newsreader", Georgia, serif; font-weight: 500;
  color: var(--ink); font-size: 22px; margin: 0 0 6px;
}
</style>
"""


def render_sidebar(stats: dict | None, online: bool) -> None:
    total = stats.get("total_memories", 0) if stats else 0
    pending = stats.get("unconsolidated", 0) if stats else 0
    consols = stats.get("consolidations", 0) if stats else 0

    total_s = str(total).zfill(2)
    pending_s = str(pending).zfill(2)
    consols_s = str(consols).zfill(2)
    consols_cls = "st-stat-tile wide zero" if consols == 0 else "st-stat-tile wide"

    st.markdown(
        f"""<h4 class="st-side-h4">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="#9B4F2C" stroke-width="1.4">
          <rect x="2" y="9" width="3" height="5" rx="0.5"/><rect x="6.5" y="5" width="3" height="9" rx="0.5"/>
          <rect x="11" y="2" width="3" height="12" rx="0.5"/>
        </svg>
        Memory Stats</h4>
        <div class="st-stats-grid">
          <div class="st-stat-tile">
            <div class="v">{total_s}</div>
            <div class="l">Memories</div>
            <div class="delta up">stored</div>
          </div>
          <div class="st-stat-tile">
            <div class="v">{pending_s}</div>
            <div class="l">Pending</div>
            <div class="delta">awaiting review</div>
          </div>
          <div class="{consols_cls}">
            <div class="v">{consols_s}</div>
            <div class="l">Consolidations</div>
            <div class="delta">{"none scheduled" if consols == 0 else "completed"}</div>
          </div>
        </div>""",
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.markdown(
        "<p style='text-align:center;color:#8C8779;font-size:11px;text-transform:uppercase;"
        "letter-spacing:0.12em;margin-bottom:12px;font-family:JetBrains Mono,monospace;'>Powered by</p>",
        unsafe_allow_html=True,
    )
    logo_col1, logo_col2 = st.columns(2)
    with logo_col1:
        st.image("docs/Gemini_logo.png", use_container_width=True)
    with logo_col2:
        st.image("docs/adk_logo.png", width=90)
    st.caption(f"Endpoint: `{AGENT_URL}`")


def render_ingest_tab() -> None:
    st.markdown(
        "<h4 style='font-family:Newsreader,Georgia,serif;font-weight:500;color:#1C1B17;"
        "font-size:22px;letter-spacing:-0.01em;margin-bottom:4px;'>Feed information into memory</h4>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='color:#8C8779;font-size:13px;margin-bottom:16px;'>"
        "Paste text or drop files in <code style=\"background:#EBE7DD;padding:1px 5px;"
        "border-radius:4px;\">./inbox</code>. The <strong>IngestAgent</strong> processes everything automatically.</p>",
        unsafe_allow_html=True,
    )

    input_text = st.text_area("Input", height=150, placeholder="Paste text here…", label_visibility="collapsed")

    col_ingest, col_samples = st.columns([1, 1])
    with col_ingest:
        if st.button("Process into Memory", type="primary", use_container_width=True):
            if input_text.strip():
                with st.spinner("IngestAgent processing…"):
                    t0 = time.time()
                    result = api_post("/ingest", {"text": input_text, "source": "dashboard"})
                    elapsed = time.time() - t0
                if result:
                    st.success(f"Processed in {elapsed:.1f}s")
                    st.markdown(result.get("response", ""))

    with col_samples:
        st.markdown(
            "<p style='color:#8C8779;font-size:12px;font-family:JetBrains Mono,monospace;"
            "text-transform:uppercase;letter-spacing:0.08em;'>Try a sample:</p>",
            unsafe_allow_html=True,
        )
        for s in SAMPLE_TEXTS:
            if st.button(s["title"], use_container_width=True):
                with st.spinner(f"IngestAgent processing…"):
                    t0 = time.time()
                    result = api_post("/ingest", {"text": s["text"], "source": s["title"]})
                    elapsed = time.time() - t0
                if result:
                    st.success(f"**{s['title']}** processed in {elapsed:.1f}s")
                    st.markdown(result.get("response", ""))

    st.markdown("---")
    st.markdown(
        "<h4 style='font-family:Newsreader,Georgia,serif;font-weight:500;color:#1C1B17;"
        "font-size:22px;letter-spacing:-0.01em;margin-bottom:4px;'>Upload Files</h4>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='color:#8C8779;font-size:13px;margin-bottom:16px;'>"
        "Upload images, audio, video, PDFs, or text files — saved to "
        "<code style=\"background:#EBE7DD;padding:1px 5px;border-radius:4px;\">./inbox</code> "
        "and processed automatically.</p>",
        unsafe_allow_html=True,
    )

    uploaded_files = st.file_uploader(
        "Drop files here",
        type=UPLOAD_EXTENSIONS,
        accept_multiple_files=True,
        label_visibility="collapsed",
    )
    if uploaded_files:
        INBOX_DIR.mkdir(parents=True, exist_ok=True)
        for uf in uploaded_files:
            dest = INBOX_DIR / uf.name
            if dest.exists():
                st.warning(f"**{uf.name}** already exists in inbox, skipping.")
                continue
            dest.write_bytes(uf.getvalue())
            ext = Path(uf.name).suffix.lower()
            icon = (
                "🖼️" if ext in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"} else
                "🎵" if ext in {".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac"} else
                "🎬" if ext in {".mp4", ".webm", ".mov", ".avi", ".mkv"} else
                "📑" if ext == ".pdf" else "📄"
            )
            st.success(f"{icon} **{uf.name}** saved to inbox — agent will process it shortly.")

    st.markdown("---")
    st.markdown(
        "<h4 style='font-family:Newsreader,Georgia,serif;font-weight:500;color:#1C1B17;"
        "font-size:22px;letter-spacing:-0.01em;margin-bottom:4px;'>Consolidate Memories</h4>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='color:#8C8779;font-size:13px;margin-bottom:16px;'>"
        "The <strong>ConsolidateAgent</strong> runs automatically every 30 minutes. Trigger it manually here.</p>",
        unsafe_allow_html=True,
    )
    if st.button("Run Consolidation", use_container_width=True):
        with st.spinner("ConsolidateAgent processing…"):
            t0 = time.time()
            result = api_post("/consolidate", {})
            elapsed = time.time() - t0
        if result:
            st.success(f"Consolidated in {elapsed:.1f}s")
            st.markdown(result.get("response", ""))


def render_query_tab() -> None:
    st.markdown(
        "<h4 style='font-family:Newsreader,Georgia,serif;font-weight:500;color:#1C1B17;"
        "font-size:22px;letter-spacing:-0.01em;margin-bottom:4px;'>Ask your memory anything</h4>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='color:#8C8779;font-size:13px;margin-bottom:16px;'>"
        "The <strong>QueryAgent</strong> searches all memories and synthesises answers with citations.</p>",
        unsafe_allow_html=True,
    )

    question = st.text_input("Question", placeholder="What do you know about AI agents?", label_visibility="collapsed")

    sample_qs = [
        "What are the main themes across everything you remember?",
        "What connections do you see between different memories?",
        "What should I focus on based on what you know?",
        "Summarise everything in 3 bullet points.",
    ]
    cols = st.columns(2)
    for i, sq in enumerate(sample_qs):
        with cols[i % 2]:
            if st.button(sq, use_container_width=True, key=f"sq_{i}"):
                question = sq

    if question:
        with st.spinner("QueryAgent searching memory…"):
            t0 = time.time()
            result = api_get(f"/query?q={question}")
            elapsed = time.time() - t0
        if result:
            st.markdown(
                f"""<div style="background:rgba(155,79,44,0.04);border:1px solid rgba(155,79,44,0.12);
                border-radius:12px;padding:20px;margin:16px 0;">
                <span style="font-family:JetBrains Mono,monospace;font-size:11px;color:#8C8779;">{elapsed:.1f}s</span>
                <div style="color:#57544C;line-height:1.7;margin-top:8px;font-size:15px;">{result.get("answer","")}</div>
                </div>""",
                unsafe_allow_html=True,
            )


def render_gallery_tab(stats: dict | None) -> None:
    data = api_get("/memories")
    if not data or not data.get("memories"):
        st.markdown(
            '<div class="gc-empty"><h4>No memories yet</h4>'
            '<p style="color:#8C8779;font-size:14px;">Ingest some information or drop files in <code>./inbox</code></p></div>',
            unsafe_allow_html=True,
        )
        return

    raw = data["memories"]
    memories = [transform_memory(m, i) for i, m in enumerate(raw)]

    query = st.text_input("Search", placeholder="Search memories, tags, sources…", label_visibility="collapsed")
    if query:
        q = query.lower()
        memories = [
            m for m in memories
            if q in (m["title"] + " " + m["description"] + " " + " ".join(m["tags"]) + " " + m["source"]).lower()
        ]

    if not memories:
        st.markdown('<div class="gc-empty"><h4>No memories match</h4><p style="color:#8C8779;font-size:14px;">Try adjusting your search.</p></div>', unsafe_allow_html=True)
    else:
        cards = "\n".join(_card_html(m) for m in memories)
        st.markdown(f'<div class="gc-grid">{cards}</div>', unsafe_allow_html=True)

    st.markdown("---")
    with st.expander("Danger Zone"):
        st.markdown(
            "<p style='color:#ef4444;font-size:13px;'>This permanently deletes all memories, "
            "consolidations, processed file history, <strong>and all inbox files</strong>.</p>",
            unsafe_allow_html=True,
        )
        if st.button("Clear All Memories", type="primary", use_container_width=True):
            result = api_post("/clear", {})
            if result:
                files_del = result.get("files_deleted", 0)
                msg = f"Cleared {result.get('memories_deleted', 0)} memories"
                if files_del:
                    msg += f" and {files_del} inbox files"
                st.toast(msg)
                st.rerun()


def main() -> None:
    st.set_page_config(
        page_title="Agent Memory Layer",
        page_icon="🧠",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.markdown(_THEME_CSS, unsafe_allow_html=True)

    stats = api_get("/status")
    online = stats is not None

    # Sidebar
    with st.sidebar:
        render_sidebar(stats, online)

    # Header
    crumb_pulse = '<span class="st-crumb-pulse"></span>' if online else ""
    crumb_status = (
        f'<span style="color:#57544C;">{crumb_pulse} Online · always on</span>'
        if online else
        '<span style="color:#8C8779;">Offline</span>'
    )
    st.markdown(
        f"""<div class="st-crumb">
        <span>Agent · memory layer</span>
        <span style="color:#B5AF9E;margin:0 4px;">—</span>
        {crumb_status}
        </div>
        <h1 class="st-title">Agent &nbsp;<em>memories</em></h1>
        <p class="st-subtitle">
          Everything the agent has filed away — slides, invoices, articles, maps.<br>
          Browse the collection, search by content, or filter by topic.
        </p>
        <div style="margin: 28px 0 0;"></div>""",
        unsafe_allow_html=True,
    )

    # Navigation tabs
    tab_gallery, tab_ingest, tab_query = st.tabs(["Gallery", "Ingest", "Query"])

    with tab_gallery:
        render_gallery_tab(stats)

    with tab_ingest:
        render_ingest_tab()

    with tab_query:
        render_query_tab()


if __name__ == "__main__":
    main()
