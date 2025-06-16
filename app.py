import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import folium
from streamlit_folium import st_folium
from folium.plugins import HeatMap
import numpy as np
from geopy.distance import geodesic

st.set_page_config(page_title="⚽ Futbolcu Antrenman Analizi", layout="wide")
st.markdown(
    """
    <style>
    body {
        background-color: #0b3d91;
        color: #f5f5f5;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .css-1d391kg {background-color: #004d1a;}
    .stButton>button {
        background-color: #008000;
        color: white;
        font-weight: bold;
    }
    h1, h2, h3 {
        color: #ffd700;
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

st.title("⚽ Futbolcu Antrenman Analizi")

uploaded_file = st.sidebar.file_uploader("📂 CSV Dosyasını Yükle", type=["csv"])
csv_text = None
if uploaded_file is None:
    csv_text = st.sidebar.text_area("📋 Veya CSV metnini buraya yapıştır")

df = None
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
elif csv_text and csv_text.strip() != "":
    from io import StringIO
    df = pd.read_csv(StringIO(csv_text))

if df is not None:
    if 'datetime' in df.columns:
        df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')
    else:
        st.error("Veride 'datetime' sütunu bulunamadı.")
        st.stop()

    player_name = df.get('player', ['Bilinmiyor'])[0] if 'player' in df.columns else "Bilinmiyor"
    st.subheader(f"👤 Oyuncu: {player_name}")

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
    ax.set_title("Oyuncu İvme Verileri")
    st.pyplot(fig)

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

    st.markdown("### 📝 Antrenörün Yorumları")

    def coach_style_comments(df):
        comments = []
        total_time_sec = (df['datetime'].iloc[-1] - df['datetime'].iloc[0]).total_seconds()
        total_min = int(total_time_sec // 60)

        comments.append(f"Antrenmanın toplam süresi yaklaşık {total_min} dakika.")

        # Mesafe hesapla
        if 'lat' in df.columns and 'lon' in df.columns:
            distance = 0
            for i in range(1, len(df)):
                p1 = (df['lat'].iloc[i-1], df['lon'].iloc[i-1])
                p2 = (df['lat'].iloc[i], df['lon'].iloc[i])
                distance += geodesic(p1, p2).meters
            km = distance / 1000
            comments.append(f"Bu sürede yaklaşık {km:.2f} kilometre koştun.")

            ort_hiz = distance / total_time_sec if total_time_sec > 0 else 0
            comments.append(f"Ortalama hızın saniyede {ort_hiz:.2f} metre, yani iyi bir tempoyla oynuyorsun.")

        # İvme (hareketlilik) durumu
        acc = np.sqrt(df['accX']**2 + df['accY']**2 + df['accZ']**2)
        ort_acc = acc.mean()

        if ort_acc > 1.2:
            comments.append("Maçta ve antrenmanda oldukça hareketlisin, bu iyi bir enerji işareti.")
        elif ort_acc > 0.8:
            comments.append("Hareketlerin dengeli, biraz daha tempolu olabilirsin.")
        else:
            comments.append("Hareketlerin düşük görünüyor, biraz daha aktif olman gerek.")

        # Duraklama kontrolü
        duraklama_say = (acc < 0.3).sum()
        if duraklama_say > total_time_sec * 0.1:
            comments.append("Antrenman sırasında sık sık duraksadığını fark ettim, dayanıklılığını artırmaya çalış.")

        # Bölgesel yorum
        if 'lat' in df.columns and 'lon' in df.columns:
            lat_mode = df['lat'].mode()[0]
            lon_mode = df['lon'].mode()[0]
            comments.append(f"En çok vakit geçirdiğin yer: yaklaşık ({lat_mode:.5f}, {lon_mode:.5f}). Burada daha hareketli olmaya çalış.")

        comments.append("Genel olarak iyi gidiyorsun, ama dayanıklılık ve tempoyu biraz daha geliştirmelisin. Devam!")

        return "\n\n".join(comments)

    yorumlar = coach_style_comments(df)
    st.text_area("Oyuncuya Antrenör Yorumu", value=yorumlar, height=250)

else:
    st.info("Lütfen sol menüden CSV dosyası yükleyin veya veriyi yapıştırın.")
