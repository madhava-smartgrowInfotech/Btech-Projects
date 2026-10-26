"""Chapter 2: Literature survey."""

from . import facts as F
from . import lit
from .blocks import B, H1, H2, P, TAB
from .refs import N as C


def blocks():
    out = _blocks()
    if F.REPORT:   # compact report variant: shorter comparison table
        from .ch1 import trim
        keep = ("base", "ijedr", "geo", "mega", "sirius", "plutus", "rbac01", "audit99")
        out = trim(out, replace={"The works surveyed are cryptographic": ("p", "The surveyed works are cryptographic and systems papers, so they have no training datasets; what they share is a set of primitives and standards, listed with the parameters this project uses in the next table."), "Evaluation set-ups reported": None, "Comparison of the surveyed work": (
            "tab", "Comparison of the surveyed work", ["Work", "Approach", "Reported result", "Limitation"],
            [[r[1], r[2], r[4], r[5]] for r in lit.ROWS if r[0] in keep],
            [1.1, 2.3, 1.6, 1.5], ["l", "l", "l", "l"], 8.5)})
    return out


def _timing_rows():
    pi = lit.BASE_ANALYSIS["numbers"]["primitives_pi_us"]
    hp = lit.BASE_ANALYSIS["numbers"]["primitives_hpe_us"]
    return [[k, str(pi[k]), str(hp[k])] for k in pi]


def _blocks():
    ba = lit.BASE_ANALYSIS
    nb = ba["numbers"]
    prop = nb["proposed_us"]
    tot = nb["compared_totals_us"]
    return [
        H1("CHAPTER 2: LITERATURE SURVEY"),
        H2("2.1 Overview"),
        P("The survey follows the four bodies of work that the project joins: storage systems that treat the server as untrusted, access-control models and cryptographic enforcement of them, "
          "key management and the primitives that protect keys and files, and tamper-evident audit logging. A fifth thread, the measurements that these works report, is examined at the end because it decides what can and cannot be compared. "
          f"The base paper {C('base')} is analysed in depth in Section 2.2; every statement about it in this report was checked against the paper itself, which is in the batch folder. "
          "Statements about the other works come from their own papers, abstracts, standards pages or DOI records and are limited to what those sources say."),
        P("The batch literature survey (5.LITERATURE SURVEY.docx) lists five works: the base paper, three titles from 2026 on AES-based cloud storage, data-integrity and access-control storage, and chaotic-map image encryption, "
          f"and Geocrypt {C('geo')}. We searched for each by title. Geocrypt was located and is described below. The other three could not be found online, so they are listed in the reference list as the batch gives them "
          f"({C('s2', 's3', 's4')}) and no claim is made about their content. In their place we added the paper that is closest in architecture to this project, a 2026 IJEDR article on zero-trust file storage {C('ijedr')}, "
          f"which is present in the batch folder and was read in full, and the classic and standards-level sources on which the design rests. (The repository note `archived_base_papers/BASEPAPER_REFERENCES.md` also names that IJEDR paper as the best architectural match; "
          "the batch documents name the health-record paper as the base paper, and that is the one analysed as such here.)"),
        H2("2.2 Base Paper Analysis"),
        P(f"**Reference.** {F.BASE_PAPER}"),
        P("**Problem and method.** " + ba["summary"]),
        P("**Reported numbers and how they were obtained.** The paper's evaluation does not run a storage system. It lists the measured time of each primitive operation in OpenSSL on two machines, "
          f"{nb['hpe']}, and {nb['pi']}, and then multiplies these by the number of operations each scheme needs. Table 3 of the paper (reproduced in the next table, in microseconds) gives the primitive timings. "
          f"For the setting {nb['setting']}, the proposed scheme costs about {prop['encryption']} microseconds for encryption, {prop['decryption']} for decryption and {prop['total']} in total, which is roughly {prop['total_x5']:,} microseconds "
          f"at x = 5, while the compared attribute-based schemes total between {min(tot):,} and {max(tot):,} microseconds in the paper's comparison. The paper reports no dataset, no accuracy for the attribute-extraction step, "
          "no upload or download time and no cost for the ledger or for access checks."),
        TAB("Primitive timings reported in Table 3 of the base paper (microseconds per operation, OpenSSL)", ["Operation", "Raspberry Pi 3 B+", "HPE server"],
            _timing_rows(), widths=[3.0, 1.6, 1.6], align=["l", "r", "r"], size=10),
        P("**Strengths.**"),
        B(*ba["strengths"]),
        P("**Limitations relevant to this project.**"),
        B(*ba["limitations"]),
        P("**What this project adopts and what it does not.** The project adopts the trust model, the plaintext-hash check after decryption, the view that revocation and auditing belong to the design, and the habit of reporting cost per primitive."),
        B(*ba["adopts"]),
        P("It does not adopt the machinery:"),
        B(*ba["not_adopts"]),
        P("**Comparability.** " + ba["comparability"]),
        H2("2.3 " + lit.THEMES[0][0]),
        P(lit.THEMES[0][1]),
        H2("2.4 " + lit.THEMES[1][0]),
        P(lit.THEMES[1][1]),
        H2("2.5 " + lit.THEMES[2][0]),
        P(lit.THEMES[2][1]),
        H2("2.6 " + lit.THEMES[3][0]),
        P(lit.THEMES[3][1]),
        H2("2.7 " + lit.THEMES[4][0]),
        P(lit.THEMES[4][1]),
        P("The next table sets the surveyed works side by side. The entries state only what the paper, its abstract or the standards page says, and the limitation column records what the source does not address, not a judgement of its quality."),
        TAB("Comparison of the surveyed work", ["Work", "Approach", "Data", "Reported result", "Limitation"],
            lit.rows(), widths=[0.9, 1.7, 0.9, 1.4, 1.2], align=["l", "l", "l", "l", "l"], size=8),
        H2("2.8 Primitives, Standards and Evaluation Data Used in Related Work"),
        P("The works surveyed are cryptographic and systems papers, so they have no training datasets. What they share is a set of primitives and standards, and a set of evaluation set-ups. "
          "The primitives used by this project, and the standard that defines each, are given in the next table; the evaluation set-ups of the two closest papers are given in the table after it."),
        TAB("Primitives used by CipherVault and the sources that define them", ["Purpose", "Primitive", "Parameters in this project", "Source"],
            [["File encryption", "AES-256 in Galois/Counter Mode", "random 256-bit key and 96-bit IV per write; 16-byte tag", f"{C('aes')}, {C('gcm')}"],
             ["Key wrapping", "RSA-OAEP with SHA-256", "2048-bit modulus; 256-byte wrapped key", f"{C('oaep')}, {C('oaep94')}"],
             ["Private-key protection", "PBKDF2-HMAC-SHA-256 then AES-GCM", f"{F.PBKDF2_ITER:,} iterations, 16-byte salt", f"{C('pbkdf2')}, {C('sp800132')}"],
             ["Plaintext integrity and audit chain", "SHA-256", "hash of plaintext; chained entry hashes", f"{C('sha')}"],
             ["Password storage", "bcrypt", f"cost factor {F.BCRYPT_COST}", f"{C('bcrypt')}"],
             ["Sessions", "JSON Web Token, HS256", f"{F.JWT_MINUTES}-minute expiry", f"{C('jwt')}"],
             ["Browser crypto interface", "Web Cryptography API", "SubtleCrypto in Chrome", f"{C('webcrypto')}"],
             ["Access model", "Owner / Editor / Viewer roles", "checked on every request", f"{C('rbac96')}, {C('rbac01')}"]],
            widths=[1.4, 1.7, 1.9, 1.0], align=["l", "l", "l", "l"], size=9),
        TAB("Evaluation set-ups reported by the two closest papers", ["Item", f"Base paper {C('base')}", f"IJEDR paper {C('ijedr')}"],
            [["Kind of evidence", "calculated cost from operation counts and primitive timings", "reported system-level outcomes"],
             ["Hardware", "HPE server (E5-2620 v3, 32 GB) and Raspberry Pi 3 B+", "not stated"],
             ["Workload", "x = 5 attributes, l = 10, r = 30", "50 users in 3 roles; 900 access attempts; 30-day test; 50 tamper events"],
             ["Headline result", f"about {prop['total_x5']:,} us total at x = 5 (Pi)", "+320 ms for a 10 MB upload; 98.6% access accuracy; 100% of 50 tamper events detected"],
             ["Key parameters", "160-bit elliptic curve, 23 protocol phases", "PBKDF2 with 310,000 iterations; 4 MB chunks; TOTP; ECDSA-signed log entries"]],
            widths=[1.3, 2.4, 2.4], align=["l", "l", "l"], size=9.5),
        H2("2.9 Strengths and Limitations of Existing Research"),
        P("The existing work is strong where each paper is narrow. Attribute-based encryption gives fine-grained policies with no key escrow. The cryptographic storage systems of the 2000s showed how to split read and write "
          "access and how to keep servers blind. The standards give precise, reviewed definitions of the primitives, and the work on tamper-evident logging gives sound constructions for audit trails. "
          "The recent file-storage papers show that the client-side hybrid design can be put into practice with commodity components."),
        P("Their limitations are the other side of the same focus. The attribute-based schemes are heavy, depend on key-generation infrastructure and are evaluated analytically. The classic systems are file-system clients, not web applications, "
          "and most do not include a tamper-evident audit trail. The role-based models say nothing about keys. The audit-log constructions are separate from the storage systems that need them. The recent file-storage papers report "
          "outcomes that cannot be reproduced or judged because hardware, timings and methods are missing. Most importantly for a student implementation, a design that is complete on paper still leaves open how it behaves under real load "
          "and where it fails; for example, none of the works read here reports what happens to a hash-chained log when many writers append at once."),
        H2("2.10 Research Gap"),
        P(lit.GAP),
        P("The project responds to this gap by implementing the whole design, measuring every layer on one documented machine, and publishing both the successes and the defects found. "
          "The objectives of Section 1.5 follow directly from the four statements of the problem: encryption before storage, role enforcement, integrity checking on retrieval, and a verifiable audit log, together with an evaluation."),
    ]
