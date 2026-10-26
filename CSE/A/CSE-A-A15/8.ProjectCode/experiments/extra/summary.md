# Extra experiments

## A. RSA key size

| RSA bits | keygen ms (median) | wrap ms | unwrap + decrypt ms | wrapped key B | overhead B |
|---|---|---|---|---|---|
| 2048 | 32.497 | 0.164 | 31.054 | 256 | 401 |
| 3072 | 191.488 | 0.173 | 93.693 | 384 | 529 |
| 4096 | 353.921 | 0.236 | 221.139 | 512 | 657 |

## B. Fill ratio: max |measured - theory| PSNR = 0.053 dB, max PSNR std over 5 payload seeds = 0.0987 dB

| Cover | Fill | Used % | PSNR mean | PSNR theory | SSIM mean |
|---|---|---|---|---|---|
| astronaut_512x512.png | 0.01 | 1.4 | 69.651 | 69.655 | 0.999951 |
| astronaut_512x512.png | 0.05 | 5.38 | 63.84 | 63.828 | 0.999735 |
| astronaut_512x512.png | 0.1 | 10.36 | 60.987 | 60.988 | 0.999518 |
| astronaut_512x512.png | 0.25 | 25.27 | 57.113 | 57.114 | 0.998924 |
| astronaut_512x512.png | 0.5 | 50.13 | 54.136 | 54.14 | 0.997833 |
| astronaut_512x512.png | 0.75 | 74.99 | 52.394 | 52.391 | 0.99592 |
| astronaut_512x512.png | 1.0 | 99.94 | 51.146 | 51.144 | 0.993347 |
| cat_451x300.png | 0.01 | 1.78 | 68.611 | 68.614 | 0.999974 |
| cat_451x300.png | 0.05 | 5.74 | 63.539 | 63.545 | 0.999859 |
| cat_451x300.png | 0.1 | 10.69 | 60.841 | 60.85 | 0.999719 |
| cat_451x300.png | 0.25 | 25.53 | 57.071 | 57.07 | 0.999304 |
| cat_451x300.png | 0.5 | 50.26 | 54.128 | 54.129 | 0.998664 |
| cat_451x300.png | 0.75 | 74.99 | 52.393 | 52.391 | 0.997924 |
| cat_451x300.png | 1.0 | 99.88 | 51.148 | 51.147 | 0.997049 |
| coffee_600x400.png | 0.01 | 1.44 | 69.533 | 69.541 | 0.999963 |
| coffee_600x400.png | 0.05 | 5.42 | 63.807 | 63.799 | 0.999776 |
| coffee_600x400.png | 0.1 | 10.39 | 60.982 | 60.974 | 0.99957 |
| coffee_600x400.png | 0.25 | 25.3 | 57.103 | 57.11 | 0.99893 |
| coffee_600x400.png | 0.5 | 50.15 | 54.136 | 54.139 | 0.998021 |
| coffee_600x400.png | 0.75 | 74.99 | 52.392 | 52.391 | 0.997135 |
| coffee_600x400.png | 1.0 | 99.93 | 51.145 | 51.144 | 0.996277 |
| coffee_small_200x200.png | 0.01 | 3.65 | 65.438 | 65.491 | 0.999926 |
| coffee_small_200x200.png | 0.05 | 7.5 | 62.362 | 62.375 | 0.999832 |
| coffee_small_200x200.png | 0.1 | 12.32 | 60.193 | 60.226 | 0.999708 |
| coffee_small_200x200.png | 0.25 | 26.78 | 56.872 | 56.86 | 0.999264 |
| coffee_small_200x200.png | 0.5 | 50.87 | 54.082 | 54.076 | 0.998464 |
| coffee_small_200x200.png | 0.75 | 74.96 | 52.393 | 52.392 | 0.997559 |
| coffee_small_200x200.png | 1.0 | 99.58 | 51.168 | 51.159 | 0.996634 |
| generated_landscape_1280x720.png | 0.01 | 1.12 | 70.669 | 70.663 | 0.999948 |
| generated_landscape_1280x720.png | 0.05 | 5.11 | 64.051 | 64.057 | 0.999648 |
| generated_landscape_1280x720.png | 0.1 | 10.1 | 61.104 | 61.097 | 0.999276 |
| generated_landscape_1280x720.png | 0.25 | 25.08 | 57.148 | 57.148 | 0.998154 |
| generated_landscape_1280x720.png | 0.5 | 50.04 | 54.147 | 54.148 | 0.996298 |
| generated_landscape_1280x720.png | 0.75 | 75.0 | 52.391 | 52.391 | 0.994619 |
| generated_landscape_1280x720.png | 1.0 | 99.98 | 51.142 | 51.142 | 0.992893 |
| rocket_640x427.png | 0.01 | 1.39 | 69.681 | 69.703 | 0.99995 |
| rocket_640x427.png | 0.05 | 5.37 | 63.853 | 63.841 | 0.999661 |
| rocket_640x427.png | 0.1 | 10.34 | 60.991 | 60.994 | 0.999301 |
| rocket_640x427.png | 0.25 | 25.26 | 57.117 | 57.116 | 0.998235 |
| rocket_640x427.png | 0.5 | 50.13 | 54.142 | 54.14 | 0.99665 |
| rocket_640x427.png | 0.75 | 74.99 | 52.389 | 52.391 | 0.995205 |
| rocket_640x427.png | 1.0 | 99.94 | 51.144 | 51.144 | 0.994194 |

## C. Plain vs encrypted

| Payload | Kind | Bytes | Ones fraction | Entropy b/B | Changed % of bits | PSNR |
|---|---|---|---|---|---|---|
| accounts.csv | plain | 2774 | 0.4649 | 4.346 | 49.67 | 72.119 |
| accounts.csv | encrypted | 3182 | 0.4971 | 7.94 | 50.37 | 71.462 |
| confidential_memo.pdf | plain | 21517 | 0.4367 | 6.933 | 49.96 | 63.201 |
| confidential_memo.pdf | encrypted | 21935 | 0.5004 | 7.992 | 50.09 | 63.107 |
| meeting_notes.txt | plain | 169 | 0.4512 | 4.379 | 49.06 | 84.229 |
| meeting_notes.txt | encrypted | 581 | 0.489 | 7.609 | 50.09 | 78.848 |
| settings.json | plain | 99 | 0.4167 | 4.246 | 51.58 | 86.264 |
| settings.json | encrypted | 506 | 0.5091 | 7.577 | 51.3 | 79.34 |

## D. Steganalysis (chi-square flagged 27 of 30 cases)

| Cover | Fill | True fraction | chi2 p cover | chi2 p stego | WS cover | WS stego |
|---|---|---|---|---|---|---|
| astronaut_512x512.png | 0.1 | 0.1036 | 0.0 | 1.0 | 0.0828 | 0.182 |
| astronaut_512x512.png | 0.25 | 0.2527 | 0.0 | 1.0 | 0.0828 | 0.3345 |
| astronaut_512x512.png | 0.5 | 0.5013 | 0.0 | 1.0 | 0.0828 | 0.5696 |
| astronaut_512x512.png | 0.75 | 0.7499 | 0.0 | 1.0 | 0.0828 | 0.8085 |
| astronaut_512x512.png | 1.0 | 0.9994 | 0.0 | 0.9999 | 0.0828 | 0.9944 |
| cat_451x300.png | 0.1 | 0.1069 | 0.9988 | 1.0 | 0.0037 | 0.102 |
| cat_451x300.png | 0.25 | 0.2553 | 0.8405 | 1.0 | 0.0037 | 0.2621 |
| cat_451x300.png | 0.5 | 0.5025 | 0.3416 | 0.9991 | 0.0037 | 0.5218 |
| cat_451x300.png | 0.75 | 0.7498 | 0.129 | 1.0 | 0.0037 | 0.7745 |
| cat_451x300.png | 1.0 | 0.9987 | 0.0135 | 1.0 | 0.0037 | 1.0044 |
| coffee_600x400.png | 0.1 | 0.1039 | 0.0 | 1.0 | 0.0868 | 0.1915 |
| coffee_600x400.png | 0.25 | 0.253 | 0.0 | 1.0 | 0.0868 | 0.326 |
| coffee_600x400.png | 0.5 | 0.5014 | 0.0 | 0.9999 | 0.0868 | 0.5434 |
| coffee_600x400.png | 0.75 | 0.7499 | 0.0 | 1.0 | 0.0868 | 0.7853 |
| coffee_600x400.png | 1.0 | 0.9993 | 0.0 | 1.0 | 0.0868 | 1.0104 |
| coffee_small_200x200.png | 0.1 | 0.1233 | 0.5819 | 1.0 | 0.1804 | 0.3008 |
| coffee_small_200x200.png | 0.25 | 0.2678 | 0.0001 | 0.9999 | 0.1804 | 0.3918 |
| coffee_small_200x200.png | 0.5 | 0.5086 | 0.0 | 1.0 | 0.1804 | 0.6205 |
| coffee_small_200x200.png | 0.75 | 0.7495 | 0.0 | 1.0 | 0.1804 | 0.8641 |
| coffee_small_200x200.png | 1.0 | 0.9958 | 0.0 | 0.9993 | 0.1804 | 0.9865 |
| generated_landscape_1280x720.png | 0.1 | 0.101 | 0.0 | 0.9982 | -0.005 | 0.0956 |
| generated_landscape_1280x720.png | 0.25 | 0.2508 | 0.0 | 1.0 | -0.005 | 0.2473 |
| generated_landscape_1280x720.png | 0.5 | 0.5004 | 0.0 | 1.0 | -0.005 | 0.4933 |
| generated_landscape_1280x720.png | 0.75 | 0.75 | 0.0 | 1.0 | -0.005 | 0.7499 |
| generated_landscape_1280x720.png | 1.0 | 0.9998 | 0.0 | 1.0 | -0.005 | 0.9972 |
| rocket_640x427.png | 0.1 | 0.1034 | 0.0 | 0.9935 | 0.1082 | 0.2026 |
| rocket_640x427.png | 0.25 | 0.2526 | 0.0 | 0.9695 | 0.1082 | 0.3469 |
| rocket_640x427.png | 0.5 | 0.5013 | 0.0 | 0.9999 | 0.1082 | 0.5659 |
| rocket_640x427.png | 0.75 | 0.7499 | 0.0 | 1.0 | 0.1082 | 0.8035 |
| rocket_640x427.png | 1.0 | 0.9994 | 0.0 | 1.0 | 0.1082 | 1.0311 |

## E. Tamper study: 240 single-bit flips, accepted with wrong data: 0

- length header: {'rejected: bad length header': 13, 'rejected: AES-GCM tag check failed': 27}
- magic: {'rejected: No CipherVeil bundle found in this image': 40}
- wrapped-key length: {'rejected: This bundle was wrapped for a different key size': 40}
- wrapped key: {'rejected: RSA unwrap failed': 40}
- nonce: {'rejected: AES-GCM tag check failed': 40}
- ciphertext and tag: {'rejected: AES-GCM tag check failed': 40}

## F. Freshness: {'encryptions': 50, 'distinct_nonces': 50, 'distinct_wrapped_keys': 50, 'mean_bit_difference_between_bundles': 0.4992, 'all_decrypt': True}

## G. Extra attacks (6 covers)

| Attack | Recovered |
|---|---|
| PNG re-save, compression 9 | 6 / 6 |
| PNG with alpha channel added | 6 / 6 |
| WebP lossless | 6 / 6 |
| WebP lossy q90 | 0 / 6 |
| JPEG quality 100 | 0 / 6 |
| Grayscale conversion | 0 / 6 |
| Rotate 90 degrees | 0 / 6 |
| Flip horizontally | 0 / 6 |
| 256-colour palette | 0 / 6 |
