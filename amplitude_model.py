import numpy as np
from scipy.integrate import simpson
import math

def clebsch(j1, m1, j2, m2, j3, m3):
    """
    Exact Algebraic Clebsch-Gordan Coefficient <j1 m1 j2 m2 | j3 m3>.
    Implements the pure Racah formula to avoid any numerical integration noise.
    """
    if m1 + m2 != m3 or not (abs(j1 - j2) <= j3 <= j1 + j2):
        return 0.0
    
    # Physics rule: parity conservation for <j1 0 j2 0 | j3 0>
    if m1 == 0 and m2 == 0 and m3 == 0 and (j1 + j2 + j3) % 2 != 0:
        return 0.0

    # Racah Triangle Coefficient
    delta = math.sqrt(math.factorial(int(j1+j2-j3)) * math.factorial(int(j1-j2+j3)) * math.factorial(int(-j1+j2+j3)) / math.factorial(int(j1+j2+j3+1)))
    
    prefactor = math.sqrt(2 * j3 + 1) * delta * math.sqrt(
        math.factorial(int(j1+m1)) * math.factorial(int(j1-m1)) * math.factorial(int(j2+m2)) * math.factorial(int(j2-m2)) * math.factorial(int(j3+m3)) * math.factorial(int(j3-m3))
    )
    
    res = 0.0
    k_min = max(0, j2 - j3 - m1, j1 - j3 + m2)
    k_max = min(j1 + j2 - j3, j1 - m1, j2 + m2)
    
    for k in range(int(k_min), int(k_max) + 1):
        num = (-1)**k
        den = (math.factorial(int(k)) * math.factorial(int(j1+j2-j3-k)) * math.factorial(int(j1-m1-k)) * math.factorial(int(j2+m2-k)) * math.factorial(int(j3-j2+m1+k)) * math.factorial(int(j3-j1-m2+k)))
        res += num / den
        
    return prefactor * res


class AmplitudeModel:
    def __init__(self, Mx_min, Mx_max, num_bins, m1=0.1395, m2=0.1395):
        """
        Initializes the model over a specific mass window.
        """
        self.Mx = np.linspace(Mx_min, Mx_max, num_bins)
        self.waves = []
        self.m1 = m1
        self.m2 = m2

    def add_wave(self, particle, l, m, epsilon, fraction, phase=0.0):
        """
        Adds a partial wave to the model.
        """
        from partial_wave import PartialWave
        
        if epsilon not in (-1, +1):
            raise ValueError("epsilon must be -1 or +1")
        if abs(m) > l:
            raise ValueError(f"Invalid m={m} for l={l}")
            
        wave = PartialWave(
            name_or_dict=particle, l=l, m=m, epsilon=epsilon, 
            fraction=fraction, phase=phase, 
            m1=self.m1, m2=self.m2
        )
        self.waves.append(wave)

    def _get_normalized_amps(self):
        """
        Calculates the mass-dependent amplitudes, normalized to their target fractions.
        Returns a dictionary mapping (epsilon, l, m) to complex amplitude arrays.
        """
        normalized_amplitudes = {}
        total_fraction = sum(wave.fraction for wave in self.waves)
        fraction_scale = 1.0 / total_fraction if total_fraction > 1.0 else 1.0
        
        if total_fraction > 1.0:
            print(f"Warning: Sum of fractions ({total_fraction}) > 1.0. Scaling down.")
            
        for wave in self.waves:
            raw_shape = wave.get_shape(self.Mx)
            intensity = np.abs(raw_shape)**2
            raw_yield = simpson(y=intensity, x=self.Mx)
            
            target_fraction = wave.fraction * fraction_scale
            C_k = 0.0 if raw_yield <= 0 else np.sqrt(target_fraction / raw_yield)
            
            complex_amp = C_k * np.exp(1j * wave.phase) * raw_shape
            
            # FIX: Properly sum waves that share the exact same quantum numbers
            key = (wave.epsilon, wave.l, wave.m)
            if key not in normalized_amplitudes:
                normalized_amplitudes[key] = np.zeros_like(self.Mx, dtype=complex)
            normalized_amplitudes[key] += complex_amp
            
        return normalized_amplitudes

    def generate_moments(self, L_max, alpha=0, include_zeros=False):
        """
        Calculates moments H^alpha(L, M) directly from partial waves 
        using Exact SDMEs and Clebsch-Gordan coefficients (Glazier & Mathieu, Eq 8 & 10).
        NO numerical angular integration used!
        """
        if alpha not in [0, 1, 2, 3]:
            raise ValueError("Alpha must be 0, 1, 2, or 3")
            
        amps = self._get_normalized_amps()
        
        # Find unique spins l and reflectivities epsilon present in the model
        epsilons = set(k[0] for k in amps.keys())
        spins = sorted(set(k[1] for k in amps.keys()))
        
        # Safe zero-array for missing waves
        zero_amp = np.zeros_like(self.Mx, dtype=complex)
        
        moments = {}
        
        for L in range(L_max + 1):
            for M in range(0, L + 1):
                # Work with a complex sum initially
                H_LM = np.zeros_like(self.Mx, dtype=complex)
                
                for eps in epsilons:
                    for l in spins:
                        for lp in spins:
                            # Precompute geometric coupling factor (Eq 8)
                            cg_zero = clebsch(lp, 0, L, 0, l, 0)
                            if cg_zero == 0: continue
                            
                            term_factor = np.sqrt((2*lp + 1)/(2*l + 1)) * cg_zero
                            
                            # Sum over all m, mp projections
                            for m in range(-l, l + 1):
                                for mp in range(-lp, lp + 1):
                                    if m - mp != M: continue
                                    
                                    cg_m = clebsch(lp, mp, L, M, l, m)
                                    if cg_m == 0: continue
                                    
                                    # Fetch amplitudes (default to zero array if wave doesn't exist)
                                    A_lm     = amps.get((eps, l, m), zero_amp)
                                    A_lpm    = amps.get((eps, lp, mp), zero_amp)
                                    A_l_nm   = amps.get((eps, l, -m), zero_amp)
                                    A_lp_nmp = amps.get((eps, lp, -mp), zero_amp)
                                    
                                    # --- SDME EVALUATION (Eq 10) ---
                                    rho = 0.0
                                    if alpha == 0:
                                        rho = A_lm * np.conj(A_lpm) + ((-1)**(m-mp)) * A_l_nm * np.conj(A_lp_nmp)
                                    elif alpha == 1:
                                        rho = -eps * ( ((-1)**m) * A_l_nm * np.conj(A_lpm) + ((-1)**mp) * A_lm * np.conj(A_lp_nmp) )
                                    elif alpha == 2:
                                        rho = -1j * eps * ( ((-1)**m) * A_l_nm * np.conj(A_lpm) - ((-1)**mp) * A_lm * np.conj(A_lp_nmp) )
                                    elif alpha == 3:
                                        rho = A_lm * np.conj(A_lpm) - ((-1)**(m-mp)) * A_l_nm * np.conj(A_lp_nmp)
                                    
                                    H_LM += term_factor * cg_m * rho
                
                # Enforce physics constraints: H0,H1 are purely Real; H2,H3 are purely Imaginary
                final_val = np.real(H_LM) if alpha in [0, 1] else np.imag(H_LM)
                
                if include_zeros or np.any(np.abs(final_val) > 1e-13):
                    moments[(L, M)] = final_val
                    
        return moments

  
