import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap
from streamlit_folium import folium_static
from datetime import datetime, timedelta, timezone
import plotly.express as px
import matplotlib.pyplot as plt
import glob

st.set_page_config(page_title="Earthquake Dashboard", layout="wide")

st.title("🌍 Real-Time Earthquake Dashboard")

# Load CSVs
def load_data():
    csv_files = glob.glob("output/earthquake_stream/part-*.csv")
    columns = [
        "id", "place", "magnitude", "magType", "time", "time_str", 
        "longitude", "latitude", "depth", "tsunami", "sig", 
        "type", "status", "gap", "rms", "event_time"
    ]
    dataframes = []

    for file in csv_files:
        try:
            df = pd.read_csv(file, names=columns, header=None)
            df = df.dropna(subset=["latitude", "longitude", "magnitude"])
            df["time_str"] = pd.to_datetime(df["time_str"], errors='coerce', utc=True)

            now = datetime.now(timezone.utc)
            df = df[df["time_str"] > now - timedelta(days=1)]
            dataframes.append(df)
        except Exception as e:
            st.warning(f"Skipping {file}: {e}")

    return pd.concat(dataframes, ignore_index=True) if dataframes else pd.DataFrame()

# Initial load
df = load_data()

# Refresh button
if st.button("🔄 Refresh Data"):
    df = load_data()
    st.success(f"Reloaded {len(df)} records.")

if df.empty:
    st.warning("No data found.")
    st.stop()

# Show overview
st.markdown(f"**Total Earthquakes in the Last 24 Hours:** {len(df)}")
st.dataframe(df.head(10), use_container_width=True)

# Tabs for better organization
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🗺️ Heatmap", 
    "📊 Magnitude Range", 
    "🥧 Type Distribution", 
    "📈 Timeline", 
    "📍 Top Locations"
])

with tab1:
    mean_lat = df["latitude"].mean()
    mean_lon = df["longitude"].mean()
    m = folium.Map(location=[mean_lat, mean_lon], zoom_start=2, tiles="CartoDB positron")
    heat_data = df[["latitude", "longitude", "magnitude"]].values.tolist()
    HeatMap(heat_data, radius=10, blur=15).add_to(m)
    st.subheader("🌋 Earthquake Heatmap (by Magnitude)")
    folium_static(m, width=1000, height=600)

with tab2:
    st.subheader("📊 Earthquakes by Magnitude Range")
    bins = [0, 1, 2, 3, 4, 5, 6, 10]
    labels = ['0–1', '1–2', '2–3', '3–4', '4–5', '5–6', '6+']
    df['mag_range'] = pd.cut(df['magnitude'], bins=bins, labels=labels, include_lowest=True)
    mag_counts = df['mag_range'].value_counts().sort_index()
    fig_mag = px.bar(
        x=mag_counts.index, 
        y=mag_counts.values,
        labels={'x': 'Magnitude Range', 'y': 'Earthquake Count'},
        color=mag_counts.values,
        color_continuous_scale='Viridis'
    )
    st.plotly_chart(fig_mag, use_container_width=True)

with tab3:
    st.subheader("🥧 Earthquake Type Distribution")
    type_counts = df['type'].value_counts()
    fig_type = px.pie(
        names=type_counts.index, 
        values=type_counts.values, 
        title='Distribution by Event Type',
        hole=0.3
    )
    st.plotly_chart(fig_type, use_container_width=True)

with tab4:
    st.subheader("📈 Earthquakes Over Time (Hourly)")
    df['hour'] = df['time_str'].dt.floor('H')
    hour_counts = df['hour'].value_counts().sort_index()
    fig_time = px.line(
        x=hour_counts.index, 
        y=hour_counts.values, 
        labels={'x': 'Time (UTC)', 'y': 'Earthquake Count'},
        markers=True
    )
    st.plotly_chart(fig_time, use_container_width=True)

with tab5:
    st.subheader("📍 Top Locations by Event Count")
    top_places = df['place'].value_counts().head(10)
    st.table(top_places.reset_index().rename(columns={'index': 'Location', 'place': 'Count'}))
