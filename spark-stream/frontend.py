import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap
from streamlit_folium import folium_static
from datetime import datetime, timedelta, timezone
import glob
import reverse_geocoder as rg
import altair as alt

import logging

logging.basicConfig(level=logging.INFO)
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')


st.set_page_config(page_title="Disaster Analytics Dashboard", layout="wide")
st.title("🌍 Real-Time Disaster Dashboard")


# --- Extract region from "place"
def extract_region(place):
    if pd.isna(place) or not isinstance(place, str):
        return "Unknown"
    if "," in place:
        return place.split(",")[-1].strip()
    return "Unknown"


# --- Reverse geocoding to get country from lat/lon
def get_country(lat, lon):
    try:
        result = rg.search((lat, lon))[0]
        return result['cc']
    except:
        return "Unknown"


# --- Load Earthquake Data
def load_earthquake_data():
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
            df["magnitude"] = pd.to_numeric(df["magnitude"], errors='coerce')
            df = df.dropna(subset=["magnitude", "latitude", "longitude"])
            df["time_str"] = pd.to_datetime(df["time_str"], errors='coerce', utc=True)
            now = datetime.now(timezone.utc)
            df = df[df["time_str"] > now - timedelta(days=1)]

            # Extract region safely
            if "place" in df.columns:
                df["region"] = df["place"].fillna("").apply(extract_region)
            else:
                df["region"] = "Unknown"

            dataframes.append(df)

        except Exception as e:
            logging.warning(f"Skipping earthquake file {file}: {e}")

    return pd.concat(dataframes, ignore_index=True) if dataframes else pd.DataFrame()


# --- Load Wildfire Data
def load_wildfire_data():
    csv_files = glob.glob("output/wildfire_stream/part-*.csv")
    columns = [
        "latitude", "longitude", "brightness", "scan", "track", "acq_date",
        "acq_time", "satellite", "confidence", "version", "bright_t31",
        "frp", "daynight", "location", "acq_datetime"
    ]
    dataframes = []
    
    for file in csv_files:
        try:
            df = pd.read_csv(file, names=columns, header=None)
            df = df.dropna(subset=["latitude", "longitude"])
            df["acq_date"] = pd.to_datetime(df["acq_date"], errors="coerce", utc=True)
            now = datetime.now(timezone.utc)
            df = df[df["acq_date"] > now - timedelta(days=1)]
            
            if not df.empty:
                coords = list(zip(df["latitude"], df["longitude"]))
                results = rg.search(coords)
                df["country_code"] = [res["cc"] for res in results]
                dataframes.append(df)
        except Exception as e:
            logging.warning(f"Skipping wildfire file {file}: {e}")
    
    return pd.concat(dataframes, ignore_index=True) if dataframes else pd.DataFrame()


# --- Load data
eq_df = load_earthquake_data()
fire_df = load_wildfire_data()

# --- Tabs
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "🌋 Earthquake Heatmap",
    "🔥 Wildfire Heatmap",
    "📊 EQ Magnitudes",
    "📈 EQ Timeline",
    "📍 EQ Locations & Regions",
    "🔥 Fire Country Counts",
    "📏 EQ Depth Distribution",
    "🌐 Magnitude vs. Depth"
])

# --- 🌋 Earthquake Heatmap ---
with tab1:
    st.subheader("🌋 Earthquake Heatmap (Last 24h)")
    if eq_df.empty:
        st.warning("No earthquake data available.")
    else:
        mean_lat = eq_df["latitude"].mean()
        mean_lon = eq_df["longitude"].mean()
        m = folium.Map(location=[mean_lat, mean_lon], zoom_start=2, tiles="CartoDB positron")
        heat_data = eq_df[["latitude", "longitude", "magnitude"]].values.tolist()
        HeatMap(heat_data, radius=10, blur=15).add_to(m)
        folium_static(m, width=None, height=600)

# --- 🔥 Wildfire Heatmap ---
with tab2:
    st.subheader("🔥 Wildfire Heatmap (Last 24h)")
    if fire_df.empty:
        st.warning("No wildfire data available.")
    else:
        mean_lat = fire_df["latitude"].mean()
        mean_lon = fire_df["longitude"].mean()
        m = folium.Map(location=[mean_lat, mean_lon], zoom_start=2, tiles="CartoDB positron")
        heat_data = fire_df[["latitude", "longitude"]].values.tolist()
        HeatMap(heat_data, radius=8, blur=12).add_to(m)
        folium_static(m, width=None, height=600)

# --- 📊 EQ Magnitude Distribution ---
with tab3:
    st.subheader("📊 Earthquake Magnitude Distribution")
    if eq_df.empty:
        st.warning("No earthquake data.")
    else:
        mag_bins = pd.cut(eq_df["magnitude"], bins=[-1, 1, 2, 3, 4, 5])
        bin_counts = mag_bins.value_counts().sort_index()
        bin_counts.index = bin_counts.index.astype(str)
        df = bin_counts.reset_index()
        df.columns = ["Magnitude Range", "Count"]

        chart = alt.Chart(df).mark_bar(color="#FF6B35").encode(
            x=alt.X("Magnitude Range:N", title="Magnitude Range"),
            y=alt.Y("Count:Q", title="Count")
        ).properties(width=700, height=400)

        st.altair_chart(chart, use_container_width=True)


# --- 📈 EQ Timeline ---
with tab4:
    st.subheader("📈 Earthquake Frequency Over Time")
    if eq_df.empty:
        st.warning("No earthquake data.")
    else:
        eq_df['minute'] = eq_df['time_str'].dt.floor('min')
        counts = eq_df.groupby("minute").size().reset_index(name="count")

        chart = alt.Chart(counts).mark_line(color="#3D5AFE").encode(
            x=alt.X("minute:T", title="Time"),
            y=alt.Y("count:Q", title="Earthquakes")
        ).properties(width=800, height=400)

        st.altair_chart(chart, use_container_width=True)


# --- 📍 Top EQ Locations + Regions ---
with tab5:
        st.subheader("🌍 Top Earthquake Regions (Last 24h)")
        region_counts = eq_df["region"].value_counts().reset_index()
        region_counts.columns = ["Region", "Count"]

        st.dataframe(region_counts.head(10))

        chart = alt.Chart(region_counts.head(10)).mark_bar(color="#00C49F").encode(
            x=alt.X("Region:N", sort="-y"),
            y=alt.Y("Count:Q"),
            tooltip=["Region", "Count"]
        ).properties(width=800)

        st.altair_chart(chart, use_container_width=True)


# --- 🔥 Fire Country Counts ---
with tab6:
    st.subheader("🔥 Top Wildfire Countries")
    if fire_df.empty:
        st.warning("No wildfire data.")
    else:
        country_counts = fire_df["country_code"].value_counts().reset_index()
        country_counts.columns = ["Country", "Count"]

        st.dataframe(country_counts.head(10))

        chart = alt.Chart(country_counts.head(10)).mark_bar(color="#EF476F").encode(
            x=alt.X("Country:N", sort="-y"),
            y=alt.Y("Count:Q"),
            tooltip=["Country", "Count"]
        ).properties(width=800)

        st.altair_chart(chart, use_container_width=True)


# --- 📏 EQ Depth Distribution ---
with tab7:
    st.subheader("📏 Earthquake Depth Distribution")
    if eq_df.empty:
        st.warning("No earthquake data.")
    else:
        chart = alt.Chart(eq_df).mark_bar(color="#FFC300").encode(
            alt.X("depth", bin=alt.Bin(maxbins=30), title="Depth (km)"),
            y='count()',
        ).properties(width=800, height=400)

        st.altair_chart(chart, use_container_width=True)


# --- 🌐 Magnitude vs. Depth ---
with tab8:
    st.subheader("🌐 Magnitude vs. Depth")
    if eq_df.empty:
        st.warning("No earthquake data.")
    else:
        chart = alt.Chart(eq_df).mark_circle(
            size=60,
            color="#2E86DE",  # Vibrant blue for visibility
            opacity=0.6
        ).encode(
            x=alt.X("depth", title="Depth (km)"),
            y=alt.Y("magnitude", title="Magnitude"),
            tooltip=["depth", "magnitude", "region", "time_str"]
        ).properties(
            width=800,
            height=450,
            title="Scatter Plot of Earthquake Magnitude vs. Depth"
        )

        st.altair_chart(chart, use_container_width=True)

