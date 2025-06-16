import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import folium
from streamlit_folium import st_folium
from folium.plugins import HeatMap
import numpy as np
from io import StringIO

# --- Haversine formülü ile mesafe hesaplama (metre cinsinden) ---
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0  # Dünya yarıçapı km
    lat1_rad = np.radians(lat1)
    lat2_rad = np.radians(lat2)
    delta_lat = np.radians(lat2 - lat1)
    delta_lon = np.radians(lon2 - lon1)

    a = np.sin(delta_lat / 2) ** 2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(delta_lon / 2) ** 2
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c * 1000  # metre

# --- Antrenör yorumları ---
def coach_style_comments(df):
    comments = []
    if 'datetime' not in df.columns:
        return "Zaman bilgisi yok, analiz yapılamıyor."

    total_time_sec = (df['datetime'].iloc[-1] - df['datetime'].iloc[0]).total_seconds()
    total_min = int(total_time_sec // 60)
    comments.append(f"Antrenmanın toplam süresi yaklaşık {total_min} dakika.")

    if 'lat' in df.columns and 'lon' in df.columns:
        distance = 0
        for i in range(1, len(df)):
            distance += haversine(df['lat'].iloc[i-1], df['lon'].iloc[i-1], df['lat'].iloc[i], df['lon'].iloc[i])
        km = distance / 1000
        comments.append(f"Bu sürede yaklaşık {km:.2f} kilometre koştun.")
        ort_hiz = distance / total_time_sec if total_time_sec > 0 else 0
        comments.append(f"Ortalama hızın saniyede {ort_hiz:.2f} metre, iyi bir tempo tutturuyorsun.")

    # İvme yorumu (örnek)
    if all(col in df.columns for col in ['accX', 'accY', 'accZ']):
        acc_mean = df[['accX', 'accY', 'accZ']].abs().mean().mean()
        if acc_mean < 5:
            comments.append("Daha fazla hareket etmeye çalış, biraz durağansın.")
        else:
            comments.append("Hareketlerin iyi, tempoyu koru!")

    comments.append("Genel olarak performansın güzel, ancak dayanıklılık üzerinde çalışmaya devam etmelisin.")
    return "\n\n".join(comments)

# --- Streamlit sayfa ayarları ---
st.set_page_config(page_title="Futbol Veri Analizi", page_icon="⚽", layout="wide")

# --- Arka plan stili (mavi tonları) ---
page_bg_img = '''
<style>
body {
    background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
    color: white;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}
h1, h2, h3 {
    color: #e6e6fa;
}
.stButton>button {
    background-color: #1e90ff;
    color: white;
    border-radius: 8px;
    border: none;
}
.stButton>button:hover {
    background-color: #3742fa;
    color: white;
}
</style>
'''
st.markdown(page_bg_img, unsafe_allow_html=True)

# --- Başlık ---
st.title("⚽ Futbol Veri Analizi ve Antrenör Yorumu")
st.markdown("CSV dosyanızı yükleyin veya veriyi yapıştırın, antrenman performansınızı anında görün!")

# --- Veri yükleme seçeneği ---
data_option = st.radio("Veri yükleme yöntemi seçin:", ("CSV Dosyası Yükle", "CSV Metni Yapıştır"))

df = None
if data_option == "CSV Dosyası Yükle":
    uploaded_file = st.file_uploader("CSV dosyasını seçin", type="csv")
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
elif data_option == "CSV Metni Yapıştır":
    csv_text = st.text_area("CSV verisini buraya yapıştırın")
    if csv_text.strip() != "":
        df = pd.read_csv(StringIO(csv_text))

if df is not None:
    # Zaman kolonunu datetime'a çevir
    if 'datetime' in df.columns:
        df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')

    # Oyuncu adı varsa göster
    player_name = df['player'].iloc[0] if 'player' in df.columns else "Bilinmiyor"
    st.subheader(f"📋 Oyuncu: {player_name}")

    # Özet tablo
    st.markdown("### 📊 İvme İstatistikleri (X, Y, Z)")
    if all(col in df.columns for col in ['accX', 'accY', 'accZ']):
        st.dataframe(df[['accX', 'accY', 'accZ']].describe().round(2))
    else:
        st.info("İvme verileri bulunamadı.")

    # İvme zaman grafiği
    st.markdown("### 📈 İvme Zaman Grafiği")
    if all(col in df.columns for col in ['datetime', 'accX', 'accY', 'accZ']):
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(df['datetime'], df['accX'], label='accX')
        ax.plot(df['datetime'], df['accY'], label='accY')
        ax.plot(df['datetime'], df['accZ'], label='accZ')
        ax.legend()
        ax.set_xlabel("Zaman")
        ax.set_ylabel("İvme")
        ax.grid(True, linestyle='--', alpha=0.5)
        st.pyplot(fig)
    else:
        st.info("İvme zaman grafiği için veriler eksik.")

    # GPS rotası ve ısı haritası
    if all(col in df.columns for col in ['lat', 'lon']):
        st.markdown("### 🗺️ GPS Rotası")
        start_lat, start_lon = df['lat'].mean(), df['lon'].mean()
        gps_map = folium.Map(location=[start_lat, start_lon], zoom_start=16)
        points = df[['lat', 'lon']].dropna().values.tolist()
        folium.PolyLine(points, color="cyan", weight=3).add_to(gps_map)
        folium.Marker(points[0], popup="Başlangıç", icon=folium.Icon(color="green")).add_to(gps_map)
        folium.Marker(points[-1], popup="Bitiş", icon=folium.Icon(color="red")).add_to(gps_map)
        st_folium(gps_map, width=700, height=400)

        st.markdown("### 🔥 GPS Isı Haritası")
        heat_map = folium.Map(location=[start_lat, start_lon], zoom_start=16)
        HeatMap(points, radius=15, blur=20).add_to(heat_map)
        st_folium(heat_map, width=700, height=400)
    else:
        st.info("GPS (lat, lon) verileri eksik.")

    # Antrenör yorumları
    st.markdown("### 📝 Antrenör Yorumu")
    comments = coach_style_comments(df)
    st.info(comments)

else:
    st.info("Lütfen sol taraftan CSV dosyasını yükleyin veya veri yapıştırın.")

