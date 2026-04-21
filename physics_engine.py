import numpy as np

def get_breakup_momentum(M, m1, m2):
    """
    Calculates the 2-body breakup momentum q(M) in the rest frame of M.
    M: Invariant mass of the resonance (array or scalar)
    m1, m2: Masses of the decay products
    
    Returns 0 if below threshold (M < m1 + m2) to prevent NaN errors.
    """
    # Create an array of zeros with the same shape as M
    q = np.zeros_like(M, dtype=float)
    
    # Only calculate where kinematically allowed (above threshold)
    valid = M > (m1 + m2)
    
    # Standard 2-body kinematic formula
    M_valid = M[valid]
    term1 = M_valid**2 - (m1 + m2)**2
    term2 = M_valid**2 - (m1 - m2)**2
    
    q[valid] = np.sqrt(term1 * term2) / (2 * M_valid)
    return q

def blatt_weisskopf(L, q, q0=0.1973):
    """
    Calculates the Blatt-Weisskopf centrifugal barrier factors F_L(q).
    L: Orbital angular momentum
    q: Breakup momentum
    q0: Scale parameter (default 0.1973 GeV/c corresponds to ~1 fm radius)
    """
    z = (q / q0)**2
    
    if L == 0:
        return np.ones_like(q)
    elif L == 1:
        return np.sqrt(z / (z + 1.0))
    elif L == 2:
        return np.sqrt((z**2) / (z**2 + 3.0*z + 9.0))
    elif L == 3:
        return np.sqrt((z**3) / (z**3 + 6.0*z**2 + 45.0*z + 225.0))
    else:
        raise ValueError(f"Blatt-Weisskopf for L={L} not yet implemented.")

def relativistic_breit_wigner(M, M0, Gamma0, L, m1, m2, q0=0.1973):
    """
    Calculates the complex mass-dependent Relativistic Breit-Wigner amplitude.
    M: Array of mass bins to evaluate
    M0: Resonance mass
    Gamma0: Resonance width
    L: Angular momentum of the decay
    m1, m2: Decay product masses
    """
    # 1. Kinematics at the running mass M
    q = get_breakup_momentum(M, m1, m2)
    
    # 2. Kinematics at the resonance pole M0
    # (Using np.array to handle M0 as a scalar gracefully)
    qR = get_breakup_momentum(np.array([M0]), m1, m2)[0] 
    
    if qR <= 0:
        raise ValueError(f"Resonance pole M0={M0} is below decay threshold {m1+m2}!")

    # 3. Barrier factors
    F_L_q = blatt_weisskopf(L, q, q0)
    F_L_qR = blatt_weisskopf(L, qR, q0)
    
    # 4. Mass-dependent width Gamma(M)
    # The width grows with available phase space and barrier penetration
    # We add a tiny epsilon to q to avoid division by zero right at threshold
    Gamma_M = Gamma0 * (M0 / M) * (q / (qR + 1e-9)) * (F_L_q / (F_L_qR + 1e-9))**2
    
    # 5. The complex amplitude
    numerator = M0 * Gamma0  # Convention varies, but this keeps the peak height stable
    denominator = (M0**2 - M**2) - 1j * (M0 * Gamma_M)
    
    amplitude = numerator / denominator
    
    # Suppress amplitude strictly below threshold
    amplitude[M <= (m1 + m2)] = 0.0 + 0.0j
    
    # Apply the barrier factor to the shape itself (production + decay vertex)
    return amplitude * F_L_q
