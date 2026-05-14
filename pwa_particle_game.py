import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import random
from particle import Particle
from amplitude_model import AmplitudeModel

# ==========================================
# 1. VISUALIZATION HELPERS & CSS
# ==========================================

def draw_m_dial(j, m):
    """Generates a polar plot acting as a 'compass' for the m-projection."""
    fig, ax = plt.subplots(figsize=(2.0, 1.5), subplot_kw={'projection': 'polar'})
    
    if j > 0: 
        theta = np.pi/2 - (m/j) * (np.pi/2)
    else: 
        theta = np.pi/2
        
    ax.set_thetamin(0)
    ax.set_thetamax(180)
    ax.annotate('', xy=(theta, 1), xytext=(0, 0),
                arrowprops=dict(facecolor='crimson', edgecolor='black', width=2, headwidth=8))
    
    ax.set_yticklabels([])
    ax.set_xticklabels(['+m', '', '0', '', '-m'], fontsize=7)
    ax.set_theta_direction(1)
    ax.set_theta_offset(0)
    
    fig.patch.set_alpha(0.0)
    ax.patch.set_alpha(0.0)
    return fig

def draw_refl_viz(active_eps):
    """Generates a Cartesian plot representing the active reflectivities."""
    fig, ax = plt.subplots(figsize=(2.0, 1.5))
    ax.axhline(0, color='gray', lw=2, linestyle='--') # The horizontal line
    
    if 1 in active_eps:
        # Circle Above (Natural)
        ax.plot(0, 0.5, 'o', markersize=12, color='royalblue', markeredgecolor='black')
        ax.text(0.3, 0.5, '+1', va='center', fontsize=10, fontweight='bold', color='royalblue')
    if -1 in active_eps:
        # Circle Below (Unnatural)
        ax.plot(0, -0.5, 'o', markersize=12, color='crimson', markeredgecolor='black')
        ax.text(0.3, -0.5, '-1', va='center', fontsize=10, fontweight='bold', color='crimson')
        
    ax.set_xlim(-1, 1)
    ax.set_ylim(-1, 1)
    ax.axis('off')
    
    fig.patch.set_alpha(0.0)
    ax.patch.set_alpha(0.0)
    return fig

# Custom CSS for UI polish
st.markdown("""
<style>
    [data-testid="baseButton-primary"] {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%) !important;
        border: none !important;
        color: white !important;
    }
    .stButton > button {
        border-radius: 12px !important;
        border: 2px solid #555 !important;
        padding: 10px !important;
        font-family: monospace;
        transition: all 0.2s ease-in-out;
    }
    .stButton > button:hover {
        transform: scale(1.02);
        border-color: #4facfe !important;
        box-shadow: 0px 4px 10px rgba(79, 172, 254, 0.3);
    }
    
    /* Landing Page Specific CSS */
    .hero-banner {
        background: linear-gradient(135deg, #141E30 0%, #243B55 100%);
        padding: 3rem 2rem;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0px 10px 20px rgba(0,0,0,0.4);
        border-bottom: 4px solid #4facfe;
    }
    .hero-banner h1 {
        color: #ffffff !important; font-size: 2.8rem; font-weight: 800; margin-bottom: 0.5rem;
    }
    .hero-banner h3 {
        color: #4facfe !important; font-weight: 400;
    }
    .landing-text { font-size: 1.15rem; line-height: 1.6; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. CORE ENGINE
# ==========================================

def generate_secret_truth(config, pool):
    # Dynamically set max mass
    model = AmplitudeModel(Mx_min=0.3, Mx_max=config['m_max'], num_bins=250)
    true_waves_info = []
    
    weights = [random.uniform(0.3, 0.5)] + [random.uniform(0.1, 0.4) for _ in range(config['num_waves'] - 1)]
    norm_fracs = [w / sum(weights) for w in weights]
    
    for i in range(config['num_waves']):
        if i == 0: 
            w = {'name': 'f_0(500)', 'mass': 0.500, 'width': 0.400, 'l': 0, 'm': 0}
            model.add_wave({'mass': w['mass'], 'width': w['width'], 'name': w['name']}, w['l'], 0, 1, norm_fracs[i], 0.0)
            true_waves_info.append({'name': w['name'], 'mass': w['mass'], 'width': w['width'], 'l': w['l'], 'm': 0, 'eps': 1})
        else:
            w = random.choice(pool)
            m_val = random.choice(range(-w['l'], w['l'] + 1))
            
            if not config['polarized']:
                reflectivities = [1]
            else:
                if config['num_refl'] == 1:
                    reflectivities = [1]
                else:
                    reflectivities = random.choice([[1], [-1], [1, -1]])
            
            if len(reflectivities) == 1:
                refl_fracs = {reflectivities[0]: norm_fracs[i]}
            else:
                split = random.uniform(0.1, 0.9)
                refl_fracs = {1: norm_fracs[i] * split, -1: norm_fracs[i] * (1.0 - split)}
            
            for eps in reflectivities:
                phase = random.uniform(-3.14, 3.14)
                sub_frac = refl_fracs[eps]
                model.add_wave({'mass': w['mass'], 'width': w['width'], 'name': w['name']}, w['l'], m_val, eps, sub_frac, phase)
                true_waves_info.append({'name': w['name'], 'mass': w['mass'], 'width': w['width'], 'l': w['l'], 'm': m_val, 'eps': eps})
    
    L_max = config['j_max'] * 2
    true_data = {a: model.generate_moments(L_max=L_max, alpha=a, include_zeros=True) for a in ([0,1,2,3] if config['polarized'] else [0])}
    baseline = sum(sum(np.sum(arr**2) for arr in true_data[a].values()) for a in true_data)
    
    return model.Mx, true_data, true_waves_info, baseline

def build_particle_pool(config):
    # Dynamically filter by both j_max and m_max
    mesons = Particle.findall(lambda p:
        p.pdgid.is_meson and p.charge == 0 and p.J is not None and
        p.mass is not None and p.width is not None and
        400 < p.mass < (config['m_max'] * 1000.0) and p.width > 10 and int(p.J) <= config['j_max']
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

def init_game(config):
    pool = build_particle_pool(config)
    Mx, t_data, t_waves, baseline = generate_secret_truth(config, pool)
    st.session_state.game_active = True
    st.session_state.config = config
    st.session_state.pool = pool
    st.session_state.Mx = Mx
    st.session_state.true_data = t_data
    st.session_state.true_waves = t_waves
    st.session_state.baseline = baseline
    st.session_state.inventory = []
    st.session_state.history = []
    st.session_state.attempts_used = 0

# ==========================================
# 3. UI INITIALIZATION & ROUTING
# ==========================================

st.set_page_config(page_title="PWA Amplitude Game", layout="wide")

if 'app_mode' not in st.session_state:
    st.session_state.app_mode = 'landing'
if 'game_active' not in st.session_state:
    # Changed polarized default to False
    init_game({'num_waves': 3, 'attempts': 5, 'j_max': 2, 'm_max': 2.2, 'polarized': False, 'num_refl': 2})

# ==========================================
# 4. LANDING PAGE VIEW (GRADUATE LEVEL)
# ==========================================

if st.session_state.app_mode == 'landing':
    st.markdown("""<style>[data-testid="stSidebar"] {display: none;}</style>""", unsafe_allow_html=True)
    col_space1, col_main, col_space2 = st.columns([1, 6, 1])
    
    with col_main:
        st.markdown("""
        <div class="hero-banner">
            <h1>⚛️ Partial Wave Analysis Game</h1>
            <h3>Mastering Meson Spectroscopy & Interference</h3>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("## 🎯 Motivation: The Hunt for Hybrids")
        st.markdown("""
        <div class="landing-text">
        As we execute the GlueX-III exploitation phase and ongoing CLAS12 analyses, the central objective of the hadron spectroscopy program remains clear: the unambiguous identification of exotic states, such as the hybrid meson candidate $\pi_1(1600)$. 
        
        However, exotics do not exist in isolation. They are intrinsically buried beneath the dominant, conventional $q\bar{q}$ resonances. As highlighted in the recent <a href="https://www.jlab.org/news/releases/standard-candle-particle-measurement-enables-hunt-hybrid-mesons" target="_blank">JLab news release on standard candles</a>, we cannot claim an exotic discovery until we can perfectly model the interference patterns of the prominent, known states (such as the $\rho$, $\omega$, $\phi$, and $a_2(1320)$). 
        
        This interactive platform acts as a digital twin to our theoretical frameworks. It is designed to build your physics intuition for exactly how these states cross-mix in the observables.
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()

        st.markdown("## 📐 The JPAC Formalism")
        st.markdown("""
        <div class="landing-text">
        The mathematics driving this engine bypass numerical angular integration in favor of exact algebraic calculations based on the JPAC photoproduction frameworks outlined in <a href="https://arxiv.org/abs/1906.04841" target="_blank">arXiv:1906.04841</a> and <a href="https://arxiv.org/abs/2509.18827" target="_blank">arXiv:2509.18827</a>. 
        </div>
        """, unsafe_allow_html=True)

        st.write("**From 2509.18827 (Eq. 5), the general intensity distribution for a polarized photon beam is given by:**")
        st.latex(r"I(\Omega, \Phi) = \sum_{\alpha=0}^3 P^\alpha I^\alpha(\Omega)")

        st.write("**Where each polarized intensity component (Eq. 7) is expanded into spherical harmonics:**")
        st.latex(r"I^\alpha(\Omega) = \sum_{L, M} H^\alpha(L,M) Y_L^M(\Omega)")

        # Using a raw string literal (r"...") prevents Python from evaluating \a as an ASCII bell character
        st.write(r"**Crucially, the experimentally measured moments $H^\alpha(L,M)$ (Eq. 8) are constructed from the bilinear combinations of the underlying complex partial wave amplitudes ($V$):**")
        st.latex(r"H^\alpha(L,M) = \sum_{\ell, m, \epsilon} \sum_{\ell', m', \epsilon'} \rho^\alpha(\epsilon, \epsilon') \langle \ell m \epsilon | L M | \ell' m' \epsilon' \rangle V_{\ell m}^\epsilon V_{\ell' m'}^{\epsilon' *}")
        
        st.info("The complexity arises because a single moment $H(L,M)$ is rarely populated by a single particle; it is the coherent sum of interference between multiple partial waves.")

        st.divider()

        st.markdown("## 🔍 Bilinear Expansions in Practice (Appendix D)")
        st.markdown("""
        <div class="landing-text">
        To succeed in the game, you must visually invert the mathematics. Consider the expansions detailed in Appendix D. If we observe a non-zero $L=3$ moment, what waves must be active?
        </div>
        """, unsafe_allow_html=True)

        st.latex(r"H^0(3, 0) \propto \sqrt{\frac{3}{7}} |P_0| |D_0| \cos(\phi_P - \phi_D) + \dots")
        st.latex(r"H^1(3, 1) \propto \sqrt{\frac{2}{7}} |P_1| |D_0| \cos(\phi_P - \phi_D) - \sqrt{\frac{1}{21}} |P_0| |D_1| \cos(\phi_P - \phi_D) + \dots")

        st.markdown("""
        <div class="landing-text">
        Notice that $L=3$ moments strictly require the interference of states with differing spins (like a $P$-wave ($L=1$) and a $D$-wave ($L=2$)). Furthermore, the strength of the moment is heavily modulated by their relative phase difference ($\phi_P - \phi_D$).
        </div>
        """, unsafe_allow_html=True)

        st.divider()
        
        st.markdown("## 📜 Rules of Engagement")
        st.markdown("""
        1. **The Secret Truth:** Upon starting, the engine evaluates exact Clebsch-Gordan Racah formulas to generate a noise-free, "Truth" intensity distribution composed of several interfering meson resonances.
        2. **Your Hypothesis:** Using the PDG Roster, you must select the appropriate particle states to build a candidate model.
        3. **Fit the Parameters:** Manually adjust the reflectivity, coupling strengths, and relative phases of your selected waves to recreate the exact moment distributions of the target.
        4. **Minimize the $\chi^2$:** The scoring logic uses a symmetric, moment-by-moment localized error function.
        5. **Polarization:** By default, the game uses unpolarized beams (only $H^0$ is calculated and visible). You can enable **"Include Polarization"** in the sidebar settings to compute the $H^1, H^2$, and $H^3$ observables. Adding these observables provides crucial additional mathematical constraints for resolving phase ambiguities.
        """)

        # Swapped to native st.info to prevent rendering/CSS issues
        st.info("""
        **💡 Expert Hints for Improving Your Model:**
        * **Check the Limits:** The maximum non-zero $L$ in the moments dictates the maximum spin of the constituent particles ($L_{max} \le 2\ell_{max}$).
        * **Parity Conservation:** Natural ($\\epsilon=+1$) and Unnatural ($\\epsilon=-1$) exchanges do not interfere in the unpolarized $H^0$ moments. If a moment requires interference, the two waves must share the same reflectivity!
        * **Complex Conjugate Ambiguity:** Resolving phase ambiguities that plague unpolarized data requires looking closely at $H^2$ and $H^3$, which are strictly imaginary and behave differently under phase shifts.
        * **Phase Locking:** A mass-dependent phase motion (Breit-Wigner) will cause the interference terms to oscillate over the mass range $M_X$. Pay close attention to where the moments cross zero.
        """)

        st.write("")
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            if st.button("🚀 INITIALIZE AMPLITUDE GAME", type="primary", use_container_width=True):
                st.session_state.app_mode = 'game'
                st.rerun()
                
        st.write("")

# ==========================================
# 5. GAME SANDBOX VIEW
# ==========================================
elif st.session_state.app_mode == 'game':
    
    with st.sidebar:
        st.header("⚙️ Game Settings")
        curr_cfg = st.session_state.config
        
        cfg_waves = st.number_input("Target Resonances", 1, 6, curr_cfg['num_waves'], key="cfg_waves")
        cfg_attempts = st.number_input("Attempts", 1, 20, curr_cfg['attempts'], key="cfg_attempts")
        
        st.divider()
        st.subheader("Kinematics")
        cfg_jmax = st.number_input("Max Spin (J)", 0, 10, curr_cfg.get('j_max', 2), key="cfg_jmax")
        cfg_mmax = st.slider("Max Mass (GeV)", 1.5, 3.0, float(curr_cfg.get('m_max', 2.2)), step=0.1, key="cfg_mmax")
        
        st.divider()
        cfg_pol = st.checkbox("Include Polarization", value=curr_cfg['polarized'], key="cfg_pol")
        
        if cfg_pol:
            cfg_refl = st.radio("Number of Reflectivities", [1, 2], index=0 if curr_cfg.get('num_refl', 1) == 1 else 1, 
                                help="1 = Natural (+1) only. 2 = Both Natural (+1) and Unnatural (-1).")
        else:
            cfg_refl = 1
            st.caption("Polarization disabled (Reflectivity locked to +1).")
        
        st.divider()
        if st.button("🔄 Start New Game", type="primary", use_container_width=True):
            init_game({
                'num_waves': cfg_waves, 'attempts': cfg_attempts, 
                'j_max': cfg_jmax, 'm_max': cfg_mmax,
                'polarized': cfg_pol, 'num_refl': cfg_refl
            })
            st.rerun()
        
        if st.button("💡 Get Hint", disabled=not st.session_state.game_active, use_container_width=True):
            inv_sigs = []
            for w in st.session_state.inventory:
                active_refls = [1, -1] if (st.session_state.config['polarized'] and st.session_state.config['num_refl'] == 2) else [1]
                for eps in active_refls:
                    inv_sigs.append((w['name'], w['m'], eps))
                    
            missing = [w for w in st.session_state.true_waves if (w['name'], w['m'], w['eps']) not in inv_sigs]
            if missing:
                c = random.choice(missing)
                st.info(f"Missing State: **{c['name']}** (m={c['m']}, eps={c['eps']})")
            else:
                st.success("Resonances match! Fine-tune phase and strengths.")
                
        st.divider()
        if st.button("⬅️ Back to Theory Primer"):
            st.session_state.app_mode = 'landing'
            st.rerun()

    col_roster, col_model, col_plot = st.columns([2.5, 3.5, 4], gap="medium")

    with col_roster:
        sc = st.session_state.history[-1][1] if st.session_state.history else 0
        rem = st.session_state.config['attempts'] - st.session_state.attempts_used
        
        sc1, sc2 = st.columns([3, 1])
        with sc1:
            st.subheader(f"🎯 Attempts: {rem}")
            if st.button("🚀 EVALUATE FIT", use_container_width=True, type="primary", disabled=not st.session_state.game_active):
                st.session_state.attempts_used += 1
                # Generate amplitude model up to configured max mass
                gm = AmplitudeModel(Mx_min=0.3, Mx_max=st.session_state.config['m_max'], num_bins=250)
                
                refls_allowed = [1, -1] if (st.session_state.config['polarized'] and st.session_state.config['num_refl'] == 2) else [1]
                
                for w in st.session_state.inventory:
                    if 1 in refls_allowed and w['frac_pos'] > 0:
                        gm.add_wave({'mass': w['mass'], 'width': w['width'], 'name': w['name']}, w['l'], w['m'], 1, w['frac_pos'], w['phase_pos'])
                    if -1 in refls_allowed and w['frac_neg'] > 0:
                        gm.add_wave({'mass': w['mass'], 'width': w['width'], 'name': w['name']}, w['l'], w['m'], -1, w['frac_neg'], w['phase_neg'])
                
                L_max = st.session_state.config['j_max'] * 2
                g_data = {a: gm.generate_moments(L_max=L_max, alpha=a, include_zeros=True) for a in st.session_state.true_data.keys()}
                
                moment_scores = []
                for a in st.session_state.true_data:
                    t_moms = st.session_state.true_data[a]
                    g_moms = g_data.get(a, {})
                    all_keys = set(t_moms.keys()).union(g_moms.keys())
                    
                    for k in all_keys:
                        T = t_moms.get(k, np.zeros_like(st.session_state.Mx))
                        G = g_moms.get(k, np.zeros_like(st.session_state.Mx))
                        
                        if np.max(np.abs(T)) < 1e-12 and np.max(np.abs(G)) < 1e-12:
                            continue 
                        
                        error_sum = np.sum((T - G)**2)
                        norm_sum = np.sum(T**2) + np.sum(G**2)
                        
                        if norm_sum > 1e-12:
                            m_score = 1.0 - (error_sum / norm_sum)
                            moment_scores.append(max(0.0, m_score))
                        
                if moment_scores:
                    score = int(100 * np.mean(moment_scores))
                else:
                    score = 0
                    
                st.session_state.history.append((g_data, score))
                
                if score >= 98 or st.session_state.attempts_used >= st.session_state.config['attempts']:
                    st.session_state.game_active = False
                st.rerun()
                
        with sc2:
            st.markdown(f"""
                <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%;">
                    <div style="font-size: 11px; margin-bottom: 2px; color: #888; font-weight: bold;">SCORE</div>
                    <div style="height: 60px; width: 22px; background-color: #222; border-radius: 11px; position: relative; border: 1px solid #555; overflow: hidden;">
                        <div style="position: absolute; bottom: 0; width: 100%; height: {sc}%; background: linear-gradient(0deg, #D7191C, #FDAE61, #1A9641); transition: height 0.5s ease-in-out;"></div>
                    </div>
                    <div style="margin-top: 4px; font-weight: bold; font-size: 16px;">{sc}</div>
                </div>
            """, unsafe_allow_html=True)

        st.divider()

        st.subheader("⚛️ PDG Roster")
        st.caption("Click a particle box to add it to your model.")
        
        emoji_map = {('-', '+'): '🔵', ('-', '-'): '🔴', ('+', '+'): '🟢', ('+', '-'): '🟣'}
        
        for i in range(0, len(st.session_state.pool), 2):
            cols = st.columns(2)
            for k in range(2):
                if i + k < len(st.session_state.pool):
                    p = st.session_state.pool[i+k]
                    emoji = emoji_map.get((p['P'], p['C']), '⚪')
                    card_text = f"{emoji} {p['name']}\nMass: {p['mass']:.2f}\nWidth: {p['width']:.3f}\nJPC: {p['l']}{p['P']}{p['C']}"
                    
                    with cols[k]:
                        if st.button(card_text, key=f"add_{p['name']}_{i+k}", use_container_width=True, disabled=not st.session_state.game_active):
                            st.session_state.inventory.append({
                                'name': p['name'], 'mass': p['mass'], 'width': p['width'], 'l': p['l'],
                                'P': p['P'], 'C': p['C'],
                                'm': 0, 
                                'frac_pos': 0.1, 'phase_pos': 0.0,
                                'frac_neg': 0.1, 'phase_neg': 0.0
                            })
                            st.rerun()

    with col_model:
        st.subheader("📋 Active Model")
        if not st.session_state.inventory:
            st.info("Your model is empty. Select particles from the roster on the left!")
            
        for idx, w in enumerate(st.session_state.inventory):
            with st.container(border=True):
                r1c1, r1c2 = st.columns([4, 1])
                with r1c1:
                    st.markdown(f"**{w['name']}** | M={w['mass']:.3f} | JPC={w['l']}{w['P']}{w['C']}")
                with r1c2:
                    if st.button("❌", key=f"del_{idx}", disabled=not st.session_state.game_active):
                        st.session_state.inventory.pop(idx)
                        st.rerun()

                active_refls = [1, -1] if (st.session_state.config['polarized'] and st.session_state.config['num_refl'] == 2) else [1]
                c_m, c_refl = st.columns([1, 1.5])
                
                with c_m:
                    st.pyplot(draw_m_dial(w['l'], w['m']))
                    m_opts = list(range(-w['l'], w['l'] + 1))
                    if len(m_opts) > 1:
                        w['m'] = st.select_slider("m-projection", options=m_opts, value=w['m'], key=f"m_{idx}", disabled=not st.session_state.game_active)
                    else:
                        st.markdown("<div style='text-align: center; color: gray; font-size: 14px;'>m=0 (Locked)</div>", unsafe_allow_html=True)
                        w['m'] = 0
                with c_refl:
                    st.pyplot(draw_refl_viz(active_refls))
                    
                    if 1 in active_refls:
                        st.markdown("<span style='color: royalblue; font-size: 12px; font-weight: bold;'>● Natural Exchange (ε = +1)</span>", unsafe_allow_html=True)
                        s1, s2 = st.columns(2)
                        w['frac_pos'] = s1.slider("Strength", 0.0, 1.0, float(w['frac_pos']), key=f"fp_{idx}", disabled=not st.session_state.game_active)
                        w['phase_pos'] = s2.slider("Phase", -3.14, 3.14, float(w['phase_pos']), key=f"pp_{idx}", disabled=not st.session_state.game_active)
                        
                    if -1 in active_refls:
                        st.markdown("<span style='color: crimson; font-size: 12px; font-weight: bold;'>● Unnatural Exchange (ε = -1)</span>", unsafe_allow_html=True)
                        s1, s2 = st.columns(2)
                        w['frac_neg'] = s1.slider("Strength", 0.0, 1.0, float(w['frac_neg']), key=f"fn_{idx}", disabled=not st.session_state.game_active)
                        w['phase_neg'] = s2.slider("Phase", -3.14, 3.14, float(w['phase_neg']), key=f"pn_{idx}", disabled=not st.session_state.game_active)

    with col_plot:
        if not st.session_state.game_active:
            if any(h[1] >= 98 for h in st.session_state.history):
                st.balloons()
                st.success("🎉 Fit Match Found!")
            else: 
                st.error("💥 Out of attempts! Truth Revealed:")
                for w in st.session_state.true_waves:
                    st.write(f"- **{w['name']}**: m={w['m']}, eps={w['eps']}")

        sc = st.session_state.history[-1][1] if st.session_state.history else 0
        cmap = mpl.colormaps['plasma']
        try:
            color = cmap(sc/100.0)
        except:
            color = 'magenta'

        alphas = list(st.session_state.true_data.keys())
        tabs = st.tabs([f"H^{a} (Alpha={a})" for a in alphas]) if st.session_state.config['polarized'] else [st.container()]

        for tab_idx, alpha in enumerate(alphas):
            with tabs[tab_idx]:
                t_moms = st.session_state.true_data[alpha]
                sorted_keys = sorted(t_moms.keys())
                
                n_plots = len(sorted_keys)
                if n_plots > 0:
                    n_cols = 3 if n_plots <= 12 else 4
                    n_rows = max(1, int(np.ceil(n_plots / n_cols)))
                    
                    fig, axes = plt.subplots(n_rows, n_cols, figsize=(10, 2.5 * n_rows))
                    axes = np.atleast_1d(axes).flatten()
                    
                    for i, ax in enumerate(axes):
                        if i < n_plots:
                            K = sorted_keys[i]
                            ax.plot(st.session_state.Mx, t_moms[K], color='black', lw=5, alpha=0.8)
                            
                            if st.session_state.history:
                                guess = st.session_state.history[-1][0][alpha].get(K, np.zeros_like(st.session_state.Mx))
                                ax.plot(st.session_state.Mx, guess, color=color, lw=3, ls='--')
                                
                            ax.set_title(f"H{K}", fontweight='bold')
                            ax.grid(True, linestyle='--', alpha=0.5)
                        else: 
                            ax.axis('off')
                            
                    plt.tight_layout()
                    st.pyplot(fig, use_container_width=True)
                else:
                    st.info("No non-zero moments generated.")
