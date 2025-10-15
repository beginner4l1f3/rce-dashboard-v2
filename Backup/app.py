import streamlit as st
import pandas as pd
import altair as alt
from streamlit_echarts import st_echarts
from pyecharts import options as opts
from pyecharts.charts import Pie, Bar as PBar, Line as PLine

st.set_page_config(page_title="RCE Dashboard (Lite)", page_icon="🗺️", layout="wide")

@st.cache_data
def load(path):
    df = pd.read_csv(path)
    for c in df.columns:  # normalize
        if isinstance(c, str):
            df.rename(columns={c: c.strip()}, inplace=True)
    return df

st.sidebar.title("🔧 Controls")
csv_path = st.sidebar.text_input("CSV file", "data/rce_combined_summary.csv")
df = load(csv_path)

# filters
domain = st.sidebar.selectbox("Domain", sorted(df["Domain"].unique()))
sub = df[df["Domain"] == domain].copy()
item = st.sidebar.multiselect("Item(s)", sorted(sub["Item"].unique()))
if item:
    sub = sub[sub["Item"].isin(item)]

metric = st.sidebar.radio("Metric", ["Count_2015_2019","Count_2020_2024","Share_2015_2019_pct","Share_2020_2024_pct","Delta_Count","Delta_Share_pp"], index=1)
chart = st.sidebar.radio("Chart", ["Bar","Line","Pie"], index=0)

st.title("RCE Dashboard (Lite)")
st.caption("Reads the combined CSV and lets you slice by domain/item.")

# table
st.dataframe(sub[["Item","Count_2015_2019","Count_2020_2024","Share_2015_2019_pct","Share_2020_2024_pct","Delta_Count","Delta_Share_pp","Rank_2020_2024_Count_in_Domain","Rank_2020_2024_Share_in_Domain"]], use_container_width=True)

# basic charts
if chart in ["Bar","Line"]:
    x = sub["Item"].tolist()
    y = sub[metric].tolist()
    if chart == "Bar":
        options = {
            "tooltip":{"trigger":"axis"},
            "xAxis":{"type":"category","data":x,"axisLabel":{"interval":0,"rotate":30}},
            "yAxis":{"type":"value"},
            "series":[{"data":y,"type":"bar"}],
            "grid":{"left":60,"right":20,"bottom":80,"top":20},
            "toolbox":{"show":True,"feature":{"saveAsImage":{}}}
        }
        st_echarts(options=options, height="520px")
    else:
        l = PLine().add_xaxis(x).add_yaxis(metric, y).set_global_opts(toolbox_opts=opts.ToolboxOpts(is_show=True, feature={"saveAsImage":{}}))
        st.pyecharts(l, key="line")
else:  # Pie
    pie_data = list(zip(sub["Item"], sub[metric]))
    radius = ["40%","70%"] if "Share" in metric else ["0%","70%"]
    label_fmt = "{b}: {c}%" if "Share" in metric else "{b}: {c}"
    p = Pie().add("", pie_data, radius=radius).set_series_opts(label_opts=opts.LabelOpts(formatter=label_fmt)).set_global_opts(legend_opts=opts.LegendOpts(orient="horizontal", pos_top="top"))
    st.pyecharts(p, height=560)

# downloads
st.download_button("⬇️ Download current slice (CSV)", sub.to_csv(index=False).encode("utf-8"), file_name="rce_slice.csv", mime="text/csv")
