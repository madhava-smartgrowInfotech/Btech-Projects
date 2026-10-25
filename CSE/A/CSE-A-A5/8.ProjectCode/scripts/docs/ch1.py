"""Chapter 1: Introduction."""

from . import facts as F
from .blocks import B, H1, H2, N, P, TAB
from .refs import CITE as R


def _key(b):
    """First piece of text of a block, used to find blocks to drop or replace in report mode."""
    v = b[1]
    return v[0] if isinstance(v, list) and v else (v if isinstance(v, str) else "")


def trim(blocks, drop=(), drop_sections=(), replace=None, table_rows=None):
    """Report-mode trimming. drop: block-text prefixes to remove; drop_sections: heading prefixes whose whole section
    (up to the next heading of the same or higher level) is removed; replace: {prefix: block}; table_rows: {caption prefix: keep(row)}."""
    replace = replace or {}
    table_rows = table_rows or {}
    out, skip_level = [], None
    for b in blocks:
        if b[0] in ("h1", "h2", "h3"):
            lvl = int(b[0][1])
            if skip_level is not None and lvl <= skip_level:
                skip_level = None
            if skip_level is None and any(b[1].startswith(x) for x in drop_sections):
                skip_level = lvl
        if skip_level is not None:
            continue
        k = _key(b)
        if any(k.startswith(x) for x in drop):
            continue
        hit = next((x for x in replace if k.startswith(x)), None)
        if hit:
            if replace[hit] is not None:
                out.append(replace[hit])
            continue
        if b[0] == "tab":
            cap = next((x for x in table_rows if b[1].startswith(x)), None)
            if cap:
                b = ("tab", b[1], b[2], [r for r in b[3] if table_rows[cap](r)], b[4], b[5], b[6])
        out.append(b)
    return out


def blocks():
    b = _full()
    if not F.REPORT:
        return b
    return trim(
        b,
        drop=("Security for such a transmission rests", "The motivation for this project is therefore practical", "The base paper's enhanced elliptic-curve scheme"),
        replace={
            "**Both protections together.**": P("The work is needed because the surveyed studies treat the two protections separately and rarely measure their combined cost; because authenticated "
                                                 "encryption should be shown by repeated tamper trials and not by argument; and because a detector trained on generated data can look excellent and fail "
                                                 "on real traffic, so the real-data evidence and the claims of the default demonstration model must be kept apart."),
            "Two objectives differ from the original wording": P("Two objectives differ from the original wording. Objective 1 asks for RSA in the key exchange; the implementation uses elliptic-curve "
                                                                 f"Diffie-Hellman, because a fresh ephemeral key per message gives every message its own key and a 65-byte public value in place of a 256-byte wrapped key, and "
                                                                 f"an RSA-OAEP hybrid [{R['oaep']}] was benchmarked as the baseline. Objective 2 covers key storage, which is not met: the cloud key pair is kept in memory."),
            "**Chapter 2** surveys": P("The report continues with the literature survey (Chapter 2), the feasibility study and requirements (Chapters 3 and 4), the design (Chapter 5), the methodology and "
                                       "implementation (Chapter 6), testing (Chapter 7), results with the comparison against the base paper (Chapter 8), the conclusion and future scope "
                                       "(Chapters 9 and 10), the references and three appendices."),
        },
    )


def _full():
    off, pap = F.OFFS, F.PAPS
    real = F.SHIFT["shipped_on_real_official_test"]["stack"]
    base, survey = R["base"], f"{R['s_fmdb']}]-[{R['s_hybrid_gmr']}"
    ip = F.IP
    obj_rows = [
        ["1", "Design a hybrid encryption scheme using AES for the payload and RSA for key exchange", "AES-256-GCM for the payload; ECDH P-256 + HKDF-SHA256 for key agreement (RSA-OAEP hybrid benchmarked as a baseline only)"],
        ["2", "Implement secure key generation, distribution and storage between sender and receiver", "Fresh ephemeral P-256 key pair per message; public key travels in the envelope; the cloud key pair lives in process memory only"],
        ["3", "Build a transmission module that encrypts before upload and decrypts after download", "Encrypt / decrypt-and-verify API and console screen for text and files up to 5 MB, against a mock cloud endpoint"],
        ["4", "Train a classifier on a benchmark intrusion dataset to detect anomalous access", "XGBoost + 1D CNN + logistic-regression stacking, trained and evaluated on real UNSW-NB15; the shipped default is trained on synthetic data"],
        ["5", "Integrate the detection layer so suspicious sessions are flagged and logged during transfer", "Flow records and CSV batches are scored; attacks are logged with severity in a 500-entry alert list"],
        ["6", "Evaluate encryption and decryption time, throughput overhead and detection accuracy", "Crypto latency by size and algorithm, combined per-transfer overhead, detection metrics over seeds, thresholds and categories"],
    ]
    return [
        H1("CHAPTER 1: INTRODUCTION"),
        P(f"This chapter introduces the domain of the project, the motivation for building {F.PRODUCT}, the problem it addresses, the objectives set for it, the scope that "
          "was actually delivered, its contributions, and the limitations and assumptions that govern every result reported later. It closes with a map of the rest of the report."),

        H2("1.1 Domain"),
        P("Cloud computing lets an organisation keep its files, databases and services on infrastructure owned by someone else and reach them over the Internet. The attraction is "
          "economic and operational: capacity is rented as needed, backups and availability are handled by the provider, and users reach their data from anywhere. The price is that "
          "the data no longer stays inside a network the organisation controls. Every upload and every download crosses links, routers and gateways that belong to third parties, and "
          "the data finally rests on machines run by a provider that can, unless the data is protected, read it."),
        P("Security for such a transmission rests on the classic triad of confidentiality, integrity and availability. Confidentiality means that only the intended receiver can read "
          "the content; integrity means that a modification on the way is detected; availability means that the service keeps working while someone is attacking it. Two families of "
          "technique serve these goals and they work at different layers. Cryptography acts on the data itself: whoever intercepts an encrypted message learns little, and an "
          "authenticated cipher also exposes tampering. Intrusion detection acts on the behaviour of the network: a classifier looks at the statistics of each connection, "
          "such as its duration, byte counts and the number of similar connections seen recently, and decides whether the flow looks like normal use or like an attack such as a "
          "denial-of-service burst, a scan or an exploit attempt."),

        H2("1.2 Background and Motivation"),
        P(f"The base paper of this project [{base}] states the dilemma clearly: once an attacker has access to a network they can quickly collect information, so an intrusion "
          "detection system is needed, and because the data crossing the network is itself valuable, it must also be encrypted. The paper therefore combines a deep-learning "
          "detector with an enhanced elliptic-curve scheme in one framework. Other recent work follows the same two tracks separately: detectors built from deep networks, "
          f"ensembles and feature-selection pipelines for cloud traffic [{R['nadeem']}], [{R['bakro']}], [{R['alrayes']}], and encryption schemes proposed or tuned for cloud "
          f"storage and transfer [{survey}]."),
        P("Symmetric ciphers such as AES are fast but need a secure way to share the key; asymmetric ciphers such as RSA or elliptic-curve Diffie-Hellman solve the key exchange but "
          f"are too slow for bulk data. Hybrid cryptography uses the asymmetric step to agree a key and the symmetric step to protect the payload. Modern authenticated modes such as "
          f"AES-GCM [{R['gcm']}] add an integrity tag to the ciphertext, so a single changed bit is detected at decryption. Encryption alone, however, says nothing about an attacker "
          "who already holds valid credentials or who is flooding the service with legitimate-looking requests, and that is the case where a machine-learning detector adds value."),
        P("The motivation for this project is therefore practical: build one platform on which both protections can be seen working together, tested, and measured, so that the "
          "cost of adding detection to an encrypted path is a number and not an assumption. A second motivation is honesty about evaluation. Published accuracy figures on the "
          f"UNSW-NB15 dataset [{R['unsw15']}] range widely depending on the split and the subset, so every number in this report states the data and the protocol behind it."),

        H2("1.3 Problem Statement"),
        P("The batch problem statement lists four weaknesses of current practice:"),
        B("data placed in a public cloud is readable by the provider unless it is encrypted before upload;",
          "symmetric encryption alone leaves the key exchange itself vulnerable to interception;",
          "encryption cannot detect an attacker who has already obtained valid credentials;",
          "most academic systems address either cryptography or intrusion detection, rarely both together."),
        P("The problem addressed here is to build and evaluate a transmission framework that encrypts data with a hybrid asymmetric-symmetric scheme and, on the same data path, "
          "monitors network flows with a machine-learning intrusion detector, so that confidentiality and integrity are protected and suspicious traffic is flagged and logged."),

        H2("1.4 Need for the Work"),
        B("**Both protections together.** The literature survey of this project found that cryptography and intrusion detection are mostly treated as separate concerns, and that the "
          "combined cost of running both on one path is rarely measured. This report measures it.",
          "**Verified integrity, not only secrecy.** An authenticated cipher turns an undetected modification into a rejected message; the tamper tests of Chapter 7 show this behaviour "
          "repeatedly rather than by argument.",
          "**Honest detection results.** A detector trained on generated data can look excellent and fail on real traffic. The project needs real-data evidence and a clear statement of "
          "what the default demonstration model can and cannot claim.",
          "**A tool a reviewer can run.** A secured-transfer screen, a scoring screen, an alert list and a performance page make the system inspectable by people who do not read code."),

        H2("1.5 Objectives"),
        P("The six objectives set for the project, and what each became, are summarised in Table 1.1. Chapter 8 returns to this table with the measured outcome for each."),
        TAB("Project objectives and how each was addressed", ["No.", "Objective", "How it was addressed"], obj_rows, widths=[0.5, 2.8, 3.0], align=["c", "l", "l"], size=10),
        P("Two objectives differ from the original wording and the report says so plainly. Objective 1 asks for RSA in the key exchange; the implementation uses elliptic-curve "
          f"Diffie-Hellman instead, because a fresh ephemeral key per message gives every message its own key and a 65-byte public value in place of a 256-byte wrapped key. An RSA-2048 "
          f"and RSA-3072 OAEP hybrid [{R['oaep']}] was implemented in the benchmark script so that the two designs could be compared on the same machine. Objective 2 covers key storage, which "
          "is not met: the cloud key pair is generated at start-up and kept in memory."),

        H2("1.6 Scope"),
        P(f"{F.PRODUCT} consists of two modules and two interfaces:"),
        B("**SecureChannel**: ECDH P-256 key agreement, HKDF-SHA256 key derivation, AES-256-GCM authenticated encryption, with an ephemeral key pair per message, 12-byte random nonces "
          f"and a {F.ENVELOPE_OVERHEAD_BYTES}-byte fixed envelope overhead.",
          f"**ThreatSense Engine**: preprocessing of the 42-feature UNSW-NB15 flow schema, an XGBoost classifier, a one-dimensional CNN in PyTorch, and a logistic-regression meta-model that stacks "
          "their probabilities; severity bands and an in-memory alert log.",
          f"**Interfaces**: a FastAPI service (port {F.API_PORT}) with nine API routes, a React 19 console (port {F.WEB_PORT}) with live scoring, secure transfer, alerts and model-performance "
          "screens, and the original HTML dashboard served by the API.",
          "**Evidence**: an experiment suite on the real UNSW-NB15 official partition and on the base paper's 9,000-flow protocol, a crypto benchmark, a latency measurement of the "
          f"combined path, {F.PYTEST_TOTAL} automated tests and {F.SMOKE_TOTAL} smoke checks."),
        P("Out of scope are live packet capture, automatic blocking of flagged sessions, a real cloud provider, user accounts and authentication, persistent storage of alerts, "
          "and the quantum-inspired network and the enhanced elliptic-curve scheme of the base paper."),

        H2("1.7 Contributions"),
        N(f"A working platform that places authenticated encryption and ML intrusion detection around one cloud data path, with a console, an API and {F.PYTEST_TOTAL} automated tests.",
          f"A measured cost of protection: a protected 100 KB transfer takes {F.f2(ip['protected_transfer_100kb']['median_ms'])} ms in process, of which detection is {F.pct(ip['share_of_transfer_median']['ids'], 0)}; "
          "the cost is reported by payload size and compared with RSA-OAEP hybrids.",
          f"Tamper-resistance evidence: six tamper and key cases, 1,000 trials each, all behaving as expected, and no repeated nonce in 20,000 encryptions.",
          f"A real-data evaluation of the stacked detector: {F.mstd(off, 'stack', 'accuracy')} accuracy on the official UNSW-NB15 test set over five seeds, with XGBoost alone at "
          f"{F.mstd(off, 'xgb', 'accuracy')}, and {F.f3(pap['stack']['accuracy']['mean'])} under the base paper's protocol.",
          f"An explicit demonstration of the synthetic-data trap: the shipped synthetic-trained model scores {F.pct(F.SHIPPED['accuracy'])} on its own data and {F.pct(real['accuracy'])} on real flows."),

        H2("1.8 Limitations and Assumptions"),
        P("The conclusions of this report hold under the following limitations and assumptions."),
        B("The shipped default model is trained on a generated synthetic dataset; the real-trained bundle is an experiment kept under `experiments/`, not the default.",
          "The official UNSW-NB15 test set comes from a different capture period than its training set, which makes it harder than a random split; the detector produces many false alarms "
          f"on normal traffic at the default threshold (false-positive rate {F.f3(off['stack']['fpr']['mean'])}).",
          "Traffic is supplied as flow records or CSV rows; the system does not sniff packets, and it does not block or quarantine anything on its own.",
          "The cloud is a mock endpoint in the same process, with a key pair that lives only as long as the server process; there is no authentication, TLS or rate limiting.",
          "Alerts are kept in an in-memory list of at most 500 entries and are lost on restart; there is no database.",
          "Timings were measured on one shared Intel Core i5-12500 machine with 15.7 GB of memory and are indicative; no multi-user load, adversarial-evasion or browser-compatibility testing was done."),
        P("The base paper's enhanced elliptic-curve scheme and its quantum-inspired network are not reproduced; where this report compares with the base paper it says that the "
          "datasets, subsets and conditions differ."),

        H2("1.9 Organisation of the Report"),
        B("**Chapter 2** surveys the literature, analyses the base paper and states the research gap.",
          "**Chapter 3** studies feasibility; **Chapter 4** analyses the existing system and the requirements of the proposed one.",
          "**Chapter 5** presents the system design: architecture, data flow diagrams, UML, entities, modules and screens.",
          "**Chapter 6** describes the methodology and the software implementation: data, preprocessing, models, cryptographic protocol, API and security handling.",
          "**Chapter 7** reports system testing; **Chapter 8** reports results and output screens, with the comparison against the base paper.",
          "**Chapters 9 and 10** give the conclusion and the future scope, followed by the references and three appendices (important code, installation and user guide, additional screens)."),
    ]
