"""
Writes the facts the documents quote about the machine, the software and the network:
experiments/environment.json and experiments/model_summary.json.

    python scripts/collect_env.py
"""

import json
import os
import platform
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")

import numpy as np


def cmd(args):
    try:
        return subprocess.run(args, capture_output=True, text=True, shell=True, timeout=30).stdout.strip()
    except Exception:
        return None


def main():
    import tensorflow as tf  # first: importing scipy/sklearn before TensorFlow breaks its DLL initialisation on this machine

    import cv2
    import fastapi
    import sklearn
    import uvicorn
    from importlib.metadata import version

    from model.model_builder import build_custom_cnn

    cpu = cmd('powershell -NoProfile -Command "(Get-CimInstance Win32_Processor).Name"')
    cores = cmd('powershell -NoProfile -Command "(Get-CimInstance Win32_Processor).NumberOfCores"')
    threads = cmd('powershell -NoProfile -Command "(Get-CimInstance Win32_Processor).NumberOfLogicalProcessors"')
    ram = cmd('powershell -NoProfile -Command "[math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory/1GB,1)"')
    env = {
        "os": platform.platform(), "cpu": cpu, "cores": cores, "logical_processors": threads, "ram_gb": ram, "gpu": "none (CPU only)",
        "python": platform.python_version(), "tensorflow": tf.__version__, "keras": version("keras"), "numpy": np.__version__,
        "opencv": cv2.__version__, "scikit_learn": sklearn.__version__, "fastapi": fastapi.__version__, "uvicorn": uvicorn.__version__,
        "flask": version("flask"), "node": cmd("node --version"), "npm": cmd("npm --version"),
        "pinned_requirements": open(os.path.join(ROOT, "requirements.txt")).read().split(),
    }
    json.dump(env, open(os.path.join(ROOT, "experiments", "environment.json"), "w"), indent=2)

    m = build_custom_cnn(num_classes=3)
    layers = []
    for l in m.layers:
        try:
            shp = list(l.output.shape)[1:]
        except Exception:
            shp = None
        layers.append({"name": l.name, "type": l.__class__.__name__, "output_shape": shp, "params": int(l.count_params())})
    trainable = int(sum(np.prod(w.shape) for w in m.trainable_weights))
    non_trainable = int(sum(np.prod(w.shape) for w in m.non_trainable_weights))
    json.dump({"layers": layers, "total_params": int(m.count_params()), "trainable": trainable, "non_trainable": non_trainable,
               "float32_mb": round(m.count_params() * 4 / 1e6, 2)},
              open(os.path.join(ROOT, "experiments", "model_summary.json"), "w"), indent=2)
    print(json.dumps(env, indent=1)[:1500])
    print("params", m.count_params(), "trainable", trainable, "non-trainable", non_trainable)


if __name__ == "__main__":
    main()
