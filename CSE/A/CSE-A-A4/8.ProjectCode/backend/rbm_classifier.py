"""
Gaussian-Bernoulli Restricted Boltzmann Machine Classifier (GRBMC)
Implements Sec II-A, II-B, Appendix A/B from paper.
Supports 3 samplers:
 - classical PCD with Gibbs sampling
 - simulated annealing sampling
 - quantum-inspired sampling (noisy SA with tunneling)

For prototype speed we use numpy. Visible units are Gaussian (Z-scored continuous),
hidden and label units are binary.

Architecture:
 - visible: n_visible (continuous)
 - hidden: n_hidden (binary)
 - label: n_label (2 for binary classification one-hot)
QUBO concatenation x = [v_bin_expanded, y, h] but for training we keep continuous v.
"""

import numpy as np

def sigmoid(x):
    # stable sigmoid
    return 1/(1+np.exp(-np.clip(x, -30, 30)))

class GRBMC:
    def __init__(self, n_visible=22, n_hidden=65, n_label=2, sigma=1.0, lr=0.005, batch_size=32, rng_seed=42):
        self.n_visible = n_visible
        self.n_hidden = n_hidden
        self.n_label = n_label
        self.sigma = sigma
        self.lr = lr
        self.batch_size = batch_size
        self.rng = np.random.default_rng(rng_seed)

        # Weights: W (visible-hidden), U (label-hidden)
        # Xavier init
        self.W = self.rng.normal(0, 0.01, size=(n_visible, n_hidden))
        self.U = self.rng.normal(0, 0.01, size=(n_label, n_hidden))
        self.b = np.zeros(n_hidden)  # hidden bias
        self.c = np.zeros(n_visible) # visible bias
        self.d = np.zeros(n_label)   # label bias

        # PCD persistent chain
        self.persistent_v = None
        self.persistent_y = None
        self.persistent_h = None

    def _visible_to_hidden_prob(self, v, y):
        # v: (batch, n_visible) continuous, y: (batch, n_label) one-hot
        # hidden activation: p(h=1|v,y) = sigmoid(b + W^T v/sigma + U^T y)
        # Paper eq 17 extended with label
        act = self.b + (v @ self.W)/ (self.sigma) + (y @ self.U)
        return sigmoid(act)

    def _hidden_to_visible_params(self, h):
        # p(v | h) = N( c + W h * sigma, sigma^2 ) -- simplified Appendix A eq 24
        # mu = c + sigma * W h
        mu = self.c + self.sigma * (h @ self.W.T)
        return mu

    def _hidden_to_label_prob(self, h):
        act = self.d + h @ self.U.T
        # softmax for label
        e = np.exp(act - np.max(act, axis=1, keepdims=True))
        return e / e.sum(axis=1, keepdims=True)

    def gibbs_step(self, v, y):
        h_prob = self._visible_to_hidden_prob(v, y)
        h_sample = (self.rng.random(h_prob.shape) < h_prob).astype(float)
        # sample v
        mu = self._hidden_to_visible_params(h_sample)
        v_sample = self.rng.normal(mu, self.sigma)
        # sample y
        y_prob = self._hidden_to_label_prob(h_sample)
        # categorical sample
        y_sample = np.zeros_like(y_prob)
        for i in range(y_prob.shape[0]):
            choice = self.rng.choice(self.n_label, p=y_prob[i])
            y_sample[i, choice] = 1
        return v_sample, y_sample, h_sample, h_prob, y_prob

    def pcd_step(self, v_data, y_data, k=1):
        batch = v_data.shape[0]
        if self.persistent_v is None or self.persistent_v.shape[0] != batch:
            self.persistent_v = self.rng.normal(0,1, size=(batch, self.n_visible))
            self.persistent_y = np.zeros((batch, self.n_label)); self.persistent_y[np.arange(batch), self.rng.integers(0, self.n_label, batch)] = 1
            self.persistent_h = (self.rng.random((batch, self.n_hidden)) < 0.5).astype(float)

        # Positive phase
        pos_h_prob = self._visible_to_hidden_prob(v_data, y_data)
        # Negative phase via persistent chain with k Gibbs steps
        v_model, y_model, h_model = self.persistent_v, self.persistent_y, self.persistent_h
        for _ in range(k):
            v_model, y_model, h_model, _, _ = self.gibbs_step(v_model, y_model)
        # update persistent
        self.persistent_v, self.persistent_y, self.persistent_h = v_model, y_model, h_model

        neg_h_prob = self._visible_to_hidden_prob(v_model, y_model)

        # Gradients Eq 5-7
        dW = (v_data.T @ pos_h_prob - v_model.T @ neg_h_prob) / batch / self.sigma
        dU = (y_data.T @ pos_h_prob - y_model.T @ neg_h_prob) / batch
        db = (pos_h_prob - neg_h_prob).mean(axis=0)
        dc = (v_data - v_model).mean(axis=0) / (self.sigma**2)
        dd = (y_data - y_model).mean(axis=0)

        return dW, dU, db, dc, dd, (v_model, y_model)

    def train_epoch(self, X, y_labels, sampler='classical', sampler_fn=None):
        """One epoch with batches. sampler_fn for SA/QA injected."""
        n = X.shape[0]
        indices = np.arange(n)
        self.rng.shuffle(indices)
        X_shuf = X[indices]
        y_shuf = y_labels[indices]
        # one-hot encode labels
        y_onehot = np.zeros((n, self.n_label))
        y_onehot[np.arange(n), y_shuf.astype(int)] = 1

        total_loss = 0
        for start in range(0, n, self.batch_size):
            end = min(start+self.batch_size, n)
            v_batch = X_shuf[start:end]
            y_batch = y_onehot[start:end]
            if sampler == 'classical':
                dW, dU, db, dc, dd, _ = self.pcd_step(v_batch, y_batch, k=1)
            else:
                # For SA/QA we delegate sampling to sampler_fn which returns v_model, y_model, h_prob approximations
                # sampler_fn should return (v_model, y_model, pos_h_prob, neg_h_prob)
                # fallback to pcd if not provided
                if sampler_fn is not None:
                    dW, dU, db, dc, dd = sampler_fn(self, v_batch, y_batch)
                else:
                    dW, dU, db, dc, dd, _ = self.pcd_step(v_batch, y_batch, k=1)

            # Update with learning rate
            self.W += self.lr * dW
            self.U += self.lr * dU
            self.b += self.lr * db
            self.c += self.lr * dc
            self.d += self.lr * dd

            # pseudo reconstruction loss
            total_loss += np.mean((v_batch - self._hidden_to_visible_params(self._visible_to_hidden_prob(v_batch, y_batch)>0.5))**2)

        return total_loss / (n // self.batch_size + 1)

    def predict_proba(self, X):
        n = X.shape[0]
        # try both label hypotheses and compute free energy
        # Free energy F(v,y) = -c^T v/sigma - d^T y - sum softplus(b + W^T v/sigma + U^T y)
        # we compute for y=0 and y=1 and softmax over -F
        y0 = np.zeros((n, self.n_label)); y0[:,0]=1
        y1 = np.zeros((n, self.n_label)); y1[:,1]=1
        def free_energy(v, y):
            # visible term
            term_v = -np.sum((v * self.c)/ (self.sigma), axis=1)  # approximate
            term_y = -(y * self.d).sum(axis=1)
            hidden_act = self.b + (v @ self.W)/self.sigma + (y @ self.U)
            term_h = -np.sum(np.log(1+np.exp(hidden_act)), axis=1)
            return term_v + term_y + term_h
        f0 = free_energy(X, y0)
        f1 = free_energy(X, y1)
        # p(y=1|v) = exp(-f1) / (exp(-f0)+exp(-f1))
        # use log softmax
        maxf = np.maximum(-f0, -f1)
        e0 = np.exp(-f0 - maxf)
        e1 = np.exp(-f1 - maxf)
        prob1 = e1/(e0+e1+1e-12)
        prob0 = 1-prob1
        return np.vstack([prob0, prob1]).T

    def predict(self, X):
        proba = self.predict_proba(X)
        return (proba[:,1] > 0.5).astype(int)

    def get_qubo_matrix(self):
        """Build Q matrix per Appendix B for visualization"""
        n_total = self.n_visible + self.n_label + self.n_hidden  # Note: for binary expansion we approximate
        Q = np.zeros((n_total, n_total))
        # diagonal biases
        Q[np.arange(self.n_visible), np.arange(self.n_visible)] = -self.c  # Qvv = diag(c) but negated per eq27
        off_v = self.n_visible
        Q[np.arange(off_v, off_v+self.n_label), np.arange(off_v, off_v+self.n_label)] = -self.d
        off_h = off_v + self.n_label
        Q[np.arange(off_h, off_h+self.n_hidden), np.arange(off_h, off_h+self.n_hidden)] = -self.b
        # off-diagonal weights
        # Qvh = 1/2 W
        for i in range(self.n_visible):
            for j in range(self.n_hidden):
                Q[i, off_h+j] = -0.5*self.W[i,j]
                Q[off_h+j, i] = -0.5*self.W[i,j]
        for i in range(self.n_label):
            for j in range(self.n_hidden):
                Q[off_v+i, off_h+j] = -0.5*self.U[i,j]
                Q[off_h+j, off_v+i] = -0.5*self.U[i,j]
        return Q
