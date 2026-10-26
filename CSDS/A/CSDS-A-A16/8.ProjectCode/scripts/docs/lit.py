"""Literature and framing data for the decks (Review 1, Review 2, final), the chapters and the IEEE paper.

Every literature fact traces to the base-paper PDF (Documentary/), the archived PDFs in this batch (Galkaduwa 2026, Liu et al. 2024, Su and Rosdi 2026),
the abstract-level information recorded in refs.py (REF_NOTES), or the batch's own .docx files.  Batch-survey items [3] and [5] have verified
bibliographic records but no abstract could be read, so they are never quoted for results.  Reference numbers match refs.py (CITE keys).
"""
from . import facts as F
from .refs import CITE as R

BASE_PAPER_TITLE = "Complex Emotion Estimation Using Analysis-by-Synthesis of Facial Expression Images"
BASE_PAPER_VENUE = "W. S. S. Khine, P. Siritanawan, K. Kotani - IEEE Access, vol. 13, pp. 88731-88744, 2025"

# [work, year, approach, finding / limitation]   (each cell <= 95 characters)
LIT_TABLE = [
    [f"Khine et al. [{R['base']}] (base paper)", "2025", "cEmoGANs (encoder + conditional GAN, 6-d multi-hot label) generate mixed faces; CNN with sigmoid outputs",
     "f-beta 0.99 / 0.99 / 0.80 on CK+ / JAFFE / MUG, scored on generated images; qualitative tests only on real photos"],
    [f"Liu, Ni, Cai [{R['cdgan']}]", "2025", "CD-GAN: separate identity and expression encoders, contrastive + adversarial learning",
     "Abstract: comparable to state of the art on field and laboratory sets; single-label recognition"],
    [f"Ni et al. [{R['migan']}]", "2024", "Multi-level integration disentangled GAN for expression recognition (title only)",
     "Batch survey item; abstract not available, results not quoted"],
    [f"Khemakhem, Ltifi [{R['nstgan']}]", "2023", "NST-GAN: style-transfer GAN that removes identity cues, tested on CK+, FER-2013, JAFFE",
     "Single basic label per image; numbers not quoted (abstract only)"],
    [f"Zhou et al. [{R['facecycle']}]", "2024", "Transfer learning + Face-Cycle GAN for cross-domain recognition (title only)",
     "Batch survey item; abstract not available, results not quoted"],
    [f"Galkaduwa [{R['galkaduwa']}]", "2026", "HOG+SVM, LBP+LogReg and a light CNN on FER-2013, CK+ and KDEF",
     "FER-2013 accuracy: CNN 51.6 %, HOG+SVM 44.0 %, LBP 25.0 %; basic labels only"],
    [f"Liu et al. [{R['abaw7']}]", "2024", "ViT / PosterV2 / ResNet-50 ensemble for compound expressions (ABAW7), pre-trained on RAF-DB",
     "RAF-DB compound validation: accuracy 60.4-64.3 %, F1 51.5-55.4 % (7 classes); needs real compound labels"],
    [f"Du, Tao, Martinez [{R['du2014']}]", "2014", "Compound facial expressions of emotion: psychology study of mixed categories",
     "Defines the compound categories used by the base paper and by Mosaic's taxonomy"],
    [f"Li, Deng, Du [{R['rafdb']}]", "2017", "RAF-DB: crowd-sourced real-world faces including compound labels",
     "Source of real compound labels; licence on request (not available in this project)"],
    [f"Su, Rosdi [{R['su']}]", "2026", "Systematic review of 62 multimodal emotion-recognition studies (2020-2025)",
     "CNNs remain the main visual extractor; models heavy, poor generalisation across settings"],
]

# [work, approach, data, reported result, limitation]  - short cells for the IEEE paper's TABLE I
PAPER_TABLE = [
    [f"Khine et al. [{R['base']}]", "cEmoGANs + CNN, multi-label", "CK+, JAFFE, MUG (morphed pairs)", "f-beta 0.99/0.99/0.80", "Scored on generated faces"],
    [f"Liu et al. [{R['cdgan']}]", "Identity/expression disentangling GAN", "Lab and field sets", "Comparable to SOTA", "Single basic label"],
    [f"Khemakhem, Ltifi [{R['nstgan']}]", "Style-transfer GAN", "CK+, FER-2013, JAFFE", "Reported above baselines", "Single basic label"],
    [f"Galkaduwa [{R['galkaduwa']}]", "HOG+SVM vs. light CNN", "FER-2013, CK+, KDEF", "CNN 51.6 % on FER-2013", "Basic labels only"],
    [f"Liu et al. [{R['abaw7']}]", "ViT/PosterV2/ResNet ensemble", "RAF-DB compound, 7 classes", "Acc. 60.4-64.3 %, F1 51.5-55.4 %", "Needs real compound labels"],
    [f"Li, Deng [{R['lideng']}]", "Survey of deep FER", "Many datasets", "Taxonomy of methods", "Mostly single-label"],
]

# the five objectives of the batch (6.OBJECTIVES&PROBLEM STATEMENT.docx), shortened for status tables
OBJECTIVES = [
    "Generate identity-preserving facial images with complex emotions using cEmoGANs",
    "Enlarge the complex-emotion dataset with generated images",
    "Train a CNN multi-label classifier for basic and complex emotions",
    "Evaluate recognition performance against single-label baselines",
    "Provide an interface for emotion recognition from uploaded images",
]

PROBLEM_STATEMENT = [
    "Existing systems recognise only single basic emotions.",
    "Real expressions often contain several emotions at once.",
    "Complex-emotion training data is scarce.",
    "Expression-editing methods distort facial identity.",
]
NEED = "A system that generates realistic complex-emotion data and recognises multiple emotions in a single face."

# research gaps, stated from the batch survey and from what the sources above report
GAPS = [
    "Most facial emotion recognition handles only single basic emotions, and datasets with mixed-emotion samples are small (batch survey).",
    "The base paper scores its recogniser on images produced by its own generator; recognition of compound emotions on real photographs is shown only qualitatively.",
    "Few open implementations connect generation, multi-label training and an end-user application, and the effect of the synthetic images on a real test set is rarely isolated with a no-synthesis control.",
]
