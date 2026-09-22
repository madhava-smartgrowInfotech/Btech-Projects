// SignalScout ESP32 node - configuration.
// Copy this file to config.h (same folder) and fill in your values. config.h is git-ignored.
#pragma once

// ---- Wi-Fi: the network this node monitors and uploads through ----
#define WIFI_SSID          "your-wifi-name"
#define WIFI_PASSWORD      "your-wifi-password"
// Name shown for this network in SignalScout; empty = use WIFI_SSID
#define NETWORK_NAME       ""

// ---- SignalScout API ----
// On the same network as the PC: http://<PC LAN address>:8202 (see "Connect a phone" for the address).
// Elsewhere: the https:// tunnel address shown by run.bat.
#define API_BASE           "http://192.168.1.10:8202"
// Device key, shown once when you add an ESP32 node on the Devices page
#define DEVICE_KEY         "ssk_paste_your_device_key_here"
// For an https:// API_BASE only. 1 = encrypted, certificate not checked (quick-tunnel addresses change).
// 0 = check the certificate against API_ROOT_CA below.
#define TLS_SKIP_VERIFY    1
// #define API_ROOT_CA "-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----\n"

// ---- Timing ----
#define MEASURE_INTERVAL_S 10      // one reading every 10 s
#define UPLOAD_INTERVAL_S  30      // upload buffered readings every 30 s
#define PINGS_PER_READING  3       // round trips per reading for latency and loss

// ---- GPS: NEO-6M on UART2. Set GPS_ENABLED 0 for a fixed node and set its location on the Devices page. ----
#define GPS_ENABLED        1
#define GPS_RX_PIN         16      // ESP32 pin wired to the GPS module's TX
#define GPS_TX_PIN         17      // ESP32 pin wired to the GPS module's RX
#define GPS_BAUD           9600

// ---- BLE scan: RSSI of the strongest advertiser, or only of BLE_BEACON_MAC when set ("aa:bb:cc:dd:ee:ff") ----
#define BLE_ENABLED        1
#define BLE_SCAN_MS        2000
#define BLE_BEACON_MAC     ""

// ---- Optional cellular modem (SIM800L / SIM7600) on UART1: signal level from AT+CSQ ----
#define CELL_MODEM_ENABLED 0
#define CELL_RX_PIN        26      // ESP32 pin wired to the modem's TX
#define CELL_TX_PIN        27      // ESP32 pin wired to the modem's RX
#define CELL_BAUD          9600
#define CELL_TYPE          "2G"    // "2G" for SIM800L, "4G" for SIM7600

// ---- Offline buffer (LittleFS): readings kept while the API cannot be reached ----
#define BUFFER_MAX         500     // oldest readings are dropped beyond this
#define UPLOAD_BATCH       100     // readings per upload

// ---- Time ----
#define NTP_SERVER         "pool.ntp.org"
