# SignalScout ESP32 node

A fixed or portable sensor that watches one Wi-Fi network (for example a community hotspot) and reports to SignalScout. It sends the same JSON as `scripts/esp32_simulator.py`, so the dashboard treats real and simulated nodes the same way.

## What it measures

Every 10 seconds the node records:

- Wi-Fi signal (RSSI) of the access point it is connected to. While disconnected, it scans for the network instead.
- BLE signal: the strongest nearby advertiser, or one beacon you choose.
- Round-trip time and loss: three HTTP requests to the SignalScout API over one kept-alive connection.
- Position from a NEO-6M GPS. Without a GPS fix, the location set for the node on the Devices page is used.
- Optional: the cellular signal level from a SIM800L or SIM7600 modem (`AT+CSQ`).

Readings are written to flash (LittleFS) first. They are uploaded in batches, so readings taken while the network or the API is down are sent later with their original timestamps. The node keeps up to 500 readings; beyond that the oldest are dropped. The clock is set by NTP or, when there is no internet, by GPS time.

On the server, node readings are judged with Wi-Fi ranges:

| Class | Rule |
|---|---|
| Strong | RSSI ≥ -67 dBm |
| Weak | -80 to -67 dBm, or latency above 300 ms, or loss above 20% |
| Dead | below -80 dBm, or disconnected |

## Parts and wiring

| Part | Pin | ESP32 pin |
|---|---|---|
| NEO-6M GPS | TX | GPIO 16 (`GPS_RX_PIN`) |
| | RX | GPIO 17 (`GPS_TX_PIN`) |
| | VCC / GND | 3V3 / GND |
| SIM800L (optional) | TX | GPIO 26 (`CELL_RX_PIN`) |
| | RX | GPIO 27 (`CELL_TX_PIN`) |
| | VCC / GND | separate 3.7–4.2 V supply rated for 2 A, with a common GND |

Any ESP32 DevKit (ESP32-WROOM-32) works. The GPS is optional: set `GPS_ENABLED 0` for a node that stays in one place.

## Flashing

1. Install the Arduino IDE 2. In **Boards Manager**, install **esp32 by Espressif Systems** (3.x).
2. In **Library Manager**, install **ArduinoJson** (7.x), **TinyGPSPlus** and **NimBLE-Arduino** (2.x).
3. In SignalScout, open **Devices → Add ESP32 node**. Give it a name and the Wi-Fi network name. If it has no GPS, also give its position. Copy the device key; it is shown only once.
4. Copy `config.example.h` to `config.h` in this folder and fill in:
   - `WIFI_SSID` and `WIFI_PASSWORD`.
   - `API_BASE`: if the node is on the same network as the PC, use `http://<PC LAN address>:8202`. Otherwise use the `https://` tunnel address that `run.bat` prints.
   - `DEVICE_KEY`: the key from step 3.
5. Open `esp32_node.ino` and select the board **ESP32 Dev Module**. Set **Tools → Partition Scheme → Huge APP (3MB No OTA/1MB SPIFFS)**. With Wi-Fi, BLE and TLS the sketch is about 1.35 MB, larger than the default 1.25 MB app partition. The 1 MB data partition holds the reading buffer. Upload.
6. Open the Serial Monitor at 115200 baud. Each reading is printed as JSON, followed by `uploaded N readings`. The node appears as online on the Devices page.

`config.h` is git-ignored, so the Wi-Fi password and device key never reach the repository.

## Troubleshooting

| Serial output | Meaning and fix |
|---|---|
| `upload refused (401)` | Wrong or rotated device key. Copy a new key from the Devices page. |
| `upload refused (400) ... no GPS position and has no fixed location` | No GPS fix yet, and the node has no location set. Set one on the Devices page, or wait for the GPS fix (outdoors, 1–5 minutes on a cold start). |
| `upload failed (-1)` | The API cannot be reached. Check `API_BASE`. On a LAN, allow port 8202 in Windows Firewall for private networks. |
| `buffer full - dropping ...` | The node has been offline for more than about 80 minutes at the default interval. |
| No `ts` field in readings | The clock is not set yet: there is no internet for NTP and no GPS time. The server then uses the time the reading was received. |
