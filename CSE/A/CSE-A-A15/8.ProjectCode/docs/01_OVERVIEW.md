# CipherVeil - overview

CipherVeil protects a confidential file twice. The file is encrypted with a hybrid AES + RSA scheme, then the encrypted bundle is hidden in the least significant bits of an ordinary-looking PNG image. The receiver extracts the bundle, unwraps the key with their private RSA key, verifies the authentication tag and gets the original file back byte for byte.

## The problem it solves

- Encryption alone signals that sensitive data is moving, which invites attack.
- Hiding alone offers no protection once the payload is found.
- Symmetric encryption is fast, but sharing its key is the weak point.
- Naive LSB embedding can degrade the picture and be detected.

CipherVeil combines the layers: AES-256-GCM for the data, RSA-OAEP for the key, LSB substitution for concealment, and it measures how visible the result actually is.

## Who uses it

- Anyone sending a confidential file over an untrusted channel.
- Security-conscious teams that want the transfer itself to look unremarkable.
- Reviewers who want to check the scheme's strength with numbers.

## Features

| # | Feature | Where |
|---|---|---|
| F1 | Key management: generate, import, export RSA keypairs; fresh AES session key per message | Keys |
| F2 | Encrypt and embed with a capacity check before embedding | Send |
| F3 | Extract and decrypt; input and output hashes side by side | Receive |
| F4 | PSNR, SSIM, histograms and bit planes against the original cover | Analysis |
| F5 | Capacity per cover and timings for encrypt, embed, extract, decrypt | Analysis, Robustness |
| F6 | Recompression, noise, resize and crop tests with an honest verdict | Robustness |
| F7 | Operation log with sizes, timings and metrics, never secrets | Log |

## Related work

ProSt (provably secure homomorphic steganography, IEEE Access, 2026) advances steganography and encryption independently, including provably secure constructions. CipherVeil is the practical counterpart: a hybrid AES-RSA plus LSB pipeline evaluated end to end on capacity, imperceptibility and speed. The provably secure construction, audio/video carriers and edge-adaptive embedding are deliberately out of scope.

## Honest limits

- LSB data lives only in lossless images. Send the PNG as a file; do not let a chat app, social site or email client re-encode it.
- A statistical steganalysis tool can detect sequential LSB embedding in heavily filled images. Low fill ratios are much harder to spot.
- Private keys are stored unencrypted in the local database on the machine running the backend. Treat `data/app.db` as sensitive.
