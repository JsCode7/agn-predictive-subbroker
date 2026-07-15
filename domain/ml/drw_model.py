import torch
import torch.nn as nn
import torch.optim as optim

class DRWModel(nn.Module):
    def __init__(self):
        super(DRWModel, self).__init__()
        self.log_tau = nn.Parameter(torch.tensor(0.0))
        self.log_sigma = nn.Parameter(torch.tensor(0.0))
        
    def forward(self, t, y, yerr):
        tau = torch.exp(self.log_tau)
        sigma = torch.exp(self.log_sigma)
        
        dt = torch.abs(t.unsqueeze(0) - t.unsqueeze(1))
        K = (sigma ** 2) * torch.exp(-dt / tau)
        K += torch.diag(yerr ** 2)
        K += torch.eye(t.size(0)) * 1e-6
        
        L = torch.linalg.cholesky(K)
        alpha = torch.cholesky_solve(y.unsqueeze(1), L).squeeze()
        
        nll = 0.5 * torch.dot(y, alpha) + torch.sum(torch.log(torch.diag(L)))
        return nll

def infer_parameters(t, y, yerr, epochs=40):
    model = DRWModel()
    optimizer = optim.Adam(model.parameters(), lr=0.1)
    
    t_tensor = torch.tensor(t, dtype=torch.float32)
    y_tensor = torch.tensor(y, dtype=torch.float32)
    yerr_tensor = torch.tensor(yerr, dtype=torch.float32)
    
    y_tensor = y_tensor - torch.mean(y_tensor)
    
    for epoch in range(epochs):
        optimizer.zero_grad()
        loss = model(t_tensor, y_tensor, yerr_tensor)
        loss.backward()
        optimizer.step()
        
    tau = torch.exp(model.log_tau).item()
    sigma = torch.exp(model.log_sigma).item()
    return tau, sigma
