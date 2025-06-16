# GEREKLİ KÜTÜPHANELERİN OTOMATİK YÜKLENMESİ
try:
    import streamlit as st
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    import folium
    from streamlit_folium import st_folium
    from folium.plugins import HeatMap
    from io import StringIO
except ModuleNotFoundError:
    import os
    os.system("pip install streamlit pandas numpy matplotlib folium streamlit-folium")
    import streamlit as st
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    import folium
    from streamlit_folium import st_folium
    from folium.plugins import HeatMap
    from io import StringIO

st.set_page_config(page_title="Futbol Veri Analizi", layout="wide")

# Stil
page_style = """
<style>
body {
  background: linear-gradient(135deg, #002147, #004080);
  color: white;
  font-family: 'Segoe UI', sans-serif;
}
h1, h2, h3 {
  color: #FFD700;
  text-align: center;
}
.sidebar .sidebar-content {
  background: #001F3F;
  color: white;
  padding: 20px;
  text-align: center;
}
</style>
"""
st.markdown(page_style, unsafe_allow_html=True)

# Başlık
st.markdown("""
    <h1 style='text-align:center;'>⚽ Futbol Antrenman Performans Analizi</h1>
    <p style='text-align:center;'>Oyuncunun fiziksel performans verilerini analiz ederek sahadaki etkisini anlamaya yardımcı olur.</p>
""", unsafe_allow_html=True)

# Menü
st.sidebar.title("🔍 Veri Yükleme ve Seçim")
data_option = st.sidebar.radio("Veri yükleme yöntemi seçin:", ("CSV Dosyası Yükle", "CSV Metni Yapıştır"))

# CSV Yükleme
if data_option == "CSV Dosyası Yükle":
    uploaded_file = st.sidebar.file_uploader("CSV dosyasını seçin", type="csv")
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
elif data_option == "CSV Metni Yapıştır":
    csv_text = st.sidebar.text_area("CSV verisini buraya yapıştırın")
    if csv_text.strip():
        df = pd.read_csv(StringIO(csv_text))
else:
    df = None

# Fonksiyonlar
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    a = np.sin(dlat/2)**2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c * 1000  # metre

def calculate_metrics(df):
    df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')
    df = df.dropna(subset=['lat', 'lon', 'datetime'])
    distances = [haversine(df.lat[i-1], df.lon[i-1], df.lat[i], df.lon[i]) for i in range(1, len(df))]
    df = df.iloc[1:].copy()
    df['distance'] = distances
    df['time_diff'] = (df['datetime'] - df['datetime'].shift(1)).dt.total_seconds().fillna(1)
    df['speed_mps'] = df['distance'] / df['time_diff']
    df['acceleration'] = df['speed_mps'].diff().fillna(0)
    
    total_distance = df['distance'].sum() / 1000
    high_speed_dist = df[df['speed_mps'] > 5]['distance'].sum() / 1000
    max_speed = df['speed_mps'].max() * 3.6
    avg_speed = df['speed_mps'].mean() * 3.6
    sprint_count = (df['speed_mps'] > 7).sum()
    high_acc = (df['acceleration'] > 2).sum()
    high_dec = (df['acceleration'] < -2).sum()

    return {
        'df': df,
        'total_distance': total_distance,
        'high_speed_dist': high_speed_dist,
        'max_speed': max_speed,
        'avg_speed': avg_speed,
        'sprint_count': sprint_count,
        'accelerations': high_acc,
        'decelerations': high_dec
    }

if 'df' in locals() and df is not None:
    st.success("Veri başarıyla yüklendi")
    metrics = calculate_metrics(df)
    df = metrics['df']

    st.markdown("### 📈 Fiziksel Performans İstatistikleri")
    st.write(f"**Toplam Koşu Mesafesi:** {metrics['total_distance']:.2f} km")
    st.write(f"**Yüksek Hızlı Koşu Mesafesi:** {metrics['high_speed_dist']:.2f} km")
    st.write(f"**Sprint Sayısı:** {metrics['sprint_count']}")
    st.write(f"**Maksimum Hız:** {metrics['max_speed']:.2f} km/s")
    st.write(f"**Ortalama Hız:** {metrics['avg_speed']:.2f} km/s")
    st.write(f"**İvmelenme Sayısı:** {metrics['accelerations']}")
    st.write(f"**Yavaşlama Sayısı:** {metrics['decelerations']}")

    st.markdown("### 🗺️ GPS Hareket Haritası")
    map_center = [df.lat.mean(), df.lon.mean()]
    gps_map = folium.Map(location=map_center, zoom_start=17)
    HeatMap(df[['lat', 'lon']].dropna().values, radius=12).add_to(gps_map)
    st_folium(gps_map, width=700, height=450)

    st.markdown("### 📝 Antrenör Yorumu")
    yorumlar = []
    yorumlar.append(f"Oyuncu toplamda {metrics['total_distance']:.2f} km koştu. Bu değer, kondisyonunun iyi olduğunu gösteriyor.")
    if metrics['sprint_count'] > 15:
        yorumlar.append("Sprint sayısı çok iyi, oyuncu yüksek tempoda etkili.")
    else:
        yorumlar.append("Sprint sayısı düşük, patlayıcı kuvvet çalışmaları önerilir.")
    if metrics['avg_speed'] < 6:
        yorumlar.append("Ortalama hız düşük, dayanıklılık artırılmalı.")
    if metrics['accelerations'] < 10:
        yorumlar.append("Daha fazla hızlı yön değişim antrenmanları yapılmalı.")
    yorumlar.append("Yorgunluk analizi için zaman serileri detaylandırılabilir.")

    st.write("\n\n".join(yorumlar))
else:
    st.info("Lütfen veri yükleyin.")
