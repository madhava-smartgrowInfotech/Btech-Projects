"""Chapter 1 sections (Introduction) shared by the chapter documents and the full report."""
from __future__ import annotations

from doc_common import CV, LAT, PRODUCT, R, T, X, p


def sec_domain(d):
    d.h2("Domain Overview")
    d.p("Phishing is a form of social engineering in which an attacker imitates a trusted organisation, such as a bank, a shop, a mail provider "
        "or a government service, to make a victim reveal credentials, payment details or other personal data [20]. The attack usually "
        "ends in a web page: the victim receives a message, follows a link, and meets a page that looks like the real site. The link is therefore "
        "the single artefact that every phishing campaign needs, and it is the object that this project analyses.")
    d.p("Defending against phishing at the link level is attractive because the Uniform Resource Locator (URL) is small, always available "
        "and cheap to inspect. A URL can be examined before the page is fetched, which keeps the victim away from malicious content and "
        "avoids the cost and risk of downloading it. The weakness of the approach is that attackers choose the URL. They register new "
        "domains, hide the brand name inside sub-domains or paths, add credential-related words, and abandon a domain within hours. Any "
        "defence has to keep up with that speed.")
    d.p("Three families of defence are in common use. Blacklists such as those behind browser warnings record URLs that someone has already "
        "reported. Rule-based filters flag fixed patterns such as an IP address in place of a host name. Machine-learning (ML) classifiers "
        "learn the difference between phishing and legitimate URLs from labelled examples [18], [19]. Each has a known limit: a blacklist is "
        "blind to a URL that has not been reported yet, a fixed rule is easy to evade, and a classifier trained once ages as attack "
        "patterns change [1].")
    d.h3("Why combine machine learning with community reports")
    d.p("The base paper of this project argues that the weaknesses are complementary [1]. A classifier can score a URL that has never been "
        "seen, and it needs no list. A community of users and public threat feeds can recognise a new attack within hours, before a model "
        "could learn from it, and can also point out when a classifier is wrong. Feeding confirmed community verdicts back into the "
        "classifier closes the loop. This is the design that PhishGuard implements.")


def sec_motivation(d):
    d.h2("Background and Motivation")
    d.p("The base paper reports that phishing affects more than 83 % of businesses and cost companies about USD 17.4 billion in 2024 [1]. "
        "Those figures come from the paper's own sources and are quoted here as context, not as results of this project. What matters for "
        "this work is the pattern that the paper describes in its introduction: most published detectors reach very high accuracy on a static "
        "benchmark, yet they are trained once, they have no structured way to take in new attacks, and they do not turn user reports into "
        "training data [1].")
    d.p("The motivation of the project is to show that the three-stage idea of the base paper can be built end to end with ordinary tools, "
        "run on an ordinary computer, and be inspected by its users. The aim is a working system, not a larger benchmark score. The project "
        "therefore chose interpretable URL features, three classical classifiers that train in seconds, a transparent vote-based community store, "
        "and a web interface that explains every verdict.")
    d.bullets(["**Speed of attacks.** New phishing domains appear daily and many live only a few hours, so any list is behind.",
               "**Reachability of the evidence.** Only the URL is needed. No page is downloaded, so the check is fast and safe.",
               "**Human knowledge.** Users and security communities notice attacks first; the system should be able to use that knowledge at once.",
               "**Trust.** A verdict is only useful if the user can see why it was given, so the system lists red flags and the reason."])


def sec_problem(d):
    d.h2("Problem Statement")
    d.p("Phishing websites continue to steal user credentials and financial data at scale. Blacklist-based methods cannot detect newly created, "
        "zero-day phishing URLs. Static rules and one-time-trained models fail as attack patterns evolve, and high false-positive rates in "
        "existing filters block legitimate websites and reduce user trust.")
    d.p("**Need.** An adaptive phishing detection system that classifies unseen URLs with machine learning and stays current through "
        "crowdsourced threat intelligence.")
    d.p("**Formal statement.** Given a URL string u, produce a verdict in {phishing, suspicious, safe} with a probability and a human-readable "
        "explanation, using (i) a classifier trained on labelled URLs and (ii) a store of community-confirmed verdicts that can override the "
        "classifier and can be added to its training data; and make the system available through a web interface that answers in real time.")


def sec_need(d):
    d.h2("Need for the System")
    d.bullets(["Blacklists miss zero-day URLs, so a learned model is needed for URLs that no one has reported.",
               "A model alone cannot know about a campaign that started this morning, so a community channel is needed.",
               "A model alone will sometimes be wrong about a legitimate site, so the community must also be able to say \"this one is safe\".",
               "Retraining by hand is slow, so the system must retrain itself from confirmed reports and load the new model without a restart.",
               "Users do not trust a bare label, so every verdict must come with its reasons."])


def sec_objectives(d):
    d.h2("Objectives")
    d.p("The six objectives set at the start of the project, and the part of the system that addresses each, are listed below. How far each "
        "was achieved is assessed in Chapter 8 and Chapter 9.")
    d.table([["No.", "Objective", "Where it is implemented"],
             ["1", "Collect and preprocess a dataset of phishing and legitimate URLs", "data/urls_sample.csv (40,000 URLs); phishguard/data.py"],
             ["2", "Extract lexical, structural and domain-based URL features", "phishguard/features.py (47 features)"],
             ["3", "Train and compare Random Forest, XGBoost and Logistic Regression", "phishguard/train.py"],
             ["4", "Integrate crowdsourced threat intelligence for newly reported phishing URLs", "phishguard/threat_intel.py; decision order in detector.py"],
             ["5", "Refine the model continuously as new threat data arrives", "phishguard/retrain.py; hot reload in detector.py"],
             ["6", "Provide real-time URL classification through a simple web interface", "Flask API (port 8103) and React UI (port 5103)"]],
            "Project objectives and where each is implemented", widths=[0.07, 0.5, 0.43], font=10)


def sec_scope(d):
    d.h2("Scope of the Project")
    d.h3("In scope")
    d.bullets(["Classification of a single URL or a pasted or uploaded batch of up to 100 URLs, in real time.",
               "47 offline URL features in three groups, with a plain-language list of red flags.",
               "Comparison of three classifiers on one 40,000-URL dataset with a fixed 80/20 split, plus 5-fold cross-validation.",
               "A SQLite store of community reports with vote counting, consensus, and optional import from two public feeds.",
               "Retraining from confirmed reports, with automatic reload of the new model.",
               "A React web interface (seven pages) over a Flask JSON API, a command-line interface, and the original Flask pages."])
    d.h3("Out of scope")
    d.bullets(["Downloading or rendering the page behind a URL, and any WHOIS, DNS or certificate lookup.",
               "E-mail, SMS or attachment analysis, and image or logo comparison of the page.",
               "User accounts, authentication, moderation workflows and administrator verification of reports.",
               "Browser extensions, mail-gateway plug-ins and deployment at internet scale.",
               "Deep-learning models; the base paper's LSTM network is not reproduced."])


def sec_contrib(d):
    d.h2("Key Contributions")
    d.numbered([
        "A complete, working implementation of the base paper's three-stage design (feature extraction, ML classification, crowdsourced refinement) that runs offline on one Windows computer.",
        f"A 47-feature offline URL extractor (23 lexical, 9 structural, 15 domain) with human-readable red flags; extraction takes {LAT['feature_extraction_ms_per_url']:.2f} ms per URL.",
        f"A controlled comparison of Random Forest, XGBoost and Logistic Regression: the selected XGBoost model reaches F1 {p(X['f1'])} and ROC-AUC {X['roc_auc']:.3f} on 8,000 held-out URLs and F1 {p(CV['xgboost']['f1']['mean'])} in 5-fold cross-validation.",
        "A transparent crowdsourced threat-intelligence store: vote-based consensus, trusted public feeds, and a decision order in which a confirmed community verdict, phishing or safe, overrides the model immediately.",
        "A retraining loop that merges confirmed URLs into the training data with a weight of three and hot-reloads the new model; it was exercised end to end on real feed data (model version 1 to 2).",
        f"A measured, honest evaluation: feature-group ablation, threshold sweep, learning curve, a crowd-feedback experiment that shows what retraining does and does not change, and {T['total']} extra automated checks.",
        "A seven-page React interface and a JSON API that make the whole pipeline usable and demonstrable, with documented limits."])
    d.p("The novelty of the project against the base paper is discussed in Chapter 2 and in the methodology document; the contributions above "
        "are of an engineering and evaluation kind, and are not claimed to beat the base paper's reported accuracy.")


def sec_limits(d):
    d.h2("Limitations and Assumptions")
    d.h3("Assumptions")
    d.bullets(["A URL string carries enough lexical, structural and domain evidence to separate most phishing from legitimate pages.",
               "The labels of the 40,000-URL dataset are correct and its two classes are drawn from representative sources.",
               "Community reporters act in good faith; two net votes are treated as sufficient confirmation.",
               "The user runs the system locally, where network and disk access are trusted."])
    d.h3("Limitations")
    d.bullets([f"The dataset has 40,000 URLs from one source; the base paper used 235,804 URLs, so the two accuracy figures are not comparable.",
               "Only URL text is used. A phishing page hosted on a clean-looking domain will often be missed (311 of 4,000 phishing URLs in the test set).",
               "The popular-domain list is hand-written (145 names), so some legitimate sites are flagged; two such cases were observed (docs.python.org and amazon.in).",
               "Community verdicts are anonymous votes with no reputation, rate limit or administrator review; one actor can file two reports.",
               "A confirmed phishing URL also marks every other URL on the same host as phishing, which over-blocks shared hosting.",
               "The application has no sign-in; anyone who can reach it can report URLs and trigger retraining.",
               "Retraining on random in-distribution URLs did not change the average score; the benefit on genuinely new attack campaigns could not be measured with a static dataset.",
               "No load, concurrency or user-acceptance testing was carried out."])


def sec_organisation(d):
    d.h2("Organisation of the Report")
    d.table([["Chapter", "Title", "Content"],
             ["1", "Introduction", "Domain, motivation, problem, objectives, scope, contributions, limits"],
             ["2", "Literature Survey", "Base paper analysis, related work, datasets, algorithms, research gap"],
             ["3", "Feasibility Study", "Technical, economic, operational and schedule feasibility"],
             ["4", "System Requirements and Analysis", "Existing and proposed system, requirements, platform, roles"],
             ["5", "System Design", "Architecture, workflow, DFDs, UML, database, modules, user interface"],
             ["6", "Methodology and Software Implementation", "Dataset, preprocessing, algorithms, training, application, API, security, installation"],
             ["7", "System Testing", "Strategy, unit, integration, functional, security, validation, performance, limits"],
             ["8", "Results and Output Screens", "Output screens, model results, comparison with the base paper, failure analysis"],
             ["9", "Conclusion", "Summary, objectives achieved, findings, applications, limitations"],
             ["10", "Future Scope", "Improvements, features, deployment, research directions"]],
            "Organisation of the report", widths=[0.1, 0.32, 0.58], font=10)
    d.p(f"Appendix A lists the important code, Appendix B the installation and user guide, and Appendix C additional screens. "
        f"All figures quoted for {PRODUCT} come from `docs/REPORT_FACTS.md` and the measurement files in `docs/experiments/`.")
