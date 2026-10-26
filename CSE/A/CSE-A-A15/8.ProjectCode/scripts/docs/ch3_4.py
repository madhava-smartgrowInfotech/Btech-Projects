"""Chapters 3 (Feasibility Study) and 4 (System Requirements and Analysis) for CipherVeil."""

from . import facts as F
from .blocks import B, H1, H2, H3, N, P, TAB
from .refs import CITE as R


def c(*keys):
    return "[" + "], [".join(str(R[k]) for k in keys) + "]"


def lat(prefix):
    """Median API latency (ms) of the call whose label starts with prefix."""
    for k, v in F.API.items():
        if k.startswith(prefix):
            return v["median_ms"]
    raise KeyError(prefix)


def rsa(bits, key):
    return next(r[key] for r in F.EX["rsa_study"] if r["rsa_bits"] == bits)


def blocks():
    return chapter3() + chapter4()


# =====================================================================================================================
def chapter3():
    s = F.S
    return [
        H1("CHAPTER 3: FEASIBILITY STUDY"),
        H2("3.1 Introduction"),
        P("This chapter asks whether CipherVeil can be built, run and maintained with the resources available to the team. The question is answered partly by argument and partly by evidence, because "
          "the system was built and measured on one ordinary desktop PC with no graphics card and no paid software."),

        H2("3.2 Technical Feasibility"),
        P("**Hardware.** Every measurement in this report was taken on an Intel Core i5-12500 (6 cores, 12 threads) with 15.7 GB of memory, running Windows 11 Pro. No GPU was used or needed: the "
          "cryptography and the pixel arithmetic run on the CPU in milliseconds. Machines of lower specification were not tested."),
        P("**Software.** The stack is mature open-source software: Python 3.11.9 with FastAPI 0.115.6, SQLAlchemy 2.0.36, `cryptography` 44.0.0, Pillow 11.0.0, NumPy 2.1.3 and scikit-image 0.24.0 on the "
          "server, and React 18.3.1 with Vite 6.0.3 and Tailwind CSS 4 in the browser. The standard algorithms are not re-implemented: AES-GCM and RSA-OAEP come from a maintained library, "
          f"which is the usual rule of applied cryptography {c('katz')}, and the algorithms themselves are public standards {c('aes', 'gcm', 'rfc8017')}."),
        P("**Data.** No dataset is needed. The system is deterministic and does not learn anything, so there is no training set, no labelling and no data-quality risk. The cover images are six small pictures "
          "(four from scikit-image, one crop of one of them, one generated procedurally with a fixed seed) and the payloads are four synthetic files. The corresponding risk is one of validity "
          "rather than feasibility: six covers do not represent every kind of photograph."),
        P("**Technical risks and the measurements that retired them.** Each risk below was tested on the running system rather than assumed away."),
        TAB("Technical risks and the measurements that addressed them",
            ["Risk", "Measurement", "Verdict"],
            [["Encryption and embedding too slow for interactive use",
              f"Median encrypt {s['median_encrypt_ms']} ms, embed {s['median_embed_ms']} ms, extract {s['median_extract_ms']} ms; RSA unwrap and decrypt {s['median_decrypt_ms']} ms (RSA-3072)",
              "Feasible"],
             ["A whole send call too slow for a web console",
              f"Median {lat('send (21 KiB memo, 512x512') / 1000:.2f} s on a 512x512 cover and {lat('send (21 KiB memo, 1280x720') / 1000:.2f} s on 1280x720, mostly PSNR/SSIM and PNG encoding",
              "Feasible"],
             ["RSA key generation too slow",
              f"Median {rsa(2048, 'keygen_ms_median'):.0f} ms (2048), {rsa(3072, 'keygen_ms_median'):.0f} ms (3072), {rsa(4096, 'keygen_ms_median'):.0f} ms (4096), with large run-to-run variation",
              "Feasible"],
             ["The cover is too small for realistic files",
              "Capacity is 3.0 bits per pixel: 14.6 KiB (200x200) to 337.5 KiB (1280x720); oversize files are blocked by a capacity check",
              "Feasible for documents and small files; not for large files"],
             ["Embedding visibly damages the picture",
              f"PSNR {s['psnr_db_min']}-74.6 dB and SSIM at least {s['ssim_min']} on 22 runs; at least 51.1 dB even at 100 % fill",
              "Feasible"],
             ["The payload does not survive a normal image channel",
              "Lossless re-save survives; JPEG at quality 100, noise, resizing and recolouring do not",
              "A real limit, accepted and documented"]],
            widths=[1.9, 3.4, 1.2], align=["l", "l", "l"], size=9.5),
        P("**Defect found during documentation.** The `Send` page of the console fails for an account that has no keys, because one icon component is used but not imported "
          "(`KeyRound is not defined`, reproduced with a fresh account). It does not affect the flow with a key; it is recorded in Chapter 8 and was left unfixed in the product code."),

        H2("3.3 Economic Feasibility"),
        P("No prices are quoted, because none were measured. All software is free and open source (Python, FastAPI, `cryptography`, Pillow, NumPy, scikit-image, React, Vite). Development, testing "
          "and the measurements used one existing desktop PC. The six cover images are public-domain or CC0 pictures from scikit-image or are generated in-house, and the payloads are synthetic. "
          "Deployment of the demonstration needs a machine that can run Python and Node, and nothing else. A production service would add costs not studied here: managed key storage, "
          "monitoring, a certificate for transport security, and an independent security review."),
        P("The benefit is also qualitative. A team that must send a confidential file over a channel it does not control gets a concrete tool and, more importantly, a measured account of what that "
          "tool protects and what it does not; the cost of reproducing and extending the work is small because every experiment is a script that regenerates its own result file."),

        H2("3.4 Operational Feasibility"),
        B("**Operators.** One role, a signed-in user, can generate keys, send, receive, analyse and read the log through a browser console without using a command line.",
          "**Installation.** `setup.bat` creates the virtual environment, installs the packages and runs `npm install`; `run.bat` starts the backend on port 8315 and the frontend on port 5315. "
          "A demonstration account (`demo`) is created automatically.",
          "**Maintenance.** The backend is about 1,040 lines in 16 small modules; the 39 automated tests and the 21-check smoke test catch regressions in the cryptography, the embedding, the API and the log.",
          "**Training.** The workflow is three steps (generate a key, send, receive). The one real operating rule, that the stego image must travel as a PNG file and must not be re-encoded by a chat app, "
          "is shown on the Robustness page and in the landing text.",
          "**Risk of misuse.** The tool can hide data in a picture; it is intended for protecting confidential files. It makes no claim of resisting a determined steganalyst (Chapter 8)."),

        H2("3.5 Schedule Feasibility"),
        P("The work was planned in six phases over twelve weeks. The table is the plan used by the team, not a log of measured effort."),
        TAB("Planned schedule (weeks)", ["Phase", "Weeks", "Work", "Output"],
            [["1", "1-2", "Literature survey, base paper and problem statement", "Survey table, objectives, gap"],
             ["2", "3-4", "Design: bundle format, key handling, database, API", "Design notes, diagrams"],
             ["3", "5-7", "Backend: crypto, LSB, metrics, robustness, API", "`backend/app/`, smoke test"],
             ["4", "8-9", "Frontend: keys, send, receive, analysis, robustness, log", "`frontend/src/`"],
             ["5", "10-11", "Evaluation, tests, extra experiments", "`ml/eval.py`, `tests/`, `experiments/`"],
             ["6", "12", "Documentation, decks, report and paper", "Review decks, report, IEEE paper"]],
            widths=[0.6, 0.7, 3.4, 1.8], align=["c", "c", "l", "l"], size=10),
        P("The schedule is feasible because the largest risks (cryptographic correctness and a defensible evaluation) are small in code and large in checking; the plan therefore reserves more time "
          "for testing and measurement than for the console."),

        H2("3.6 Advantages and Constraints"),
        TAB("Advantages and constraints of the chosen approach", ["Advantages", "Constraints"],
            [["Standard primitives (AES-256-GCM, RSA-OAEP-SHA256) from a maintained library",
              "LSB data lives only in lossless images; the stego file must stay a PNG"],
             ["Authenticated encryption: a flipped bit or a wrong key releases nothing (240 of 240 flips rejected)",
              "Embedding is sequential and key-independent, so statistical tests detect medium and high fill"],
             ["Imperceptible change: PSNR at least 51.1 dB at any fill, SSIM at least 0.9929",
              "No error correction, no sender authentication, RSA only"],
             ["Runs offline on one PC with no GPU and no paid software",
              "Private keys are stored unencrypted in the local database; the JWT secret ships as a placeholder; no login rate limit"],
             ["Every number is regenerated by a script (`ml/eval.py`, `scripts/run_experiments.py`)",
              "Six covers and four small payloads; no camera photographs or large corpus"]],
            widths=[3.2, 3.3], align=["l", "l"], size=10),
    ]


# =====================================================================================================================
def chapter4():
    s = F.S
    return [
        H1("CHAPTER 4: SYSTEM REQUIREMENTS AND ANALYSIS"),
        H2("4.1 Introduction"),
        P("This chapter describes the situation the system replaces, the system that was built, and the requirements it was built to meet. The requirements are stated so that Chapter 7 can test them and "
          "Chapter 8 can report whether they were met."),

        H2("4.2 Existing System and Its Limitations"),
        P("To protect a confidential file in transit, people today use one of three approaches, each with a known weakness."),
        TAB("Existing approaches and their limitations", ["Approach", "What it gives", "Limitation"],
            [["Encryption alone (an encrypted archive or message)",
              "Confidentiality of the content",
              "The ciphertext announces that something secret is moving, which invites interception or pressure; with a shared key, key exchange is the weak point"],
             ["Steganography alone (a plain LSB tool)",
              "The existence of the message is not obvious",
              f"Nothing protects the data once the payload is found; naive embedding changes the picture and is detectable {c('provos', 'westfeld', 'rs')}"],
             ["Hybrid encryption without hiding",
              "Fast bulk encryption with a safely exchanged key",
              "Same visibility problem as encryption alone"],
             ["Advanced steganography (adaptive, deep-learning or provably secure schemes)",
              f"Better undetectability or formal guarantees {c('stc', 'cachin', 'base')}",
              "Complex, research-grade, and not packaged as an end-to-end tool measured on capacity, imperceptibility and speed"]],
            widths=[1.8, 1.7, 3.0], align=["l", "l", "l"], size=9.5),
        P(f"The base paper {c('base')} is an example of the last row: it studies how secret bits can be hidden among random decoy bits and processed by an untrusted cloud, with a security argument about the "
          "adversary's advantage. It is not a file-transfer tool and reports no PSNR, SSIM or capacity. The batch literature survey (Chapter 2) found the same gap: encryption and steganography are "
          "advanced separately, and a practical AES-RSA plus LSB pipeline evaluated end to end on capacity, imperceptibility and speed is missing."),

        H2("4.3 Proposed System and Its Advantages"),
        P("CipherVeil protects a file twice. The sender chooses a receiver's public key, a file and a cover image. The system builds a fresh 256-bit AES session key and a 96-bit nonce, "
          "encrypts the file and a small header (name, size, SHA-256) with AES-256-GCM, wraps the session key with the receiver's RSA public key using OAEP, assembles a bundle, checks that it fits in the cover, "
          "and writes it into the lowest bit of every red, green and blue value of the cover as a PNG. The receiver reverses the steps with the private key, and the tag and the hash prove that the restored "
          "file is exactly the sent one."),
        B("**Two independent layers.** The content stays confidential even if the hiding is discovered, and the transfer looks like an ordinary picture.",
          "**No shared secret.** The AES key is fresh for every message and travels only under the receiver's RSA public key.",
          "**Integrity built in.** The GCM tag and the stored SHA-256 reject any modification (0 of 240 single-bit flips accepted).",
          "**Measured, not claimed.** PSNR, SSIM, capacity, timings and a robustness report are computed for every message and logged.",
          "**Usable.** A six-page console and an API allow the whole flow without a command line."),

        H2("4.4 Functional Requirements"),
        P("The seven features of the product (F1 to F7) were derived from the six project objectives; F8 is the sign-in that scopes everything to an account. Each requirement below is testable."),
        TAB("Functional requirements", ["ID", "Requirement", "Objective", "Where"],
            [["F1", "Generate, import and export RSA keypairs of 2048, 3072 or 4096 bits; keep public-only entries for recipients; a fresh AES key for every message", "2", "Keys page, `/api/keys`"],
             ["F2", "Encrypt a file, wrap the key, check capacity before embedding and download the stego PNG", "1, 3", "Send page, `/api/send`"],
             ["F3", "Extract, unwrap, verify the GCM tag and restore the file; show input and output SHA-256 side by side", "4", "Receive page, `/api/receive`"],
             ["F4", "Compute PSNR, SSIM, MSE, histograms and bit planes against the original cover", "5", "Analysis page, `/api/analysis`"],
             ["F5", "Report capacity per cover and timings of encrypt, embed, extract and decrypt", "6", "Robustness page, `/api/benchmark`"],
             ["F6", "Attack the stego image (JPEG, noise, resize, crop) and state honestly what survives", "6", "Robustness page, `/api/robustness`"],
             ["F7", "Log every operation with sizes, timings and metrics, never secrets", "6", "Log page, `/api/log`"],
             ["F8", "Register and sign in; every key and operation belongs to its owner", "-", "Login page, `/api/auth`"]],
            widths=[0.5, 3.6, 0.8, 1.6], align=["c", "l", "c", "l"], size=9.5),

        H2("4.5 Non-Functional Requirements"),
        TAB("Non-functional requirements and how they were checked", ["Quality", "Requirement", "Check"],
            [["Confidentiality", "AES-256-GCM with a fresh key and nonce per message; RSA at least 2048 bits", "Unit tests; 50 encryptions gave 50 distinct nonces and wrapped keys"],
             ["Integrity", "Any modification is rejected before data is released", "240 of 240 tamper trials rejected"],
             ["Imperceptibility", "PSNR above 50 dB", f"Minimum {s['psnr_db_min']} dB on the evaluation; 51.1 dB at 100 % fill"],
             ["Correctness", "Byte-exact round trip", f"{s['runs']} of {s['runs']} evaluation runs exact"],
             ["Performance", "Interactive response for small files", f"Send {lat('send (21 KiB memo, 512x512') / 1000:.2f} s, receive {lat('receive') / 1000:.2f} s (median)"],
             ["Security of the service", "Authentication, ownership checks, upload cap, no secrets in the log", "API tests; 25 MB cap; log scanned for key material"],
             ["Usability", "Errors say what failed and what to do", "Capacity, wrong-key and no-payload messages (Chapter 8)"],
             ["Portability", "Windows with Python 3.11 and Node; no GPU", "Measured on one PC only"],
             ["Maintainability", "Small modules; automated tests", "39 pytest tests, 21 smoke checks"]],
            widths=[1.2, 2.7, 2.6], align=["l", "l", "l"], size=9.5),

        H2("4.6 Hardware Requirements"),
        TAB("Hardware used for development and measurement", ["Item", "Specification"],
            [["Processor", "Intel Core i5-12500, 6 cores, 12 threads"],
             ["Memory", "15.7 GB"],
             ["Graphics", "None required; CPU only"],
             ["Storage", "A few hundred MB for the environment and the node packages; each stego image is a PNG of a few hundred KB"],
             ["Network", "None for operation; the browser and the server run on the same machine"]],
            widths=[1.6, 4.8], align=["l", "l"], size=10.5),
        P("The minimum machine was not determined; the figures above are what was used."),

        H2("4.7 Software Requirements"),
        TAB("Software used", ["Layer", "Software and version"],
            [["Operating system", "Windows 11 Pro"],
             ["Language and runtime", "Python 3.11.9; Node.js v24.19.0 with npm 11.17.0"],
             ["Server", "FastAPI 0.115.6, Uvicorn 0.34.0, SQLAlchemy 2.0.36 on SQLite, PyJWT 2.10.1, bcrypt 4.2.1, python-multipart 0.0.20"],
             ["Cryptography and imaging", "`cryptography` 44.0.0, Pillow 11.0.0, NumPy 2.1.3, scikit-image 0.24.0, matplotlib 3.9.3"],
             ["Frontend", "React 18.3.1, Vite 6.0.3, Tailwind CSS 4, React Router 6, Axios, Recharts 3, three.js for the landing backdrop"],
             ["Testing", "pytest 9.1.1 with httpx; Playwright with Chrome for the screen captures"]],
            widths=[1.7, 4.7], align=["l", "l"], size=10),

        H2("4.8 User Roles and Constraints"),
        P("There is one role, the **signed-in user**. A user can be a sender, a receiver or both: keys, operations and logs are scoped to the account, and one user cannot read another's keys or messages (the API "
          "returns \"not found\"). A **visitor** sees only the public landing page. The **developer or evaluator** runs the scripts and tests but has no special rights in the application."),
        P("The constraints that shape the design are: the stego file must be a PNG and stay lossless; the cover must be large enough (capacity is (width x height x 3 - 32) / 8 bytes); uploads are capped at 25 MB; "
          "the RSA key must be at least 2048 bits; and the user must keep the private key, because there is no recovery path."),

        H2("4.9 Requirements Traceability"),
        P("Each project objective from the batch file maps to requirements, to the code that implements them and to the test that checks them, so that nothing in Chapter 8 is claimed without a requirement behind it."),
        TAB("Objectives, requirements and verification", ["Objective", "Requirements", "Verification"],
            [["1. AES for the payload, RSA for the AES key", "F2; confidentiality, integrity", "`tests/test_crypto.py` (13 tests); tamper study (240 flips); 50 distinct nonces"],
             ["2. Key generation and exchange", "F1; F8", "`tests/test_api.py` key lifecycle; fingerprints; PEM import and export"],
             ["3. Embed by LSB", "F2; imperceptibility", "`tests/test_lsb.py` (9 tests); PSNR model within 0.053 dB of measurement"],
             ["4. Extraction and decryption", "F3; correctness", "22 of 22 byte-exact round trips; end-to-end API test; smoke test"],
             ["5. PSNR and SSIM against the cover", "F4", "`tests/test_metrics_pipeline.py` (7 tests); evaluation tables"],
             ["6. Capacity, time and robustness", "F5, F6, F7; performance", "Benchmark, nine attacks over six covers, extra attacks, API latency, steganalysis"]],
            widths=[2.1, 1.5, 2.9], align=["l", "l", "l"], size=9.5),
        P("The table also shows what is not covered: there is no requirement, and therefore no test, for sender authentication, resistance to a professional steganalyst, or recovery of a lost key. "
          "They appear as limitations and future work."),

        H2("4.10 Summary"),
        P("The existing options each protect one thing; the proposed system protects the content and the fact of the transfer together, measures what it costs, and states what it cannot do. "
          "Chapter 5 shows the design that meets these requirements."),
    ]
