from amplitude_model import AmplitudeModel
import plot_utils
import io_utils

print("Building pi+ pi- Amplitude Model...")

# 1. Initialize the Kinematic Window
# Let's go from 0.3 to 1.7 GeV to easily cover the f2(1270) tail
model = AmplitudeModel(Mx_min=0.3, Mx_max=1.7, num_bins=300)

# 2. Add the Resonances
# I am making some standard assumptions for the M projections and phases here.

# ---------------------------------------------------------
# S-WAVES (L=0)
# ---------------------------------------------------------
# 1. The broad background: f0(500) / sigma | PDG ID: 9000212
model.add_wave(9000221, l=0, m=0, epsilon=1, fraction=0.20, phase=0.0)

# S-wave: f0(980) | PDG ID: 9000211
model.add_wave(9000211, l=0, m=0, epsilon=1, fraction=0.05, phase=3.14)

# P-wave: rho(770) | PDG ID: 113
model.add_wave(113, l=1, m=1, epsilon=1, fraction=0.55, phase=-1.2)
model.add_wave(113, l=1, m=0, epsilon=1, fraction=0.15, phase=-1.5)
model.add_wave(113, l=1, m=-1, epsilon=1, fraction=0.05, phase=0.7)

# D-wave: f2(1270) | PDG ID: 225
model.add_wave(225, l=2, m=2, epsilon=1, fraction=0.05, phase=2.5)
model.add_wave(225, l=2, m=1, epsilon=1, fraction=0.02, phase=-2.5)
model.add_wave(225, l=2, m=0, epsilon=1, fraction=0.02, phase=2)

# F-wave: rho_3(1690) | PDG ID: 115
# We set the phase to 0.7 to perfectly align with the rho(m=-1) wave. 
# This alignment projects out the "Real part" of the rho Breit-Wigner,
# forcing it to cross zero exactly at 0.77 GeV!
model.add_wave(115, l=3, m=1, epsilon=1, fraction=0.1, phase=0.7)

# We can also add an m=0 F-wave to help shape H(4,1) if needed
model.add_wave(115, l=3, m=0, epsilon=1, fraction=0.01, phase=1.5)
# 3. Generate the Moments
# S, P, and D waves will interfere to produce moments up to L_max = 4
# Generate moments and force it to include the forbidden ones
print("Generating moments up to L=4...")
moments = model.generate_moments(L_max=4, include_zeros=True)

# 4. Visualize
print("Opening plots. Close the plot windows to continue to file export...")
plot_utils.plot_moments(model.Mx, moments, max_rows=3, max_cols=5)
plot_utils.show_all_plots()

# 5. Export (Executes after you close the plots)
df = io_utils.moments_to_dataframe(model.Mx, moments)
io_utils.export_to_csv(df, "pipi_model_moments.csv")
