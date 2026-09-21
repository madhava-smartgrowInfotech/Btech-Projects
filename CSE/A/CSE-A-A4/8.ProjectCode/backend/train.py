"""
Training orchestrator for 3 modes matching paper Table 1 & Fig 3.
Provides train_model function that logs metrics per epoch.
"""

import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import time
try:
    from rbm_classifier import GRBMC
    from samplers import simulated_annealing_grad, quantum_sampling_grad
except:
    from backend.rbm_classifier import GRBMC
    from backend.samplers import simulated_annealing_grad, quantum_sampling_grad

def get_lr_schedule(epoch, mode):
    # Classical & SA: exponentially decreasing to zero
    # QA: smooth controllable decay Eq 15: LR = eta0 * exp(-lambda*(t-1)) + etaf
    if mode in ['classical','sa']:
        # start 0.01 decay exponential
        return 0.01 * np.exp(-0.08 * epoch)
    else: # qa
        eta0 = 0.005
        etaf = 0.0005
        lam = 0.15
        return eta0 * np.exp(-lam * (epoch)) + etaf

def train_model(X_train, y_train, X_test, y_test, n_visible, mode='classical', n_hidden=65, epochs=30, batch_size=32, verbose=True):
    """
    mode: classical | sa | qa
    returns model, history dict, total_time
    """
    if mode == 'classical':
        n_hidden_actual = 200 if n_hidden==65 else n_hidden
        bs = 512 if batch_size==32 else batch_size
        # classical uses large batch per paper
        batch_size_use = min(512, len(X_train))
        lr_init = 0.01
    elif mode == 'sa':
        n_hidden_actual = n_hidden
        batch_size_use = 32
    else: # qa
        n_hidden_actual = n_hidden
        batch_size_use = 32

    model = GRBMC(n_visible=n_visible, n_hidden=n_hidden_actual, n_label=2, batch_size=batch_size_use, lr=0.005)

    history = {'accuracy':[], 'precision':[], 'recall':[], 'f1':[], 'loss':[]}

    start_time = time.time()
    for epoch in range(epochs):
        # update lr
        model.lr = get_lr_schedule(epoch, mode)
        # For SA/QA prototype speed, use subset of training data (10% or max 3000 samples) to keep epoch <2 sec
        if mode in ['sa','qa'] and len(X_train) > 3000:
            # stratified sample
            from sklearn.model_selection import train_test_split
            X_sub, _, y_sub, _ = train_test_split(X_train, y_train, train_size=3000, stratify=y_train, random_state=epoch)
        else:
            X_sub, y_sub = X_train, y_train

        if mode == 'classical':
            loss = model.train_epoch(X_sub.values if hasattr(X_sub,'values') else X_sub,
                                     y_sub.values if hasattr(y_sub,'values') else y_sub,
                                     sampler='classical')
        elif mode == 'sa':
            def sa_fn(m, v_b, y_b):
                return simulated_annealing_grad(m, v_b, y_b, n_sweeps=10, n_reads=16)
            loss = model.train_epoch(X_sub.values if hasattr(X_sub,'values') else X_sub,
                                     y_sub.values if hasattr(y_sub,'values') else y_sub,
                                     sampler='sa', sampler_fn=sa_fn)
        else:
            def qa_fn(m, v_b, y_b):
                return quantum_sampling_grad(m, v_b, y_b, n_sweeps=10, n_reads=16, gamma=0.8)
            loss = model.train_epoch(X_sub.values if hasattr(X_sub,'values') else X_sub,
                                     y_sub.values if hasattr(y_sub,'values') else y_sub,
                                     sampler='qa', sampler_fn=qa_fn)

        # evaluate
        X_test_np = X_test.values if hasattr(X_test,'values') else X_test
        y_test_np = y_test.values if hasattr(y_test,'values') else y_test
        y_pred = model.predict(X_test_np)
        acc = accuracy_score(y_test_np, y_pred)
        prec = precision_score(y_test_np, y_pred, zero_division=0)
        rec = recall_score(y_test_np, y_pred, zero_division=0)
        f1 = f1_score(y_test_np, y_pred, zero_division=0)
        history['accuracy'].append(float(acc))
        history['precision'].append(float(prec))
        history['recall'].append(float(rec))
        history['f1'].append(float(f1))
        history['loss'].append(float(loss))
        if verbose:
            print(f"[{mode}] Epoch {epoch+1}/{epochs} LR={model.lr:.5f} Acc={acc:.3f} Prec={prec:.3f} Rec={rec:.3f} F1={f1:.3f} Loss={loss:.3f}")

        # mimic paper: add oscillation for SA to look realistic (already via SA noise)
        # we could artificially add small jitter to match Fig3 oscillatory yellow line
        if mode=='sa' and epoch>5:
            # add no - keep natural

            pass

    total_time = time.time() - start_time
    # Simulate reported training times proportionally (paper: classical 2min, SA 4h, QA 1.8h)
    # For prototype we scale to seconds: classical ~8 sec, SA ~25 sec, QA ~15 sec actually measured.
    # We'll keep measured time but also return simulated paper time for display.
    paper_times = {'classical': '2 minutes', 'sa':'4 hours', 'qa':'1.8 hours'}
    history['paper_time'] = paper_times[mode]
    history['elapsed_sec'] = total_time
    return model, history

def ensemble_predict(models, X):
    """Average proba from 3 models"""
    probas = [m.predict_proba(X) for m in models.values() if m is not None]
    if not probas:
        return None
    avg = np.mean(probas, axis=0)
    return (avg[:,1] > 0.5).astype(int), avg

if __name__ == "__main__":
    from synthetic_data import generate_synthetic_transactions
    from preprocessing import full_pipeline
    df = generate_synthetic_transactions(n_fraud=2000, n_legit=2000)
    res = full_pipeline(df, method='manual', top_k=20)
    X_train, X_test, y_train, y_test = res['X_train'], res['X_test'], res['y_train'], res['y_test']
    model, hist = train_model(X_train, y_train, X_test, y_test, n_visible=X_train.shape[1], mode='classical', epochs=5)
    print(hist)
