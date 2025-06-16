
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import folium
from streamlit_folium import st_folium
from folium.plugins import HeatMap
from io import StringIO

st.set_page_config(page_title="Futbol Veri Analizi", layout="wide")

st.markdown("""
    <h1 style='color:navy; text-align:center;'>Futbol Veri Analizi</h1>
    <p style='text-align:center;'>CSV verilerini yükleyin ve oyuncu analizlerini anında görüntüleyin.</p>
""", unsafe_allow_html=True)

st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/9/92/Soccerball.svg/2048px-Soccerball.svg.png", width=100)
st.sidebar.title("⚽ Menü")

data_option = st.sidebar.radio("Veri yükleme yöntemi seçin:", ("CSV Dosyası Yükle", "CSV Metni Yapıştır"))

df = None
if data_option == "CSV Dosyası Yükle":
    uploaded_file = st.sidebar.file_uploader("CSV dosyasını seçin", type="csv")
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
elif data_option == "CSV Metni Yapıştır":
    csv_text = st.sidebar.text_area("CSV verisini buraya yapıştırın")
    if csv_text.strip() != "":
        df = pd.read_csv(StringIO(csv_text))

if df is not None:
    st.success(f"Veri başarıyla yüklendi! Toplam kayıt: {len(df)}")
    player_name = df.get('player', ['Bilinmiyor'])[0]
    st.subheader(f"📋 Oyuncu: {player_name}")

    if 'datetime' in df.columns:
        df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')

    st.markdown("### 📊 İvme İstatistikleri")
    st.dataframe(df[['accX','accY','accZ']].describe().round(2))

    st.markdown("### 📈 İvme Zaman Grafiği")
    fig, ax = plt.subplots(figsize=(10,4))
    ax.plot(df['datetime'], df['accX'], label='accX')
    ax.plot(df['datetime'], df['accY'], label='accY')
    ax.plot(df['datetime'], df['accZ'], label='accZ')
    ax.legend()
    ax.set_xlabel("Zaman")
    ax.set_ylabel("İvme")
    st.pyplot(fig)

    if 'lat' in df.columns and 'lon' in df.columns:
        st.markdown("### 🗺️ GPS Rotası")
        start_lat, start_lon = df['lat'].mean(), df['lon'].mean()
        gps_map = folium.Map(location=[start_lat, start_lon], zoom_start=18)
        points = df[['lat', 'lon']].dropna().values.tolist()
        folium.PolyLine(points, color="blue", weight=3).add_to(gps_map)
        folium.Marker(points[0], popup="Başlangıç").add_to(gps_map)
        folium.Marker(points[-1], popup="Bitiş").add_to(gps_map)
        st_folium(gps_map, width=700, height=400)

        st.markdown("### 🔥 GPS Isı Haritası")
        heat_map = folium.Map(location=[start_lat, start_lon], zoom_start=18)
        HeatMap(points).add_to(heat_map)
        st_folium(heat_map, width=700, height=400)
else:
    st.info("Lütfen sol menüden veri yükleyin.")
