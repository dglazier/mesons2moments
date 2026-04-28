import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from amplitude_model import AmplitudeModel

# ==========================================
# 1. HELPER FUNCTIONS & VISUALIZATIONS
# ==========================================

def draw_m_dial(l, m):
    """Generates a Matplotlib polar plot acting as a 'compass' for the m-projection."""
    fig, ax = plt.subplots(figsize=(2.5, 1.5), subplot_kw={'projection': 'polar'})
    
    if l > 0:
        theta = np.pi/2 - (m/l) * (np.pi/2)
    else:
        theta = np.pi/2
        
    ax.set_thetamin(0)
    ax.set_thetamax(180)
    
    ax.annotate('', xy=(theta, 1), xytext=(0, 0),
                arrowprops=dict(facecolor='crimson', edgecolor='black', width=3, headwidth=10))
    
    ax.set_yticklabels([])
    ax.set_xticklabels(['Right (+m)', '', 'Up (0)', '', 'Left (-m)'], fontsize=7)
    ax.set_theta_direction(1)
    ax.set_theta_offset(0)
    
    fig.patch.set_alpha(0.0)
    ax.patch.set_alpha(0.0)
    
    return fig

# ==========================================
# 2. PAGE CONFIGURATION & STATE MANAGEMENT
# ==========================================

st.set_page_config(page_title="Mesons2Moments", layout="wide")

if 'inventory' not in st.session_state:
    st.session_state.inventory = []

st.title("🎛️ Mesons2Moments: Interactive PWA Dashboard")

# ==========================================
# 3. SIDEBAR: GLOBAL EXPERIMENT SETTINGS
# ==========================================

st.sidebar.header("⚙️ Global Settings")

if st.sidebar.button("🔄 Reset Entire Simulation", type="primary", use_container_width=True):
    st.session_state.inventory = []
    st.rerun()

st.sidebar.divider()

config_lmax = st.sidebar.number_input("Max Observable Spin (L_max)", 0, 10, 4, step=1)
config_polarized = st.sidebar.checkbox("Generate Polarized Observables", value=False)

st.sidebar.divider()
st.sidebar.caption("Kinematic Window")
mx_min = st.sidebar.number_input("Min Mass (GeV)", 0.1, 3.0, 0.3)
mx_max = st.sidebar.number_input("Max Mass (GeV)", 0.1, 5.0, 1.7)
num_bins = st.sidebar.number_input("Mass Bins", 10, 1000, 200)

# ==========================================
# MAIN LAYOUT SPLIT
# ==========================================
left_panel, right_panel = st.columns([4, 5], gap="large")

with left_panel:
    # ------------------------------------------
    # 4. TOP LEFT: ADDING NEW WAVES
    # ------------------------------------------
    with st.expander("➕ Add a New Partial Wave", expanded=True):
        col_params, col_dial = st.columns([2, 1])
        
        with col_params:
            r1c1, r1c2 = st.columns(2)
            input_mass = r1c1.number_input("Mass (GeV)", 0.1, 3.0, 0.77, step=0.01)
            input_width = r1c2.number_input("Width (GeV)", 0.01, 1.0, 0.15, step=0.01)
            
            r2c1, r2c2 = st.columns(2)
            input_l = r2c1.number_input("Spin (l)", 0, 10, 1, step=1)
            
            # --- THE SLIDER FIX ---
            if input_l == 0:
                input_m = 0
                r2c2.markdown("<br>m-projection: **0**", unsafe_allow_html=True)
            else:
                m_options = list(range(-input_l, input_l + 1))
                input_m = r2c2.select_slider("m-projection", options=m_options, value=0)
            
            r3c1, r3c2 = st.columns(2)
            input_frac = r3c1.slider("Initial Fraction", 0.0, 1.0, 0.3, step=0.05)
            input_phase = r3c2.slider("Initial Phase (rad)", -3.14, 3.14, 0.0, step=0.1)
            
            input_eps = st.selectbox("Reflectivity (eps)", options=[1, -1]) if config_polarized else 1

            if st.button("Save Wave to Inventory", type="primary", use_container_width=True):
                st.session_state.inventory.append({
                    'mass': input_mass, 'width': input_width, 'l': input_l, 
                    'm': input_m, 'eps': input_eps, 'frac': input_frac, 'phase': input_phase
                })
                st.rerun()
                
        with col_dial:
            st.markdown("<div style='text-align: center'><b>Orientation</b></div>", unsafe_allow_html=True)
            st.pyplot(draw_m_dial(input_l, input_m))

    # ------------------------------------------
    # 5. BOTTOM LEFT: ACTIVE WAVE INVENTORY
    # ------------------------------------------
    st.subheader("📋 Active Wave Inventory")
    
    if not st.session_state.inventory:
        st.info("Your inventory is empty. Add a wave above.")
    else:
        for idx, wave in enumerate(st.session_state.inventory):
            with st.container(border=True):
                eps_str = f", ε={wave['eps']}" if config_polarized else ""
                st.markdown(f"**Wave {idx}: l={wave['l']}, m={wave['m']}{eps_str}** | M={wave['mass']:.2f}, Γ={wave['width']:.2f}")
                
                sc1, sc2, sc3 = st.columns([3, 3, 1])
                wave['frac'] = sc1.slider("Frac", 0.0, 1.0, wave['frac'], key=f"f_{idx}", label_visibility="collapsed")
                wave['phase'] = sc2.slider("Phase", -3.14, 3.14, wave['phase'], key=f"p_{idx}", label_visibility="collapsed")
                if sc3.button("🗑️", key=f"d_{idx}", help="Delete Wave"):
                    st.session_state.inventory.pop(idx)
                    st.rerun()

with right_panel:
    # ------------------------------------------
    # 6. RIGHT SIDE: PHYSICS CALCULATIONS & PLOTS
    # ------------------------------------------
    st.subheader("📊 Resulting Moments")
    
    if not st.session_state.inventory:
        st.warning("👈 Add some waves on the left to see the coherent interference patterns here.")
    else:
        # --- SMART PHYSICS WARNING ---
        if config_polarized:
            eps_values = set(w['eps'] for w in st.session_state.inventory)
            if len(eps_values) == 1:
                st.info("💡 **Physics Tip:** All your current waves have the same reflectivity! To see interference in $H^2$ and $H^3$, you must add waves with both $\epsilon=+1$ and $\epsilon=-1$.")

        model = AmplitudeModel(Mx_min=mx_min, Mx_max=mx_max, num_bins=num_bins)
        
        for idx, w in enumerate(st.session_state.inventory):
            model.add_wave({'mass': w['mass'], 'width': w['width'], 'name': f"W_{idx}"}, 
                           l=w['l'], m=w['m'], epsilon=w['eps'], fraction=w['frac'], phase=w['phase'])
            
        alphas_to_generate = [0, 1, 2, 3] if config_polarized else [0]
        generated_data = {}
        
        for alpha in alphas_to_generate:
            generated_data[alpha] = model.generate_moments(L_max=config_lmax, alpha=alpha, include_zeros=True)
                
        tabs = st.tabs([f"H^{a} (Alpha={a})" for a in alphas_to_generate]) if config_polarized else [st.container()]
        
        for tab_idx, alpha in enumerate(alphas_to_generate):
            with tabs[tab_idx]:
                moments_dict = generated_data[alpha]
                sorted_keys = sorted(moments_dict.keys(), key=lambda k: (k[0], k[1]))
                plot_keys = sorted_keys[:9] 
                
                fig, axes = plt.subplots(3, 3, figsize=(10, 8.5))
                axes = axes.flatten()
                
                for i, ax in enumerate(axes):
                    if i < len(plot_keys):
                        L, M = plot_keys[i]
                        ax.plot(model.Mx, moments_dict[(L, M)], color='royalblue', lw=3)
                        ax.set_title(f"H({L}, {M})", fontweight='bold')
                        ax.axhline(0, color='black', lw=1, alpha=0.3)
                        ax.grid(True, linestyle='--', alpha=0.5)
                        
                        if np.all(moments_dict[(L, M)] == 0):
                            ax.set_facecolor('#f8f9fa')
                    else:
                        ax.axis('off')
                        
                plt.tight_layout()
                st.pyplot(fig, use_container_width=True)
