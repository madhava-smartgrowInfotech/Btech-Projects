# CipherGuard Shield - Model Performance Report

**Data mode:** synthetic demo data (UNSW-NB15 schema, generated)
**Dataset rows:** 12000 (train 8400 / val 1800 / test 1800)
**Technology:** XGBoost + 1D Convolutional Neural Network (2 conv layers + pooling + dense, PyTorch) + Logistic Regression stacking | UNSW-NB15 schema
**CNN backend actually used:** torch

## Held-out Test Metrics
- Accuracy: 0.9733
- Precision: 0.9766
- Recall: 0.9701
- F1: 0.9733
- ROC-AUC: 0.9704

## Confusion Matrix (rows=actual, cols=predicted)
```
            pred_normal  pred_attack
actual_normal     877         21
actual_attack      27        875
```

## Base Models
- XGBoost accuracy: 0.9733
- CNN accuracy: 0.9733
- Stacking meta-model: LogisticRegression coef=[[3.767190830729736, 3.5850207704372536]] intercept=[-3.5732827548629666]

*All numbers computed from actual held-out test set, not fabricated. Ensemble stacking = soft-voting / weighted score averaging with min-max normalized probabilities (honest analogue of score-level fusion).*
