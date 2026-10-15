"""Generate notebooks/pulmovision_kaggle.ipynb from the ml/ and backend/ sources (keeps them in sync).

python scripts/make_notebook.py
"""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
FILES = [
    ("backend/app/__init__.py", "work/backend/app/__init__.py"),
    ("backend/app/services/__init__.py", "work/backend/app/services/__init__.py"),
    ("backend/app/services/imaging.py", "work/backend/app/services/imaging.py"),
    ("backend/app/services/nets.py", "work/backend/app/services/nets.py"),
    ("ml/common.py", "work/ml/common.py"),
    ("ml/prepare_data.py", "work/ml/prepare_data.py"),
    ("ml/train.py", "work/ml/train.py"),
    ("ml/eval.py", "work/ml/eval.py"),
]


def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text}


def code(text):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": text}


cells = [
    md("# PulmoVision - GPU training on Kaggle\n\n"
       "Add these inputs with **Add Data**: `tawsifurrahman/covid19-radiography-database`, "
       "`tawsifurrahman/tuberculosis-tb-chest-xray-dataset`, `mohamedhanyyy/chest-ctscan-images`. "
       "Set **Accelerator: GPU** and **Run All**. Download `/kaggle/working/models` and `/kaggle/working/experiments` "
       "and copy them into the project's `models/` and `experiments/` folders."),
    code("!pip install -q segmentation-models-pytorch==0.3.4 timm==0.9.7 pydicom==3.0.1"),
    code("import glob, os\n"
         "def find(pattern):\n"
         "    hits = glob.glob(f'/kaggle/input/**/{pattern}', recursive=True)\n"
         "    assert hits, f'dataset folder {pattern} not found - add it with Add Data'\n"
         "    return hits[0]\n"
         "os.environ['COVID_ROOT'] = find('COVID-19_Radiography_Dataset')\n"
         "os.environ['TB_ROOT'] = find('TB_Chest_Radiography_Database')\n"
         "os.environ['CT_ROOT'] = os.path.dirname(find('Data/train'))\n"
         "print({k: os.environ[k] for k in ('COVID_ROOT', 'TB_ROOT', 'CT_ROOT')})"),
]
for src, dst in FILES:
    text = (ROOT / src).read_text(encoding="utf-8")
    cells.append(code(f"%%writefile {dst}\n{text}" if text.strip() else f"!mkdir -p {pathlib.PurePosixPath(dst).parent} && touch {dst}"))
cells[3:3] = [code("!mkdir -p work/backend/app/services work/ml")]
cells += [
    md("Larger GPU config: raise the per-class counts in prepare_data.py and the epochs below if you have time."),
    code("%cd work/ml\n!python prepare_data.py"),
    code("!python train.py modality && python train.py xray --epochs 12 && python train.py ct --epochs 25 && python train.py unet --epochs 10"),
    code("!python eval.py"),
    code("import shutil\nfor d in ('models', 'experiments'):\n    shutil.copytree(f'/kaggle/working/work/{d}', f'/kaggle/working/{d}', dirs_exist_ok=True)\nprint(os.listdir('/kaggle/working/models'))"),
]
nb = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                                   "language_info": {"name": "python"}, "accelerator": "GPU"}, "nbformat": 4, "nbformat_minor": 5}
out = ROOT / "notebooks" / "pulmovision_kaggle.ipynb"
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(nb, indent=1), encoding="utf-8")
print("wrote", out)
