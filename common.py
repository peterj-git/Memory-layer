"""
Shared helpers, theme, and chrome for the Agent Memory Layer dashboard.

The editorial theme and page designs are carried over from dashboard-2.py.
"""

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


# ---------- Editorial theme (from dashboard-2.py) ----------

THEME_CSS = """
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

.stApp { background: var(--bg) !important; }

html, body, .stApp, .stMarkdown, .stTextInput, .stTextArea, button {
  font-family: "Inter Tight", -apple-system, BlinkMacSystemFont, sans-serif !important;
}

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
.stButton > button:hover { background: var(--bg-2) !important; border-color: #D9D2BF !important; }
.stButton > button[kind="primary"] {
  background: var(--ink) !important; color: var(--bg) !important; border-color: var(--ink) !important;
}
.stButton > button[kind="primary"]:hover { background: #2F1B10 !important; border-color: #2F1B10 !important; }

/* Markdown text */
.stMarkdown p, .stMarkdown li { color: var(--ink-2) !important; }
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3 { color: var(--ink) !important; }

/* File uploader */
[data-testid="stFileUploader"] {
  background: var(--panel) !important;
  border: 1px dashed var(--line) !important;
  border-radius: 12px !important;
}

.stAlert { border-radius: 8px !important; }
.stSpinner > div { border-top-color: var(--accent) !important; }
.stCaption { color: var(--ink-3) !important; }
code { background: var(--bg-2) !important; color: var(--ink) !important; }
div[data-testid="stNotification"] { border-radius: 8px !important; }

/* Hide streamlit chrome */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header[data-testid="stHeader"] { display: none !important; }
[data-testid="stToolbar"] { background: transparent !important; }
[data-testid="stToolbarActions"] { display: none !important; }
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] { display: none !important; }

/* Leave room for the fixed hamburger */
.block-container { padding-top: 72px !important; }

hr { border-color: var(--line) !important; margin: 16px 0 !important; }

/* Header */
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
@keyframes st-pulse {
  0% { transform: scale(1); opacity: 0.8; }
  100% { transform: scale(2.6); opacity: 0; }
}
.st-title {
  font-family: "Newsreader", Georgia, serif !important;
  font-weight: 500; font-size: 52px; line-height: 1.02; letter-spacing: -0.02em;
  color: var(--ink) !important; margin: 0 0 12px;
}
.st-title em { font-style: italic; color: var(--ink-3) !important; font-weight: 400; }
.st-subtitle { color: var(--ink-2) !important; font-size: 15px; max-width: 56ch; line-height: 1.5; margin: 0; }
</style>
"""


def render_hamburger(active: str = "") -> None:
    """Fixed hamburger menu in the top-left with links to each page."""
    items = [("/", "Gallery"), ("/query", "Query"), ("/ingest", "Ingest")]
    links = ""
    for href, label in items:
        cls = ' class="ham-active"' if label.lower() == active else ""
        links += f'<a href="{href}" target="_self"{cls}>{label}</a>'
    st.markdown(
        f"""
        <style>
          .ham {{ position: fixed; top: 14px; left: 16px; z-index: 1000000; }}
          .ham > summary {{
            list-style: none; cursor: pointer; width: 40px; height: 40px;
            display: flex; align-items: center; justify-content: center;
            background: #FFFFFF; border: 1px solid #E5E0D2; border-radius: 10px;
            box-shadow: 0 1px 2px rgba(28,27,23,0.06); transition: border-color .15s;
          }}
          .ham > summary::-webkit-details-marker {{ display: none; }}
          .ham > summary:hover {{ border-color: #D9D2BF; }}
          .ham .bars {{ display: block; width: 18px; height: 2px; background: #1C1B17; border-radius: 2px; position: relative; }}
          .ham .bars::before, .ham .bars::after {{
            content: ""; position: absolute; left: 0; width: 18px; height: 2px; background: #1C1B17; border-radius: 2px;
          }}
          .ham .bars::before {{ top: -6px; }}
          .ham .bars::after {{ top: 6px; }}
          .ham nav {{
            position: absolute; top: 48px; left: 0; min-width: 180px;
            background: #FFFFFF; border: 1px solid #E5E0D2; border-radius: 12px;
            box-shadow: 0 12px 32px -12px rgba(28,27,23,0.18);
            padding: 8px; display: flex; flex-direction: column; gap: 2px;
          }}
          .ham nav a {{
            font-family: "Inter Tight", sans-serif; font-size: 14px; color: #1C1B17;
            text-decoration: none; padding: 9px 12px; border-radius: 8px;
          }}
          .ham nav a:hover {{ background: #EBE7DD; }}
          .ham nav a.ham-active {{ background: rgba(28,27,23,0.06); font-weight: 600; }}
        </style>
        <details class="ham">
          <summary><span class="bars"></span></summary>
          <nav>{links}</nav>
        </details>
        """,
        unsafe_allow_html=True,
    )


def render_header(title_html: str, subtitle: str) -> None:
    """Editorial crumb + title header, with live online status."""
    online = api_get("/status") is not None
    crumb_pulse = '<span class="st-crumb-pulse"></span>' if online else ""
    crumb_status = (
        f'<span style="color:#57544C;">{crumb_pulse} Online · always on</span>'
        if online else '<span style="color:#8C8779;">Offline</span>'
    )
    st.markdown(
        f"""<div class="st-crumb">
        <span>Agent · memory layer</span>
        <span style="color:#B5AF9E;margin:0 4px;">—</span>
        {crumb_status}
        </div>
        <h1 class="st-title">{title_html}</h1>
        <p class="st-subtitle">{subtitle}</p>
        <div style="margin: 28px 0 0;"></div>""",
        unsafe_allow_html=True,
    )
