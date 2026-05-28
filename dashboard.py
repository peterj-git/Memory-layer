"""
Agent Memory Layer — Dashboard

Multipage app. The Gallery page renders the exact `index.html` UI backed by live
agent data; a top-left hamburger menu links to the Query and Ingest pages
(designs carried over from dashboard-2.py).
"""

import json
import math
import re
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from common import api_get, render_hamburger
from ingest_page import render_ingest
from query_page import render_query

INDEX_HTML = Path(__file__).with_name("index.html")


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
        ext_upper = Path(source).suffix.lower().lstrip(".").upper()
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


def build_page(memories: list[dict], stats: dict, online: bool) -> str:
    """Inject live data into the index.html template."""
    html = INDEX_HTML.read_text(encoding="utf-8")

    memories_js = "const MEMORIES = " + json.dumps(memories) + ";"
    html = re.sub(r"const MEMORIES = \[.*?\n\];", lambda _: memories_js, html, count=1, flags=re.DOTALL)

    stats_js = "const stats = " + json.dumps(stats) + ";"
    html = re.sub(r"const stats = \{.*?\n  \};", lambda _: stats_js, html, count=1, flags=re.DOTALL)

    if not online:
        html = html.replace(
            '<span className="crumb-pulse"></span>\n'
            '              <span>Online</span>\n'
            '              <span className="ping">· last ping 12s ago</span>',
            '<span>Offline</span>',
        )

    return html


def render_gallery() -> None:
    # Strip all Streamlit chrome so only the embedded page (and hamburger) shows.
    st.markdown(
        """
        <style>
          #MainMenu, footer, header[data-testid="stHeader"] { display: none !important; }
          [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] { display: none !important; }
          .stApp { background: #F4F1EB !important; }
          .block-container { padding: 0 !important; max-width: 100% !important; }
          [data-testid="stAppViewBlockContainer"] { padding: 0 !important; }
          /* Iframe fills the viewport and scrolls internally, so the modal's
             position:fixed centers on the real window instead of the tall frame. */
          .stApp iframe { width: 100% !important; height: 100vh !important; display: block; }
          div[data-testid="stIFrame"], div:has(> iframe) { height: 100vh !important; overflow: hidden !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    render_hamburger(active="gallery")

    status = api_get("/status")
    online = status is not None
    status = status or {}

    data = api_get("/memories") or {}
    raw = data.get("memories", []) or []
    memories = [transform_memory(m, i) for i, m in enumerate(raw)]

    stats = {
        "memories": status.get("total_memories", len(memories)),
        "pending": status.get("unconsolidated", 0),
        "consolidations": status.get("consolidations", 0),
    }

    page = build_page(memories, stats, online)

    rows = math.ceil(max(len(memories), 1) / 2)
    height = 360 + rows * 360
    components.html(page, height=height, scrolling=True)


def main() -> None:
    st.set_page_config(
        page_title="Stored Memories",
        page_icon="🧠",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    pg = st.navigation(
        [
            st.Page(render_gallery, title="Gallery", url_path="gallery", default=True),
            st.Page(render_query, title="Query", url_path="query"),
            st.Page(render_ingest, title="Ingest", url_path="ingest"),
        ],
        position="hidden",
    )
    pg.run()


if __name__ == "__main__":
    main()
