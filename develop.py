import numpy as np
import physics_engine as pe

def test_breakup_momentum():
    print("--- Testing Breakup Momentum ---")
    m1, m2 = 0.139, 0.139 # Approximate charged pion masses
    
    # 1. Test below threshold (e.g., M = 0.200 GeV)
    M_below = np.array([0.200])
    q_below = pe.get_breakup_momentum(M_below, m1, m2)
    assert np.all(q_below == 0), f"FAIL: Expected q=0 below threshold, got {q_below}"
    
    # 2. Test exactly at threshold (M = m1 + m2)
    M_thresh = np.array([m1 + m2])
    q_thresh = pe.get_breakup_momentum(M_thresh, m1, m2)
    assert np.all(q_thresh == 0), f"FAIL: Expected q=0 at threshold, got {q_thresh}"

    # 3. Test above threshold (e.g., M = 0.770 GeV)
    M_above = np.array([0.770])
    q_above = pe.get_breakup_momentum(M_above, m1, m2)
    assert np.all(q_above > 0), f"FAIL: Expected q>0 above threshold, got {q_above}"
    
    print("✓ Breakup momentum tests passed!\n")


def test_blatt_weisskopf():
    print("--- Testing Blatt-Weisskopf Factors ---")
    q = np.array([0.1, 0.5, 1.0])
    
    # 1. L=0 should be exactly 1.0 everywhere
    F0 = pe.blatt_weisskopf(0, q)
    assert np.all(F0 == 1.0), "FAIL: L=0 factor should be exactly 1"
    
    # 2. Higher L should be strictly between 0 and 1, and scale with momentum
    F1 = pe.blatt_weisskopf(1, q)
    F2 = pe.blatt_weisskopf(2, q)
    
    assert np.all((F1 > 0) & (F1 < 1.0)), "FAIL: L=1 factor should be between 0 and 1"
    assert np.all((F2 > 0) & (F2 < 1.0)), "FAIL: L=2 factor should be between 0 and 1"
    
    # F2 centrifugal barrier should suppress low momentum more strongly than F1
    assert F2[0] < F1[0], "FAIL: L=2 should be more suppressed at low q than L=1"
    
    print("✓ Blatt-Weisskopf tests passed!\n")


def test_breit_wigner():
    print("--- Testing Relativistic Breit-Wigner ---")
    # Simulate a mass window from 200 MeV to 1.2 GeV
    M = np.linspace(0.2, 1.2, 1000) 
    
    # Let's test the rho(770) -> pi+ pi-
    M0 = 0.7754  
    Gamma0 = 0.149 
    L = 1 # P-wave decay
    m1, m2 = 0.1395, 0.1395
    
    amp = pe.relativistic_breit_wigner(M, M0, Gamma0, L, m1, m2)
    
    # 1. Check complex types
    assert np.iscomplexobj(amp), "FAIL: Amplitude must be a complex array"
    
    # 2. Check threshold behavior
    below_thresh_mask = M <= (m1 + m2)
    assert np.all(np.abs(amp[below_thresh_mask]) == 0.0), "FAIL: Amplitude must be exactly 0 below decay threshold"
    
    # 3. Check Peak Mass
    intensity = np.abs(amp)**2
    peak_idx = np.argmax(intensity)
    peak_mass = M[peak_idx]
    
    # Note: The peak of the intensity shape isn't exactly at M0 due to the mass-dependent width 
    # and phase space factors opening up, but it should be very close.
    assert abs(peak_mass - M0) < 0.02, f"FAIL: Peak at {peak_mass:.3f} is too far from M0={M0:.3f}"
    
    print(f"✓ Breit-Wigner tests passed! (Peak correctly found near {peak_mass:.3f} GeV)\n")

def test_partial_wave():
    print("--- Testing PartialWave Object ---")
    from partial_wave import PartialWave
    
    m1, m2 = 0.1395, 0.1395
    
    # 1. Test PDG Lookup
    rho = PartialWave("rho(770)0", L=1, M=1, epsilon=1, fraction=0.4, phase=0.0, m1=m1, m2=m2)
    # Note: PDG mass is ~0.77526 GeV
    assert abs(rho.mass - 0.775) < 0.01, f"FAIL: Expected rho mass ~0.775 GeV, got {rho.mass}"
    assert abs(rho.width - 0.149) < 0.01, f"FAIL: Expected rho width ~0.149 GeV, got {rho.width}"
    
    # 2. Test Custom Dictionary
    custom = PartialWave({'mass': 1.6, 'width': 0.3, 'name': 'pi_1'}, L=1, M=0, epsilon=-1, fraction=0.1, phase=1.0, m1=m1, m2=m2)
    assert custom.mass == 1.6, "FAIL: Custom mass not set correctly"
    
    # 3. Test get_shape integration with the physics engine
    M_X = np.linspace(0.2, 1.2, 100)
    shape = rho.get_shape(M_X)
    assert np.iscomplexobj(shape), "FAIL: Shape must be complex"
    assert len(shape) == 100, "FAIL: Shape array length mismatch"
    
    print("✓ PartialWave tests passed!\n")

def test_cg_engine():
    print("--- Testing Clebsch-Gordan Engine ---")
    import cg_engine as cg
    import numpy as np
    
    # 1. Test Selection Rules (M must equal m1 - m2)
    # P-wave (1, 1) interfering with P-wave (1, -1) cannot produce M=0
    factor_bad_M = cg.get_moment_factor(l1=1, m1=1, l2=1, m2=-1, L=2, M=0)
    assert factor_bad_M == 0.0, "FAIL: Selection rule M = m1 - m2 violated"
    
    # 2. Test Triangle Inequality
    # Two P-waves (l=1) cannot produce an L=4 moment
    factor_bad_L = cg.get_moment_factor(l1=1, m1=0, l2=1, m2=0, L=4, M=0)
    assert factor_bad_L == 0.0, "FAIL: Triangle inequality for L violated"
    
    # 3. Test Parity Rule
    # P-wave (l=1) and D-wave (l=2) cannot produce an L=2 moment 
    # because 1 + 2 + 2 = 5 (odd)
    factor_bad_parity = cg.get_moment_factor(l1=1, m1=0, l2=2, m2=0, L=2, M=0)
    assert factor_bad_parity == 0.0, "FAIL: Parity rule (l1+l2+L must be even) violated"
    
    # 4. Test a known valid factor (Intensity / 0th Moment)
    # The interference of a wave with itself into H(0,0) should be positive
    factor_H00 = cg.get_moment_factor(l1=2, m1=1, l2=2, m2=1, L=0, M=0)
    assert factor_H00 > 0.0, "FAIL: Self-interference into H(0,0) must be positive"
    
    # Check that caching works implicitly (it shouldn't crash on repeat calls)
    factor_H00_repeat = cg.get_moment_factor(l1=2, m1=1, l2=2, m2=1, L=0, M=0)
    assert factor_H00 == factor_H00_repeat, "FAIL: Caching produced inconsistent results"

    print("✓ Clebsch-Gordan tests passed!\n")

def test_amplitude_model():
    print("--- Testing AmplitudeModel Orchestrator ---")
    from amplitude_model import AmplitudeModel
    from scipy.integrate import simpson
    
    # 1. Setup a model from 0.3 to 1.5 GeV
    model = AmplitudeModel(Mx_min=0.3, Mx_max=1.5, num_bins=200)
    
    # 2. Add two waves with known fractions
    # A P-wave (rho) making up 60% of the total cross-section
    model.add_wave("rho(770)0", L=1, M=1, epsilon=1, fraction=0.60)
    # A D-wave (f2) making up 40%
    model.add_wave("f(2)(1270)", L=2, M=0, epsilon=1, fraction=0.40, phase=1.5)
    # 3. Generate moments up to L=4
    moments = model.generate_moments(L_max=4)
    
 # 4. Rigorous Normalization Checks
    assert (0, 0) in moments, "FAIL: H(0,0) moment was not generated"
    H00 = moments[(0, 0)]
    
    # Integrate the H(0,0) array over the mass window
    total_yield_H00 = simpson(y=H00, x=model.Mx)
    
    # Multiply by sqrt(4*pi) to get the true angularly-integrated physical yield
    physical_yield = total_yield_H00 * np.sqrt(4 * np.pi)
    
    # Because we asked for 0.60 + 0.40 = 1.0, the physical yield must be 1.0
    assert abs(physical_yield - 1.0) < 0.01, f"FAIL: Expected total yield 1.0, got {physical_yield}"
    
    # 5. Check Interference Generation
    # Since we have an L=1 and L=2 wave with the same reflectivity, 
    # they must interfere to produce an odd-L moment like H(1,1) or H(3,1)
    assert (1, 1) in moments or (1, -1) in moments, "FAIL: Expected odd moment from P-D interference is missing"
    
    print("✓ AmplitudeModel integration tests passed!\n")
    
if __name__ == "__main__":
    print("Starting Test Suite for physics_engine.py...\n")
    test_breakup_momentum()
    test_blatt_weisskopf()
    test_breit_wigner()
    test_partial_wave()
    test_cg_engine()
    test_amplitude_model()
    print("⭐⭐⭐ ALL TESTS PASSED! ⭐⭐⭐")
