# Evaluation summary

Scheme: AES-256-GCM + RSA-OAEP-SHA256 + 1-bit LSB, sequential, RGB (RSA-3072).

- Runs: 22 (every round trip byte-exact: True)
- PSNR: min 52.479 dB, mean 61.731 dB
- SSIM: min 0.995806, mean 0.999039
- Median time: encrypt 0.15 ms, embed 0.25 ms, extract 0.05 ms, decrypt 86.37 ms
- Capacity: up to 3.0 bits per pixel

## Capacity

| Cover | Pixels | Max hidden (KiB) | Bits/pixel |
|---|---|---|---|
| astronaut_512x512.png | 512x512 | 96.0 | 3.0 |
| cat_451x300.png | 451x300 | 49.5 | 3.0 |
| coffee_600x400.png | 600x400 | 87.9 | 3.0 |
| coffee_small_200x200.png | 200x200 | 14.6 | 2.999 |
| generated_landscape_1280x720.png | 1280x720 | 337.5 | 3.0 |
| rocket_640x427.png | 640x427 | 100.1 | 3.0 |

## Quality and speed

| Cover | Payload | Used % | PSNR dB | SSIM | Encrypt ms | Embed ms | Extract ms | Decrypt ms |
|---|---|---|---|---|---|---|---|---|
| astronaut_512x512.png | 1024 B | 1.584 | 69.171 | 0.999941 | 0.131 | 0.115 | 0.034 | 87.481 |
| astronaut_512x512.png | 4096 B | 4.709 | 64.423 | 0.999767 | 0.19 | 0.222 | 0.047 | 86.009 |
| astronaut_512x512.png | 16384 B | 17.211 | 58.754 | 0.999256 | 0.154 | 0.183 | 0.091 | 88.198 |
| astronaut_512x512.png | 65536 B | 67.213 | 52.865 | 0.996392 | 0.211 | 0.684 | 0.178 | 85.482 |
| astronaut_512x512.png | 131072 B | does not fit | | | | | | |
| cat_451x300.png | 1024 B | 3.069 | 66.217 | 0.999934 | 0.12 | 0.102 | 0.028 | 86.946 |
| cat_451x300.png | 4096 B | 9.124 | 61.531 | 0.999764 | 0.158 | 0.112 | 0.03 | 84.322 |
| cat_451x300.png | 16384 B | 33.347 | 55.898 | 0.999078 | 0.146 | 0.17 | 0.059 | 86.181 |
| cat_451x300.png | 65536 B | does not fit | | | | | | |
| cat_451x300.png | 131072 B | does not fit | | | | | | |
| coffee_600x400.png | 1024 B | 1.73 | 68.74 | 0.999948 | 0.138 | 0.175 | 0.028 | 93.163 |
| coffee_600x400.png | 4096 B | 5.144 | 63.993 | 0.999786 | 0.139 | 0.266 | 0.037 | 85.139 |
| coffee_600x400.png | 16384 B | 18.799 | 58.409 | 0.999195 | 0.153 | 0.374 | 0.066 | 87.478 |
| coffee_600x400.png | 65536 B | 73.414 | 52.479 | 0.997186 | 0.21 | 0.828 | 0.234 | 84.241 |
| coffee_600x400.png | 131072 B | does not fit | | | | | | |
| coffee_small_200x200.png | 1024 B | 10.383 | 61.014 | 0.99977 | 0.129 | 0.095 | 0.022 | 87.388 |
| coffee_small_200x200.png | 4096 B | 30.868 | 56.264 | 0.999166 | 0.14 | 0.121 | 0.051 | 89.865 |
| coffee_small_200x200.png | 16384 B | does not fit | | | | | | |
| coffee_small_200x200.png | 65536 B | does not fit | | | | | | |
| coffee_small_200x200.png | 131072 B | does not fit | | | | | | |
| generated_landscape_1280x720.png | 1024 B | 0.451 | 74.615 | 0.99999 | 0.135 | 0.55 | 0.03 | 92.94 |
| generated_landscape_1280x720.png | 4096 B | 1.339 | 69.876 | 0.999931 | 0.174 | 0.595 | 0.059 | 85.656 |
| generated_landscape_1280x720.png | 16384 B | 4.895 | 64.234 | 0.999664 | 0.145 | 0.565 | 0.066 | 87.522 |
| generated_landscape_1280x720.png | 65536 B | 19.118 | 58.321 | 0.998598 | 0.212 | 0.796 | 0.208 | 85.791 |
| generated_landscape_1280x720.png | 131072 B | 38.081 | 55.333 | 0.99718 | 0.367 | 1.674 | 0.507 | 95.645 |
| rocket_640x427.png | 1024 B | 1.519 | 69.365 | 0.999941 | 0.176 | 0.138 | 0.033 | 84.905 |
| rocket_640x427.png | 4096 B | 4.517 | 64.581 | 0.999723 | 0.205 | 0.242 | 0.042 | 85.478 |
| rocket_640x427.png | 16384 B | 16.509 | 58.955 | 0.998853 | 0.144 | 0.315 | 0.084 | 86.566 |
| rocket_640x427.png | 65536 B | 64.474 | 53.049 | 0.995806 | 0.213 | 0.543 | 0.17 | 84.287 |
| rocket_640x427.png | 131072 B | does not fit | | | | | | |

## Robustness (6 covers, accounts.csv)

| Attack | Payload recovered | Payload lost | Mean LSB error rate |
|---|---|---|---|
| Lossless PNG re-save | 6 | 0 | 0.0 |
| JPEG quality 95 | 0 | 6 | 0.4973 |
| JPEG quality 75 | 0 | 6 | 0.4999 |
| JPEG quality 50 | 0 | 6 | 0.5032 |
| Gaussian noise sigma 1 | 0 | 6 | 0.4935 |
| Gaussian noise sigma 3 | 0 | 6 | 0.4988 |
| Resize to 90% | 0 | 6 | 0.501 |
| Crop bottom 10% | 6 | 0 | 0.0 |
| Crop left 10% | 0 | 6 | 0.4995 |
