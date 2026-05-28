"""Ingest page — feed information into memory (design from dashboard-2.py)."""

import time
from pathlib import Path

import streamlit as st

from common import (
    INBOX_DIR,
    SAMPLE_TEXTS,
    THEME_CSS,
    UPLOAD_EXTENSIONS,
    api_post,
    render_hamburger,
    render_header,
)


def render_ingest() -> None:
    st.markdown(THEME_CSS, unsafe_allow_html=True)
    render_hamburger(active="ingest")
    render_header(
        "Feed &nbsp;<em>memory</em>",
        "Paste text or upload files. The IngestAgent processes everything automatically.",
    )

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
                with st.spinner("IngestAgent processing…"):
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
