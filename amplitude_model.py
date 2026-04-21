import numpy as np
from scipy.integrate import simpson
from partial_wave import PartialWave
import cg_engine as cg

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
        wave = PartialWave(
            name_or_dict=particle, l=l, m=m, epsilon=epsilon, 
            fraction=fraction, phase=phase, 
            m1=self.m1, m2=self.m2
        )
        self.waves.append(wave)

    def _normalize_waves(self):
        normalized_amplitudes = []
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
            normalized_amplitudes.append((wave, complex_amp))
            
        return normalized_amplitudes

    def generate_moments(self, L_max, alpha=0, include_zeros=False):
        """
        Calculates moments H^alpha(L, M) following the Mathieu reflectivity formulation.
        alpha = 0 (Unpol), 1 (Lin Cos), 2 (Lin Sin), 3 (Circular)
        """
        if alpha not in [0, 1, 2, 3]:
            raise ValueError("Alpha must be 0, 1, 2, or 3")
            
        normalized_amplitudes = self._normalize_waves()
        moments = {}
        
        for L in range(L_max + 1):
            for M in range(0, L + 1):
                H_LM = np.zeros_like(self.Mx, dtype=float)
                
                for w1, A1 in normalized_amplitudes:
                    for w2, A2 in normalized_amplitudes:
                        
                        # --- MATHIEU REFLECTIVITY SWITCHBOARD ---
                        if alpha == 0:
                            # H0 ~ |A+|^2 + |A-|^2
                            if w1.epsilon != w2.epsilon: continue
                            eps_factor = 1.0
                            bilinear_part = np.real(A1 * np.conj(A2))
                            
                        elif alpha == 1:
                            # H1 ~ |A+|^2 - |A-|^2
                            if w1.epsilon != w2.epsilon: continue
                            eps_factor = w1.epsilon
                            bilinear_part = np.real(A1 * np.conj(A2))
                            
                        elif alpha == 2:
                            # H2 ~ 2 Im(A+ A-*)
                            if w1.epsilon == w2.epsilon: continue
                            # w1.epsilon flips sign for the (-, +) pair to cleanly extract the Im part
                            eps_factor = w1.epsilon 
                            bilinear_part = np.imag(A1 * np.conj(A2))
                            
                        elif alpha == 3:
                            # H3 ~ 2 Re(A+ A-*)
                            if w1.epsilon == w2.epsilon: continue
                            eps_factor = 1.0
                            bilinear_part = np.real(A1 * np.conj(A2))
                        # ----------------------------------------
                        
                        factor = cg.get_moment_factor(w1.l, w1.m, w2.l, w2.m, L, M)
                        if factor == 0.0:
                            continue
                            
                        H_LM += eps_factor * factor * bilinear_part
                        
                if include_zeros or np.any(H_LM != 0):
                    moments[(L, M)] = H_LM
                    
        return moments
