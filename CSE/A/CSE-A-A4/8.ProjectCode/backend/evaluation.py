from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, roc_auc_score, classification_report
import numpy as np

def evaluate(y_true, y_pred, y_proba=None):
    cm = confusion_matrix(y_true, y_pred).tolist()
    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred, zero_division=0)
    rec = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    auc = None
    if y_proba is not None:
        try:
            auc = roc_auc_score(y_true, y_proba[:,1] if y_proba.ndim>1 else y_proba)
        except:
            auc = None
    return {
        'accuracy': float(acc), 'precision': float(prec), 'recall': float(rec), 'f1': float(f1),
        'confusion_matrix': cm, 'roc_auc': float(auc) if auc is not None else None,
        'report': classification_report(y_true, y_pred, output_dict=True, zero_division=0)
    }
