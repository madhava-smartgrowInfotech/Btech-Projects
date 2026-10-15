// Project copy taken from the existing Streamlit pages (app.py, pages/4_About.py) and README.md.
// Static project text only - nothing here is a metric or a result.

export const OVERVIEW =
  'Plastic pollution in oceans is a growing environmental crisis that harms marine ecosystems and is difficult to monitor manually. This project builds a computer-vision system that automatically detects and localises plastic waste in ocean/water images using a YOLO object-detection model, then presents the results through an interactive interface - a working prototype suitable for future extension to video, drone and robotic-collection systems.'

export const PROBLEM =
  'Plastic waste in oceans harms marine ecosystems. Manual monitoring is slow, costly and limited in coverage. Classification-only approaches identify that plastic is present but do not localise individual objects. This project addresses that gap by detecting and drawing bounding boxes around each plastic item in an image, along with a confidence score for every detection.'

export const OBJECTIVES = [
  'Collect and annotate a dataset of ocean images containing plastic waste.',
  'Preprocess images to handle lighting, reflections and turbidity.',
  'Train a deep-learning object detector for plastic waste.',
  'Localise each plastic item with bounding boxes and confidence scores.',
  'Provide a prototype interface to upload images and view detections.',
  'Evaluate detection accuracy using precision, recall and mAP.',
]

export const TECH_STACK = [
  { group: 'Backend', items: ['Python', 'OpenCV', 'NumPy', 'Pandas', 'PyTorch'] },
  { group: 'Model', items: ['Ultralytics YOLO (YOLOv8)'] },
  { group: 'Interface', items: ['React + Vite', 'FastAPI layer'] },
  { group: 'Visualization', items: ['Recharts', 'Matplotlib plots from evaluate.py'] },
  { group: 'Storage', items: ['Local filesystem', 'SQLite detection history'] },
]

export const HOW_IT_WORKS = [
  { title: 'Upload', text: 'Upload an ocean or water image (JPG, JPEG or PNG).' },
  { title: 'Preprocess', text: 'The image is colour-corrected, denoised and contrast-enhanced.' },
  { title: 'Detect', text: 'The YOLO model runs object detection on the cleaned image.' },
  { title: 'Localise', text: 'Bounding boxes and a confidence score are drawn for each object.' },
  { title: 'Report', text: 'Results, statistics and a downloadable report are generated.' },
]

export const ARCHITECTURE = [
  { title: 'User', meta: 'Opens the web interface' },
  { title: 'Web interface', meta: 'React app talking to the FastAPI layer (the original Streamlit app still runs too)' },
  { title: 'Image upload', meta: 'JPG, JPEG or PNG' },
  { title: 'Image preprocessing', meta: 'Denoise, contrast, colour correction' },
  { title: 'YOLO object detection model', meta: 'Ultralytics YOLOv8' },
  { title: 'Bounding box + confidence scores', meta: 'One box and one score per detected object' },
  { title: 'Post processing', meta: 'Sorting, table, statistics' },
  { title: 'Results dashboard', meta: 'Detection view and aggregate dashboard' },
  { title: 'Database / downloadable report', meta: 'SQLite history, annotated image and JSON report' },
]

export const BASE_PAPER_POINTS = [
  'Plastic waste detection',
  'Image-based detection',
  'Object localisation with bounding boxes',
  'Confidence scores per detection',
  'A user-friendly prototype interface (this web app)',
]

export const BASE_PAPER_TEXT =
  'The base paper uses YOLOv7 for floating-water-garbage detection, combined with an improved A* algorithm for robotic collection path planning. This project adopts the YOLO-based detection concept from the base paper but focuses specifically on the detection/localisation stage:'

export const NOT_IMPLEMENTED =
  'This project does not implement the robotic path-planning / collection component from the base paper - that is listed under Future Scope, not claimed as implemented.'

export const WHY_YOLOV8 =
  'Both are members of the YOLO family of single-stage object detectors trained the same way conceptually: transfer learning from a COCO-pretrained backbone onto a custom dataset, then evaluated with Precision/Recall/mAP. This project uses the Ultralytics implementation (YOLOv8) because it provides a stable, actively maintained Python API for training, validation and inference - making it far easier for a B.Tech project to install, train and demonstrate reliably, while keeping the detection methodology and evaluation approach consistent with the base paper.'

export const FUTURE_SCOPE = [
  { label: 'Real-time video detection', icon: 'Video' },
  { label: 'Drone-based monitoring', icon: 'Plane' },
  { label: 'Underwater camera integration', icon: 'Waves' },
  { label: 'Robotic waste collection (the path-planning component from the base paper)', icon: 'Route' },
  { label: 'Mobile application', icon: 'Smartphone' },
  { label: 'Cloud deployment', icon: 'Cloud' },
  { label: 'Edge AI (on-device inference)', icon: 'Cpu' },
  { label: 'GPS-based pollution mapping', icon: 'MapPin' },
  { label: 'Plastic-type classification (bottle, bag, net, etc.)', icon: 'Layers' },
  { label: 'Real-time ocean monitoring networks', icon: 'Radar' },
]

export const VIVA = [
  {
    q: 'Why is preprocessing done before detection?',
    a: 'Ocean images often have colour cast (water absorbs red light), low contrast/haze, and sensor noise. The preprocessing pipeline (colour correction, denoising, CLAHE contrast enhancement) reduces these issues so plastic objects are easier to distinguish from the water/background - without over-processing, which could remove the texture information the model needs.',
  },
  {
    q: 'How is the model evaluated?',
    a: 'Using standard object-detection metrics computed by the Ultralytics validation routine: Precision, Recall, mAP@0.5, and mAP@0.5:0.95, plus a confusion matrix and PR curve. These are only shown after running evaluate.py on a real trained model - nothing is fabricated.',
  },
  {
    q: 'What happens if no trained model is available?',
    a: 'The app falls back to a general COCO-pretrained model purely so the interface remains demoable end-to-end, and clearly labels this as a placeholder. Real plastic detection requires running train.py on an annotated dataset to produce models/best.pt.',
  },
]

export const PREPROCESS_STEPS = [
  'Resize (longest side capped at 1280 px)',
  'Grey-world colour-cast correction',
  'Mild non-local-means denoising',
  'CLAHE contrast enhancement',
]
