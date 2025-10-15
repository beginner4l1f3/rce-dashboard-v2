import streamlit as st
import pandas as pd
from pathlib import Path
from streamlit_echarts import st_pyecharts
from pyecharts.charts import Pie, Bar
from pyecharts import options as opts

# -----------------------------
# Config
# -----------------------------
st.set_page_config(page_title="RCE Dashboard", page_icon="assets/rce_logo.png", layout="wide")
ENABLE_LOGIN = False  # set True to enable simple login
LIGHT_BG = "#f8fafc"
SHOW_TIP_AND_TABLE = False  # hide tip card + data table (set True to show)
SHOW_SIDEBAR = False  # hide the left Filters panel

# -----------------------------
# Optional: Simple Login
# -----------------------------
USER_CREDENTIALS = {"jf.papel@gmail.com": {"password": "rce@2025", "name": "João Filipe Papel"}}
if "logged_in" not in st.session_state:
    st.session_state.logged_in = not ENABLE_LOGIN
if "username" not in st.session_state:
    st.session_state.username = ""
if "full_name" not in st.session_state:
    st.session_state.full_name = ""
if ENABLE_LOGIN and not st.session_state.logged_in:
    st.title("Login to RCE Dashboard")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Login"):
        if u in USER_CREDENTIALS and USER_CREDENTIALS[u]["password"] == p:
            st.session_state.logged_in = True
            st.session_state.username = u
            st.session_state.full_name = USER_CREDENTIALS[u]["name"]
            st.rerun()
        else:
            st.error("Invalid username or password.")
    st.stop()

# -----------------------------
# Data
# -----------------------------
@st.cache_data
def load(path: str):
    df = pd.read_csv(path)
    df.columns = [c.strip() if isinstance(c, str) else c for c in df.columns]
    return df

DATA_PATH = "data/rce_combined_summary.csv"
if not Path(DATA_PATH).exists():
    st.error("Missing data/rce_combined_summary.csv. Place the file in the data folder.")
    st.stop()

df = load(DATA_PATH)

# -----------------------------
# FORCE LIGHT MODE (CSS only)
# -----------------------------
st.markdown(
    f"""
    <style>
      :root {{
        --rce-bg: #ffffff;
        --rce-bg-2: {LIGHT_BG};
        --rce-text: #111827;
        --rce-border: #e2e8f0;
        --rce-primary: #2563eb;
      }}
      html, body, [data-testid="stAppViewContainer"] {{
        background-color: var(--rce-bg) !important;
        color: var(--rce-text) !important;
      }}
      [data-testid="stHeader"], [data-testid="stSidebar"], [data-testid="stToolbar"] {{
        background-color: var(--rce-bg) !important;
        color: var(--rce-text) !important;
      }}
      .block-container {{ padding-top: 1.0rem; }}
      div[data-baseweb="select"] > div,
      .stTextInput>div>div>input,
      .stNumberInput input,
      .stTextArea textarea,
      .stDateInput input {{
        background-color: var(--rce-bg-2) !important;
        color: var(--rce-text) !important;
        border-color: var(--rce-border) !important;
      }}
      .stExpander, .st-expander__header {{
        background-color: var(--rce-bg-2) !important;
        color: var(--rce-text) !important;
      }}
      [data-testid="stTable"], .stDataFrame, .stDataFrame div {{
        background-color: var(--rce-bg) !important;
        color: var(--rce-text) !important;
      }}
      .stButton>button, .stDownloadButton>button {{
        background-color: var(--rce-primary) !important;
        color: white !important;
        border: 1px solid var(--rce-primary) !important;
      }}
      .small-note {{ color:#64748b; font-size:0.9rem; }}
      .card {{
        background: var(--rce-bg-2);
        border:1px solid var(--rce-border);
        border-radius:12px;
        padding:12px 16px;
        margin:12px 0;
      }}
    </style>
    """,
    unsafe_allow_html=True,
)

# Simple, safe title (no image to avoid clipping)
st.title("RCE Survey Dashboard")

# -----------------------------
# Sidebar — left filter bar (optional)
# -----------------------------
if SHOW_SIDEBAR:
    st.sidebar.title("🔍 Filters")
    with st.sidebar.expander("Search & Limit (coming soon)", expanded=True):
        st.caption("We’ll add Top-N, sort and thresholds here.")
    with st.sidebar.expander("Display Options (coming soon)", expanded=False):
        st.caption("We’ll add switches for labels, orientation, palette, etc.")
    with st.sidebar.expander("Export (coming soon)", expanded=False):
        st.caption("We’ll add multi-sheet Excel download here.")

# -----------------------------
# Chart helpers
# -----------------------------
MAX_PIE_LABELS = 6  # show outside labels only when slices <= this number

def bar_counts(x_labels, y15, y20, show15=True, show20=True):
    """Full-width bar; horizontal if many items; value labels; no slider."""
    if not show15 and not show20:
        show20 = True  # guarantee at least one series

    many = len(x_labels) >= 8
    bar = Bar(init_opts=opts.InitOpts(bg_color="white", height="560px"))
    bar.add_xaxis(x_labels)
    if show15:
        bar.add_yaxis("2015–2019", [int(x) for x in y15],
                      label_opts=opts.LabelOpts(is_show=True, position="right" if many else "top"))
    if show20:
        bar.add_yaxis("2020–2024", [int(x) for x in y20],
                      label_opts=opts.LabelOpts(is_show=True, position="right" if many else "top"))
    if many:
        bar = bar.reversal_axis()
    bar.set_global_opts(
        tooltip_opts=opts.TooltipOpts(trigger="axis", axis_pointer_type="shadow"),
        legend_opts=opts.LegendOpts(pos_top="top"),
        toolbox_opts=opts.ToolboxOpts(is_show=True, feature={"saveAsImage": {"type": "png"}}),
        xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=0 if many else 25)),
        yaxis_opts=opts.AxisOpts(name="Projects"),
    )
    return bar

def pie_share(labels, shares, donut=True, title=None):
    """Donut with smart labeling."""
    data = [list(z) for z in zip(labels, [float(v) for v in shares])]
    radius = ["40%", "70%"] if donut else ["0%", "70%"]
    show_labels = len(labels) <= MAX_PIE_LABELS
    pie = (
        Pie(init_opts=opts.InitOpts(bg_color="white", height="520px"))
        .add("", data, radius=radius)
        .set_global_opts(
            title_opts=opts.TitleOpts(title=title or ""),
            legend_opts=opts.LegendOpts(orient="vertical", pos_right="2%", pos_top="middle"),
            toolbox_opts=opts.ToolboxOpts(is_show=True, feature={"saveAsImage": {"type": "png"}}),
            tooltip_opts=opts.TooltipOpts(formatter="{b}: {c}%"),
        )
        .set_series_opts(
            label_opts=opts.LabelOpts(is_show=show_labels, position="outside", formatter="{b}: {c}%")
        )
    )
    return pie

def table_download(df_slice, filename: str):
    st.dataframe(df_slice, use_container_width=True)
    st.download_button(
        "⬇️ Download table (CSV)",
        df_slice.to_csv(index=False).encode("utf-8"),
        file_name=filename,
        mime="text/csv"
    )

# -----------------------------
# Section selector (combobox)
# -----------------------------
SECTIONS = {
    "Overall regional representation of the projects": ("Region", "Overall regional representation of the projects"),
    "SDG coverage of RCE projects": ("SDG", "SDG coverage of RCE projects"),
    "Global RCE projects by GAP Priority Action Area targeted": ("PAA", "Global RCE projects by GAP Priority Action Area targeted"),
    "Global RCE projects by leading organizations": ("Organization", "Global RCE projects by leading organizations"),
    "Global RCE projects by theme targeted": ("Theme", "Global RCE projects by theme targeted"),
    "Global RCE Projects by Audience": ("Audience", "Global RCE Projects by Audience"),
}
section_label = st.selectbox("Choose a section to display", list(SECTIONS.keys()), index=0)
selected_domain, section_heading = SECTIONS[section_label]

# -----------------------------
# Main content for selected section
# -----------------------------
# (Heading suppressed intentionally)
sub = df[df["Domain"] == selected_domain].copy()

# ---- Checkbox filter (instead of multiselect) ----
items = sorted(sub["Item"].unique())
with st.expander("Filter items (optional):", expanded=False):
    top_col, _ = st.columns([0.25, 0.75])
    with top_col:
        select_all = st.checkbox("Select all", key=f"all-{selected_domain}", value=False)

    ncols = 4 if len(items) >= 8 else 2
    cols = st.columns(ncols)
    chosen_items = []
    for i, it in enumerate(items):
        with cols[i % ncols]:
            checked = st.checkbox(it, key=f"chk-{selected_domain}-{it}", value=select_all)
            if checked:
                chosen_items.append(it)

if chosen_items:
    sub = sub[sub["Item"].isin(chosen_items)]

# ---- Period toggles (drive both bar & pies) ----
col_t1, col_t2, _ = st.columns([0.18, 0.2, 0.62])
with col_t1:
    show15 = st.checkbox("2015–2019", value=True, key=f"tgl15-{selected_domain}")
with col_t2:
    show20 = st.checkbox("2020–2024", value=True, key=f"tgl20-{selected_domain}")
if not show15 and not show20:
    st.warning("Select at least one period. Showing 2020–2024 by default.")
    show20 = True

# ---- Bar chart ----
st.markdown("##### 2015–2019 | 2020–2024")
bar = bar_counts(
    sub["Item"].tolist(),
    sub["Count_2015_2019"].tolist(),
    sub["Count_2020_2024"].tolist(),
    show15=show15,
    show20=show20,
)
st_pyecharts(bar, key=f"bar-{selected_domain}")

# ---- Pie chart(s) ----
# If both toggles are on, show two pies side-by-side; else show a single pie
if show15 and show20:
    st.markdown("##### Share (in %)")
    c1, c2 = st.columns(2)
    with c1:
        pie15 = pie_share(
            sub["Item"].tolist(),
            sub["Share_2015_2019_pct"].tolist(),
            donut=True,
            title="2015–2019"
        )
        st_pyecharts(pie15, key=f"pie15-{selected_domain}")
    with c2:
        pie20 = pie_share(
            sub["Item"].tolist(),
            sub["Share_2020_2024_pct"].tolist(),
            donut=True,
            title="2020–2024"
        )
        st_pyecharts(pie20, key=f"pie20-{selected_domain}")
elif show15:
    st.markdown("##### Share (in %) — 2015–2019")
    pie15 = pie_share(
        sub["Item"].tolist(),
        sub["Share_2015_2019_pct"].tolist(),
        donut=True,
        title="2015–2019"
    )
    st_pyecharts(pie15, key=f"pie15-{selected_domain}")
else:
    st.markdown("##### Share (in %) — 2020–2024")
    pie20 = pie_share(
        sub["Item"].tolist(),
        sub["Share_2020_2024_pct"].tolist(),
        donut=True,
        title="2020–2024"
    )
    st_pyecharts(pie20, key=f"pie20-{selected_domain}")

# Optional tip/table
if SHOW_TIP_AND_TABLE:
    st.markdown(
        '<div class="card small-note">Tip: export any chart via the toolbox on each chart.</div>',
        unsafe_allow_html=True,
    )
    st.markdown("#### Data table")
    table_cols = [
        "Item", "Count_2015_2019", "Count_2020_2024",
        "Share_2015_2019_pct", "Share_2020_2024_pct",
        "Delta_Count", "Delta_Share_pp",
        "Rank_2020_2024_Count_in_Domain", "Rank_2020_2024_Share_in_Domain"
    ]
    table_download(sub[table_cols], f"{selected_domain.lower()}_table.csv")
