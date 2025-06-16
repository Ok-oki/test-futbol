import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import HeatMap
import numpy as np
from io import StringIO

# Koordinatlar arası mesafe (Haversine)
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0  # km
    lat1_rad = np.radians(lat1)
    lat2_rad = np.radians(lat2)
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    a = np.sin(dlat/2)**2 + np.cos(lat1_rad)*np.cos(lat2_rad)*np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c  # km

def calculate_stats(df):
    # Toplam koşulan mesafe
    dist_km = 0
    speeds = []
    for i in range(1, len(df)):
        dist = haversine(df.lat.iloc[i-1], df.lon.iloc[i-1], df.lat.iloc[i], df.lon.iloc[i])
        dist_km += dist

        time_diff = (df.datetime.iloc[i] - df.datetime.iloc[i-1]).total_seconds()
        speed = (dist*1000)/time_diff if time_diff > 0 else 0  # m/s
        speeds.append(speed)

    if len(speeds) == 0:
        avg_speed_kmh = 0
        max_speed_kmh = 0
        sprint_count = 0
    else:
        avg_speed_kmh = (np.mean(speeds)) * 3.6  # m/s to km/h
        max_speed_kmh = (np.max(speeds)) * 3.6
        sprint_count = sum([1 for s in speeds if s > 5])  # 5 m/s üstü sprint kabul

    return dist_km, avg_speed_kmh, max_speed_kmh, sprint_count

# Sayfa stili - futbol teması mavi tonlar
page_style = """
<style>
body {
  background: linear-gradient(135deg, #002147, #004080);
  color: white;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  padding: 0 2rem;
}
h1, h2, h3 {
  color: #FFD700;
  text-align: center;
}
.stButton>button {
  background-color: #004080;
  color: #FFD700;
  border-radius: 10px;
  border: none;
  padding: 0.5rem 1rem;
  font-weight: bold;
  transition: 0.3s;
}
.stButton>button:hover {
  background-color: #002147;
  color: white;
  cursor: pointer;
}
</style>
"""

st.markdown(page_style, unsafe_allow_html=True)

st.title("⚽ Şükrü Saraçoğlu Stadyumu Futbolcu Analizi")
st.write("Antrenman verinizi yükleyin, futbol performansınızı görün ve antrenörünüzün sizi yönlendirmesine hazır olun!")

data_option = st.radio("Veri yükleme yöntemi:", ("CSV Dosyası Yükle", "CSV Metni Yapıştır"))

df = None
if data_option == "CSV Dosyası Yükle":
    uploaded_file = st.file_uploader("CSV dosyasını seçin", type="csv")
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
elif data_option == "CSV Metni Yapıştır":
    csv_text = st.text_area("CSV verisini buraya yapıştırın")
    if csv_text.strip():
        df = pd.read_csv(StringIO(csv_text))

if df is not None:
    if 'datetime' in df.columns:
        df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')
    else:
        st.error("Veride 'datetime' sütunu yok, analiz yapılamıyor.")
        st.stop()

    # Zorunlu kolonlar kontrolü
    for col in ['lat','lon']:
        if col not in df.columns:
            st.error(f"Veride '{col}' sütunu yok, analiz yapılamıyor.")
            st.stop()

    st.success(f"Veri yüklendi. Toplam {len(df)} kayıt.")

    player_name = df['player'].iloc[0] if 'player' in df.columns else "Bilinmeyen Oyuncu"
    st.subheader(f"🏅 Oyuncu: {player_name}")

    # İstatistikleri hesapla
    toplam_mesafe, ort_hiz, max_hiz, sprint_sayisi = calculate_stats(df)

    # Özet gösterim
    st.markdown("### 📋 Özet Performans İstatistikleri")
    st.write(f"- **Toplam koşulan mesafe:** {toplam_mesafe:.2f} km")
    st.write(f"- **Ortalama hız:** {ort_hiz:.2f} km/saat")
    st.write(f"- **Maksimum hız:** {max_hiz:.2f} km/saat")
    st.write(f"- **Sprint sayısı (5 m/s üzeri):** {sprint_sayisi}")

    # Harita gösterimi
    st.markdown("### 🗺️ Koşu Isı Haritası ve Rota")
    stadium_location = [40.9829, 29.1212]  # Şükrü Saraçoğlu Stadyumu
    map_ = folium.Map(location=stadium_location, zoom_start=16)

    # GPS noktalarını haritaya ekle
    coords = df[['lat','lon']].dropna().values.tolist()
    if coords:
        folium.PolyLine(coords, color='yellow', weight=3).add_to(map_)
        folium.Marker(coords[0], popup="Başlangıç", icon=folium.Icon(color='green')).add_to(map_)
        folium.Marker(coords[-1], popup="Bitiş", icon=folium.Icon(color='red')).add_to(map_)
        HeatMap(coords, radius=15).add_to(map_)

    st_folium(map_, width=700, height=450)

    # Antrenör yorumları
    st.markdown("### 📝 Antrenörün Yorumu")
    yorumlar = []
    yorumlar.append(f"{player_name} toplam {toplam_mesafe:.2f} km koştu. Bu, saha içindeki hareketliliği oldukça iyi gösteriyor.")
    if max_hiz > 28:
        yorumlar.append("Maksimum hızın çok iyi, bu sprint gücünü kullanmaya devam etmelisin.")
    elif max_hiz > 20:
        yorumlar.append("Hızı iyi, ama sprint kapasiteni artırabilirsin.")
    else:
        yorumlar.append("Sprint hızını geliştirmek faydalı olacaktır.")

    if sprint_sayisi > 15:
        yorumlar.append("Sprint sayın yüksek, kondisyonun iyi.")
    else:
        yorumlar.append("Sprint sayını artırarak saha içi etkini artırabilirsin.")

    yorumlar.append("Ortalama hızına bakılırsa, dayanıklılık antrenmanlarına devam etmelisin.")
    yorumlar.append("Antrenmanda toparlanmaya ve dinlenmeye de önem ver, sakatlanma riskini azaltmak için.")

    st.write("\n\n".join(yorumlar))

else:
    st.info("Lütfen sol üstten verinizi yükleyin veya yapıştırın.")
