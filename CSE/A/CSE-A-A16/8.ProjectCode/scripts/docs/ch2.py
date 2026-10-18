"""Chapter 2: Literature survey."""

from . import facts as F
from .blocks import B, EQ, H1, H2, H3, N, P, TAB
from .lit import LIT_TABLE


def blocks():
    return [
        H1("CHAPTER 2: LITERATURE SURVEY"),

        H2("2.1 Overview"),
        P("This chapter reviews the work on which SignSpeak builds and against which it must be judged. It starts with the base paper assigned to the batch [1], analyses it in "
          "detail, and then groups related work by theme: early and sensor-based recognition, image-based CNN recognition of the manual alphabet, video and skeleton methods, "
          "translation, and model compression. It then describes the dataset and the algorithms that SignSpeak itself uses, summarises the strengths and limitations of the "
          "approaches, lists the additional sources named in the project's literature survey, and ends with the research gap."),
        P("Two comments on method. Numerical results are quoted only where we read them in the paper itself (this holds for the base paper, from which we extracted the "
          "figures directly) or where the reference list of the base paper states the bibliographic details. For the other works the table gives the approach and the "
          "stated limitation without reproducing accuracy figures that we did not verify."),

        H2("2.2 Analysis of the Base Paper"),
        P("The base paper is \"MAG-KD: Mask-Guided Adaptive Gating Knowledge Distillation for Skeleton-Based Sign Language Recognition on Edge Devices\" by Vo, Nguyen, Nguyen and Vo, "
          "published in IEEE Access in 2026 [1]. Its subject is not the recognition of single hand shapes but the recognition of signs in video with a graph convolutional network "
          "(GCN) that works on a skeleton - the coordinates of body, arm and hand joints extracted from each frame by a pose estimator."),
        H3("Problem and idea"),
        P("Skeleton-based GCNs, beginning with ST-GCN [11], are efficient and largely indifferent to background, but the strongest models are large. Knowledge distillation [12] "
          "compresses a large teacher network into a small student that imitates the teacher's output probabilities. The authors argue that existing multi-teacher distillation "
          "assumes that teachers are always right, whereas skeletons from pose estimators (the paper names HRNet and MediaPipe [13]) are noisy because of missing joints, jitter and "
          "self-occlusion, so teachers are sometimes confidently wrong and the student copies the error - a failure called negative transfer."),
        P("MAG-KD therefore has two mechanisms. A hard correctness mask compares each teacher's top prediction with the ground-truth label and sets the teacher's weight to zero "
          "when it is wrong. An adaptive gating network - a small multilayer perceptron over the student's pooled features and the teachers' logits - assigns the remaining "
          "teachers their importance, and the masked weights are renormalised so that they sum to one. Distillation is decoupled: intermediate features are aligned by static "
          "averaging with a mean-squared-error loss, while the logits are distilled with the gated Kullback-Leibler loss. The input is modelled as a spatio-temporal graph of 27 "
          "keypoints per frame, with the usual graph-convolution update"),
        EQ("H(l+1) = sigma( sum_j  D~_j^(-1/2) A~_j D~_j^(-1/2) H(l) W_j(l) )"),
        P("and the gated weight of teacher m for sample i is w_m,i = (w_raw_m,i x M_m,i) / (sum_j w_raw_j,i x M_j,i + epsilon), where M is the binary correctness mask [1]."),
        H3("Experimental set-up reported"),
        P("The teachers are SL-GCN, CTR-GCN and TD-GCN, frozen and pre-trained; the student is the lightweight STA-GCN. Training used PyTorch 2.1.2 on one NVIDIA RTX A4000 with SGD "
          "(Nesterov momentum 0.9, weight decay 1e-4), batch size 64, 150 epochs, initial learning rate 0.1 divided by 10 at epochs 60, 90 and 120. The distillation temperature was 4, "
          "both loss coefficients were 1.0, and runs used seeds 1, 42 and 100. The gating module raised the training time per epoch from 82.5 s to 188 s, a cost paid only during "
          "training. For deployment the student was exported to ONNX and compiled to a TensorRT FP16 engine on a Jetson Nano (4 GB, 10 W MAXN mode)."),
        P("Two datasets were used. AUTSL [14] holds 38,336 Turkish Sign Language videos from 43 signers in 20 backgrounds covering 226 sign classes, recorded with a Kinect V2. "
          "WLASL-100 [15] is a 100-class subset of the word-level ASL dataset, with 1,442 training and 596 validation videos."),
        H3("Results reported"),
        TAB("Results of the base paper [1] (as stated in the paper)", ["Item", "Reported value"], [
            ["AUTSL Top-1, MAG-KD student (0.48 M parameters, mean of three seeds)", "94.25 % +/- 0.19"],
            ["WLASL-100 Top-1, student baseline STA-GCN", "54.92 % +/- 0.77"],
            ["WLASL-100 Top-1, MAG-KD", "66.33 % +/- 0.54 (+11.41 points)"],
            ["AUTSL ablation: correctness mask removed", "85.30 % (a drop of 8.95 points)"],
            ["AUTSL: soft mask instead of hard mask", "94.20 % (hard mask 94.25 %)"],
            ["Jetson Nano: throughput and power", "33.13 FPS at 6.23 W"],
            ["Training time per epoch, baseline versus MAG-KD", "82.5 s versus 188 s"],
        ], widths=[4.3, 2.0], align=["l", "l"]),
        H3("Strengths and stated limits"),
        P("The paper is careful in several respects: results are averaged over three seeds with standard deviations, an ablation isolates the mask, a second dataset tests "
          "language independence, and the edge measurements (latency, power, utilisation, model size) are made on real hardware with a warm-up phase. The authors themselves state "
          "two limits: the correctness mask needs ground-truth labels, which rules out semi-supervised use, and the whole system is bottlenecked by the latency and accuracy of the "
          "upstream pose extractor in difficult environments [1]."),
        H3("Relation to SignSpeak"),
        P("It is important to be precise about what SignSpeak takes from this paper and what it does not. SignSpeak does not implement knowledge distillation, graph convolution, "
          "skeleton extraction or TensorRT export, and it does not recognise word signs from video. What it shares with the base paper is the motivation - a sign language "
          "recogniser should run in real time on modest hardware and be usable outside a laboratory - and the observation that background and pose noise are the practical enemies "
          "of recognition. SignSpeak answers with a different modality (a segmented single-hand image classified by a small CNN) for a different task (the static manual alphabet). "
          "For that reason the numbers of the two works are not comparable, and Chapter 8 presents the comparison as context only."),

        H2("2.3 Related Work by Theme"),
        H3("2.3.1 Early and sensor-based recognition"),
        P("Starner, Weaver and Pentland recognised sentence-level ASL in real time from a desk-mounted camera or a camera worn on the body, using hidden Markov models [4]; the system worked "
          "with a restricted vocabulary and grammar. Pugeault and Bowden used a Kinect sensor, which provides colour and depth, to read fingerspelled letters in real time [5]. "
          "These works show that fingerspelling is recognisable live, but they depend on special sensors or controlled settings."),
        H3("2.3.2 CNN recognition of the manual alphabet from images"),
        P("After CNNs became the standard for image classification [7], [8], several authors applied them to static ASL images. Bheda and Radpour used a deep convolutional "
          "network to classify images of ASL letters and digits [6]. The public ASL Alphabet archive on Kaggle [25] made this setting easy to reproduce and is the data source "
          "used here. The survey by Rastgoo et al. [3] and the review by Al Abdullah et al. [2] place this static, image-based setting in the wider field and list its recurring "
          "difficulties: background clutter, lighting, similar hand shapes (for example the closed-fist letters A, E, M, N, S and T) and dependence on the signer."),
        H3("2.3.3 Video and skeleton methods"),
        P("Word-level and continuous recognition needs motion. Three-dimensional convolutions [9], inflated 3D networks [10] and recurrent models process RGB video directly, at a high "
          "computational cost. Skeleton-based graph networks such as ST-GCN [11] and its successors operate on joint coordinates and are much cheaper. Pose extraction frameworks "
          "such as MediaPipe [13] supply the skeletons. Large benchmarks - AUTSL [14] and WLASL [15] - allow these methods to be compared, and the base paper is a current "
          "representative of the line [1]."),
        H3("2.3.4 Translation of signing into text"),
        P("Camgoz et al. posed sign language translation as a sequence-to-sequence problem that maps sign video to spoken-language sentences [16]. This is the long-term "
          "direction of the field; the present project is a small first step at the letter level, followed by a sentence builder that is rule-based rather than learned."),
        H3("2.3.5 Efficiency and model compression"),
        P("Edge deployment motivates compression. Knowledge distillation [12] trains a small student on the soft outputs of a large teacher, and the base paper extends it to "
          "multiple noisy teachers [1]. SignSpeak takes the other route to efficiency - a model that is small from the start (2.2 million parameters, 26.48 MB) - and reports "
          "what that achieves on a CPU."),
        TAB("Comparison of the surveyed work", ["Work", "Approach", "Data", "Reported result", "Limitation"], [list(r) for r in LIT_TABLE],
            widths=[1.15, 1.45, 1.1, 1.3, 1.1], size=9, align=["l", "l", "l", "l", "l"]),

        H2("2.4 Datasets and Algorithms Used in This Project"),
        P("The dataset is the Kaggle ASL Alphabet archive [25]. The copy used here holds 87,000 training images in 29 folders of 3,000 images (A-Z, space, del, nothing) of 200 x 200 "
          "pixels, and a separate test folder of 28 images. A working set of 250 evenly spaced images per class, 7,250 in all, is used for training and evaluation. The archive "
          "is derived from video, which is why neighbouring images are almost identical."),
        P("The algorithms are standard and are cited to their sources. Segmentation uses Gaussian smoothing and Otsu's threshold [17], which chooses the grey level that maximises the "
          "between-class variance of the histogram, followed by morphological opening and closing [18]. Classification uses a CNN whose layers are convolution, batch "
          "normalisation [19], max pooling and dropout [20], ending in a softmax over 29 classes. The network is trained with the Adam optimiser [21] on augmented images [22], "
          "using TensorFlow and Keras [23], [26]; OpenCV [24] supplies the image operations and FastAPI [27] the web service. The mathematical form of each is given in Chapter 6."),

        H2("2.5 Strengths and Limitations of the Surveyed Approaches"),
        TAB("Approach families compared", ["Family", "Strengths", "Limitations for a live letter recogniser"], [
            ["Special sensors (depth, gloves)", "Robust to background and lighting", "Extra hardware; not available on a normal laptop"],
            ["Static-image CNN", "Simple, fast, trains from labelled photos", "Sensitive to background, orientation and signer; letters only"],
            ["RGB video with 3D CNNs", "Captures motion; handles words", "Heavy computation; needs large video datasets"],
            ["Skeleton GCNs [1], [11]", "Cheap; background-invariant", "Depends on a pose estimator; noise from occlusion"],
            ["Distilled students [1], [12]", "Small and fast at test time", "Needs trained teachers and labels; complex training"],
        ], widths=[1.6, 2.1, 2.6], align=["l", "l", "l"]),

        H2("2.6 Sources Named in the Project Survey"),
        P("The batch literature survey (5.LITERATURE SURVEY) lists five papers, the base paper and four others. For the four others it records only the title, the year and the "
          "venue. We were not able to verify their authors or findings, so we list them but do not quote results from them; they are not used as evidence anywhere in this report."),
        TAB("Additional sources named in the project literature survey", ["Title as recorded", "Year", "Source as recorded", "Reference"], [
            ["Sign Language Recognition", "2024", "Sign Language Processing", "[28]"],
            ["Gesture Recognition For Sign Language With AI", "2024", "not recorded", "[29]"],
            ["Implementation Of A Dynamic Gesture Recognition Based Indian Sign Language", "2024", "i-manager's Journal on Pattern Recognition", "[30]"],
            ["Translation Independent Gesture Recognition System for Multilingual Sign Language", "2025", "not recorded", "[31]"],
        ], widths=[3.3, 0.6, 1.7, 0.7], align=["l", "c", "l", "c"]),

        H2("2.7 Research Gap"),
        P("The survey shows a field that has moved from image classifiers towards skeleton-based and distillation methods for accuracy and efficiency [1]. Four gaps follow, "
          "and they define what SignSpeak sets out to do."),
        N("Few openly available projects deliver the whole chain from live camera to spoken sentence; most report a model and a number. This is the gap named in the batch survey.",
          "Static-image systems rarely report latency, a rejection rule or robustness to rotation and lighting, so their usefulness in a live setting is unknown.",
          "Results on frame-derived alphabet data are often reported without noting that neighbouring frames are near-duplicates, which inflates apparent accuracy.",
          "An inspectable, reproducible workflow (collect, train, evaluate, recognise) in one tool is uncommon, although it is what lets a teacher or a student retrain the model on new signers."),
        P("SignSpeak addresses the first, second and fourth gaps by construction and the third by measurement: it reports the held-out split as the headline and labels the other "
          "figure as optimistic. It does not address word-level recognition or unseen-signer generalisation, and Chapter 10 lists these as future work."),
    ]
