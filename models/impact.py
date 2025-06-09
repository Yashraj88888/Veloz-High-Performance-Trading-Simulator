import numpy as np
from scipy.integrate import quad

# Implementation of the Gatheral's non-linear transient impact model
def calculate_impact(orderbook, qty_usd, sigma, delta, gamma, lam, T=1.0, N=100):


   
    bids = [float(lvl[0]) for lvl in orderbook[:5]]
    asks = [float(lvl[0]) for lvl in orderbook[:5]]
    mid_price = (np.mean(bids) + np.mean(asks)) / 2.0

    #Converting USD notional to share count
    X = qty_usd / mid_price

    #Time grid discretization
    t_grid = np.linspace(0, T, N+1)
    dt = T/N

    # 4) Optimal trading trajectory (numerical solution)
    def decay_kernel(t, s):
        return (t - s)**(-gamma) if t > s else 0.0

    # Solve non-linear integral equation for optimal execution
    # Using fixed-point iteration method
    v = np.ones(N) * X/(T*N)  # Initial guess (constant rate)
    
    for _ in range(100):  # Iteration convergence
        new_v = np.zeros(N)
        for i in range(N):
            integral = sum(
                v[j]**(delta) * decay_kernel(t_grid[i], t_grid[j]) 
                for j in range(i+1)
            )
            new_v[i] = (lam * sigma**2 / (2 * delta))**(1/(2*delta - 1)) * integral**(-1/(2*delta - 1))
        
        # Normalize to meet total shares constraint
        total = np.sum(new_v)*dt
        new_v *= X / total
        v = 0.5*v + 0.5*new_v  # Damping for convergence

    # 5) Calculate cost components
    transient_cost = 0.0
    permanent_impact = 0.0
    risk_term = 0.0

    for i in range(N):
        
        transient_cost += v[i]**(1 + delta) * dt**(1 - gamma)
        
     
        permanent_impact += 0.5 * v[i] * np.sum(v[:i+1] * dt * (t_grid[i] - t_grid[:i+1])**(-gamma))
        

        risk_term += lam * sigma**2 * (X - np.sum(v[:i]*dt))**2 * dt

    # Convert costs to USD
    transient_cost *= mid_price * (1 + delta)/(delta + 1)
    permanent_impact *= mid_price * gamma
    risk_term *= mid_price

    total_cost = transient_cost + permanent_impact + risk_term

    return total_cost, {
        'transient': transient_cost,
        'permanent': permanent_impact,
        'risk': risk_term
    }
