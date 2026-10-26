"""Chapter 1: Introduction (Mosaic, CSDS-A-A16)."""

from . import facts as F
from . import lit
from .blocks import B, FIG, H1, H2, N, P, TAB
from .refs import CITE as R


def blocks():
    fin, base = F.FIN, F.BASE
    comp = fin["compound_on_real_test"]
    syn = F.SYN["final_model"]["0.5"]
    gan = F.GAN
    return [
        H1("1. INTRODUCTION"),
        H2("1.1 Domain and Background"),
        P("Emotions shape how people communicate, and the face is one of the richest signals of emotional state. Facial expression recognition (FER) is therefore studied for "
          f"human-computer interaction, mental-health monitoring, driver-safety systems, smart classrooms and customer-experience analysis [{R['lideng']}]. The dominant way to frame the task is categorical: "
          f"following Ekman and Friesen [{R['ekman']}], a face is assigned one of six basic emotions (anger, disgust, fear, happiness, sadness and surprise), usually with a neutral class added, which gives the seven classes of the "
          f"FER2013 benchmark [{R['fer2013']}] used in this project."),
        P("Real expressions are often not that simple. A winner at a sports event may look both happy and tearful, and a person on a roller coaster may look both happy and frightened. "
          f"Du, Tao and Martinez [{R['du2014']}] showed that people routinely produce and recognise *compound* facial expressions, combinations of two basic emotions such as \"happily surprised\" or \"sadly angry\", "
          f"and the base paper of this project, Khine et al. [{R['base']}], argues that a six- or seven-class system \"oversimplifies emotional expression\" and proposes to estimate complex emotions as a multi-label problem."),
        P("The technical difficulty is data. Datasets with compound labels are small, and the large in-the-wild datasets that exist are labelled with a single category per face. "
          f"The base paper therefore uses *analysis by synthesis*: a conditional generative adversarial network [{R['cgan']}] (its cEmoGAN) is trained to generate faces for a requested mixture of emotions, and a recognition "
          "network is then trained on those generated faces with one sigmoid output per emotion, so that a single image can carry several labels at once."),
        P(f"This project builds {F.PRODUCT}, a complete, runnable application around that idea: a training pipeline (a seven-class backbone, a conditional GAN, and a final 18-output multi-label network "
          "trained on real and synthetic faces), a FastAPI service with accounts and history, and a Next.js web console in which a user uploads a photo or takes a webcam frame and sees a basic-emotion chart, "
          "compound-emotion scores and a dominant emotion."),
        P("Two design choices of the base paper are worth keeping in mind throughout the report. The first is that the recogniser is *multi-label*: instead of one softmax over seven classes it has one sigmoid per emotion, "
          "so \"happy\" and \"surprise\" can both be high at the same time and a compound class such as \"happily surprised\" can be added as one more output. The second is that the generator is conditional: a vector "
          "that says which emotions are present is fed to the generator, so the person building the training set controls what is produced. Mosaic keeps both choices and builds the compound label set from eleven pairs of basic emotions."),
        FIG(F.diag("01_system_architecture.png"), "System architecture of Mosaic: browser tier, FastAPI service, ML modules and local files.", 5.6),
        P("The figure shows the four tiers. The browser tier is a Next.js application; the FastAPI process owns the routers, token handling and the inference module; the ML modules detect the face, "
          "classify it and (at training time only) synthesise faces; SQLite, the checkpoint files and a folder of face thumbnails hold the state. Chapter 5 explains each tier."),
        H2("1.2 Motivation"),
        P("Three observations from the batch survey and the base paper motivate the work."),
        B("**Single-label systems cannot express mixtures.** A model with a softmax output must pick one class, so a face that is both happy and surprised is forced into one of them.",
          "**Compound-emotion data is scarce.** The base paper builds its compound ground truth by morphing two peak-expression images and then trains its generator on those morphs and uses it to generate new images, because labelled mixtures hardly exist.",
          "**Editing methods distort identity.** Expression-editing GANs can change the emotion but often change the person; the base paper's encoder-plus-conditional-GAN design is meant to keep the identity fixed while the label changes the expression."),
        P("A fourth, practical motivation is that published pipelines of this kind are rarely available as an end-to-end application that a non-specialist can run. Building one forces every stage to be "
          "made explicit and measurable: how many images go in, what the generator actually produces, and what the final network does on real photographs."),
        H2("1.3 Problem Statement"),
        P("The batch problem statement is reproduced here, followed by the engineering questions it raises."),
        B(*lit.PROBLEM_STATEMENT),
        P(f"*Need.* {lit.NEED}"),
        P("In engineering terms the project asks four questions. (1) Can a conditional GAN trained on a few thousand labelled faces produce faces that carry two emotions at once? (2) Does adding such faces "
          "to the training set give a multi-label network that recognises both basic and compound emotions? (3) How does that network compare with a single-label baseline on real faces? (4) Can all of this be "
          "delivered as an application that a user can operate from a browser? Chapters 6 to 8 answer these questions with measurements, including the answers that turned out to be negative."),
        H2("1.4 Need for the System"),
        B("Applications such as driver monitoring, well-being tools and customer-experience analytics need to know more than \"this person is happy\"; a mixture such as \"happily surprised\" or \"sadly fearful\" changes what the right response is.",
          "Researchers need a working reference implementation in which the synthetic-data step can be switched on and off, so that its effect can be measured rather than assumed.",
          "Students and practitioners need a documented, tested example of a face-analysis service that keeps uploaded photographs off disk and stores only a cropped grayscale thumbnail for signed-in users."),
        P("The need is also methodological. A claim such as \"the synthetic images improve recognition\" can only be tested by training the same network with and without them under the same seeds and evaluating on data the generator never "
          "saw. This report treats that as a requirement of the system, not an afterthought, and the measurement scripts that produce every number in Chapter 8 are part of the delivered code. A service that analyses faces also handles "
          "personal data, so the design stores no uploaded photograph, keeps only a cropped grayscale thumbnail for signed-in users, protects passwords with bcrypt, signs session tokens and lets a user delete any history entry."),
        H2("1.5 Objectives"),
        P("The five objectives of the batch (document 6) and where this report addresses each are listed below. Their measured status is given in Chapter 8."),
        TAB("Project objectives and where they are addressed", ["No.", "Objective", "Where addressed"],
            [[str(i), o, w] for i, (o, w) in enumerate(zip(lit.OBJECTIVES, [
                "Chapter 6 (cEmoGAN training and synthesis); Chapter 8 (generator fidelity)",
                "Chapter 6 (11 compound classes x 200 synthetic faces); Chapter 8 (sweep over 0, 50, 200 and 800 per class)",
                "Chapter 6 (18-output network and its training)",
                "Chapter 8 (baseline, seeded ablation, per-class results)",
                "Chapters 5 and 6 (API and web console); Chapter 7 (tests); Chapter 8 (output screens)"]), 1)],
            widths=[0.5, 3.6, 2.2], align=["c", "l", "l"]),
        H2("1.6 Scope of the Work"),
        P("**In scope.**"),
        B("Training, on a CPU, of a seven-class backbone, a conditional GAN and an 18-output classifier on FER2013 (28,709 training and 7,178 test images, 48 by 48 pixels, resized to 64 by 64).",
          "Synthesis of faces for eleven compound-emotion classes by conditioning the generator on two basic emotions at once.",
          "A FastAPI service with registration, login, optional-token analysis, history list, read and delete, a health check, and static thumbnails.",
          "A Next.js console with landing page, authentication pages, an upload and webcam analysis page and a history page.",
          "Measurements: basic-emotion accuracy and F1 with confusion matrices, a seeded ablation with and without synthetic faces, generator fidelity, compound-output behaviour, face-detection rate, API latency and abuse probes, and automated tests."),
        P("**Out of scope.** Identity-preserving encoders, video or temporal modelling, other modalities (voice, text, physiology), GPU training, deployment beyond a single machine and any claim "
          "of clinical or safety-critical validity. These are discussed again as limitations in Section 1.8 and in Chapter 10."),
        H2("1.7 Contributions"),
        N("An end-to-end, runnable implementation of the analysis-by-synthesis pipeline of the base paper: training scripts, 18-label taxonomy, API, database and web console, with a one-command training run.",
          "A seeded, controlled evaluation on FER2013 that isolates the effect of the synthetic images: the same network is trained with and without them, over three seeds, and compared with the single-label baseline.",
          "A measurement of the generator that the application depends on: how often a classifier recovers the requested emotion from its faces, and a feature-space distance to real faces.",
          "An honest account of the compound outputs: on real test faces their largest probability averages "
          f"{comp['mean_top_compound_confidence']:.4f}, and on {F.SYN['n']:,} synthetic compound faces their macro ROC-AUC is {syn['compound_roc_auc_macro']:.2f} (chance).",
          f"A tested service: {F.TESTS['tests']} automated tests, 24 abuse probes, latency measurements and a list of the defects found in the shipped application."),
        H2("1.8 Limitations and Assumptions"),
        P("Limitations that shape every result in this report are stated here once and revisited in Chapters 7, 8 and 10."),
        B(f"**No compound ground truth.** FER2013 carries one basic label per image, so the eleven compound outputs cannot be scored on real data; the only compound-labelled images are the synthetic ones the model was trained on.",
          f"**Small, low-resolution data and short training.** Faces are 48 by 48 pixels; the backbone, generator and final network were trained for 5, 10 and 5 epochs on a shared CPU. The generator saw only {2800:,} faces.",
          f"**The generator does not follow its condition.** A classifier recovers the requested basic emotion on {gan['mean_basic_conditional_accuracy'] * 100:.1f} % of generated faces (chance 14.3 %), and generated faces are blurry; "
          "identity preservation, which is the base paper's main generative contribution, is not implemented (there is no encoder).",
          "**Base-paper numbers are not comparable.** The base paper reports f-beta 0.99, 0.99 and 0.80 on CK+, JAFFE and MUG, measured on 7:3 splits of images generated by its own cEmoGANs. This project's test set is real FER2013 data.",
          "**Framing mismatch.** The network is trained on aligned 48 by 48 crops, but the service feeds it a Haar-cascade crop of the uploaded photograph."),
        P("The main *assumptions* are that FER2013 labels are correct enough to evaluate on (they are known to be noisy), that the Hugging Face copy of FER2013 matches the original partition, that users upload "
          "roughly frontal faces with one dominant face, and that a single machine without a GPU is the deployment target."),
        H2("1.9 Organisation of the Report"),
        TAB("Organisation of the report", ["Chapter", "Content"],
            [["1 Introduction", "Domain, motivation, problem, objectives, scope, contributions, limitations."],
             ["2 Literature Survey", "Base paper, related work by theme, datasets and algorithms, research gap."],
             ["3 Feasibility Study", "Technical, economic, operational and schedule feasibility."],
             ["4 System Requirements and Analysis", "Existing and proposed system, requirements, hardware, software, users."],
             ["5 System Design", "Architecture, workflow, data flow diagrams, UML, database, modules, user interface."],
             ["6 Methodology and Software Implementation", "Data, preprocessing, model, training, formulation, API, security, installation."],
             ["7 System Testing", "Strategy, unit, integration, functional, security, performance, edge cases, limits."],
             ["8 Results and Output Screens", "Output screens, model performance, ablation, generator fidelity, comparison, objectives versus outcomes."],
             ["9 Conclusion", "Summary, findings, applications, known limitations."],
             ["10 Future Scope", "Improvements, features, scalability, further research."],
             ["References and Appendices", "IEEE reference list; important code; installation and user guide; additional screens."]],
            widths=[2.3, 4.0], align=["l", "l"]),
    ]
