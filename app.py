import streamlit as st
import pandas as pd
from pathlib import Path
from streamlit_echarts import st_pyecharts
from pyecharts.charts import Pie, Bar
from pyecharts import options as opts
import re

# -----------------------------
# Config
# -----------------------------
st.set_page_config(page_title="RCE Dashboard", page_icon="assets/rce_logo.png", layout="wide")
LIGHT_BG = "#f8fafc"
SHOW_TIP_AND_TABLE = False  # set True if you want the helper card + data table

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

# -----------------------------
# Title
# -----------------------------
st.title("RCE Survey Dashboard")

# -----------------------------
# SDG color mapping + helpers
# -----------------------------
SDG_COLOR_HEX = {
    1:  "#E5243B", 2:  "#DDA63A", 3:  "#4C9F38", 4:  "#C5192D", 5:  "#FF3A21",
    6:  "#26BDE2", 7:  "#FCC30B", 8:  "#A21942", 9:  "#FD6925", 10: "#DD1367",
    11: "#FD9D24", 12: "#BF8B2E", 13: "#3F7E44", 14: "#0A97D9", 15: "#56C02B",
    16: "#00689D", 17: "#19486A",
}
sdg_num_re = re.compile(r"^\s*SDG\s*(\d{1,2})\s*$", re.IGNORECASE)

def sdg_num(label: str) -> int:
    m = sdg_num_re.match(str(label))
    return int(m.group(1)) if m else 999  # non-SDGs sink to the end (just in case)

def sdg_colors_for(labels):
    colors = []
    for lab in labels:
        n = sdg_num(lab)
        colors.append(SDG_COLOR_HEX.get(n, "#cccccc"))
    return colors

# -----------------------------
# Chart helpers
# -----------------------------
def bar_counts(x_labels, y15, y20, show15=True, show20=True, height_px="560px"):
    """
    Full-width bar; horizontal if many items; value labels.
    height_px can be a string like '740px' to give more space for long lists.
    """
    if not show15 and not show20:
        show20 = True  # guarantee at least one series

    many = len(x_labels) >= 8
    bar = Bar(init_opts=opts.InitOpts(bg_color="white", height=height_px))
    bar.add_xaxis(x_labels)

    if show15:
        bar.add_yaxis("2015–2019", [int(x) for x in y15],
                      label_opts=opts.LabelOpts(is_show=True, position="right" if many else "top"))
    if show20:
        bar.add_yaxis("2020–2024", [int(x) for x in y20],
                      label_opts=opts.LabelOpts(is_show=True, position="right" if many else "top"))

    if many:
        bar = bar.reversal_axis()  # category labels move to Y axis (left)

    bar.set_global_opts(
        tooltip_opts=opts.TooltipOpts(trigger="axis", axis_pointer_type="shadow"),
        legend_opts=opts.LegendOpts(pos_top="top"),
        toolbox_opts=opts.ToolboxOpts(is_show=True, feature={"saveAsImage": {"type": "png"}}),

        # Force all labels to show on the category axis (works when reversed too)
        xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=0, interval=0)),
        yaxis_opts=opts.AxisOpts(name="Projects", axislabel_opts=opts.LabelOpts(interval=0)),
    )
    return bar

def pie_share(labels, shares, donut=True, title=None, colors=None):
    """Donut: legends hidden, labels always outside with percentages."""
    data = [list(z) for z in zip(labels, [float(v) for v in shares])]
    radius = ["40%", "70%"] if donut else ["0%", "70%"]

    pie = (
        Pie(init_opts=opts.InitOpts(bg_color="white", height="520px"))
        .add("", data, radius=radius)
        .set_global_opts(
            title_opts=opts.TitleOpts(title=title or ""),
            legend_opts=opts.LegendOpts(is_show=False),  # hide legend
            toolbox_opts=opts.ToolboxOpts(is_show=True, feature={"saveAsImage": {"type": "png"}}),
            tooltip_opts=opts.TooltipOpts(formatter="{b}: {c}%"),
        )
        .set_series_opts(
            label_opts=opts.LabelOpts(is_show=True, position="outside", formatter="{b}: {c}%")
        )
    )
    if colors:
        pie.set_colors(colors)  # apply SDG colors in label order
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
selected_domain, _ = SECTIONS[section_label]

# -----------------------------
# Main content for selected section
# -----------------------------
sub = df[df["Domain"] == selected_domain].copy()

# ---- Filter (checkboxes) with SDG ordering when relevant
raw_items = sub["Item"].unique().tolist()
if selected_domain == "SDG":
    items = sorted(raw_items, key=sdg_num)       # SDG 1 -> SDG 17
else:
    items = sorted(raw_items)                    # alphabetical for others

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

# ---- Period toggles (drive both bar & pies)
col_t1, col_t2, _ = st.columns([0.18, 0.2, 0.62])
with col_t1:
    show15 = st.checkbox("2015–2019", value=True, key=f"tgl15-{selected_domain}")
with col_t2:
    show20 = st.checkbox("2020–2024", value=True, key=f"tgl20-{selected_domain}")
if not show15 and not show20:
    st.warning("Select at least one period. Showing 2020–2024 by default.")
    show20 = True

# ---- Dynamic height for long SDG lists to show ALL labels
rows = len(sub)
if selected_domain == "SDG":
    # ~38 px per row + top/bottom padding; min 560px
    dynamic_height = f"{max(560, 38 * rows + 180)}px"
else:
    dynamic_height = "560px"

# ---- Bar chart
st.markdown("##### 2015–2019 | 2020–2024")
bar = bar_counts(
    sub["Item"].tolist(),
    sub["Count_2015_2019"].tolist(),
    sub["Count_2020_2024"].tolist(),
    show15=show15,
    show20=show20,
    height_px=dynamic_height,
)
st_pyecharts(bar, key=f"bar-{selected_domain}")

# ---- Pie chart(s) with SDG colors if applicable
def maybe_sdg_colors(labels):
    return sdg_colors_for(labels) if selected_domain == "SDG" else None

labels = sub["Item"].tolist()
colors_for_pies = maybe_sdg_colors(labels)

if show15 and show20:
    st.markdown("##### Share (in %)")
    c1, c2 = st.columns(2)
    with c1:
        pie15 = pie_share(
            labels,
            sub["Share_2015_2019_pct"].tolist(),
            donut=True,
            title="2015–2019",
            colors=colors_for_pies
        )
        st_pyecharts(pie15, key=f"pie15-{selected_domain}")
    with c2:
        pie20 = pie_share(
            labels,
            sub["Share_2020_2024_pct"].tolist(),
            donut=True,
            title="2020–2024",
            colors=colors_for_pies
        )
        st_pyecharts(pie20, key=f"pie20-{selected_domain}")
elif show15:
    st.markdown("##### Share (in %) — 2015–2019")
    pie15 = pie_share(
        labels,
        sub["Share_2015_2019_pct"].tolist(),
        donut=True,
        title="2015–2019",
        colors=colors_for_pies
    )
    st_pyecharts(pie15, key=f"pie15-{selected_domain}")
else:
    st.markdown("##### Share (in %) — 2020–2024")
    pie20 = pie_share(
        labels,
        sub["Share_2020_2024_pct"].tolist(),
        donut=True,
        title="2020–2024",
        colors=colors_for_pies
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
