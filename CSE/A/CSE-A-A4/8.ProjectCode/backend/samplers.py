"""
Samplers replicating paper Sec III-C/D, II-D
- Classical PCD (Gibbs) is inside GRBMC itself
- Simulated Annealing (SA) via PIMC-like sweeps
- Quantum Sampling (QS) via noisy QA simulation with tunneling
These produce gradient estimates without explicit Gibbs chains.
"""

import numpy as np

def simulated_annealing_grad(model, v_data, y_data, n_sweeps=20, n_reads=32, temp_start=2.0, temp_end=0.1):
    """
    Approximate quantum annealing via classical simulated annealing.
    We sample model configurations using SA instead of Gibbs.
    Returns gradients dW, dU, db, dc, dd
    """
    batch = v_data.shape[0]
    n_visible = model.n_visible
    n_hidden = model.n_hidden
    n_label = model.n_label
    sigma = model.sigma

    # sample model expectations via SA
    # Represent state as (v_bin_placeholder, y, h). For continuous v we sample h,y first then reconstruct v.
    # Simplified: run SA over binary hidden+label space with visible clamped influence via energy.

    # Energy function for a config (h, y) given ? We approximate joint energy:
    # E(v,h,y) = ||v - c||^2 /2sigma^2 -b^T h - d^T y - (v/sigma)^T W h - y^T U h
    # For sampling we average over v_data distribution approximated as v_data mean? Instead sample full.

    # Simple approach: generate multiple annealed samples of (h,y) then generate v ~ N(mu, sigma)
    beta_start = 1/temp_start
    beta_end = 1/temp_end

    # initialize random binary states
    h_samples = (model.rng.random((n_reads, n_hidden)) < 0.5).astype(float)
    y_samples = np.zeros((n_reads, n_label))
    for i in range(n_reads):
        y_samples[i, model.rng.integers(0, n_label)] = 1

    # annealing schedule
    betas = np.linspace(beta_start, beta_end, n_sweeps)
    for beta in betas:
        # propose flip for each h_j with probability derived from energy delta (Metropolis)
        # compute hidden field: b + W^T v/sigma + U^T y
        # use average v_data for field approx (faster)
        v_avg = v_data.mean(axis=0)
        for _ in range(2):  # sweeps over all hidden
            field = model.b + (v_avg @ model.W)/sigma + (y_samples @ model.U)  # (n_reads, n_hidden)
            prob = 1/(1+np.exp(-2*beta*field))  # scaled by beta
            # Flip with probability
            flip = model.rng.random(h_samples.shape) < 0.05  # minor random flip then accept via prob
            # simpler: sample new h from prob
            h_new = (model.rng.random(h_samples.shape) < prob).astype(float)
            # Metropolis acceptance: blend
            h_samples = np.where(flip, h_new, h_samples)
            # update y via softmax biased
            logits = model.d + h_samples @ model.U.T  # (n_reads, n_label)
            # beta scaling
            scaled = logits * beta
            e = np.exp(scaled - np.max(scaled, axis=1, keepdims=True))
            p = e / e.sum(axis=1, keepdims=True)
            for i in range(n_reads):
                if model.rng.random() < 0.3:
                    choice = model.rng.choice(n_label, p=p[i])
                    y_samples[i] = 0; y_samples[i, choice]=1

    # now we have n_reads model samples; average to get expectations
    # For gradient we need v_model distribution: generate v from h
    v_model_reads = np.array([model.rng.normal(model._hidden_to_visible_params(h_samples[i:i+1])[0], sigma) for i in range(n_reads)])
    # tile to batch size for gradient calc (use average across reads)
    v_model_mean = v_model_reads.mean(axis=0)  # (n_visible,)
    y_model_mean = y_samples.mean(axis=0)
    h_model_mean = h_samples.mean(axis=0)

    # expand to batch for gradient formulas
    batch_v_model = np.tile(v_model_mean, (batch,1))
    batch_y_model = np.tile(y_model_mean, (batch,1))
    batch_h_model = np.tile(h_model_mean, (batch,1))

    pos_h_prob = model._visible_to_hidden_prob(v_data, y_data)
    neg_h_prob = np.tile(h_model_mean, (batch,1))

    dW = (v_data.T @ pos_h_prob - batch_v_model.T @ neg_h_prob) / batch / sigma
    dU = (y_data.T @ pos_h_prob - batch_y_model.T @ neg_h_prob) / batch
    db = (pos_h_prob - neg_h_prob).mean(axis=0)
    dc = (v_data - batch_v_model).mean(axis=0) / (sigma**2)
    dd = (y_data - batch_y_model).mean(axis=0)
    return dW, dU, db, dc, dd

def quantum_sampling_grad(model, v_data, y_data, n_sweeps=20, n_reads=32, gamma=0.8):
    """
    Quantum-inspired sampling: adds tunneling term and noise to simulate D-Wave QA.
    Similar to SA but with additional quantum fluctuation (transverse field) decay.
    """
    # Use SA as base but inject quantum noise: at early sweeps allow larger jumps, final sweeps collapse
    # gamma controls transverse field strength
    batch = v_data.shape[0]
    n_hidden = model.n_hidden; n_label = model.n_label; sigma = model.sigma
    n_reads = max(16, n_reads)
    h_samples = (model.rng.random((n_reads, n_hidden)) < 0.5).astype(float)
    y_samples = np.zeros((n_reads, n_label))
    for i in range(n_reads):
        y_samples[i, model.rng.integers(0, n_label)] = 1

    # quantum annealing schedule: A(s) and B(s) like paper eq 14
    # A(s) = gamma*(1-s), B(s)= s .  s in [0,1]
    ss = np.linspace(0,1, n_sweeps)
    for s in ss:
        A = gamma * (1 - s)
        B = s
        # effective beta scaled by B, fluctuation by A
        beta_eff = 0.5 + B*2.0
        transverse_p = A * 0.3  # probability of quantum tunneling flip
        v_avg = v_data.mean(axis=0)
        field = model.b + (v_avg @ model.W)/sigma + (y_samples @ model.U)
        # classical Boltzmann prob scaled by B
        prob = 1/(1+np.exp(-2*beta_eff*field*B))
        # add quantum tunneling: with prob transverse_p force random flip irrespective of energy
        quantum_flip = model.rng.random(h_samples.shape) < transverse_p
        classical_sample = (model.rng.random(h_samples.shape) < prob).astype(float)
        # where quantum_flip true, randomize
        h_samples = np.where(quantum_flip, (model.rng.random(h_samples.shape) < 0.5).astype(float), classical_sample)
        # label sampling with B scaling + noise
        logits = (model.d + h_samples @ model.U.T) * B
        e = np.exp(logits - np.max(logits, axis=1, keepdims=True))
        p = e / e.sum(axis=1, keepdims=True)
        # add depolarizing noise proportional to A
        p = (1 - A*0.2)*p + A*0.2 / n_label
        for i in range(n_reads):
            if model.rng.random() < 0.5:
                choice = model.rng.choice(n_label, p=p[i])
                y_samples[i]=0; y_samples[i,choice]=1

    v_model_reads = np.array([model.rng.normal(model._hidden_to_visible_params(h_samples[i:i+1])[0], sigma) for i in range(n_reads)])
    v_model_mean = v_model_reads.mean(axis=0)
    y_model_mean = y_samples.mean(axis=0)
    h_model_mean = h_samples.mean(axis=0)

    pos_h_prob = model._visible_to_hidden_prob(v_data, y_data)
    neg_h_prob = np.tile(h_model_mean, (batch,1))
    batch_v_model = np.tile(v_model_mean, (batch,1))
    batch_y_model = np.tile(y_model_mean, (batch,1))

    dW = (v_data.T @ pos_h_prob - batch_v_model.T @ neg_h_prob) / batch / sigma
    dU = (y_data.T @ pos_h_prob - batch_y_model.T @ neg_h_prob) / batch
    db = (pos_h_prob - neg_h_prob).mean(axis=0)
    dc = (v_data - batch_v_model).mean(axis=0) / (sigma**2)
    dd = (y_data - batch_y_model).mean(axis=0)
    return dW, dU, db, dc, dd
