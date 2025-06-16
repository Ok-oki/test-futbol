# app.py

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import folium
from streamlit_folium import st_folium
from folium.plugins import HeatMap
import numpy as np

st.set_page_config(page_title="Futbol Antrenman Analizi", layout="wide", page_icon="⚽")

# --- STİL ---

st.markdown("""
    <style>
    .main {
        background: linear-gradient(135deg, #004080, #1e90ff);
        color: white;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        padding: 20px;
    }
    .stButton>button {
        background-color: #1e90ff;
        color: white;
        font-weight: bold;
    }
    .css-1aumxhk {
        color: white !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- BAŞLIK ---

st.title("⚽ Futbol Antrenman Performans Analizi")
st.markdown("**Oyuncu verilerini yükleyin, antrenman performansını anında görün!**")
st.markdown("---")

# --- VERİ YÜKLEME ---

data_option = st.radio("Veri yükleme seçeneği:", ("CSV Dosyası Yükle", "CSV Metni Yapıştır"))

df = None
if data_option == "CSV Dosyası Yükle":
    uploaded_file = st.file_uploader("CSV dosyanı seç (örn: player_mehmet.csv)", type=["csv"])
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
elif data_option == "CSV Metni Yapıştır":
    csv_text = st.text_area("CSV verisini buraya yapıştır")
    if csv_text.strip() != "":
        from io import StringIO
        df = pd.read_csv(StringIO(csv_text))

if df is not None:
    st.success(f"Veri başarıyla yüklendi! Toplam {len(df)} kayıt.")

    # Temel veri işlemleri
    if 'datetime' in df.columns:
        df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')
    else:
        st.error("Veride 'datetime' sütunu bulunamadı!")
    
    player_name = df.get('player', ['Bilinmiyor'])[0] if 'player' in df.columns else "Bilinmiyor"
    st.header(f"🏅 Oyuncu: {player_name}")

    # Temel özetler
    st.subheader("🏃‍♂️ Antrenman Özeti")
    
    # Mesafe tahmini (basit, GPS verisinden)
    if 'lat' in df.columns and 'lon' in df.columns:
        coords = df[['lat', 'lon']].dropna().values
        def haversine(lat1, lon1, lat2, lon2):
            from math import radians, cos, sin, asin, sqrt
            R = 6371e3  # metre
            phi1, phi2 = radians(lat1), radians(lat2)
            dphi = radians(lat2 - lat1)
            dlambda = radians(lon2 - lon1)
            a = sin(dphi/2)**2 + cos(phi1)*cos(phi2)*sin(dlambda/2)**2
            c = 2*asin(sqrt(a))
            return R * c

        total_distance = 0
        for i in range(1, len(coords)):
            total_distance += haversine(coords[i-1][0], coords[i-1][1], coords[i][0], coords[i][1])
        total_distance_km = total_distance / 1000
        st.metric("Toplam Koşulan Mesafe", f"{total_distance_km:.2f} km")
    else:
        st.warning("GPS (lat, lon) verileri bulunamadı, mesafe hesaplanamıyor.")

    # Ortalama ve maksimum hız (varsa)
    if 'speed' in df.columns:
        avg_speed = df['speed'].mean()
        max_speed = df['speed'].max()
        st.metric("Ortalama Hız", f"{avg_speed:.2f} m/s")
        st.metric("Maksimum Hız", f"{max_speed:.2f} m/s")
    else:
        st.info("Hız (speed) verisi bulunamadı.")

    # İvme analizi
    st.subheader("📊 İvme Analizi")
    if all(col in df.columns for col in ['accX', 'accY', 'accZ']):
        df['total_acc'] = np.sqrt(df['accX']**2 + df['accY']**2 + df['accZ']**2)
        st.metric("Ortalama İvme", f"{df['total_acc'].mean():.2f} m/s²")
        st.metric("Maksimum İvme", f"{df['total_acc'].max():.2f} m/s²")

        # Grafik
        fig, ax = plt.subplots(figsize=(10,4))
        ax.plot(df['datetime'], df['accX'], label='accX')
        ax.plot(df['datetime'], df['accY'], label='accY')
        ax.plot(df['datetime'], df['accZ'], label='accZ')
        ax.set_xlabel("Zaman")
        ax.set_ylabel("İvme (m/s²)")
        ax.legend()
        st.pyplot(fig)
    else:
        st.info("İvme (accX, accY, accZ) verileri eksik.")

    # Koşu ve Zıplama tahmini (örnek: ivme toplamından threshold ile)
    st.subheader("⚡ Antrenman Hareketleri")

    if 'total_acc' not in df.columns and all(col in df.columns for col in ['accX', 'accY', 'accZ']):
        df['total_acc'] = np.sqrt(df['accX']**2 + df['accY']**2 + df['accZ']**2)

    if 'total_acc' in df.columns:
        # Basit zıplama/hızlanma tahmini: ivme 2.5 m/s² üzeri anlar
        jump_events = df[df['total_acc'] > 2.5]
        st.metric("Tahmini Zıplama/Hızlanma Sayısı", len(jump_events))

        fig2, ax2 = plt.subplots(figsize=(10,3))
        ax2.plot(df['datetime'], df['total_acc'], label='Toplam İvme', color='orange')
        ax2.axhline(2.5, color='red', linestyle='--', label='Eşik (2.5 m/s²)')
        ax2.set_ylabel("İvme (m/s²)")
        ax2.legend()
        st.pyplot(fig2)
    else:
        st.info("Toplam ivme verisi bulunamadı, hareket analizi yapılamıyor.")

    # GPS rotası ve ısı haritası
    if 'lat' in df.columns and 'lon' in df.columns:
        st.subheader("🗺️ Antrenman GPS Rotası ve Isı Haritası")
        start_lat, start_lon = df['lat'].mean(), df['lon'].mean()
        gps_map = folium.Map(location=[start_lat, start_lon], zoom_start=17)
        points = df[['lat', 'lon']].dropna().values.tolist()
        folium.PolyLine(points, color="blue", weight=4).add_to(gps_map)
        folium.Marker(points[0], popup="Başlangıç").add_to(gps_map)
        folium.Marker(points[-1], popup="Bitiş").add_to(gps_map)
        st_folium(gps_map, width=700, height=400)

        heat_map = folium.Map(location=[start_lat, start_lon], zoom_start=17)
        HeatMap(points).add_to(heat_map)
        st_folium(heat_map, width=700, height=400)

else:
    st.info("Lütfen soldaki menüden veri yükleyin (CSV dosyası veya metin).")
