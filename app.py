import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import folium
from streamlit_folium import st_folium
from folium.plugins import HeatMap
import numpy as np

# Sayfa ayarları ve futbol temalı CSS
st.set_page_config(page_title="⚽ Futbol Veri Analizi", layout="wide")
st.markdown(
    """
    <style>
    body {
        background-color: #0b3d91;  /* Koyu mavi stad teması */
        color: #f5f5f5;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .css-1d391kg {background-color: #004d1a;} /* Sidebar koyu yeşil */
    .stButton>button {
        background-color: #008000;
        color: white;
        font-weight: bold;
    }
    h1, h2, h3 {
        color: #ffd700; /* Altın sarısı */
        text-align: center;
        text-shadow: 1px 1px 2px black;
    }
    .stDataFrame table {
        background-color: #003300;
        color: #cfc;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Başlık
st.title("⚽ Futbolcu Antrenman Analizi")

# Dosya yükleme
uploaded_file = st.sidebar.file_uploader("📂 CSV Dosyasını Yükle", type=["csv"])
csv_text = None
if uploaded_file is None:
    csv_text = st.sidebar.text_area("📋 Veya CSV metnini buraya yapıştır")

# Veri okuma
df = None
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
elif csv_text and csv_text.strip() != "":
    from io import StringIO
    df = pd.read_csv(StringIO(csv_text))

if df is not None:
    # Zamanı datetime yap
    if 'datetime' in df.columns:
        df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')
    else:
        st.error("Veride 'datetime' sütunu bulunamadı.")
        st.stop()

    # Oyuncu adı varsa göster
    player_name = df.get('player', ['Bilinmiyor'])[0] if 'player' in df.columns else "Bilinmiyor"
    st.subheader(f"👤 Oyuncu: {player_name}")

    # İvme temel istatistikler
    st.markdown("### 📊 İvme İstatistikleri")
    st.dataframe(df[['accX','accY','accZ']].describe().round(2))

    # İvme grafiği
    st.markdown("### 📈 İvme Zaman Grafiği")
    fig, ax = plt.subplots(figsize=(10,4))
    ax.plot(df['datetime'], df['accX'], label='accX')
    ax.plot(df['datetime'], df['accY'], label='accY')
    ax.plot(df['datetime'], df['accZ'], label='accZ')
    ax.legend()
    ax.set_xlabel("Zaman")
    ax.set_ylabel("İvme")
    ax.set_title("Oyuncu İvme Verileri")
    st.pyplot(fig)

    # GPS harita ve ısı haritası
    if 'lat' in df.columns and 'lon' in df.columns:
        st.markdown("### 🗺️ GPS Rotası ve Isı Haritası")
        start_lat, start_lon = df['lat'].mean(), df['lon'].mean()
        gps_map = folium.Map(location=[start_lat, start_lon], zoom_start=17)
        points = df[['lat', 'lon']].dropna().values.tolist()
        folium.PolyLine(points, color="yellow", weight=4).add_to(gps_map)
        folium.Marker(points[0], popup="Başlangıç", icon=folium.Icon(color='green')).add_to(gps_map)
        folium.Marker(points[-1], popup="Bitiş", icon=folium.Icon(color='red')).add_to(gps_map)
        st_folium(gps_map, width=700, height=400)

        heat_map = folium.Map(location=[start_lat, start_lon], zoom_start=17)
        HeatMap(points, radius=15, blur=10).add_to(heat_map)
        st_folium(heat_map, width=700, height=400)

    # ---- Analiz & Yorum Bölümü ----
    st.markdown("### 📝 Analiz & Yorum")

    # Örnek analiz fonksiyonu
    def analyze_data(df):
        yorumlar = []

        # Toplam süre
        total_seconds = (df['datetime'].iloc[-1] - df['datetime'].iloc[0]).total_seconds()
        yorumlar.append(f"🏃‍♂️ Toplam antrenman süresi: {int(total_seconds//60)} dakika.")

        # Ortalama hız tahmini (basit, GPS noktaları arası ortalama hız)
        if 'lat' in df.columns and 'lon' in df.columns:
            from geopy.distance import geodesic
            toplam_mesafe = 0
            for i in range(1, len(df)):
                p1 = (df['lat'].iloc[i-1], df['lon'].iloc[i-1])
                p2 = (df['lat'].iloc[i], df['lon'].iloc[i])
                toplam_mesafe += geodesic(p1, p2).meters
            ort_hiz = toplam_mesafe / total_seconds if total_seconds > 0 else 0
            yorumlar.append(f"⚡ Ortalama hız yaklaşık {ort_hiz:.2f} m/s.")

        # Yorulma tahmini (ivme düşüşü veya duraklama analizi)
        acc_magnitude = np.sqrt(df['accX']**2 + df['accY']**2 + df['accZ']**2)
        acc_mean = acc_magnitude.mean()
        if acc_mean > 1.2:
            yorumlar.append("🔥 Oyuncu antrenmanda oldukça dinamik ve tempolu koştu.")
        elif acc_mean > 0.8:
            yorumlar.append("😊 Oyuncu orta tempoda antrenman yaptı, gayet dengeli.")
        else:
            yorumlar.append("😴 Oyuncu antrenmanda düşük tempoda veya dinlenme modundaydı.")

        # Duraklamalar (ivme çok düşük anlar)
        duraklama_sayisi = (acc_magnitude < 0.3).sum()
        if duraklama_sayisi > total_seconds * 0.1:
            yorumlar.append("⏸️ Oyuncu antrenman süresince sık sık durakladı veya yavaşladı.")

        # Örnek bölgesel yorum (en çok nerede durdu?)
        if 'lat' in df.columns and 'lon' in df.columns:
            # En çok vakit geçirilen nokta (yoğunluk)
            lat_mode = df['lat'].mode().iloc[0]
            lon_mode = df['lon'].mode().iloc[0]
            yorumlar.append(f"📍 Oyuncu en çok {lat_mode:.5f}, {lon_mode:.5f} koordinatlarında zaman geçirdi.")

        return "\n\n".join(yorumlar)

    yorum_metni = analyze_data(df)
    st.text_area("Analiz ve Yorumlar", value=yorum_metni, height=200)

else:
    st.info("Lütfen sol menüden CSV dosyası yükleyin veya veriyi yapıştırın.")
