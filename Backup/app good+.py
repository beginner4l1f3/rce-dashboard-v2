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
      .small-note {{ color:#64748b; font-size:0.9rem; }}
      .card {{
          background:{LIGHT_BG};
          border:1px solid #e2e8f0; border-radius:12px; padding:12px 16px; margin:12px 0;
      }}
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# Sidebar — left filter bar (scaffold)
# -----------------------------
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

def bar_counts(x_labels, y15, y20):
    """Full-width bar; horizontal if many items; value labels; no slider."""
    many = len(x_labels) >= 8
    bar = Bar(init_opts=opts.InitOpts(bg_color="white", height="560px"))
    bar.add_xaxis(x_labels)
    bar.add_yaxis("2015–2019", [int(x) for x in y15],
                  label_opts=opts.LabelOpts(is_show=True, position="right" if many else "top"))
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

def pie_share(labels, shares, donut=True):
    """
    Donut with smart labeling:
    - if few categories (<= MAX_PIE_LABELS): show outside labels
    - else: hide labels; rely on legend + tooltip
    """
    data = [list(z) for z in zip(labels, [float(v) for v in shares])]
    radius = ["40%", "70%"] if donut else ["0%", "70%"]
    show_labels = len(labels) <= MAX_PIE_LABELS

    pie = (
        Pie(init_opts=opts.InitOpts(bg_color="white", height="520px"))
        .add("", data, radius=radius)
        .set_global_opts(
            legend_opts=opts.LegendOpts(orient="vertical", pos_right="2%", pos_top="middle"),
            toolbox_opts=opts.ToolboxOpts(is_show=True, feature={"saveAsImage": {"type": "png"}}),
            tooltip_opts=opts.TooltipOpts(formatter="{b}: {c}%"),
        )
        .set_series_opts(
            label_opts=opts.LabelOpts(
                is_show=show_labels,
                position="outside",
                formatter="{b}: {c}%"
            )
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
    # label shown to user -> (domain key in CSV, heading to display)
    "Overall regional representation of the projects": ("Region", "Overall regional representation of the projects"),
    "SDG coverage of RCE projects": ("SDG", "SDG coverage of RCE projects"),
    "Global RCE projects by GAP Priority Action Area targeted": ("PAA", "Global RCE projects by GAP Priority Action Area targeted"),
    "Global RCE projects by leading organizations": ("Organization", "Global RCE projects by leading organizations"),
    "Global RCE projects by theme targeted": ("Theme", "Global RCE projects by theme targeted"),
    "Global RCE Projects by Audience (2020–2024)": ("Audience", "Global RCE Projects by Audience (2020–2024)"),
}
section_label = st.selectbox(
    "Choose a section to display",
    list(SECTIONS.keys()),
    index=0
)
selected_domain, section_heading = SECTIONS[section_label]

# -----------------------------
# Main content for selected section
# -----------------------------
st.markdown(f"### {section_heading}")

sub = df[df["Domain"] == selected_domain].copy()

# Optional subset filter within the selected section
chosen = st.multiselect("Filter items (optional):", sorted(sub["Item"].unique()), key=f"filter-{selected_domain}")
if chosen:
    sub = sub[sub["Item"].isin(chosen)]

# Charts (same style as before)
st.markdown("##### Counts (2015–2019 vs 2020–2024)")
bar = bar_counts(
    sub["Item"].tolist(),
    sub["Count_2015_2019"].tolist(),
    sub["Count_2020_2024"].tolist(),
)
st_pyecharts(bar, key=f"bar-{selected_domain}")

st.markdown("##### 2020–2024 Share (in %)")
pie = pie_share(
    sub["Item"].tolist(),
    sub["Share_2020_2024_pct"].tolist(),
    donut=True
)
st_pyecharts(pie, key=f"pie-{selected_domain}")

st.markdown('<div class="card small-note">Tip: export any chart via the toolbox on each chart. The left filter bar is ready for your options.</div>', unsafe_allow_html=True)

# Table + download
st.markdown("#### Data table")
table_cols = [
    "Item", "Count_2015_2019", "Count_2020_2024",
    "Share_2015_2019_pct", "Share_2020_2024_pct",
    "Delta_Count", "Delta_Share_pp",
    "Rank_2020_2024_Count_in_Domain", "Rank_2020_2024_Share_in_Domain"
]
table_download(sub[table_cols], f"{selected_domain.lower()}_table.csv")

# Footer
st.markdown(
    """
    <hr/>
    <div class="small-note">Source: RCE Monitoring (compiled by Papel). Totals: 2015–2019 = 479, 2020–2024 = 383.</div>
    """,
    unsafe_allow_html=True,
)
