"""Shared text used by the decks, the chapter documents, the report and (in condensed form) the paper: objectives, problem statement, literature table."""

# from 6.OBJECTIVES&PROBLEM STATEMENT.docx, verbatim
OBJECTIVES = [
    "Assemble a labelled dataset of healthy and diseased crop leaf images across target crops.",
    "Preprocess and augment the images to handle variation in lighting, angle and background.",
    "Train a CNN model to classify leaf images into specific disease categories.",
    "Map each identified disease to a treatment and fertiliser recommendation.",
    "Deliver diagnosis and advice through a web interface with multilingual support.",
    "Evaluate classification accuracy per disease class and validate recommendations against agronomic guidance.",
]

PROBLEM_POINTS = [
    "Farmers cannot identify crop disease early enough to prevent yield loss.",
    "Agricultural expertise is not available at the time and place the decision is needed.",
    "Existing tools classify disease but provide no treatment guidance.",
    "Advice presented only in English is unusable for many farmers.",
]
NEED = "a system that identifies crop disease from a leaf photograph and returns treatment advice in the farmer's own language."

PROBLEM_STATEMENT = ("Given one photograph of a crop leaf and the crop the farmer chose, name the most likely disease (or 'healthy'), say how severe it is, and return treatment "
                     "and prevention advice from a knowledge base, through a web application a non-expert can use, with the interface in English, Hindi or Marathi - and report "
                     "honestly how accurate the diagnosis is on field photographs.")

GAP = ("The surveyed work addresses leaf image generation and classification. The gap is joining reliable disease classification to actionable, multilingual treatment "
       "and fertiliser recommendation.")

# (Work, Approach, Data, Reported result, Limitation); only facts from the PDFs read
LIT_TABLE = [
    ["Pakka et al. 2026 [1] (base paper)", "Foliagen: builds annotated foliage images from single-leaf photos (background removal, phyllotactic leaf placement, chosen disease rate) and uses them to train and fine-tune classifiers",
     "ASDID (10,722 soybean leaves, 7 diseases), a Kaggle soybean set, PlantVillage tomato; real foliage set MH-SoyaHealthVision", "Up to 98 % accuracy on natural foliage when 5 % of it is added to generated data (VGG19, ResNet50, DenseNet121, Swin, CBAM-ConvNeXt; 2 x RTX 6000 Ada)",
     "Soybean and tomato only; produces data, not a farmer-facing diagnosis or advice"],
    ["Sherifi et al. 2026 [2]", "PD36-C: 18-layer compact CNN, 1,250,694 parameters (4.77 MB), Qt desktop application for offline inference", "New Plant Diseases Dataset, 87 k images, 38 classes (laboratory-style backgrounds)",
     "99.53 % average test accuracy, 99.697 % training accuracy by epoch 30", "Clean lab images; no treatment advice; authors note weather, low-quality images and mixed diseases degrade performance"],
    ["Kanakala and Ningappa 2025 [3]", "CNN and LSTM classifiers of leaf images, Adam 1e-4, categorical cross-entropy, 10 epochs", "70,295 training and 17,572 validation images, 38 classes", "CNN 99.1 % training and 96.4 % validation accuracy; LSTM 93.43 % validation",
     "Validation on a random split of the same lab-style collection; validation loss fluctuates (possible over-fitting)"],
    ["Singh et al. 2020 [4]", "PlantDoc: web-scraped field photographs; benchmark of VGG16, InceptionV3, InceptionResNetV2 on cropped leaves and VGG16 on raw photos; Faster R-CNN leaf detection",
     "2,598 images, 13 plants, 27 classes (17 disease, 10 healthy); 2,342 train / 236 test in the released split", "Cropped leaves: 44.5 to 70.5 % accuracy (best InceptionResNetV2 with ImageNet + PlantVillage); raw photos 13.7 to 29.7 % (VGG16); detection mAP 38.9",
     "Small and hard: shows that models trained on PlantVillage fail on field photographs"],
    ["Mohanty et al. 2016 [6]", "AlexNet and GoogLeNet on PlantVillage images (colour, grey, segmented)", "54,306 images, 14 crops, 26 diseases", "Up to 99.35 % accuracy on held-out PlantVillage images; far lower on images from other sources",
     "Laboratory backgrounds; the paper itself warns about generalisation"],
    ["Ferentinos 2018 [7]", "Five CNN architectures on a database of leaf images with laboratory and field backgrounds", "87,848 images, 25 plants, 58 classes", "Best model 99.53 % success rate", "Mostly laboratory images; no recommendation layer"],
    ["Barbedo 2018 [8]", "Analysis of factors that limit deep learning for plant disease recognition (background, symptom variation, small datasets, image conditions)", "Review and experiments on public sets",
     "Accuracy drops when training data lack variety in conditions", "Describes the problem; no application"],
    ["Sandler et al. 2018 [9]", "MobileNetV2: inverted residual blocks with linear bottlenecks for mobile vision", "ImageNet", "Efficient backbone used for transfer learning in this project's reference experiment",
     "General vision model, not agriculture-specific"],
]

THEMES = {
    "Datasets and benchmarks": ["plantvillage", "plantdoc", "tomatovillage", "fieldplant"],
    "Leaf disease classification with CNNs": ["mohanty", "ferentinos", "pd36c", "lstm", "convnext"],
    "Data generation and generalisation": ["base", "cgan", "barbedo"],
    "Efficient models and transfer learning": ["mobilenet", "xception", "efficientnet", "imagenet"],
}
