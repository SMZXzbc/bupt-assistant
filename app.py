import os
import sys
import html as html_module
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv
import markdown as md_lib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
load_dotenv()


def _lazy_import(module_name, func_name):
    import importlib
    module = importlib.import_module(module_name)
    return getattr(module, func_name)


def _md_to_html(text: str) -> str:
    """Convert markdown to HTML, stripping any raw HTML tags from the source text."""
    import re
    # Remove all raw HTML tags (with or without attributes) that may leak from scraper output
    clean = re.sub(r'<(div|span|button|input|img|a|p|ul|ol|li|table|tr|td|th|form|script|style|link|meta|head|body|html)\b[^>]*/?>', '', text)
    clean = re.sub(r'</(div|span|button|input|img|a|p|ul|ol|li|table|tr|td|th|form|script|style|head|body|html)>', '', clean)
    clean = re.sub(r'<!DOCTYPE[^>]*>', '', clean)
    return md_lib.markdown(
        clean,
        extensions=["fenced_code", "tables", "nl2br", "sane_lists"],
    )


# ======================== PAGE CONFIG ========================
st.set_page_config(
    page_title="北邮校园智能助手",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ======================== SESSION STATE ========================
defaults = {
    "dark_mode": True,
    "conversations": {},
    "active_conversation": None,
    "vectorstore": None,
    "vectorstore_loaded": False,
    "doc_count": 0,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


def _create_new_conversation():
    cid = datetime.now().strftime("%Y%m%d%H%M%S")
    st.session_state["conversations"][cid] = {
        "title": "新对话",
        "messages": [],
        "created": datetime.now().strftime("%H:%M"),
    }
    st.session_state["active_conversation"] = cid
    return cid


def _get_active_messages():
    cid = st.session_state.get("active_conversation")
    if cid and cid in st.session_state["conversations"]:
        return st.session_state["conversations"][cid]["messages"]
    return []


def _generate_and_store_answer(cid: str, user_text: str, now: str):
    """Generate answer using RAG pipeline and store in conversation."""
    vectorstore = st.session_state.get("vectorstore")

    # Lazy load KB from disk if not in session
    if not vectorstore and not st.session_state.get("vectorstore_loaded"):
        persist_dir = "chroma_db"
        if os.path.exists(persist_dir) and os.listdir(persist_dir):
            try:
                get_embedding_function = _lazy_import("src.embedding", "get_embedding_function")
                load_vectorstore = _lazy_import("src.retriever", "load_vectorstore")
                embeddings = get_embedding_function()
                vectorstore = load_vectorstore(embeddings, persist_dir)
                st.session_state["vectorstore"] = vectorstore
                st.session_state["vectorstore_loaded"] = True
            except Exception as e:
                st.session_state["conversations"][cid]["messages"].append(
                    {"role": "assistant", "content": f"⚠️ 知识库加载失败: {e}", "timestamp": now})
                return
        else:
            st.session_state["conversations"][cid]["messages"].append(
                {"role": "assistant",
                 "content": "⚠️ 知识库尚未加载，请先在侧边栏点击「加载 / 重新加载知识库」。",
                 "timestamp": now})
            return

    # Generate
    try:
        if vectorstore:
            from src.retriever import hybrid_search
            results = hybrid_search(vectorstore, user_text, k=8)
            generate_answer = _lazy_import("src.generator", "generate_answer")
            answer = generate_answer(user_text, results[:8])
        else:
            generate_answer = _lazy_import("src.generator", "generate_answer")
            answer = generate_answer(user_text, [])
        print(f"[DEBUG] Answer OK, len={len(answer)}", file=sys.stderr); sys.stderr.flush()
    except Exception as e:
        import traceback
        print(f"[ERROR] {type(e).__name__}: {e}", file=sys.stderr); traceback.print_exc(); sys.stderr.flush()
        answer = f"⚠️ 无法生成回答：{type(e).__name__}: {e}"

    st.session_state["conversations"][cid]["messages"].append(
        {"role": "assistant", "content": answer, "timestamp": now})


# ======================== THEME CSS ========================
D = st.session_state["dark_mode"]

# Color palette
BG_GRADIENT = "linear-gradient(160deg, rgba(8,12,28,0.88) 0%, rgba(14,22,46,0.82) 40%, rgba(10,18,38,0.88) 100%)" if D \
    else "linear-gradient(160deg, #f0f2f5 0%, #e4e9f2 40%, #edf0f7 100%)"
SB_BG = "rgba(12,18,34,0.92)" if D else "rgba(245,245,250,0.95)"
SB_BORDER = "rgba(255,255,255,0.06)" if D else "rgba(0,0,0,0.08)"
TXT = "#e2e8f0" if D else "#1a1a2e"
TXT2 = "#8b95a8" if D else "#6b7280"
CARD_BG = "rgba(20,30,55,0.65)" if D else "rgba(255,255,255,0.85)"
CARD_BD = "rgba(255,255,255,0.08)" if D else "rgba(0,0,0,0.1)"
INPUT_BG = "rgba(20,30,55,0.85)" if D else "rgba(255,255,255,0.95)"
INPUT_BD = "rgba(255,255,255,0.12)" if D else "rgba(0,0,0,0.15)"
USER_BG = "linear-gradient(135deg, #b91c24 0%, #dc2626 100%)"
AI_BG = "rgba(18,28,52,0.88)" if D else "rgba(255,255,255,0.92)"
AI_BD = "rgba(255,255,255,0.08)" if D else "rgba(0,0,0,0.08)"
SHADOW = "0 8px 32px rgba(0,0,0,0.35)" if D else "0 8px 32px rgba(0,0,0,0.12)"
ACCENT = "#dc2626"
ACCENT_H = "#b91c24"
HOVER = "rgba(255,255,255,0.05)" if D else "rgba(0,0,0,0.04)"
GLOW = "0 0 20px rgba(220,38,38,0.25)"
CODE_BG = "rgba(0,0,0,0.4)" if D else "rgba(0,0,0,0.05)"
SRC_BG = "rgba(255,255,255,0.04)" if D else "rgba(0,0,0,0.03)"

# Starfield CSS (dark mode only)
STARFIELD_CSS = ""
if D:
    STARFIELD_CSS = """
.stApp::before {
    content: "";
    position: fixed;
    top: 0; left: 0;
    width: 100%; height: 100%;
    z-index: 0;
    pointer-events: none;
    background:
        radial-gradient(1px 1px at 10% 15%, rgba(255,255,255,0.8), transparent),
        radial-gradient(1px 1px at 25% 35%, rgba(255,255,255,0.6), transparent),
        radial-gradient(1.2px 1.2px at 40% 10%, rgba(255,255,255,0.9), transparent),
        radial-gradient(1px 1px at 55% 45%, rgba(255,255,255,0.5), transparent),
        radial-gradient(1.5px 1.5px at 70% 20%, rgba(200,220,255,0.9), transparent),
        radial-gradient(1px 1px at 85% 55%, rgba(255,255,255,0.7), transparent),
        radial-gradient(1px 1px at 15% 60%, rgba(255,255,255,0.6), transparent),
        radial-gradient(1.3px 1.3px at 30% 80%, rgba(200,220,255,0.8), transparent),
        radial-gradient(1px 1px at 50% 70%, rgba(255,255,255,0.5), transparent),
        radial-gradient(1px 1px at 65% 85%, rgba(255,255,255,0.7), transparent),
        radial-gradient(1.4px 1.4px at 80% 40%, rgba(255,255,255,0.9), transparent),
        radial-gradient(1px 1px at 95% 75%, rgba(255,255,255,0.6), transparent),
        radial-gradient(1px 1px at 5% 90%, rgba(255,255,255,0.5), transparent),
        radial-gradient(1.2px 1.2px at 20% 50%, rgba(200,220,255,0.8), transparent),
        radial-gradient(1px 1px at 35% 25%, rgba(255,255,255,0.6), transparent),
        radial-gradient(1px 1px at 48% 58%, rgba(255,255,255,0.4), transparent),
        radial-gradient(1.5px 1.5px at 62% 12%, rgba(255,255,255,0.9), transparent),
        radial-gradient(1px 1px at 78% 68%, rgba(255,255,255,0.5), transparent),
        radial-gradient(1px 1px at 92% 30%, rgba(255,255,255,0.7), transparent),
        radial-gradient(1.3px 1.3px at 8% 42%, rgba(200,220,255,0.8), transparent),
        radial-gradient(1px 1px at 42% 92%, rgba(255,255,255,0.6), transparent),
        radial-gradient(1px 1px at 58% 32%, rgba(255,255,255,0.5), transparent),
        radial-gradient(1.2px 1.2px at 72% 78%, rgba(255,255,255,0.7), transparent),
        radial-gradient(1px 1px at 88% 15%, rgba(255,255,255,0.8), transparent);
    animation: starTwinkle 4s ease-in-out infinite alternate;
}
.stApp::after {
    content: "";
    position: fixed;
    top: 0; left: 0;
    width: 100%; height: 100%;
    z-index: 0;
    pointer-events: none;
    background:
        radial-gradient(1px 1px at 3% 22%, rgba(255,255,255,0.5), transparent),
        radial-gradient(1.4px 1.4px at 12% 73%, rgba(200,220,255,0.8), transparent),
        radial-gradient(1px 1px at 22% 8%, rgba(255,255,255,0.6), transparent),
        radial-gradient(1px 1px at 33% 52%, rgba(255,255,255,0.4), transparent),
        radial-gradient(1.3px 1.3px at 44% 38%, rgba(255,255,255,0.9), transparent),
        radial-gradient(1px 1px at 56% 88%, rgba(255,255,255,0.5), transparent),
        radial-gradient(1px 1px at 67% 5%, rgba(255,255,255,0.7), transparent),
        radial-gradient(1.5px 1.5px at 76% 62%, rgba(200,220,255,0.9), transparent),
        radial-gradient(1px 1px at 83% 28%, rgba(255,255,255,0.6), transparent),
        radial-gradient(1px 1px at 91% 82%, rgba(255,255,255,0.5), transparent),
        radial-gradient(1.2px 1.2px at 7% 55%, rgba(255,255,255,0.7), transparent),
        radial-gradient(1px 1px at 18% 45%, rgba(255,255,255,0.4), transparent),
        radial-gradient(1px 1px at 28% 95%, rgba(255,255,255,0.6), transparent),
        radial-gradient(1.4px 1.4px at 38% 18%, rgba(200,220,255,0.8), transparent),
        radial-gradient(1px 1px at 52% 65%, rgba(255,255,255,0.5), transparent),
        radial-gradient(1px 1px at 63% 42%, rgba(255,255,255,0.7), transparent),
        radial-gradient(1.3px 1.3px at 74% 90%, rgba(255,255,255,0.9), transparent),
        radial-gradient(1px 1px at 82% 50%, rgba(255,255,255,0.4), transparent),
        radial-gradient(1px 1px at 93% 12%, rgba(255,255,255,0.6), transparent),
        radial-gradient(1.2px 1.2px at 2% 85%, rgba(200,220,255,0.8), transparent),
        radial-gradient(1px 1px at 45% 48%, rgba(255,255,255,0.5), transparent),
        radial-gradient(1px 1px at 60% 22%, rgba(255,255,255,0.6), transparent),
        radial-gradient(1.5px 1.5px at 86% 70%, rgba(255,255,255,0.8), transparent),
        radial-gradient(1px 1px at 97% 38%, rgba(255,255,255,0.5), transparent);
    animation: starTwinkle2 5s ease-in-out infinite alternate;
}
@keyframes starTwinkle {
    0% { opacity: 0.5; }
    50% { opacity: 1; }
    100% { opacity: 0.6; }
}
@keyframes starTwinkle2 {
    0% { opacity: 0.8; }
    50% { opacity: 0.4; }
    100% { opacity: 1; }
}
"""

st.markdown(f"""
<style>
/* ===== Base ===== */
.stApp {{ background: {BG_GRADIENT}; background-attachment: fixed; color: {TXT}; }}
[data-testid="stSidebar"] {{ position: relative; z-index: 10; }}
{STARFIELD_CSS}
/* ===== Hide Streamlit chrome ===== */
#MainMenu, footer, header, .stDeployButton {{ visibility: hidden !important; }}
[data-testid="stToolbar"] {{ display: none !important; }}

/* ===== Scrollbar ===== */
::-webkit-scrollbar {{ width: 5px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{ background: rgba(220,38,38,0.35); border-radius: 3px; }}

/* ===== Sidebar ===== */
[data-testid="stSidebar"] {{
    background: {SB_BG} !important;
    backdrop-filter: blur(24px);
    border-right: 1px solid {SB_BORDER} !important;
}}

.sidebar-logo-row {{
    display: flex; align-items: center; gap: 12px;
    padding: 1.2rem 1rem 0.9rem;
    border-bottom: 1px solid {SB_BORDER};
    margin-bottom: 0.6rem;
}}
.sidebar-icon {{
    width: 40px; height: 40px;
    background: linear-gradient(135deg, #dc2626, #f59e0b);
    border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.3rem;
    box-shadow: 0 4px 12px rgba(220,38,38,0.3);
}}
.sidebar-brand {{ font-size: 1rem; font-weight: 700; color: {TXT}; }}
.sidebar-sub {{ font-size: 0.68rem; color: {TXT2}; }}

/* ===== Welcome ===== */
.welcome-wrap {{
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    min-height: 65vh; text-align: center; padding: 2rem;
}}
.welcome-glow {{
    width: 90px; height: 90px;
    background: linear-gradient(135deg, #dc2626, #f59e0b);
    border-radius: 24px;
    display: flex; align-items: center; justify-content: center;
    font-size: 2.8rem;
    margin-bottom: 1.6rem;
    box-shadow: 0 12px 40px rgba(220,38,38,0.35), 0 0 60px rgba(220,38,38,0.1);
    animation: wfloat 5s ease-in-out infinite;
}}
@keyframes wfloat {{
    0%,100% {{ transform: translateY(0); }}
    50% {{ transform: translateY(-10px); }}
}}
.welcome-h1 {{
    font-size: 2rem; font-weight: 800; margin-bottom: 0.4rem;
    background: linear-gradient(135deg, #ef4444, #f59e0b);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
}}
.welcome-p {{
    color: {TXT2}; font-size: 0.95rem; margin-bottom: 2.2rem; max-width: 420px;
}}
.feature-row {{
    display: grid; grid-template-columns: repeat(3,1fr); gap: 1rem;
    max-width: 520px; width: 100%; margin-bottom: 2.5rem;
}}
.feature-card {{
    background: {CARD_BG}; border: 1px solid {CARD_BD}; border-radius: 14px;
    padding: 1.1rem 0.8rem; text-align: center;
    backdrop-filter: blur(8px); transition: transform 0.2s, box-shadow 0.2s;
}}
.feature-card:hover {{ transform: translateY(-3px); box-shadow: {GLOW}; }}
.feature-icon {{ font-size: 1.6rem; margin-bottom: 0.3rem; }}
.feature-title {{ font-size: 0.82rem; font-weight: 700; color: {TXT}; margin-bottom: 0.15rem; }}
.feature-desc {{ font-size: 0.72rem; color: {TXT2}; }}

.q-grid {{
    display: grid; grid-template-columns: repeat(2,1fr); gap: 0.6rem;
    max-width: 520px; width: 100%;
}}
.q-card {{
    padding: 0.65rem 1rem; background: {CARD_BG}; border: 1px solid {CARD_BD};
    border-radius: 12px; color: {TXT}; font-size: 0.82rem; cursor: pointer;
    text-align: left; transition: all 0.2s; backdrop-filter: blur(8px);
}}
.q-card:hover {{
    background: rgba(220,38,38,0.12); border-color: rgba(220,38,38,0.35);
    transform: translateX(4px);
}}

/* ===== Chat bubbles ===== */
.chat-wrap {{ display: flex; flex-direction: column; gap: 0.8rem; padding: 0.5rem 0; }}
.bubble-row {{ display: flex; gap: 10px; max-width: 82%; animation: bfade 0.3s ease; }}
@keyframes bfade {{ from {{ opacity:0; transform:translateY(8px); }} to {{ opacity:1; transform:translateY(0); }} }}
.bubble-row.user {{ align-self: flex-end; flex-direction: row-reverse; }}
.bubble-row.assistant {{ align-self: flex-start; }}
.b-avatar {{
    width: 36px; height: 36px; border-radius: 11px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.1rem; flex-shrink: 0; margin-top: 2px;
}}
.b-avatar.u {{ background: linear-gradient(135deg, #dc2626, #ef4444); }}
.b-avatar.a {{ background: linear-gradient(135deg, #dc2626, #f59e0b); }}
.b-body {{ display: flex; flex-direction: column; gap: 3px; }}
.b-bubble {{
    padding: 0.75rem 1rem; border-radius: 16px; font-size: 0.88rem; line-height: 1.65;
    word-break: break-word;
}}
.b-bubble.u {{
    background: {USER_BG}; color: #fff; border-bottom-right-radius: 4px;
    box-shadow: 0 3px 12px rgba(220,38,38,0.2);
}}
.b-bubble.a {{
    background: {AI_BG}; color: {TXT}; border: 1px solid {AI_BD};
    border-bottom-left-radius: 4px; backdrop-filter: blur(12px);
    box-shadow: 0 3px 12px rgba(0,0,0,0.15);
}}
.b-meta {{ font-size: 0.7rem; color: {TXT2}; padding: 0 4px; }}
.bubble-row.user .b-meta {{ text-align: right; }}
.b-source {{
    margin-top: 6px; padding: 5px 9px; background: {SRC_BG};
    border-radius: 8px; font-size: 0.73rem; color: {TXT2};
    border-left: 2px solid {ACCENT};
}}

/* ===== Markdown in bubbles ===== */
.b-bubble h1,.b-bubble h2,.b-bubble h3 {{ color: {TXT}; margin: 0.7em 0 0.3em; font-weight: 700; }}
.b-bubble h1 {{ font-size: 1.2em; }} .b-bubble h2 {{ font-size: 1.1em; }}
.b-bubble p {{ margin: 0.35em 0; }}
.b-bubble ul,.b-bubble ol {{ padding-left: 1.4em; margin: 0.35em 0; }}
.b-bubble li {{ margin: 0.15em 0; }}
.b-bubble blockquote {{
    border-left: 3px solid {ACCENT}; margin: 0.5em 0; padding: 0.3em 0.9em;
    background: {SRC_BG}; border-radius: 0 8px 8px 0; color: {TXT2};
}}
.b-bubble code {{ background: {CODE_BG}; padding: 1px 5px; border-radius: 4px;
    font-family: 'Fira Code','Cascadia Code',monospace; font-size: 0.84em; }}
.b-bubble pre {{
    background: {CODE_BG}; border: 1px solid {CARD_BD}; border-radius: 10px;
    padding: 0.9rem; overflow-x: auto; margin: 0.5em 0;
}}
.b-bubble pre code {{ background: none; padding: 0; font-size: 0.82em; }}
.b-bubble table {{ width: 100%; border-collapse: collapse; margin: 0.5em 0; font-size: 0.85em; }}
.b-bubble th,.b-bubble td {{ padding: 0.4rem 0.7rem; border: 1px solid {CARD_BD}; text-align: left; }}
.b-bubble th {{ background: {SRC_BG}; font-weight: 600; }}
.b-bubble a {{ color: {ACCENT}; text-decoration: none; }}
.b-bubble a:hover {{ text-decoration: underline; }}
.b-bubble img {{ max-width: 100%; border-radius: 8px; }}

/* ===== Typing dots ===== */
.typing-dots {{ display:flex; align-items:center; gap:5px; padding:10px 14px; }}
.typing-dots span {{
    width:7px; height:7px; border-radius:50%; background:{ACCENT};
    animation: tbounce 1.4s ease-in-out infinite;
}}
.typing-dots span:nth-child(2) {{ animation-delay:0.2s; }}
.typing-dots span:nth-child(3) {{ animation-delay:0.4s; }}
@keyframes tbounce {{
    0%,60%,100% {{ transform:translateY(0); opacity:0.3; }}
    30% {{ transform:translateY(-7px); opacity:1; }}
}}

/* ===== Loading spinner ===== */
@keyframes spin {{ to {{ transform:rotate(360deg); }} }}

/* ===== Input bar ===== */
.input-bar {{
    background: {CARD_BG}; border: 1px solid {CARD_BD}; border-radius: 16px;
    padding: 0.7rem 1rem; backdrop-filter: blur(16px);
    box-shadow: 0 4px 20px rgba(0,0,0,0.15);
}}
.input-hint {{ font-size:0.7rem; color:{TXT2}; opacity:0.6; margin-top:4px; text-align:center; }}
</style>
""", unsafe_allow_html=True)

# ======================== LOADING OVERLAY (first load only) ========================
if "_loading_shown" not in st.session_state:
    st.session_state["_loading_shown"] = True
    st.markdown("""
    <div id="loading-overlay">
      <div style="display:flex;flex-direction:column;align-items:center;gap:24px;">
        <div class="loading-logo">🎓</div>
        <div class="loading-title">北邮校园智能助手</div>
        <div class="loading-sub">BUPT AI Assistant</div>
        <div class="loading-bar-wrap"><div class="loading-bar"></div></div>
        <div class="loading-text">正在加载...</div>
      </div>
    </div>
    <style>
    #loading-overlay{position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:99999;background:linear-gradient(160deg,#080c1c,#0e162e 40%,#0a1226);display:flex;align-items:center;justify-content:center;animation:overlayFadeOut .8s ease 2.5s forwards}
    @keyframes overlayFadeOut{0%{opacity:1;visibility:visible}100%{opacity:0;visibility:hidden;pointer-events:none}}
    .loading-logo{width:80px;height:80px;background:linear-gradient(135deg,#dc2626,#f59e0b);border-radius:22px;display:flex;align-items:center;justify-content:center;font-size:2.4rem;box-shadow:0 12px 40px rgba(220,38,38,.35),0 0 60px rgba(220,38,38,.1);animation:loadFloat 2s ease-in-out infinite}
    @keyframes loadFloat{0%,100%{transform:translateY(0) scale(1)}50%{transform:translateY(-8px) scale(1.03)}}
    .loading-title{font-size:1.5rem;font-weight:800;background:linear-gradient(135deg,#ef4444,#f59e0b);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
    .loading-sub{font-size:.8rem;color:#6b7280;margin-top:-16px}
    .loading-bar-wrap{width:240px;height:4px;background:rgba(255,255,255,.08);border-radius:4px;overflow:hidden;margin-top:8px}
    .loading-bar{width:0%;height:100%;border-radius:4px;background:linear-gradient(90deg,#dc2626,#f59e0b,#dc2626);background-size:200% 100%;animation:loadBar 2s ease-in-out forwards,loadShimmer 1.5s linear infinite}
    @keyframes loadBar{0%{width:0}30%{width:45%}60%{width:70%}85%{width:88%}100%{width:100%}}
    @keyframes loadShimmer{0%{background-position:200% 0}100%{background-position:-200% 0}}
    .loading-text{font-size:.75rem;color:#4b5563;animation:loadPulse 1.2s ease-in-out infinite}
    @keyframes loadPulse{0%,100%{opacity:.5}50%{opacity:1}}
    </style>
    """, unsafe_allow_html=True)

# ======================== QUERY PARAMS ========================
qp = st.query_params

if "conv" in qp and qp["conv"][0] in st.session_state["conversations"]:
    st.session_state["active_conversation"] = qp["conv"][0]
    st.query_params.clear()
    st.rerun()

if qp.get("new") == ["1"]:
    _create_new_conversation()
    st.query_params.clear()
    st.rerun()

if qp.get("toggle_theme") == ["1"]:
    st.session_state["dark_mode"] = not st.session_state["dark_mode"]
    st.query_params.clear()
    st.rerun()

# Ensure active conversation
if not st.session_state.get("active_conversation") or \
   st.session_state["active_conversation"] not in st.session_state["conversations"]:
    if st.session_state["conversations"]:
        st.session_state["active_conversation"] = list(st.session_state["conversations"].keys())[-1]

# Handle delete
if qp.get("delete") == ["1"] and qp.get("conv"):
    did = qp["conv"][0]
    st.session_state["conversations"].pop(did, None)
    if st.session_state.get("active_conversation") == did:
        st.session_state["active_conversation"] = \
            list(st.session_state["conversations"].keys())[-1] if st.session_state["conversations"] else None
    st.query_params.clear()
    st.rerun()

# ======================== SIDEBAR ========================
with st.sidebar:
    # Logo
    st.markdown("""
    <div class="sidebar-logo-row">
        <div class="sidebar-icon">🎓</div>
        <div>
            <div class="sidebar-brand">北邮智能助手</div>
            <div class="sidebar-sub">BUPT AI Assistant</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # New chat
    if st.button("＋ 新建对话", use_container_width=True, key="btn_new"):
        _create_new_conversation()
        st.rerun()

    st.divider()

    # KB status + load button
    dc = st.session_state.get("doc_count", 0)
    loaded = st.session_state.get("vectorstore_loaded", False)
    dot_color = "#22c55e" if loaded else "#f59e0b"
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:6px;font-size:0.75rem;color:{TXT2};padding:0 4px;margin-bottom:6px;">
        <span style="width:7px;height:7px;border-radius:50%;background:{dot_color};display:inline-block;
            {'box-shadow:0 0 6px rgba(34,197,94,0.5);' if loaded else ''}"></span>
        知识库：{'已加载' if loaded else '未加载'} ({dc} 块)
    </div>
    """, unsafe_allow_html=True)

    if st.button("🔄 加载 / 重新加载知识库", use_container_width=True, type="primary", key="btn_kb"):
        with st.spinner("正在加载知识库..."):
            load_documents = _lazy_import("src.loader", "load_documents")
            split_documents = _lazy_import("src.splitter", "split_documents")
            get_embedding_function = _lazy_import("src.embedding", "get_embedding_function")
            create_vectorstore = _lazy_import("src.retriever", "create_vectorstore")
            import shutil

            docs = load_documents("data")
            if docs:
                chunks = split_documents(docs)
                embeddings = get_embedding_function()
                for d in ["chroma_db", "vectorizer.pkl"]:
                    if os.path.isdir(d):
                        try: shutil.rmtree(d)
                        except: pass
                    elif os.path.isfile(d):
                        try: os.remove(d)
                        except: pass
                vs = create_vectorstore(chunks, embeddings, "chroma_db")
                st.session_state["vectorstore"] = vs
                st.session_state["vectorstore_loaded"] = True
                st.session_state["doc_count"] = len(chunks)
                st.success(f"加载完成！共 {len(chunks)} 个文本块")
                st.rerun()
            else:
                st.error("未找到文档，请检查 data/ 目录")

    st.divider()

    # Conversation list
    st.markdown(f"<div style='font-size:0.72rem;color:{TXT2};font-weight:600;padding:0 4px 6px;letter-spacing:0.5px;'>历史对话</div>",
                unsafe_allow_html=True)

    cids = list(st.session_state["conversations"].keys())
    if cids:
        for cid in reversed(cids):
            conv = st.session_state["conversations"][cid]
            is_active = cid == st.session_state.get("active_conversation")
            cols = st.columns([1, 0.15])
            with cols[0]:
                if st.button(f"💬 {conv['title']}", key=f"sc_{cid}", use_container_width=True):
                    st.session_state["active_conversation"] = cid
                    st.rerun()
            with cols[1]:
                if st.button("✕", key=f"sd_{cid}"):
                    st.session_state["conversations"].pop(cid, None)
                    if st.session_state.get("active_conversation") == cid:
                        st.session_state["active_conversation"] = \
                            list(st.session_state["conversations"].keys())[-1] if st.session_state["conversations"] else None
                    st.rerun()
    else:
        st.markdown(f"<div style='font-size:0.78rem;color:{TXT2};padding:8px;text-align:center;opacity:0.6;'>暂无对话记录</div>",
                    unsafe_allow_html=True)

    # Footer
    st.markdown("<div style='flex:1;'></div>", unsafe_allow_html=True)
    theme_btn = "☀️ 浅色模式" if st.session_state["dark_mode"] else "🌙 深色模式"
    if st.button(theme_btn, use_container_width=True, key="btn_theme"):
        st.session_state["dark_mode"] = not st.session_state["dark_mode"]
        st.rerun()

# ======================== MAIN CONTENT ========================
active_cid = st.session_state.get("active_conversation")
messages = _get_active_messages()
conv_title = "新对话"
if active_cid and active_cid in st.session_state["conversations"]:
    conv_title = st.session_state["conversations"][active_cid]["title"]

# Top bar
col_title, col_actions = st.columns([3, 1])
with col_title:
    st.markdown(f"<h3 style='margin:0;color:{TXT};'>💬 {html_module.escape(conv_title)}</h3>",
                unsafe_allow_html=True)
with col_actions:
    if messages:
        if st.button("📤 导出对话", use_container_width=True):
            md = "# 北邮校园智能助手 - 对话导出\n\n"
            md += f"导出时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n---\n\n"
            for m in messages:
                role = "**🧑 学生**" if m["role"] == "user" else "**🤖 助手**"
                md += f"{role}\n\n{m['content']}\n\n---\n\n"
            st.download_button("⬇️ 下载 Markdown", md, file_name="bupt_chat_export.md", mime="text/markdown")

st.divider()

# ======================== WELCOME or CHAT ========================
if not messages:
    st.markdown(f"""
    <div class="welcome-wrap">
        <div class="welcome-glow">🎓</div>
        <div class="welcome-h1">北邮校园智能助手</div>
        <div class="welcome-p">基于 RAG 技术的智能问答系统<br>为您提供准确、快速的校园信息查询服务</div>
        <div class="feature-row">
            <div class="feature-card">
                <div class="feature-icon">📚</div>
                <div class="feature-title">知识检索</div>
                <div class="feature-desc">校园文档智能检索</div>
            </div>
            <div class="feature-card">
                <div class="feature-icon">🤖</div>
                <div class="feature-title">AI 问答</div>
                <div class="feature-desc">大模型驱动回答</div>
            </div>
            <div class="feature-card">
                <div class="feature-icon">⚡</div>
                <div class="feature-title">快速响应</div>
                <div class="feature-desc">毫秒级检索速度</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"<p style='text-align:center;color:{TXT2};font-size:0.88rem;font-weight:600;margin-bottom:0.8rem;'>💡 试试这些问题</p>",
                unsafe_allow_html=True)

    qs = [
        "📚 图书馆开放时间是什么？",
        "🪪 如何办理学生证？",
        "💳 校园卡怎么充值？",
        "🍽️ 食堂在哪里？",
        "📝 如何选课？",
        "📄 毕业论文要求是什么？",
    ]
    for q in qs:
        q_clean = q.split(" ", 1)[1] if " " in q else q
        if st.button(q, key=f"qk_{q_clean[:10]}", use_container_width=True):
            if not active_cid:
                active_cid = _create_new_conversation()
            now = datetime.now().strftime("%H:%M")
            st.session_state["conversations"][active_cid]["messages"].append(
                {"role": "user", "content": q_clean, "timestamp": now})
            st.session_state["conversations"][active_cid]["title"] = q_clean[:20]
            _generate_and_store_answer(active_cid, q_clean, now)
            st.rerun()

else:
    # Render messages
    st.markdown('<div class="chat-wrap">', unsafe_allow_html=True)
    for idx, msg in enumerate(messages):
        is_user = msg["role"] == "user"
        row_cls = "user" if is_user else "assistant"
        av_cls = "u" if is_user else "a"
        b_cls = "u" if is_user else "a"
        av_icon = "🧑‍🎓" if is_user else "🤖"
        ts = msg.get("timestamp", "")

        content = msg["content"]
        source = ""
        if "📄 来源：" in content:
            parts = content.split("📄 松源：") if "📄 松源：" in content else content.split("📄 来源：")
            content = parts[0].strip()
            if len(parts) > 1:
                source = parts[1].strip()

        safe = html_module.escape(content)
        if not is_user:
            safe = _md_to_html(content)

        src_html = f'<div class="b-source">📄 来源：{html_module.escape(source)}</div>' if source else ""

        st.markdown(f"""
        <div class="bubble-row {row_cls}">
            <div class="b-avatar {av_cls}">{av_icon}</div>
            <div class="b-body">
                <div class="b-bubble {b_cls}">{safe}{src_html}</div>
                <div class="b-meta">{"🧑‍🎓 你" if is_user else "🤖 助手"} · {ts}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# ======================== INPUT ========================
st.markdown(f"""
<div class="input-hint">📎 支持上传 PDF / TXT / MD 文件 &nbsp;·&nbsp; Enter 发送 &nbsp;·&nbsp; Shift+Enter 换行</div>
""", unsafe_allow_html=True)

question = st.chat_input("输入你的问题...", key="main_input", accept_file=True, file_type=["txt", "pdf", "md"])

if question:
    if not active_cid:
        active_cid = _create_new_conversation()

    user_text = question if isinstance(question, str) else ""
    if hasattr(question, 'text') and question.text:
        user_text = question.text
    file_info = ""
    if hasattr(question, 'files') and question.files:
        for f in question.files:
            file_info += f"\n📎 {f.name}"
    if not user_text and file_info:
        user_text = f"请分析以下文件{file_info}"

    if user_text:
        now = datetime.now().strftime("%H:%M")
        st.session_state["conversations"][active_cid]["messages"].append(
            {"role": "user", "content": user_text, "timestamp": now})
        if len(st.session_state["conversations"][active_cid]["messages"]) == 1:
            st.session_state["conversations"][active_cid]["title"] = user_text[:20]

        _generate_and_store_answer(active_cid, user_text, now)
        st.rerun()
