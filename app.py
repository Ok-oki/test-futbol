// OK Athlete Series - GPS + IMU + Bluetooth Performans Takip Sistemi (ESP32 için Arduino IDE)

#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BNO055.h>
#include <TinyGPS++.h>
#include <HardwareSerial.h>
#include <BluetoothSerial.h>

Adafruit_BNO055 bno = Adafruit_BNO055(55);
TinyGPSPlus gps;
BluetoothSerial SerialBT;
HardwareSerial GPS_Serial(1); // GPS için UART

void setup() {
  Serial.begin(115200);
  GPS_Serial.begin(9600, SERIAL_8N1, 16, 17); // RX, TX
  SerialBT.begin("OK_Tracker");

  if (!bno.begin()) {
    Serial.println("BNO055 başlatılamadı");
    while (1);
  }
  delay(1000);
  bno.setExtCrystalUse(true);
}

void loop() {
  while (GPS_Serial.available() > 0) {
    gps.encode(GPS_Serial.read());
  }

  sensors_event_t orientationData;
  bno.getEvent(&orientationData, Adafruit_BNO055::VECTOR_EULER);

  String data = "";
  data += "GPS:";
  if (gps.location.isValid()) {
    data += String(gps.location.lat(), 6) + "," + String(gps.location.lng(), 6);
  } else {
    data += "no_fix";
  }

  data += "|IMU:";
  data += String(orientationData.orientation.x, 2) + "," +
          String(orientationData.orientation.y, 2) + "," +
          String(orientationData.orientation.z, 2);

  SerialBT.println(data);
  delay(500);
}

/* ------------------------------------------------------------
   OK Athlete Series - Mobil Uygulama UI Tasarımı (Flutter)
   Marka Adı: OK
   Temel Renk: Mavi (#007BFF)
-------------------------------------------------------------

1. Ana Ekran (Renk Teması: Mavi):
   - Üst: OK logosu ve "CANLI TAKİP"
   - Orta: Kartlar (Hız, Kalp Atışı, Mesafe) — Mavi zemin, beyaz yazı
   - Alt: Harita (Google Maps)
   - En altta: Büyük mavi "ANTRENMANI BAŞLAT" butonu

2. Geçmiş:
   - Liste görünüm: Beyaz zemin, mavi başlıklar
   - Antrenman detayları: Grafikler, istatistikler, rota izi

3. Ayarlar:
   - Cihaz bağlantısı: "OK_Tracker" cihazıyla eşleş
   - Tema rengi gösterimi: #007BFF (mavi)
   - Bildirim ve veri senk ayarları

Flutter Paketleri:
   - google_maps_flutter
   - flutter_blue_plus
   - provider
   - charts_flutter
   - google_fonts (daha modern yazı tipleri)

İsteğe göre profesyonel logo tasarımı ve açılış animasyonu da eklenebilir.
*/
