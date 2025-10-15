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

PRIMARY_COLOR = "#0b6bcb"
LIGHT_BG = "#f8fafc"

# -----------------------------
# Optional: Simple Login
# -----------------------------
USER_CREDENTIALS = {
    "jf.papel@gmail.com": {"password": "rce@2025", "name": "João Filipe Papel"},
}

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
# Header & CSS
# -----------------------------
logo_col, title_col, _ = st.columns([0.1, 0.6, 0.3])
with logo_col:
    if Path("assets/rce_logo.png").exists():
        st.image("assets/rce_logo.png", width=56)
with title_col:
    st.markdown(
        """
        <div style="padding-top:2px;">
          <h2 style="margin-bottom:0;">RCE Survey Dashboard</h2>
          <div style="color:#475569;">2015–2019 vs 2020–2024 | Clean visuals & exact figure titles</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown(
    f"""
    <style>
      .block-container {{ padding-top: 1rem; }}
      .stTabs [data-baseweb="tab-list"] button {{ font-weight: 600; }}
      .small-note {{ color:#64748b; font-size:0.9rem; }}
      .card {{
          background:{LIGHT_BG};
          border:1px solid #e2e8f0; border-radius:12px; padding:12px 16px; margin-bottom:8px;
      }}
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# Chart helpers (no 'icon' kwarg)
# -----------------------------
def bar_counts(title: str, x_labels, y15, y20):
    return (
        Bar(init_opts=opts.InitOpts(bg_color="white"))
        .add_xaxis(x_labels)
        .add_yaxis("2015–2019", [int(x) for x in y15])
        .add_yaxis("2020–2024", [int(x) for x in y20])
        .set_global_opts(
            title_opts=opts.TitleOpts(title=title),
            tooltip_opts=opts.TooltipOpts(trigger="axis"),
            legend_opts=opts.LegendOpts(pos_top="top"),  # ← no icon kwarg
            toolbox_opts=opts.ToolboxOpts(
                is_show=True,
                feature={"saveAsImage": {"title": "Save", "type": "png"}}
            ),
            xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=30)),
            yaxis_opts=opts.AxisOpts(name="Projects"),
            datazoom_opts=[opts.DataZoomOpts()],
        )
    )

def pie_share(title: str, labels, shares, donut=True):
    data = [list(z) for z in zip(labels, [float(v) for v in shares])]
    radius = ["40%", "70%"] if donut else ["0%", "70%"]
    return (
        Pie(init_opts=opts.InitOpts(bg_color="white"))
        .add("", data, radius=radius)
        .set_global_opts(
            title_opts=opts.TitleOpts(title=title, subtitle="2020–2024 (share)"),
            legend_opts=opts.LegendOpts(orient="horizontal", pos_top="top"),  # ← no icon kwarg
            toolbox_opts=opts.ToolboxOpts(is_show=True, feature={"saveAsImage": {"type": "png"}})
        )
        .set_series_opts(label_opts=opts.LabelOpts(formatter="{b}: {c}%"))
    )

def table_download(df_slice, filename: str):
    st.dataframe(df_slice, use_container_width=True)
    st.download_button(
        "⬇️ Download table (CSV)",
        df_slice.to_csv(index=False).encode("utf-8"),
        file_name=filename,
        mime="text/csv"
    )

# -----------------------------
# Figure tabs (titles + domain)
# -----------------------------
FIGS = [
    ("Figure 1 · Region", "Region", "Figure 1. Overall regional representation of the projects"),
    ("Figure 2 · SDG", "SDG", "Figure 2. SDG coverage of RCE projects (2020–2024)"),
    ("Figure 3 · PAA", "PAA", "Figure 3. Global RCE projects by GAP Priority Action Area targeted (2020–2024)"),
    ("Figure 4 · Organizations", "Organization", "Figure 4. Global RCE projects by leading organizations (2020–2024)"),
    ("Figure 5 · Themes", "Theme", "Figure 5. Global RCE projects by theme targeted (2020–2024)"),
    ("Figure 5.a · Ecosystems", "Ecosystem", "Figure 5.a Global RCE projects by theme targeted (2020–2024)"),
    ("Figure 6 · Audience", "Audience", "Figure 6. Global RCE Projects by Audience (2020–2024)"),
]

tabs = st.tabs([f[0] for f in FIGS])

for (tab, (tab_label, domain, title)) in zip(tabs, FIGS):
    with tab:
        st.markdown(f"### {title}")
        sub = df[df["Domain"] == domain].copy()

        # Optional subset filter
        chosen = st.multiselect("Filter items (optional):", sorted(sub["Item"].unique()))
        if chosen:
            sub = sub[sub["Item"].isin(chosen)]

        # Two charts: counts + share
        col1, col2 = st.columns([0.58, 0.42])

        with col1:
            bar = bar_counts(
                f"{title} — Counts",
                sub["Item"].tolist(),
                sub["Count_2015_2019"].tolist(),
                sub["Count_2020_2024"].tolist(),
            )
            st_pyecharts(bar, key=f"bar-{domain}")

        with col2:
            pie = pie_share(
                f"{title}",
                sub["Item"].tolist(),
                sub["Share_2020_2024_pct"].tolist(),
                donut=True
            )
            st_pyecharts(pie, key=f"pie-{domain}")

        st.markdown('<div class="card small-note">Tip: Use the toolbox to export any chart as PNG.</div>', unsafe_allow_html=True)

        # Table + download
        st.markdown("#### Data table")
        table_cols = [
            "Item", "Count_2015_2019", "Count_2020_2024",
            "Share_2015_2019_pct", "Share_2020_2024_pct",
            "Delta_Count", "Delta_Share_pp",
            "Rank_2020_2024_Count_in_Domain", "Rank_2020_2024_Share_in_Domain"
        ]
        table_download(sub[table_cols], f"{domain.lower()}_table.csv")

# Footer
st.markdown(
    """
    <hr/>
    <div class="small-note">Source: RCE Monitoring (compiled by Papel). Period totals: 2015–2019 = 479, 2020–2024 = 383.</div>
    """,
    unsafe_allow_html=True,
)
