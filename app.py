import streamlit as st
import asyncio
import pandas as pd
import altair as alt
import time
import json
import re
from phases import discovery, audit, synthesis
from utils import chemistry

st.set_page_config(layout="wide", page_title="Consensus")


# ---------------------------------------------------------------------------
# UNIFIED CARD RENDERER
# ---------------------------------------------------------------------------
def _esc(text):
    """HTML-escape user/LLM text to prevent broken tags."""
    return (str(text).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _get_img_b64(smiles: str) -> str:
    """Get base64 image string for a SMILES. Returns empty string on failure."""
    if not smiles:
        return ""
    # Check if already cached as image_b64 — skip if calling standalone
    analysis = chemistry.analyze_smiles(smiles)
    if analysis and analysis.get("image_b64"):
        return analysis["image_b64"]
    return ""


def render_card(mol: dict, is_lead: bool = False, max_text: int = 0) -> str:
    """Render a molecule as a self-contained HTML card.

    Used for BOTH the Optimized Lead and Top Candidates.
    Generates image from SMILES on every call (stateless, no caching issues).
    """
    name = _esc(mol.get("name", "Unknown"))
    smiles = mol.get("smiles", "")
    rationale = _esc(mol.get("rationale", ""))
    if max_text and len(rationale) > max_text:
        rationale = rationale[:max_text] + "..."

    # --- Image ---
    img_b64 = mol.get("image_b64", "") or _get_img_b64(smiles)
    if img_b64:
        img_html = (
            f'<img src="data:image/png;base64,{img_b64}" '
            f'style="width:100%;max-width:380px;height:auto;border-radius:4px;'
            f'margin:8px auto;display:block;">'
        )
    else:
        img_html = '<p style="color:#484F58;text-align:center;padding:30px 0;">No structure</p>'

    # --- Score ---
    score = mol.get("total_score", "")
    score_span = ""
    if score != "":
        try:
            score_val = float(score)
        except (TypeError, ValueError):
            score_val = 0.0
        if score_val > 80:
            score_color = "#238636"   # green
        elif score_val > 50:
            score_color = "#D29922"   # yellow
        else:
            score_color = "#DA3633"   # red
        score_span = (
            f'<span style="color:{score_color};font-weight:600;'
            f'font-family:IBM Plex Mono,monospace;">{score_val:.1f}/100</span>'
        )

    # --- Metrics ---
    m = []
    if mol.get("scaffold"):
        m.append(_esc(str(mol["scaffold"])))
    for key, label in [("mw", "MW"), ("logp", "LogP"), ("qed", "QED")]:
        if mol.get(key) is not None and mol.get(key) != "":
            m.append(f"{label}: {mol[key]}")
    metrics = " | ".join(m)

    # --- SMILES line (lead only) ---
    smiles_html = ""
    if is_lead and smiles:
        smiles_html = (
            f'<code style="font-size:0.78rem;color:#8B949E;word-break:break-all;'
            f'display:block;margin:4px 0 8px;">{_esc(smiles)}</code>'
        )

    # --- Improvements (lead only) ---
    impr_html = ""
    impr = mol.get("predicted_improvements")
    if impr and is_lead:
        if isinstance(impr, dict):
            rows = "".join(
                f'<tr><td style="padding:3px 8px;color:#8B949E;">{_esc(str(k))}</td>'
                f'<td style="padding:3px 8px;color:#E6EDF3;">{_esc(str(v))}</td></tr>'
                for k, v in impr.items()
            )
            impr_html = (
                '<p style="margin-top:10px;font-weight:600;">Predicted Improvements</p>'
                f'<table style="width:100%;font-size:0.82rem;">{rows}</table>'
            )
        elif isinstance(impr, list):
            items = "".join(
                f'<li style="color:#8B949E;">{_esc(str(x))}</li>' for x in impr
            )
            impr_html = (
                '<p style="margin-top:10px;font-weight:600;">Predicted Improvements</p>'
                f'<ul style="font-size:0.82rem;padding-left:20px;">{items}</ul>'
            )

    # --- Card wrapper ---
    # Lead: no height constraint. Candidate: fixed height with scroll.
    if is_lead:
        wrapper_style = ""
    else:
        wrapper_style = "min-height:480px;max-height:540px;overflow-y:auto;"

    return (
        f'<div style="background:#161B22;border:1px solid #30363D;border-radius:6px;'
        f'padding:16px;margin-bottom:16px;{wrapper_style}">'
        f'<div style="display:flex;justify-content:space-between;margin-bottom:6px;">'
        f'<b style="font-size:0.95rem;">{name}</b>{score_span}</div>'
        f'<div style="font-size:0.78rem;color:#8B949E;margin-bottom:8px;'
        f'font-family:IBM Plex Mono,monospace;">{metrics}</div>'
        f'{smiles_html}'
        f'{img_html}'
        f'<p style="font-size:0.8rem;color:#8B949E;margin-top:6px;">{rationale}</p>'
        f'{impr_html}'
        f'</div>'
    )


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@500&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&display=swap');

    .stApp {background-color: #0E1117; color: #E6EDF3;}
    #MainMenu, footer, header {visibility: hidden;}

    html, body, div, p, font,
    h1, h2, h3, h4, h5, h6,
    button, input, label, textarea, select,
    strong, b, em, a, li, td, th, caption,
    [data-testid="stMarkdownContainer"] {
        font-family: 'Inter', sans-serif !important;
        font-weight: 500 !important;
    }
    /* Icon protection — force Material Icons on expander toggle */
    [data-testid="stExpanderToggleIcon"],
    [data-testid="stExpanderToggleIcon"] span,
    .material-icons, i, svg, [data-baseweb="icon"] {
        font-family: 'Material Icons' !important;
        font-weight: normal !important;
    }

    .log-entry {
        color: #8B949E; font-size: 0.8rem; padding: 4px 0;
        border-bottom: 1px solid #21262d; line-height: 1.4;
        font-family: 'IBM Plex Mono', monospace;
    }

    /* Input container card — target stVerticalBlock with inline border */
    div.stVerticalBlock[style*="border"] {
        background-color: #202124 !important;
        border: 1px solid #3c4043 !important;
        border-radius: 8px !important;
        padding: 20px !important;
    }

    /* System Logs expander */
    [data-testid="stExpander"] {
        background-color: #202124 !important;
        border: 1px solid #3c4043 !important;
        border-radius: 8px !important;
    }
    [data-testid="stExpanderDetails"] {
        padding: 20px !important;
    }

    /* Submit button — neutral dark grey */
    .stButton > button,
    .stButton > button[kind="primary"],
    [data-testid="stBaseButton-primary"] {
        background-color: #303134 !important;
        border: 1px solid #3c4043 !important;
        color: #ffffff !important;
    }
    .stButton > button:hover,
    .stButton > button[kind="primary"]:hover,
    [data-testid="stBaseButton-primary"]:hover {
        background-color: #3c4043 !important;
        border-color: #5f6368 !important;
    }

    /* Preset pills — neutral dark grey */
    [data-testid="stBaseButton-pills"],
    [data-testid="stBaseButton-pillsActive"],
    [data-testid="stBaseButton-secondary"] {
        background-color: #303134 !important;
        border: 1px solid #3c4043 !important;
        color: #E6EDF3 !important;
    }
    [data-testid="stBaseButton-pills"]:hover,
    [data-testid="stBaseButton-pillsActive"]:hover,
    [data-testid="stBaseButton-secondary"]:hover {
        background-color: #3c4043 !important;
        border-color: #5f6368 !important;
    }
    /* Active pill — slightly brighter to indicate selection */
    [data-testid="stBaseButton-pillsActive"] {
        background-color: #3c4043 !important;
        border-color: #5f6368 !important;
        color: #ffffff !important;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# STATE
# ---------------------------------------------------------------------------
if "candidates" not in st.session_state:
    st.session_state.candidates = []
if "logs" not in st.session_state:
    st.session_state.logs = []
if "golden_lead" not in st.session_state:
    st.session_state.golden_lead = None
if "pipeline_running" not in st.session_state:
    st.session_state.pipeline_running = False
if "page" not in st.session_state:
    st.session_state.page = "Server"


# ---------------------------------------------------------------------------
# NAVIGATION
# ---------------------------------------------------------------------------
def render_header():
    """AlphaFold-style top navigation bar.

    Architecture: ONE st.markdown call renders the entire navbar as pure HTML.
    Navigation uses <a> links with target="_self" pointing to ?page=X.
    Streamlit reads query params on reload to determine the active page.
    No st.columns, no st.button, no overlays, no z-index — zero Streamlit
    widget involvement means zero layout side-effects.
    """
    # Sync page from query params
    qp = st.query_params
    page = qp.get("page", "Server")
    if page not in ("Server", "About"):
        page = "Server"
    st.session_state.page = page

    srv_cls = "cn-tab cn-active" if page == "Server" else "cn-tab"
    abt_cls = "cn-tab cn-active" if page == "About" else "cn-tab"

    st.markdown(f"""
    <style>
    .cn-bar {{
        display: flex; align-items: center;
        background: transparent;
        border-bottom: 1px solid #21262D;
        padding: 0 28px; height: 52px;
        margin: -1rem -1rem 24px -1rem;
    }}
    .cn-bar .cn-logo {{
        font-family: 'Inter', sans-serif;
        font-size: 1.2rem; font-weight: 700;
        color: #E6EDF3; margin-right: 24px;
        white-space: nowrap;
    }}
    .cn-bar .cn-sep {{
        width: 1px; height: 24px;
        background: #30363D; margin-right: 16px;
    }}
    .cn-bar .cn-tab {{
        font-family: 'Inter', sans-serif;
        font-size: 0.9rem; font-weight: 400;
        color: #8B949E; text-decoration: none;
        padding: 15px 14px; margin-bottom: -1px;
        border-bottom: 3px solid transparent;
        transition: color 0.15s;
    }}
    .cn-bar .cn-tab:visited {{ color: #8B949E; }}
    .cn-bar .cn-tab:hover {{ color: #C9D1D9; }}
    .cn-bar .cn-active,
    .cn-bar .cn-active:visited {{
        color: #E6EDF3;
        border-bottom-color: #4493F8;
    }}
    </style>
    <div class="cn-bar">
        <span class="cn-logo">Consensus</span>
        <div class="cn-sep"></div>
        <a class="{srv_cls}" href="?page=Server" target="_self">Server</a>
        <a class="{abt_cls}" href="?page=About" target="_self">About</a>
    </div>
    """, unsafe_allow_html=True)


def render_about():
    """About page content."""
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown("## Creating a Next-Gen Drug Discovery Solution")
        st.markdown(
            "Consensus is an ultra-fast, AI-powered drug ideation system that simulates "
            "an early-stage medicinal chemistry team in seconds. Instead of producing a "
            "single molecule, Consensus generates multiple candidate drug concepts, "
            "evaluates them across key pharmaceutical properties, iteratively improves "
            "them, and ranks the most promising options for human review.\n\n"
            "By leveraging Cerebras' extreme inference speed, Consensus compresses what "
            "traditionally takes researchers days or weeks of back-and-forth analysis "
            "into a single interactive session that can take seconds."
        )

        st.markdown("### Why Drug Discovery Needs High Inference")
        st.markdown(
            "Early-stage drug discovery is about reasoning through thousands of competing "
            "constraints at once. A good candidate has to balance biological effectiveness, "
            "safety, synthesizability, and chemical stability; most AI systems evaluate "
            "these one at a time or in sequence. That's slow and misses complex trade-offs. "
            "High-inference AI lets us evaluate many possibilities in parallel, compare them "
            "intelligently, and narrow down to the strongest options much faster.\n\n"
            "Drug ideation requires simultaneous reasoning about:\n"
            "- Target binding potential\n"
            "- Toxicity and side-effect risk\n"
            "- Drug-likeness (solubility, stability)\n"
            "- Synthetic feasibility\n"
            "- Novelty vs. existing compounds\n\n"
            "We turn what is normally a slow, sequential filtering process into a fast, "
            "parallel decision engine. That's exactly what is needed today."
        )

        st.markdown("### Technical Aspects of Consensus")
        st.info(
            "**Model:** Llama-3.3-70B via Cerebras Cloud SDK\n\n"
            "**Chemistry:** RDKit for structure validation & property calculation\n\n"
            "**Frontend:** Streamlit\n\n"
            "**Concurrency:** asyncio.gather (parallel agent calls, no sequential loops)\n\n"
            "---\n\n"
            "**Agent Roles:**\n"
            "- **Generation Agent:** Creates initial candidate molecules tailored to the "
            "target and design goals.\n"
            "- **Evaluation Agents:** Assess each candidate for binding potential, solubility, "
            "toxicity, and overall drug-likeness.\n"
            "- **Refinement Agent:** Improves candidates based on evaluation feedback, "
            "addressing weaknesses and optimizing properties.\n"
            "- **Orchestrator:** Coordinates all agents in parallel, tracks molecule versions, "
            "aggregates scores, and ranks the final candidates.\n\n"
            "**RDKit Integration:** Validates chemical structures and calculates key molecular "
            "properties, ensuring AI outputs remain chemically sound."
        )

        st.markdown("### Current Limitations & Next Steps")
        st.markdown(
            "**Limitations:**\n"
            "- Predictions are based on computational models and known chemical rules, "
            "not experimental (wet-lab) data.\n"
            "- Biological activity and toxicity estimates rely on proxy scoring methods "
            "rather than full simulation.\n"
            "- Generative outputs depend on training data patterns and may miss rare or "
            "unconventional chemistries.\n"
            "- Final molecule selection still requires expert human review.\n\n"
            "**Next Steps for Consensus:**\n"
            "- Integrate predictive ML models trained on experimental bioactivity datasets.\n"
            "- Add docking and binding affinity simulations for stronger target validation.\n"
            "- Incorporate synthesis-planning tools to assess real-world manufacturability."
        )


render_header()

# ---------------------------------------------------------------------------
# PAGE ROUTING
# ---------------------------------------------------------------------------
if st.session_state.page == "About":
    render_about()
    st.stop()

# ---------------------------------------------------------------------------
# SERVER PAGE — INPUT (CENTERED)
# ---------------------------------------------------------------------------
_, c_center, _ = st.columns([1, 2, 1])

with c_center:
    with st.container(border=True):
        st.markdown("#### Enter Target Protein")
        preset = st.pills(
            "Try a Preset:",
            ["KRAS G12C", "EGFR T790M", "JAK2 V617F", "Custom"],
            selection_mode="single",
        )
        default_val = preset if preset and preset != "Custom" else ""
        target = st.text_input(
            "Target Query", value=default_val,
            placeholder="e.g. BRAF V600E", label_visibility="collapsed",
        )
        st.caption("Need ideas? Search verified targets on [UniProt](https://www.uniprot.org/).")
        b1, b2, b3 = st.columns([1, 1, 1])
        with b2:
            run_btn = st.button("Submit", type="primary", use_container_width=True)

    log_container = st.empty()

# ---------------------------------------------------------------------------
# EXECUTION
# ---------------------------------------------------------------------------
if run_btn and target:
    st.session_state.logs = []
    st.session_state.pipeline_running = True

    with log_container.status("Validating Target...", expanded=True) as status:
        is_valid, reason = asyncio.run(discovery.validate_topic(target))
        if not is_valid:
            status.update(label="Validation Failed", state="error", expanded=True)
            st.error(reason)
            st.session_state.pipeline_running = False
            st.stop()

        status.update(label="Initiating Protocol...", state="running")

        st.write("Phase 1: Spawning 16 Chemical Agents...")
        st.session_state.logs.append(f"[Phase 1] Spawning agents for target: {target}")
        raw = asyncio.run(discovery.generate_candidates(target))
        st.session_state.logs.append(f"[Phase 1] Generated {len(raw)} raw candidates.")

        st.write("Phase 2: Validating structures via RDKit...")
        valid_mols = []
        for c in raw:
            analysis = chemistry.analyze_smiles(c.get("smiles", ""))
            if analysis:
                c.update(analysis)
                valid_mols.append(c)
        st.session_state.logs.append(
            f"[Phase 2] Physics Engine: {len(valid_mols)}/{len(raw)} valid."
        )

        if not valid_mols:
            status.update(label="No valid molecules", state="error", expanded=True)
            st.session_state.pipeline_running = False
            st.stop()

        st.write("Phase 3: Running Toxicity Audit (Llama-70B)...")
        ranked = asyncio.run(audit.audit_candidates(valid_mols))
        st.session_state.candidates = ranked
        st.session_state.logs.append(
            f"[Phase 3] Audit complete. Top score: {ranked[0].get('total_score')}"
        )

        st.write("Phase 4: Optimizing Lead Candidate...")
        lead = asyncio.run(synthesis.synthesize_lead(ranked, target))
        # Force consistent naming: [source candidate name]-OPT
        source_name = ranked[0].get("name", "CB-LEAD-C01")
        opt_name = f"{source_name}-OPT"
        if isinstance(lead, dict):
            lead["name"] = opt_name
            if isinstance(lead.get("raw"), str):
                # Raw text path — will be re-parsed during render;
                # inject name so the parsed dict also gets it
                pass
        st.session_state.golden_lead = lead
        st.session_state.logs.append("[Phase 4] Lead optimization complete.")

        status.update(label="Mission Complete", state="complete", expanded=False)
        st.session_state.pipeline_running = False

# ---------------------------------------------------------------------------
# LOGS (CENTERED, UNDER BUTTON)
# ---------------------------------------------------------------------------
if not st.session_state.pipeline_running and st.session_state.logs:
    with log_container.container():
        with st.expander("System Logs", expanded=False):
            for log in st.session_state.logs:
                st.markdown(
                    f"<div class='log-entry'>{log}</div>", unsafe_allow_html=True
                )

# ---------------------------------------------------------------------------
# RESULTS (FULL WIDTH)
# ---------------------------------------------------------------------------
if st.session_state.candidates:
    st.divider()

    # --- Optimized Lead ---
    gl = st.session_state.golden_lead
    if gl:
        st.markdown("### Optimized Lead")
        try:
            raw_text = ""
            opt = None

            if isinstance(gl, dict) and "raw" in gl:
                raw_text = str(gl["raw"])
            elif isinstance(gl, dict) and "name" in gl:
                opt = gl
            elif isinstance(gl, str):
                raw_text = gl

            if opt is None and raw_text:
                cleaned = re.sub(r"```json|```", "", raw_text).strip()
                match = re.search(r"\{[\s\S]*\}", cleaned)
                if match:
                    opt = json.loads(match.group(0))

            if opt:
                # Force consistent naming from the stored lead name
                if isinstance(gl, dict) and gl.get("name"):
                    opt["name"] = gl["name"]
                # Ensure image_b64 exists and persist it to session state
                if not opt.get("image_b64"):
                    # Attempt 1: generate from the lead's own SMILES
                    if opt.get("smiles"):
                        analysis = chemistry.analyze_smiles(opt["smiles"])
                        if analysis:
                            opt["image_b64"] = analysis["image_b64"]
                    # Attempt 2: fallback to top candidate's image
                    if not opt.get("image_b64") and st.session_state.candidates:
                        opt["image_b64"] = st.session_state.candidates[0].get("image_b64", "")
                    # Persist so we never regenerate on rerun
                    if isinstance(gl, dict):
                        gl["image_b64"] = opt.get("image_b64", "")
                st.markdown(render_card(opt, is_lead=True), unsafe_allow_html=True)
            else:
                st.warning("Analysis incomplete (JSON parsing failed).")
                with st.expander("Raw Output"):
                    st.text(raw_text)

        except Exception as e:
            st.error(f"Display Error: {e}")

        st.divider()

    # --- Top 6 Candidates ---
    st.markdown("### Top Candidates")
    top6 = st.session_state.candidates[:6]

    for row_start in range(0, len(top6), 3):
        row = top6[row_start:row_start + 3]
        cols = st.columns(3)
        for i, mol in enumerate(row):
            with cols[i]:
                st.markdown(
                    render_card(mol, max_text=120), unsafe_allow_html=True
                )

    # --- Visual Analytics ---
    st.divider()
    chart_data = pd.DataFrame(st.session_state.candidates)
    chart = alt.Chart(chart_data).mark_circle(size=80).encode(
        x=alt.X("mw", title="Molecular Weight"),
        y=alt.Y("logp", title="LogP (Lipophilicity)"),
        color=alt.Color("total_score", scale=alt.Scale(scheme="viridis"), title="Score"),
        tooltip=["name", "smiles", "total_score", "qed"],
    ).interactive().properties(height=400)
    st.altair_chart(chart, use_container_width=True)
