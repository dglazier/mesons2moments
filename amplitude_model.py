import numpy as np
from scipy.integrate import simpson
from scipy.special import sph_harm
from partial_wave import PartialWave


def _Ylm(l, m, theta, phi):
    return sph_harm(m, l, phi, theta)


class AmplitudeModel:
    _N_THETA = 100
    _N_PHI = 200
    _ZERO_TOL = 1.0e-13

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
        if epsilon not in (-1, +1):
            raise ValueError("epsilon must be -1 or +1")
        if abs(m) > l:
            raise ValueError(f"Invalid m={m} for l={l}")

        self.waves.append(
            PartialWave(
                name_or_dict=particle,
                l=l,
                m=m,
                epsilon=epsilon,
                fraction=fraction,
                phase=phase,
                m1=self.m1,
                m2=self.m2,
            )
        )

    def _normalize_waves(self):
        normalized_amplitudes = []
        total_fraction = sum(wave.fraction for wave in self.waves)
        fraction_scale = 1.0 / total_fraction if total_fraction > 1.0 else 1.0

        if total_fraction > 1.0:
            print(f"Warning: Sum of fractions ({total_fraction}) > 1.0. Scaling down.")

        for wave in self.waves:
            raw_shape = wave.get_shape(self.Mx)
            raw_yield = simpson(y=np.abs(raw_shape) ** 2, x=self.Mx)

            target_fraction = wave.fraction * fraction_scale
            C_k = 0.0 if raw_yield <= 0.0 else np.sqrt(target_fraction / raw_yield)

            normalized_amplitudes.append(
                (wave, C_k * np.exp(1j * wave.phase) * raw_shape)
            )

        return normalized_amplitudes

    def _angular_grid(self):
        """
        Builds the angular integration grid.
        """
        cos_theta, w_theta = np.polynomial.legendre.leggauss(self._N_THETA)
        theta = np.arccos(cos_theta)

        phi = np.linspace(0.0, 2.0 * np.pi, self._N_PHI, endpoint=False)
        w_phi = (2.0 * np.pi) / self._N_PHI

        TH, PH = np.meshgrid(theta, phi, indexing="ij")
        W = (w_theta[:, None] * w_phi) * np.ones_like(TH)

        return TH.ravel(), PH.ravel(), W.ravel()

    def _build_U_and_Utilde(self, normalized_amplitudes, epsilon, theta, phi):
        """
        U^(epsilon)      = sum_{l,m} a_{lm}^{epsilon} Y_l^m
        Utilde^(epsilon) = sum_{l,m} a_{lm}^{epsilon} (Y_l^m)^*
        """
        selected = [(w, A) for w, A in normalized_amplitudes if w.epsilon == epsilon]

        n_mass = len(self.Mx)

        if not selected:
            z = np.zeros((n_mass, len(theta)), dtype=complex)
            return z, z

        Y = np.asarray(
            [_Ylm(w.l, w.m, theta, phi) for w, _ in selected],
            dtype=complex,
        )

        A = np.asarray([amp for _, amp in selected], dtype=complex).T

        U = A @ Y
        Utilde = A @ np.conjugate(Y)

        return U, Utilde

    def _intensity(self, alpha):
        """
        Calculates the angular intensity component I^alpha.
        """
        if alpha not in (0, 1, 2, 3):
            raise ValueError("Alpha must be 0, 1, 2, or 3")

        normalized = self._normalize_waves()
        theta, phi, weights = self._angular_grid()

        U_plus, Ut_plus = self._build_U_and_Utilde(normalized, +1, theta, phi)
        U_minus, Ut_minus = self._build_U_and_Utilde(normalized, -1, theta, phi)

        if alpha == 0:
            intensity = (
                np.abs(U_plus) ** 2
                + np.abs(Ut_plus) ** 2
                + np.abs(U_minus) ** 2
                + np.abs(Ut_minus) ** 2
            )

        elif alpha == 1:
            intensity = (
                -2.0 * np.real(U_plus * np.conjugate(Ut_plus))
                + 2.0 * np.real(U_minus * np.conjugate(Ut_minus))
            )

        elif alpha == 2:
            intensity = (
                -2.0 * np.imag(U_plus * np.conjugate(Ut_plus))
                + 2.0 * np.imag(U_minus * np.conjugate(Ut_minus))
            )

        else:
            intensity = (
                np.abs(U_plus) ** 2
                - np.abs(Ut_plus) ** 2
                + np.abs(U_minus) ** 2
                - np.abs(Ut_minus) ** 2
            )

        return theta, phi, weights, intensity

    def generate_moments(self, L_max, alpha=0, include_zeros=False):
        """
        Calculates moments H^alpha(L, M) following the Mathieu reflectivity formulation.
        alpha = 0 (Unpol), 1 (Lin Cos), 2 (Lin Sin), 3 (Circular)
        """
        if alpha not in (0, 1, 2, 3):
            raise ValueError("Alpha must be 0, 1, 2, or 3")

        complex_moments = self.generate_moments_complex(
            L_max=L_max,
            alpha=alpha,
            include_zeros=include_zeros,
        )

        moments = {}

        for key, val in complex_moments.items():
            H_LM = np.real(val) if alpha in (0, 1) else np.imag(val)

            if include_zeros or np.any(np.abs(H_LM) > self._ZERO_TOL):
                moments[key] = H_LM

        return moments
