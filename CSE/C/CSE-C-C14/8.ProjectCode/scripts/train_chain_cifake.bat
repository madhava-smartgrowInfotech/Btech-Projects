@echo off
cd /d D:\abstracts\Madhav\CSE\C\CSE-C-C14\8.ProjectCode
set PYTHONUNBUFFERED=1
set OMP_NUM_THREADS=6
.venv\Scripts\python.exe scripts\train_a1.py --epochs 5 --data-root data\cifake --out models\cifake\efficientnet_a1.pt > experiments\cifake\logs\train_a1.log 2>&1
.venv\Scripts\python.exe scripts\train_c.py  --epochs 5 --data-root data\cifake --out models\cifake\mobilenetv3_c.pt > experiments\cifake\logs\train_c.log 2>&1
.venv\Scripts\python.exe scripts\train_a2.py --epochs 5 --data-root data\cifake --out models\cifake\efficientnet_a2.pt > experiments\cifake\logs\train_a2.log 2>&1
.venv\Scripts\python.exe scripts\train_b.py  --epochs 3 --data-root data\cifake --out models\cifake\resnet50_b.pt > experiments\cifake\logs\train_b.log 2>&1
echo done > experiments\cifake\logs\chain_done.txt
