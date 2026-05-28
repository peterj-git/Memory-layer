"""Query page — ask your memory anything (design from dashboard-2.py)."""

import time

import streamlit as st

from common import THEME_CSS, api_get, render_hamburger, render_header


def render_query() -> None:
    st.markdown(THEME_CSS, unsafe_allow_html=True)
    render_hamburger(active="query")
    render_header(
        "Ask &nbsp;<em>memory</em>",
        "The QueryAgent searches all memories and synthesises answers with citations.",
    )

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
