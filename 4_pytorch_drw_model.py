import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np

class DRWModel(nn.Module):
    def __init__(self):
        super(DRWModel, self).__init__()
        # Initialize log parameters (tau and sigma) for unconstrained optimization
        self.log_tau = nn.Parameter(torch.tensor(0.0))
        self.log_sigma = nn.Parameter(torch.tensor(0.0))
        
    def forward(self, t, y, yerr):
        tau = torch.exp(self.log_tau)
        sigma = torch.exp(self.log_sigma)
        
        # Calculate covariance matrix for Gaussian Process
        # K_ij = sigma^2 * exp(-|t_i - t_j| / tau)
        dt = torch.abs(t.unsqueeze(0) - t.unsqueeze(1))
        K = (sigma ** 2) * torch.exp(-dt / tau)
        
        # Add observational errors to the diagonal
        K += torch.diag(yerr ** 2)
        
        # Add jitter for numerical stability
        K += torch.eye(t.size(0)) * 1e-6
        
        # Compute negative log likelihood
        L = torch.linalg.cholesky(K)
        alpha = torch.cholesky_solve(y.unsqueeze(1), L).squeeze()
        
        nll = 0.5 * torch.dot(y, alpha) + torch.sum(torch.log(torch.diag(L)))
        return nll

def infer_parameters(t, y, yerr, epochs=200):
    model = DRWModel()
    optimizer = optim.Adam(model.parameters(), lr=0.1)
    
    t_tensor = torch.tensor(t, dtype=torch.float32)
    y_tensor = torch.tensor(y, dtype=torch.float32)
    yerr_tensor = torch.tensor(yerr, dtype=torch.float32)
    
    # Zero mean the data
    y_tensor = y_tensor - torch.mean(y_tensor)
    
    for epoch in range(epochs):
        optimizer.zero_grad()
        loss = model(t_tensor, y_tensor, yerr_tensor)
        loss.backward()
        optimizer.step()
        
    tau = torch.exp(model.log_tau).item()
    sigma = torch.exp(model.log_sigma).item()
    return tau, sigma

if __name__ == "__main__":
    # Test DRW Model with mock irregular time series data
    print("Testing PyTorch DRW Model with mock irregular time series...")
    t = np.sort(np.random.uniform(0, 1000, 100))
    y = np.sin(t / 100) + np.random.normal(0, 0.05, 100) 
    yerr = np.ones_like(t) * 0.05
    
    tau_pred, sigma_pred = infer_parameters(t, y, yerr)
    print(f"Inferred Parameters for Mock Data:")
    print(f"Tau (relaxation time): {tau_pred:.2f}")
    print(f"Sigma (long-term variability): {sigma_pred:.4f}")
