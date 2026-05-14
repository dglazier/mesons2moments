import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import random
from particle import Particle
from amplitude_model import AmplitudeModel
import io_utils

# ==========================================
# 1. VISUALIZATION HELPERS & CSS
# ==========================================

st.markdown("""
<style>
    /* Primary Button Styling */
    [data-testid="baseButton-primary"] {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%) !important;
        border: none !important;
        color: white !important;
        font-size: 1.1rem !important;
        padding: 0.75rem !important;
        box-shadow: 0px 4px 15px rgba(30, 60, 114, 0.4);
        transition: transform 0.2s ease;
    }
    [data-testid="baseButton-primary"]:hover {
        transform: translateY(-2px);
    }
    
    /* Inventory Card Buttons */
    .stButton > button {
        border-radius: 12px !important; border: 2px solid #555 !important;
        padding: 10px !important; font-family: monospace; transition: all 0.2s ease-in-out;
    }
    .stButton > button:hover {
        transform: scale(1.02); border-color: #4facfe !important;
        box-shadow: 0px 4px 10px rgba(79, 172, 254, 0.3);
    }
    .stMarkdown p {
        margin-bottom: 0px !important;
    }
    
    /* Landing Page Specific CSS */
    .hero-banner {
        background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
        padding: 3rem 2rem;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0px 10px 20px rgba(0,0,0,0.2);
    }
    .hero-banner h1 {
        color: #ffffff !important;
        font-size: 3rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
    }
    .hero-banner h3 {
        color: #4facfe !important;
        font-weight: 400;
    }
    .landing-text {
        font-size: 1.15rem;
        line-height: 1.6;
    }
    .highlight-word {
        color: #e74c3c;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. CORE DATA
# ==========================================

@st.cache_data
def build_particle_pool(j_max, m_max):
    mesons = Particle.findall(lambda p:
        p.pdgid.is_meson and p.charge == 0 and p.J is not None and
        p.mass is not None and p.width is not None and
        400 < p.mass < (m_max * 1000.0) and p.width > 10 and int(p.J) <= j_max
    )
    pool = []
    for p in mesons:
        P_str = '+' if p.P == 1 else '-' if p.P == -1 else '?'
        C_str = '+' if p.C == 1 else '-' if p.C == -1 else '?'
        pool.append({
            'name': p.name, 'mass': p.mass/1000.0, 'width': p.width/1000.0, 
            'l': int(p.J), 'P': P_str, 'C': C_str
        })
    return sorted(pool, key=lambda x: x['mass'])

# ==========================================
# 3. UI INITIALIZATION
# ==========================================

st.set_page_config(page_title="PWA Intensity Generator", layout="wide")

if 'app_mode' not in st.session_state:
    st.session_state.app_mode = 'landing'
if 'inventory' not in st.session_state:
    st.session_state.inventory = []
    st.session_state.generated_data = None
    st.session_state.Mx = None

# ==========================================
# 4. PAGE ROUTING
# ==========================================

if st.session_state.app_mode == 'landing':
    # ----------------------------------------
    # LANDING PAGE VIEW
    # ----------------------------------------
    
    # Hide the sidebar visually on the landing page
    st.markdown("""<style>[data-testid="stSidebar"] {display: none;}</style>""", unsafe_allow_html=True)
    
    col_space1, col_main, col_space2 = st.columns([1, 6, 1])
    
    with col_main:
        # Hero Banner
        st.markdown("""
        <div class="hero-banner">
            <h1>⚛️ The PWA Sandbox</h1>
            <h3>Hunting for Exotic Matter in the Quantum Realm</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Section 1: The Zoo
        st.markdown("## 🦁 The Subatomic Zoo: Meson Spectroscopy")
        col_zoo_text, col_zoo_img = st.columns([3, 2], gap="large")
        
        with col_zoo_text:
            st.markdown("""
            <div class="landing-text">
            In high school physics, you learn that protons and neutrons are made of three quarks bound together by the strong nuclear force. But the universe is much stranger than that. 
            
            When we smash high-energy particles together at national laboratories, we create <b>mesons</b>. Conventionally, a meson is a simple pair: one quark and one antiquark ($q\\bar{q}$). However, the rules of the strong force predict that much wilder <span class="highlight-word">exotic</span> combinations should exist.
            </div>
            """, unsafe_allow_html=True)
            
            st.info("""
            **The Exotic Candidates:**
            * **Tetraquarks:** Four quarks bound together ($qq\\bar{q}\\bar{q}$).
            * **Glueballs:** Particles made entirely of pure binding energy (gluons) with no quarks at all!
            * **Hybrid Mesons:** A quark and an antiquark bound together by an "excited" gluon.
            """)
            
        with col_zoo_img:
            # Local image of a particle collision event
            st.image("reaction.png", 
                     caption="Schematic of Resonant Two-Pion Photoproduction", use_container_width=True)
            
        st.divider()

        # Section 2: Fingerprints & Harmonics
        st.markdown("## 🔎 The Angular Fingerprint")
        col_harm_img, col_harm_text = st.columns([2, 3], gap="large")
        
        with col_harm_img:
            # Local image of Spherical Harmonics
            st.image("harmonics.png", 
                     caption="Visualizing Spherical Harmonics in 3D", use_container_width=True)
            
        with col_harm_text:
            st.markdown("""
            <div class="landing-text">
            To prove an exotic particle exists, we look at its <b>Quantum Numbers</b>—specifically its Spin ($J$), Parity ($P$), and Charge Parity ($C$). Because of the strict mathematical rules governing standard quark pairs, certain $J^{PC}$ combinations are absolutely forbidden. But <b>Hybrid Mesons</b> don't play by these rules!
            
            These particles only live for about $10^{-23}$ seconds before decaying into a spray of stable debris. We can't see the exotic meson itself, so we have to act like forensic scientists and study the exact <i>angles</i> of the debris flying into our detectors. 
            
            To analyze this 3D spray, we project the data onto mathematical shapes called <b>Spherical Harmonics</b>. Because exotic mesons have unique quantum numbers, they will populate specific harmonic intensities that conventional mesons cannot reach.
            </div>
            """, unsafe_allow_html=True)
            
            st.success("""
            🥁 **What is a Spherical Harmonic?** Think of the skin of a drum: when you strike it, it vibrates in complex 2D wave patterns (the fundamental thump in the center, the higher overtones near the edges). **Spherical harmonics** are the exact same mathematical concept, but wrapped around the 3D surface of a sphere. If you have taken chemistry, you have already seen them! The $s$, $p$, $d$, and $f$ electron orbitals around an atom are just 3D plots of spherical harmonics.
            """)

        st.divider()
        
        # Section 3: Interference
        st.markdown("## 🌊 Quantum Interference")
        st.warning("""
        **Here is where the quantum mechanics gets weird:** particles act like waves. When we run an experiment, we don't just create one type of meson; we often create several different overlapping states at the exact same time. 
        
        As these particles decay, their quantum probability waves **interfere** with one another—just like overlapping ripples in a pond. When you look at the generated graphs in this app, you will notice that **some intensities only light up (become non-zero) because of the direct interference between two different particle states.**
        """)

        st.write("")
        st.markdown("<h3 style='text-align: center;'>Are you ready to build your own quantum model?</h3>", unsafe_allow_html=True)
        st.write("")
        
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            if st.button("🚀 START THE SANDBOX", type="primary", use_container_width=True):
                st.session_state.app_mode = 'generator'
                st.rerun()
                
        st.write("")
        st.write("")

elif st.session_state.app_mode == 'generator':
    # ----------------------------------------
    # GENERATOR SANDBOX VIEW
    # ----------------------------------------
    
    with st.sidebar:
        st.header("⚙️ Generator Settings")
        st.divider()
        st.subheader("Kinematics")
        cfg_jmax = st.number_input("Max Spin (J)", 0, 10, 4)
        cfg_mmax = st.slider("Max Mass (GeV)", 1.5, 3.0, 2.5, step=0.1)
        
        st.divider()
        cfg_pol = st.checkbox("Include Polarization", value=False)
        if cfg_pol:
            cfg_refl = st.radio("Number of Reflectivities", [1, 2], index=1, help="1 = Natural (+1) only. 2 = Both.")
        else:
            cfg_refl = 1
            st.caption("Polarization disabled.")
            
        if st.button("🗑️ Clear Model"):
            st.session_state.inventory = []
            st.session_state.generated_data = None
            st.rerun()
            
        st.divider()
        if st.button("⬅️ Back to Intro Page"):
            st.session_state.app_mode = 'landing'
            st.rerun()

    pool = build_particle_pool(cfg_jmax, cfg_mmax)

    col_roster, col_model, col_plot = st.columns([2.5, 3.5, 4], gap="medium")

    with col_roster:
        st.subheader("⚛️ PDG Roster")
        st.caption("Click a particle box to add it to your model.")
        emoji_map = {('-', '+'): '🔵', ('-', '-'): '🔴', ('+', '+'): '🟢', ('+', '-'): '🟣'}
        
        for i in range(0, len(pool), 2):
            cols = st.columns(2)
            for k in range(2):
                if i + k < len(pool):
                    p = pool[i+k]
                    emoji = emoji_map.get((p['P'], p['C']), '⚪')
                    card_text = f"{emoji} {p['name']}\nMass: {p['mass']:.2f}\nWidth: {p['width']:.3f}\nJPC: {p['l']}{p['P']}{p['C']}"
                    
                    with cols[k]:
                        if st.button(card_text, key=f"add_{p['name']}_{i+k}", use_container_width=True):
                            st.session_state.inventory.append({
                                'name': p['name'], 'mass': p['mass'], 'width': p['width'], 
                                'l': p['l'], 'P': p['P'], 'C': p['C']
                            })
                            st.rerun()

    with col_model:
        st.subheader("📋 Selected Waves")
        if not st.session_state.inventory:
            st.info("Your model is empty. Select particles from the roster on the left!")
            
        for idx, w in enumerate(st.session_state.inventory):
            with st.container(border=True):
                r1c1, r1c2 = st.columns([4, 1])
                with r1c1:
                    st.markdown(f"**{w['name']}** | M={w['mass']:.3f} | JPC={w['l']}{w['P']}{w['C']}")
                with r1c2:
                    if st.button("❌", key=f"del_{idx}"):
                        st.session_state.inventory.pop(idx)
                        st.rerun()

    with col_plot:
        c1, c2 = st.columns([3, 2])
        with c1:
            if st.button("🚀 CALCULATE INTENSITIES", use_container_width=True, type="primary"):
                gm = AmplitudeModel(Mx_min=0.3, Mx_max=cfg_mmax, num_bins=250)
                refls_allowed = [1, -1] if (cfg_pol and cfg_refl == 2) else [1]
                
                for w in st.session_state.inventory:
                    for m in range(-w['l'], w['l'] + 1):
                        for eps in refls_allowed:
                            strength = random.uniform(0.1, 1.0)
                            phase = random.uniform(-3.14, 3.14)
                            gm.add_wave({'mass': w['mass'], 'width': w['width'], 'name': w['name']}, w['l'], m, eps, strength, phase)
                
                L_max = cfg_jmax * 2
                alphas = [0,1,2,3] if cfg_pol else [0]
                
                st.session_state.generated_data = {a: gm.generate_moments(L_max=L_max, alpha=a, include_zeros=False) for a in alphas}
                st.session_state.Mx = gm.Mx
                st.rerun()
                
        with c2:
            if st.session_state.generated_data is not None:
                df = io_utils.moments_to_dataframe(st.session_state.Mx, st.session_state.generated_data)
                csv_data = df.to_csv(index=False).encode('utf-8')
                
                st.download_button(
                    label="💾 DOWNLOAD CSV",
                    data=csv_data,
                    file_name="pwa_intensities.csv",
                    mime="text/csv",
                    use_container_width=True
                )

        st.divider()

        if st.session_state.generated_data is not None:
            alphas = list(st.session_state.generated_data.keys())
            tabs = st.tabs([f"H^{a} (Alpha={a})" for a in alphas]) if cfg_pol else [st.container()]

            for tab_idx, alpha in enumerate(alphas):
                with tabs[tab_idx]:
                    moments = st.session_state.generated_data[alpha]
                    sorted_keys = sorted(moments.keys())
                    
                    n_plots = len(sorted_keys)
                    if n_plots > 0:
                        n_cols = 3 if n_plots <= 12 else 4
                        n_rows = max(1, int(np.ceil(n_plots / n_cols)))
                        
                        fig, axes = plt.subplots(n_rows, n_cols, figsize=(10, 2.5 * n_rows))
                        axes = np.atleast_1d(axes).flatten()
                        
                        for i, ax in enumerate(axes):
                            if i < n_plots:
                                K = sorted_keys[i]
                                ax.plot(st.session_state.Mx, moments[K], color='black', lw=4)
                                ax.set_title(f"H{alpha}{K}", fontweight='bold')
                                ax.grid(True, linestyle='--', alpha=0.5)
                            else: 
                                ax.axis('off')
                                
                        plt.tight_layout()
                        st.pyplot(fig, use_container_width=True)
                    else:
                        st.info(f"No non-zero intensities generated for H^{alpha}.")
