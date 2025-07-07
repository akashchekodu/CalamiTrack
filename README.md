# 🌍 CalamiTrack – Real-Time Disaster Analytics and Forecasting Platform

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

CalamiTrack is an end-to-end real-time disaster analytics and forecasting platform designed to monitor and analyze natural disasters such as earthquakes and wildfires across the globe. It integrates live geospatial data from trusted sources, processes it in real-time using a scalable pipeline, and offers powerful visualizations and predictive insights.

## 🚀 Key Features

- 🔁 **Real-time Ingestion & Processing**: 
  - Built using **Apache Kafka** and **Apache Spark Structured Streaming**.
  - Handles live streams from **USGS (earthquakes)** and **NASA FIRMS (wildfires)**.
  - Processes over **500K+ live disaster events** seamlessly.

- 📊 **Interactive Dashboards**:
  - Visualizes global disaster activity with:
    - 🗺️ Geospatial heatmaps
    - 📈 Time-series trends
    - 🌐 Region-wise breakdowns
  - Built with **Plotly**, **Leaflet**, and **Dash** for rich user interaction.

- 📚 **Historical Analysis**:
  - Analyzed **1M+ historical earthquake records**.
  - Identified seismic risk patterns by country and fault-line proximity.

- 🔮 **Forecasting**:
  - Implemented machine learning models (**LSTM**, **Random Forests**, etc.)
  - Predicts potential seismic hotspots and long-term risk zones.

## 🛠️ Tech Stack

| Layer              | Technologies Used                                   |
|--------------------|-----------------------------------------------------|
| Data Sources       | USGS Earthquake API, NASA FIRMS API                 |
| Data Pipeline      | Apache Kafka, Spark Structured Streaming            |
| Data Storage       | PostgreSQL, HDFS                                    |
| Backend / ETL      | Python, PySpark                                     |
| ML / Forecasting   | Scikit-learn, TensorFlow (LSTM), XGBoost            |
| Visualization      | Plotly, Dash, Leaflet                               |
| Deployment         | Docker, AWS EC2                                     |



## 📈 Future Improvements

- Add real-time alert notifications
- Integrate social media or news signals
- Expand forecasting to wildfires and floods
- Deploy full-stack dashboard with user authentication

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.



Built with ❤️ by [@akashchekodu](https://github.com/akashchekodu)


