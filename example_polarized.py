from amplitude_model import AmplitudeModel
import plot_utils
#import io_utils

print("Building Polarized pi+ pi- Amplitude Model...")

model = AmplitudeModel(Mx_min=0.3, Mx_max=1.7, num_bins=300)

# --- Natural Parity Exchange Waves (epsilon = +1) ---
model.add_wave(9000221, l=0, m=0, epsilon=1, fraction=0.20, phase=0.0)    # f0(500)
model.add_wave(9000211, l=0, m=0, epsilon=1, fraction=0.05, phase=3.14)   # f0(980)

model.add_wave(113, l=1, m=1, epsilon=1, fraction=0.40, phase=-1.2)       # rho
model.add_wave(113, l=1, m=0, epsilon=1, fraction=0.10, phase=-1.5)       # rho
model.add_wave(113, l=1, m=-1, epsilon=1, fraction=0.05, phase=0.7)       # rho

model.add_wave(115, l=3, m=1, epsilon=1, fraction=0.03, phase=0.7)        # rho_3 (fixes H(4,2))
model.add_wave(115, l=3, m=0, epsilon=1, fraction=0.01, phase=1.5)        # rho_3

# --- Unnatural Parity Exchange Waves (epsilon = -1) ---
# Without these, H^1 would just be identical to H^0, and H^2/H^3 would be exactly zero!
model.add_wave(113, l=1, m=1, epsilon=-1, fraction=0.10, phase=0.0)       # rho unnatural
model.add_wave(113, l=1, m=0, epsilon=-1, fraction=0.06, phase=0.5)       # rho unnatural

print("Generating moments for all observables...")

# Loop through all 4 observables
for alpha in [0, 1, 2, 3]:
    print(f" -> Calculating H^{alpha}")
    moments = model.generate_moments(L_max=4, alpha=alpha, include_zeros=True)
    
    # Export data to file
    #df = io_utils.moments_to_dataframe(model.Mx, moments)
    #io_utils.export_to_csv(df, f"pipi_model_H_alpha_{alpha}.csv")
    
    # Queue up the plot canvas for this alpha in the background
    plot_utils.plot_moments(model.Mx, moments, title_prefix=f"H^{alpha} Observables")

print("\nOpening all 4 plots simultaneously. Close them all to finish the script.")
plot_utils.show_all_plots()

print("All polarized moments successfully generated and saved!")
