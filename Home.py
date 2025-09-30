import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
from typing import Dict
from PIL import Image

st.set_page_config(page_title="Steam Market Analyzer", layout="wide")

# Collecting the important paths.
APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "data" / "Main page"
TEXTS_AND_PICTURE_DIR = DATA_DIR / "texts and pictures"
EVENTS_CSV = DATA_DIR / "events.csv"

# Data loaders to load given data from the given paths.
@st.cache_data
def load_histories():
    """
    Loads all *_history.csv files and returns them as dataframes.

    Args:
        ---
    Returns:
        dfs: Dataframes with the expected colums: timestamp, price_mean, price_median, volume_sum.
    """
    dfs = {}
    for fp in DATA_DIR.glob("*_history.csv"):
        try:
            df = pd.read_csv(fp, parse_dates=["timestamp"])
            name = fp.stem.replace("_history", "").replace("_", " ")
            dfs[name] = df
        except Exception as e:
            st.write(f"Error loading: {fp}: {e}")
    return dfs

@st.cache_data
def load_events(csv_path: Path):
    """
    Loads the events.csv file and returns two dataframes.

    Args:
        csv_path: The path of the csv file
    Returns:
        ev_lines: Dataframe for the single day events.
        ev_spans Dataframe for the timeframe events.
    """
    if not csv_path.exists():
        return pd.DataFrame(), pd.DataFrame()

    # Reads events with a protection for different colum seperaters.
    try:
        df = pd.read_csv(csv_path, dtype=str, sep=None, engine="python", encoding="utf-8")
    except Exception:
        try:
            df = pd.read_csv(csv_path, dtype=str, sep=";", encoding="utf-8")
        except Exception:
            df = pd.read_csv(csv_path, dtype=str, sep=",", encoding="utf-8")

    df = df.fillna("")
    df.columns = [c.strip().lower() for c in df.columns]

    # Add possible missing colums.
    for col in ["type", "date", "start", "end", "label", "category"]:
        if col not in df.columns:
            df[col] = ""

    # Save events which only include one day.
    ev_lines = df[df["type"].str.lower().eq("line")].copy()
    ev_lines["date"] = pd.to_datetime(ev_lines["date"], errors="coerce")
    ev_lines = ev_lines.dropna(subset=["date"])

    # Save events which invole a timeframe.
    ev_spans = df[df["type"].str.lower().eq("span")].copy()
    ev_spans["start"] = pd.to_datetime(ev_spans["start"], errors="coerce")
    ev_spans["end"]   = pd.to_datetime(ev_spans["end"],   errors="coerce")
    ev_spans = ev_spans.dropna(subset=["start", "end"])

    # Clean up given text.
    for d in (ev_lines, ev_spans):
        d["label"] = d["label"].astype(str).str.strip()
        d["category"] = d["category"].astype(str).str.strip()

    return ev_lines, ev_spans

# Different colors for different types of events.
CATEGORY_COLORS: Dict[str, str] = {
    "Major": "red",
    "Holiday": "green",
    "Promotion": "blue",
    "Politics": "orange",
    "Global": "purple",
}
DEFAULT_COLOR = "gray"

def add_events_to_figure(fig, ev_lines: pd.DataFrame, ev_spans: pd.DataFrame, selected_categories, show_labels=True, label_angle=-45):
    """
    Draws the events into the graph.

    Args:
        fig: Graph with the given data, but without the events added.
        ev_lines: Data for the line (one day) events.
        ev_spans: Data dor the timeframe events.
        selected_categories: Gives the categories that are supposed to be shown.
        show_labels: Are the labels for the events supposed to be shown.
    Returns:
        ---
    """
    # if no categories selected -> show nothing
    if not selected_categories:
        return
    
    # Drawing line (only one day) events into the graph.
    for _, row in ev_lines.iterrows():
        if selected_categories and row["category"] not in selected_categories:
            continue
        color = CATEGORY_COLORS.get(row["category"], DEFAULT_COLOR)
        d = row["date"]
        if pd.isna(d):
            continue
        d = pd.to_datetime(d).to_pydatetime()
        
        fig.add_shape(
            type="line",
            x0=d, x1=d,
            y0=0, y1=1,
            xref="x", yref="paper",
            line=dict(color=color, width=2, dash="dash"),
            layer="above"
        )

        # Give a lable to the drawn line
        if show_labels and row.get("label"):
            fig.add_annotation(
                x=d, y=1.02,
                xref="x", yref="paper",
                text=str(row["label"]),
                showarrow=False,
                font=dict(size=14, color=color),
                align="center",
                textangle=label_angle
            )

    # Drawing events wich involve a timeframe into the graph.
    for _, row in ev_spans.iterrows():
        if selected_categories and row["category"] not in selected_categories:
            continue
        color = CATEGORY_COLORS.get(row["category"], DEFAULT_COLOR)
        s, e = row["start"], row["end"]
        if pd.isna(s) or pd.isna(e):
            continue
        s = pd.to_datetime(s).to_pydatetime()
        e = pd.to_datetime(e).to_pydatetime()
        if e < s:
            s, e = e, s  # safety for mixed up start and end of the timeframe

        fig.add_shape(
            type="rect",
            x0=s, x1=e,
            y0=0, y1=1,
            xref="x", yref="paper",
            fillcolor=color, opacity=0.12,
            line=dict(width=0),
            layer="below"
        )

        # Give a lable to the drawn rectangle
        if show_labels and row.get("label"):
            fig.add_annotation(
                x=s, y=1.02,
                xref="x", yref="paper",
                text=str(row["label"]),
                showarrow=False,
                font=dict(size=14, color=color),
                align="left",
                textangle=label_angle
            )
            

# Load the data.
ev_lines, ev_spans = load_events(EVENTS_CSV)
dfs = load_histories()
special_item = "Average (selected items)"
items = [special_item] + sorted(dfs.keys())

ev_lines_filtered = ev_lines.copy()
ev_spans_filtered = ev_spans.copy()


st.title("Homepage For Analyzing Virtual Item Markets")

racoon = Image.open(TEXTS_AND_PICTURE_DIR / "images.png")


with open(TEXTS_AND_PICTURE_DIR / "text1.md", "r", encoding="utf-8") as f:
    text1 = f.read()
with open(TEXTS_AND_PICTURE_DIR / "text2.md", "r", encoding="utf-8") as f:
    text2 = f.read()
with open(TEXTS_AND_PICTURE_DIR / "text3.md", "r", encoding="utf-8") as f:
    text3 = f.read()
with open(TEXTS_AND_PICTURE_DIR / "text4.md", "r", encoding="utf-8") as f:
    text4 = f.read()


    
with st.expander("Context / Introduction:", expanded = True):
    st.write(text1)
with st.expander("Research Topic:"):
    st.write(text2)
    st.image(racoon, caption="RACOON!!!")
with st.expander("A Short Introduction into the games:"):
    st.write(text3)
with st.expander("Short Overview"):
    st.write(text4)

all_categories = sorted(set(list(ev_lines["category"].unique()) + list(ev_spans["category"].unique())))
preferred_defaults = ["Major", "Holiday"]
default_events = [c for c in preferred_defaults if c in all_categories]
# Given default settings.
preferred_items =  ["Average (selected items)", "AK-47  Bloodsport (Field-Tested)", "AK-47  Redline (Field-Tested)", "AK-47  Vulcan (Field-Tested)", "Galil AR  Chatterbox (Field-Tested)", "M4A1-S  Golden Coil (Field-Tested)", "M4A1-S  Printstream (Field-Tested)", "M4A4  Asiimov (Field-Tested)"]
default_items = [c for c in preferred_items if c in items]
default_range = []
default_rolling = 14
default_xaxes = "Months"
years_default = 3


if "items" not in st.session_state:
    st.session_state["items"] = default_items
if "date_range" not in st.session_state:
    st.session_state["date_range"] = default_range
if "rolling" not in st.session_state:
    st.session_state["rolling"] = default_rolling
if "xaxes" not in st.session_state:
    st.session_state["xaxes"] = default_xaxes
if "events" not in st.session_state:
    st.session_state["events"] = default_events


# Build a reset button.
def _reset_filters():
    st.session_state["items"] = default_items
    st.session_state["date_range"] = default_range
    st.session_state["rolling"] = default_rolling
    st.session_state["xaxes"] = default_xaxes
    st.session_state["events"] = default_events


# Build a UI


sel_cats = st.multiselect("Event-Categories", all_categories, key="events")
# Build a filtering framework.
col1, col2, col3 = st.columns([2, 2, 1])
with col1:
    sel_items = st.multiselect("Select Items", items, key="items")
with col2:
    date_range = st.date_input("Date-Range", key="date_range")
with col3:
    rolling_days = st.slider("Rolling (Days, 0=off)", 0, 60, key="rolling")

col1, col2, col3 = st.columns([0.3, 1, 2])
with col1:
    st.button("🔄 Reset Filter", on_click=_reset_filters)
with col2:
    st.write("#### ‼️If no graph is loaded, please use the reset Button‼️")   
 
# Build a framework to change the x-axes notation.
x_label_format = st.radio(
    "X-Axes Description",
    ["Years", "Months", "Weeks", "Days"],
    key="xaxes",
    horizontal=True
)
fmt_map = {
    "Years": "%Y",
    "Months": "%b %Y",
    "Weeks": "%G-W%V",
    "Days": "%d.%m.%Y"
}

# Prepare the plot data.
frames = []
for item in sel_items:
    if item == special_item:
        continue
    df_item = dfs[item].copy()
    # Reduce the data given by a timeframe (if filtered).
    if date_range and len(date_range) == 2:
        start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
        df_item = df_item[(df_item["timestamp"] >= start) & (df_item["timestamp"] <= end)]
        
        # Filter line events
        ev_lines_filtered = ev_lines_filtered[
            (ev_lines_filtered["date"] >= start) & (ev_lines_filtered["date"] <= end)
        ]

        # Filter span events
        ev_spans_filtered = ev_spans_filtered[
            (ev_spans_filtered["end"] >= start) & (ev_spans_filtered["start"] <= end)
        ]
    
    # Reduce the colums to only needed ones.
    df_item = df_item[["timestamp", "price_median"]].rename(columns={"price_median": "price"})
    df_item["item"] = item
    frames.append(df_item)

st.write("#### Event Legend")
legend_cols = st.columns(len(sel_cats) if sel_cats else 1)

for i, cat in enumerate(sel_cats):
    color = CATEGORY_COLORS.get(cat, DEFAULT_COLOR)
    with legend_cols[i]:
        st.markdown(
            f"<div style='display:flex;align-items:center;'>"
            f"<div style='width:20px;height:10px;background:{color};margin-right:8px;'></div>"
            f"{cat}"
            f"</div>",
            unsafe_allow_html=True
        )

# Build the graph. 
if frames:
    plot_df = pd.concat(frames, ignore_index=True).sort_values(["item", "timestamp"])

    # Rolling (optional)
    if st.session_state["rolling"] > 0:
        plot_df["price"] = (
            plot_df.groupby("item", group_keys=False)["price"]
                   .apply(lambda s: s.rolling(st.session_state["rolling"], min_periods=1).median())
        )

    fig = px.line(
        plot_df,
        x="timestamp",
        y="price",
        color="item",
        labels={"timestamp": "Date", "price": "Price (Median)"},
    )
    
    if (special_item in sel_items) and (not plot_df.empty):
        avg_df = plot_df.groupby("timestamp", as_index=False)["price"].mean()
        
        
        fig.add_traces(px.area(
            avg_df,
            x="timestamp",
            y="price"
        ).update_traces(
            name=f"{special_item} (area)",
            line=dict(width=0),
            fill="tonexty",
            fillcolor="rgba(128,128,128,0.15)",  # leichtes Grau
            showlegend=True
        ).data)    

    fig.update_layout(height=600, margin=dict(l=20, r=20, t=40, b=20),
                      dragmode="zoom",
                      xaxis=dict(fixedrange=False),
                      yaxis=dict(fixedrange=False))
    fig.update_xaxes(
        rangeslider_visible=True,
        tickformat=fmt_map[x_label_format]
    )

    # Default view: last N years when no explicit date_range is set
    if not date_range or len(date_range) != 2:
        if not plot_df.empty:
            max_ts = pd.to_datetime(plot_df["timestamp"].max())
            min_ts = pd.to_datetime(plot_df["timestamp"].min())
            start  = max_ts - pd.DateOffset(years=years_default)
            start = max(start, min_ts)
            # clamp to data range
            fig.update_xaxes(range=[start, max_ts], autorange=False)
        
    add_events_to_figure(fig, ev_lines_filtered, ev_spans_filtered, sel_cats)
    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "scrollZoom": True,
            "doubleClick": "reset",
            "displaylogo": False
        }
    )

else:
    st.info("Please select at least one item.")

