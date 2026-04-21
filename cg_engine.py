import numpy as np
from sympy.physics.quantum.cg import CG

# Internal dictionary to cache Clebsch-Gordan calculations for speed
_cg_cache = {}

def get_cg(j1, m1, j2, m2, j3, m3):
    """
    Wrapper to get the exact numerical value of the Clebsch-Gordan 
    coefficient <j1, m1; j2, m2 | j3, m3>. Uses sympy and caches results.
    """
    key = (j1, m1, j2, m2, j3, m3)
    if key not in _cg_cache:
        # Evaluate exactly using sympy, then cast to standard float
        _cg_cache[key] = float(CG(j1, m1, j2, m2, j3, m3).doit())
    return _cg_cache[key]

def get_moment_factor(l1, m1, l2, m2, L, M):
    """
    Calculates the geometric coefficient for the interference of wave 1 
    and wave 2 contributing to the spherical harmonic moment H(L, M).
    
    Formula based on the integral of three spherical harmonics:
    Y_{l1}^{m1} * (Y_{l2}^{m2})^* projecting onto Y_L^M
    """
    # 1. M Selection Rule: The projections must perfectly align
    if M != (m1 - m2):
        return 0.0
        
    # 2. Triangle Inequality: L must be vector sum of l1 and l2
    if L < abs(l1 - l2) or L > (l1 + l2):
        return 0.0

    # 3. Parity Conservation: l1 + l2 + L must be an even integer
    # for the <l1, 0; l2, 0 | L, 0> coefficient to be non-zero.
    if (l1 + l2 + L) % 2 != 0:
        return 0.0

    # Get the Clebsch-Gordan coefficients
    cg_zero = get_cg(l1, 0, l2, 0, L, 0)
    cg_m = get_cg(l1, m1, l2, -m2, L, M)

    if cg_zero == 0.0 or cg_m == 0.0:
        return 0.0

    # Phase factor from the complex conjugation of the second spherical harmonic
    phase = (-1)**m2
    
    # The geometric prefactor from the spherical harmonic product rule
    prefactor = np.sqrt( ((2*l1 + 1) * (2*l2 + 1)) / (4 * np.pi * (2*L + 1)) )
    
    return phase * prefactor * cg_zero * cg_m
