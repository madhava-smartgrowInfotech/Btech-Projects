# Datasets and credits

| Dataset | Authors / source | Licence | Used for | In the repository |
|---|---|---|---|---|
| [COVID-19 Radiography Database](https://www.kaggle.com/datasets/tawsifurrahman/covid19-radiography-database) | Tawsifur Rahman, Muhammad E. H. Chowdhury, Amith Khandakar and co-authors (Qatar University, University of Dhaka and collaborators) | See the Kaggle page (research / non-commercial use, cite the papers below) | X-ray classes COVID-19, viral pneumonia, lung opacity, normal; **lung masks** for the U-Net | Sample in `data/sample/xray/` and `data/sample/lung_masks/`; full set via `scripts/download_data.py` |
| [Tuberculosis (TB) Chest X-ray Database](https://www.kaggle.com/datasets/tawsifurrahman/tuberculosis-tb-chest-xray-dataset) | Tawsifur Rahman, Amith Khandakar, Muhammad E. H. Chowdhury and co-authors | See the Kaggle page (research use, cite the paper below) | X-ray classes tuberculosis and normal | Sample in `data/sample/xray/`; full set via the script |
| [Chest CT-Scan Images](https://www.kaggle.com/datasets/mohamedhanyyy/chest-ctscan-images) | Mohamed Hany (Kaggle) | See the Kaggle page | CT classes adenocarcinoma, large-cell carcinoma, squamous-cell carcinoma, normal | **Committed in full** in `data/chest_ct/` (122 MB, no file over 100 MB) |
| scikit-learn sample images | scikit-learn project (`sklearn.datasets.load_sample_images`) | BSD-3 (bundled with scikit-learn) | Non-chest images to test the modality check | `data/sample/other/` |

The Chest X-Ray Images (Pneumonia) dataset is not used in this build (bacterial pneumonia as a separate class is deferred).

## Papers to cite

- M. E. H. Chowdhury et al., "Can AI help in screening viral and COVID-19 pneumonia?", *IEEE Access*, vol. 8, pp. 132665-132676, 2020.
- T. Rahman et al., "Exploring the effect of image enhancement techniques on COVID-19 detection using chest X-ray images", *Computers in Biology and Medicine*, vol. 132, 104319, 2021.
- T. Rahman et al., "Reliable tuberculosis detection using chest X-ray with deep learning, segmentation and visualization", *IEEE Access*, vol. 8, pp. 191586-191601, 2020.

## Fonts

Noto Sans, Noto Sans Devanagari and Noto Sans Telugu (`backend/app/assets/fonts/`) - The Noto Project Authors, SIL Open Font License 1.1.
