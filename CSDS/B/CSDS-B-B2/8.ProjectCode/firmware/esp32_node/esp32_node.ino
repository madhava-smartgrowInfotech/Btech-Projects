// SignalScout ESP32 sensor node.
//
// Every MEASURE_INTERVAL_S the node records one reading of the Wi-Fi link it watches:
//   - Wi-Fi RSSI of the connected access point (or of WIFI_SSID from a scan while disconnected)
//   - BLE RSSI (strongest advertiser, or one beacon)
//   - HTTP round-trip latency and loss to the SignalScout API
//   - position from a NEO-6M GPS, or none for a fixed node (the server uses the location set on the Devices page)
//   - optional cellular signal level from a SIM800L / SIM7600 modem
// Readings go into a LittleFS buffer first and are uploaded in batches to POST /api/ingest/node with the
// device key, so nothing is lost while the link or the API is down. Timestamps come from NTP or GPS.
//
// Libraries (Arduino Library Manager): ArduinoJson 7, TinyGPSPlus, NimBLE-Arduino 2.
// Board: "ESP32 Dev Module" (esp32 by Espressif, 3.x).

#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <WiFiClientSecure.h>
#include <LittleFS.h>
#include <ArduinoJson.h>
#include <math.h>
#include <sys/time.h>
#include <time.h>

#if __has_include("config.h")
#include "config.h"
#else
#error "Copy config.example.h to config.h and fill in your Wi-Fi name, API address and device key."
#endif

#if GPS_ENABLED
#include <TinyGPSPlus.h>
#endif
#if BLE_ENABLED
#include <NimBLEDevice.h>
#endif

#define FW_VERSION "signalscout-node-1.0.0"

static const char* BUFFER_FILE = "/buffer.jsonl";
static const char* BUFFER_TMP = "/buffer.tmp";
static const char* BOOT_FILE = "/boot";

struct Measurement {
  bool connected;
  float wifiRssi;    // NAN when unknown
  float bleRssi;
  float latencyMs;
  float loss;
  float cellRssi;
  bool hasFix;
  double lat;
  double lon;
};

static uint32_t bootNumber = 0;
static uint32_t readingCounter = 0;
static uint32_t bufferCount = 0;
static uint32_t lastMeasure = 0;
static uint32_t lastUpload = 0;
static uint32_t lastReconnect = 0;
static bool ntpStarted = false;

#if GPS_ENABLED
static TinyGPSPlus gps;
#endif

// ---------------------------------------------------------------- helpers

static void say(const String& msg) {
  Serial.printf("[%8lu] %s\n", (unsigned long)(millis() / 1000), msg.c_str());
}

static bool timeValid() {
  return time(nullptr) > 1700000000;  // after Nov 2023: the clock has been set
}

static String isoNow() {
  time_t now = time(nullptr);
  struct tm t;
  gmtime_r(&now, &t);
  char buf[25];
  strftime(buf, sizeof(buf), "%Y-%m-%dT%H:%M:%SZ", &t);
  return String(buf);
}

static const char* networkName() {
  return strlen(NETWORK_NAME) ? NETWORK_NAME : WIFI_SSID;
}

static void feedGps() {
#if GPS_ENABLED
  while (Serial2.available()) gps.encode(Serial2.read());
  // Use GPS time when NTP has not set the clock yet (for example, no internet on this network).
  if (!timeValid() && gps.date.isValid() && gps.time.isValid() && gps.date.year() >= 2024 && gps.time.age() < 2000) {
    struct tm t = {};
    t.tm_year = gps.date.year() - 1900;
    t.tm_mon = gps.date.month() - 1;
    t.tm_mday = gps.date.day();
    t.tm_hour = gps.time.hour();
    t.tm_min = gps.time.minute();
    t.tm_sec = gps.time.second();
    setenv("TZ", "UTC0", 1);
    tzset();
    struct timeval tv = {mktime(&t), 0};
    settimeofday(&tv, nullptr);
    say("clock set from GPS: " + isoNow());
  }
#endif
}

// Waits while still reading the GPS so no NMEA sentences are dropped.
static void idle(uint32_t ms) {
  uint32_t start = millis();
  do {
    feedGps();
    delay(5);
  } while (millis() - start < ms);
}

// ---------------------------------------------------------------- Wi-Fi and time

static void ensureWifi() {
  if (WiFi.status() == WL_CONNECTED) {
    if (!ntpStarted) {
      configTime(0, 0, NTP_SERVER);
      ntpStarted = true;
    }
    return;
  }
  if (millis() - lastReconnect < 15000 && lastReconnect != 0) return;
  lastReconnect = millis();
  say(String("connecting to Wi-Fi \"") + WIFI_SSID + "\"");
  WiFi.disconnect();
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
}

// RSSI of WIFI_SSID from a scan, for readings taken while the node is not connected.
static float scanForNetwork() {
  int n = WiFi.scanNetworks(false, true);
  float best = NAN;
  for (int i = 0; i < n; i++) {
    if (WiFi.SSID(i) == WIFI_SSID && (isnan(best) || WiFi.RSSI(i) > best)) best = WiFi.RSSI(i);
  }
  WiFi.scanDelete();
  return best;
}

// ---------------------------------------------------------------- HTTP

static bool beginRequest(HTTPClient& http, WiFiClient& plain, WiFiClientSecure& secure, const String& url) {
  if (url.startsWith("https://")) {
#if TLS_SKIP_VERIFY
    secure.setInsecure();
#elif defined(API_ROOT_CA)
    secure.setCACert(API_ROOT_CA);
#else
#error "Set TLS_SKIP_VERIFY 1 or define API_ROOT_CA in config.h"
#endif
    return http.begin(secure, url);
  }
  return http.begin(plain, url);
}

// Latency and loss over PINGS_PER_READING requests on one kept-alive connection, so the
// DNS, TCP and TLS handshakes of the warm-up request are not counted as round-trip time.
static void measureLatency(float& latencyMs, float& loss) {
  latencyMs = NAN;
  loss = 1.0f;
  HTTPClient http;
  WiFiClient plain;
  WiFiClientSecure secure;
  if (!beginRequest(http, plain, secure, String(API_BASE) + "/api/probe/ping")) return;
  http.setReuse(true);
  http.setTimeout(3000);
  http.setConnectTimeout(3000);
  if (http.GET() == 200) http.getString();

  float samples[PINGS_PER_READING];
  int ok = 0;
  for (int i = 0; i < PINGS_PER_READING; i++) {
    uint32_t t0 = micros();
    int code = http.GET();
    if (code == 200) {
      http.getString();
      samples[ok++] = (micros() - t0) / 1000.0f;
    }
    feedGps();
  }
  http.end();
  loss = (float)(PINGS_PER_READING - ok) / PINGS_PER_READING;
  if (ok == 0) return;
  // median of the successful round trips
  for (int i = 1; i < ok; i++)
    for (int j = i; j > 0 && samples[j - 1] > samples[j]; j--) {
      float tmp = samples[j];
      samples[j] = samples[j - 1];
      samples[j - 1] = tmp;
    }
  latencyMs = ok % 2 ? samples[ok / 2] : (samples[ok / 2 - 1] + samples[ok / 2]) / 2.0f;
}

static int postBatch(const String& body) {
  HTTPClient http;
  WiFiClient plain;
  WiFiClientSecure secure;
  if (!beginRequest(http, plain, secure, String(API_BASE) + "/api/ingest/node")) return -1;
  http.setTimeout(15000);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-Device-Key", DEVICE_KEY);
  int code = http.POST(body);
  if (code >= 400) say("upload refused (" + String(code) + "): " + http.getString().substring(0, 160));
  http.end();
  return code;
}

// ---------------------------------------------------------------- BLE and modem

static float scanBle() {
#if BLE_ENABLED
  NimBLEScan* scan = NimBLEDevice::getScan();
  scan->setActiveScan(false);
  scan->setInterval(100);
  scan->setWindow(99);
  std::string wanted = BLE_BEACON_MAC;
  for (auto& c : wanted) c = tolower(c);
  NimBLEScanResults results = scan->getResults(BLE_SCAN_MS, false);
  float best = NAN;
  for (int i = 0; i < results.getCount(); i++) {
    const NimBLEAdvertisedDevice* d = results.getDevice(i);
    if (!wanted.empty() && d->getAddress().toString() != wanted) continue;  // NimBLE prints addresses in lower case
    if (isnan(best) || d->getRSSI() > best) best = d->getRSSI();
  }
  scan->clearResults();
  return best;
#else
  return NAN;
#endif
}

static float readCellRssi() {
#if CELL_MODEM_ENABLED
  while (Serial1.available()) Serial1.read();
  Serial1.print("AT+CSQ\r");
  String resp;
  uint32_t start = millis();
  while (millis() - start < 1500 && resp.indexOf("OK") < 0) {
    while (Serial1.available()) resp += (char)Serial1.read();
    delay(10);
  }
  int at = resp.indexOf("+CSQ:");
  if (at < 0) return NAN;
  int csq = resp.substring(at + 5).toInt();
  if (csq < 0 || csq > 31) return NAN;  // 99 = not known or not detectable
  return -113.0f + 2.0f * csq;           // 3GPP TS 27.007 mapping to dBm
#else
  return NAN;
#endif
}

// ---------------------------------------------------------------- LittleFS buffer

static uint32_t countLines() {
  File f = LittleFS.open(BUFFER_FILE, "r");
  if (!f) return 0;
  uint32_t n = 0;
  uint8_t chunk[256];
  while (f.available()) {
    size_t got = f.read(chunk, sizeof(chunk));
    for (size_t i = 0; i < got; i++)
      if (chunk[i] == '\n') n++;
  }
  f.close();
  return n;
}

// Removes the oldest `n` readings by copying the rest to a new file.
static void dropOldest(uint32_t n) {
  File in = LittleFS.open(BUFFER_FILE, "r");
  if (!in) return;
  File out = LittleFS.open(BUFFER_TMP, "w");
  uint32_t skipped = 0, kept = 0;
  while (in.available()) {
    String line = in.readStringUntil('\n');
    if (skipped < n) {
      skipped++;
      continue;
    }
    out.print(line);
    out.print('\n');
    kept++;
  }
  in.close();
  out.close();
  LittleFS.remove(BUFFER_FILE);
  LittleFS.rename(BUFFER_TMP, BUFFER_FILE);
  bufferCount = kept;
}

static void bufferAppend(const String& line) {
  File f = LittleFS.open(BUFFER_FILE, FILE_APPEND);
  if (!f) {
    say("buffer write failed");
    return;
  }
  f.print(line);
  f.print('\n');
  f.close();
  bufferCount++;
  if (bufferCount > BUFFER_MAX) {
    uint32_t drop = bufferCount - BUFFER_MAX + BUFFER_MAX / 10;  // drop a little extra so this is not done on every reading
    say("buffer full - dropping the oldest " + String(drop) + " readings");
    dropOldest(drop);
  }
}

static void uploadBuffered() {
  if (WiFi.status() != WL_CONNECTED || bufferCount == 0) return;
  File f = LittleFS.open(BUFFER_FILE, "r");
  if (!f) return;
  JsonDocument doc;
  doc["firmware"] = FW_VERSION;
  doc["uptime_s"] = millis() / 1000;
  doc["network_name"] = networkName();
  JsonArray readings = doc["readings"].to<JsonArray>();
  uint32_t taken = 0;
  while (f.available() && taken < UPLOAD_BATCH) {
    String line = f.readStringUntil('\n');
    taken++;  // every line counts, so a damaged one is removed with the batch
    JsonDocument r;
    if (line.length() && deserializeJson(r, line) == DeserializationError::Ok) readings.add(r);
  }
  f.close();
  if (readings.size() == 0) {
    dropOldest(taken);
    return;
  }
  String body;
  serializeJson(doc, body);
  int code = postBatch(body);
  if ((code >= 200 && code < 300) || code == 422) {
    // 422: the server rejected the format; retrying would never succeed
    dropOldest(taken);
    say("uploaded " + String(readings.size()) + " readings (" + String(bufferCount) + " still buffered)");
  } else {
    say("upload failed (" + String(code) + ") - keeping " + String(bufferCount) + " readings for later");
  }
}

// ---------------------------------------------------------------- measuring

static Measurement measure() {
  Measurement m = {};
  m.connected = WiFi.status() == WL_CONNECTED;
  m.wifiRssi = m.connected ? (float)WiFi.RSSI() : scanForNetwork();
  if (m.connected) {
    measureLatency(m.latencyMs, m.loss);
  } else {
    m.latencyMs = NAN;
    m.loss = NAN;
  }
  m.bleRssi = scanBle();
  m.cellRssi = readCellRssi();
  m.hasFix = false;
#if GPS_ENABLED
  if (gps.location.isValid() && gps.location.age() < 5000) {
    m.hasFix = true;
    m.lat = gps.location.lat();
    m.lon = gps.location.lng();
  }
#endif
  return m;
}

static String toJsonLine(const Measurement& m) {
  JsonDocument r;
  r["seq"] = bootNumber * 100000UL + (readingCounter++ % 100000UL);
  if (timeValid()) r["ts"] = isoNow();
  if (m.hasFix) {
    r["lat"] = serialized(String(m.lat, 6));
    r["lon"] = serialized(String(m.lon, 6));
  }
  r["connected"] = m.connected;
  if (!isnan(m.wifiRssi)) r["wifi_rssi"] = m.wifiRssi;
  if (!isnan(m.bleRssi)) r["ble_rssi"] = m.bleRssi;
  if (!isnan(m.latencyMs)) r["latency_ms"] = serialized(String(m.latencyMs, 1));
  if (!isnan(m.loss)) r["packet_loss"] = serialized(String(m.loss, 3));
  if (!isnan(m.cellRssi)) {
    r["cell_rssi"] = m.cellRssi;
    r["cell_type"] = CELL_TYPE;
  }
  String line;
  serializeJson(r, line);
  return line;
}

// ---------------------------------------------------------------- setup and loop

static uint32_t nextBootNumber() {
  uint32_t n = 0;
  File f = LittleFS.open(BOOT_FILE, "r");
  if (f) {
    n = f.readString().toInt();
    f.close();
  }
  n = (n + 1) % 40000;  // keeps seq = boot * 100000 + counter inside 32 bits
  f = LittleFS.open(BOOT_FILE, "w");
  if (f) {
    f.print(n);
    f.close();
  }
  return n;
}

void setup() {
  Serial.begin(115200);
  delay(200);
  say(String(FW_VERSION) + " starting");

  if (!LittleFS.begin(true)) say("LittleFS could not be mounted - readings will not survive a restart");
  bootNumber = nextBootNumber();
  bufferCount = countLines();
  say("boot " + String(bootNumber) + ", " + String(bufferCount) + " readings waiting in the buffer");

#if GPS_ENABLED
  Serial2.begin(GPS_BAUD, SERIAL_8N1, GPS_RX_PIN, GPS_TX_PIN);
#endif
#if CELL_MODEM_ENABLED
  Serial1.begin(CELL_BAUD, SERIAL_8N1, CELL_RX_PIN, CELL_TX_PIN);
#endif
#if BLE_ENABLED
  NimBLEDevice::init("");
#endif

  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);
  ensureWifi();
  uint32_t start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < 15000) idle(250);
  say(WiFi.status() == WL_CONNECTED ? "Wi-Fi connected, IP " + WiFi.localIP().toString() : String("Wi-Fi not connected yet - buffering"));
  ensureWifi();
}

void loop() {
  feedGps();
  ensureWifi();

  if (lastMeasure == 0 || millis() - lastMeasure >= MEASURE_INTERVAL_S * 1000UL) {
    lastMeasure = millis();
    Measurement m = measure();
    String line = toJsonLine(m);
    bufferAppend(line);
    say(line);
  }
  if (millis() - lastUpload >= UPLOAD_INTERVAL_S * 1000UL) {
    lastUpload = millis();
    uploadBuffered();
  }
  idle(50);
}
