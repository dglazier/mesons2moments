import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import random
from particle import Particle
from amplitude_model import AmplitudeModel

# ==========================================
# 1. VISUALIZATION HELPERS
# ==========================================

def draw_m_dial(j, m):
    """Generates a Matplotlib polar plot acting as a 'compass' for the m-projection."""
    fig, ax = plt.subplots(figsize=(2.5, 1.5), subplot_kw={'projection': 'polar'})
    
    if j > 0:
        theta = np.pi/2 - (m/j) * (np.pi/2)
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
# 2. CORE ENGINE
# ==========================================

def generate_secret_truth(config):
    model = AmplitudeModel(Mx_min=0.3, Mx_max=1.7, num_bins=200)
    true_waves_info = []
    
    mesons = Particle.findall(lambda p:
        p.pdgid.is_meson and p.charge == 0 and p.J is not None and
        p.mass is not None and p.width is not None and
        400 < p.mass < 1650 and p.width > 10 and int(p.J) <= config['l_max']
    )
    pool = [{'name': p.name, 'mass': p.mass/1000.0, 'width': p.width/1000.0, 'l': int(p.J)} for p in mesons]
    
    weights = [random.uniform(0.3, 0.5)] + [random.uniform(0.1, 0.4) for _ in range(config['num_waves'] - 1)]
    norm_fracs = [w / sum(weights) for w in weights]
    
    for i in range(config['num_waves']):
        if i == 0: 
            w = {'name': 'f_0(500)', 'mass': 0.500, 'width': 0.400, 'l': 0, 'm': 0}
            eps = 1
        else:
            w = random.choice(pool)
            eps = (1 if random.random() > 0.5 else -1) if config['polarized'] else 1
            
        m = random.choice(range(-w['l'], w['l'] + 1))
        phase = 0.0 if i == 0 else random.uniform(-3.14, 3.14)
        
        model.add_wave({'mass': w['mass'], 'width': w['width'], 'name': w['name']}, w['l'], m, eps, norm_fracs[i], phase)
        true_waves_info.append({'name': w['name'], 'mass': w['mass'], 'width': w['width'], 'l': w['l'], 'm': m, 'eps': eps})
    
    true_data = {a: model.generate_moments(L_max=config['l_max']*2, alpha=a, include_zeros=True) for a in ([0,1,2,3] if config['polarized'] else [0])}
    baseline = sum(sum(np.sum(arr**2) for arr in true_data[a].values()) for a in true_data)
    
    return model.Mx, true_data, true_waves_info, baseline

def init_game(config):
    Mx, t_data, t_waves, baseline = generate_secret_truth(config)
    st.session_state.game_active = True
    st.session_state.config = config
    st.session_state.Mx = Mx
    st.session_state.true_data = t_data
    st.session_state.true_waves = t_waves
    st.session_state.baseline = baseline
    st.session_state.inventory = []
    st.session_state.history = []
    st.session_state.attempts_used = 0
    st.session_state.edit_idx = None

# ==========================================
# 3. UI INITIALIZATION & SIDEBAR
# ==========================================

st.set_page_config(page_title="PWA Web-Game", layout="wide")

if 'game_active' not in st.session_state:
    init_game({'num_waves': 3, 'attempts': 5, 'l_max': 2, 'polarized': False})

with st.sidebar:
    st.header("🎮 Game Control")
    
    st.subheader("New Game Settings")
    curr_cfg = st.session_state.config
    cfg_waves = st.number_input("Target Waves", 1, 6, curr_cfg['num_waves'], key="cfg_waves")
    cfg_attempts = st.number_input("Attempts", 1, 20, curr_cfg['attempts'], key="cfg_attempts")
    cfg_lmax = st.number_input("Max Spin (j_max)", 0, 10, curr_cfg['l_max'], key="cfg_lmax")
    cfg_pol = st.checkbox("Include Polarization", value=curr_cfg['polarized'], key="cfg_pol")
    
    if st.button("🔄 Start New Game", type="primary", use_container_width=True):
        init_game({
            'num_waves': cfg_waves, 
            'attempts': cfg_attempts, 
            'l_max': cfg_lmax, 
            'polarized': cfg_pol
        })
        st.rerun()
    
    st.divider()
    if st.button("💡 Get Hint", disabled=not st.session_state.game_active, use_container_width=True):
        inv_sigs = [(w['mass'], w['l'], w['m']) for w in st.session_state.inventory]
        missing = [w for w in st.session_state.true_waves if (w['mass'], w['l'], w['m']) not in inv_sigs]
        if missing:
            c = random.choice(missing)
            st.info(f"Missing: **{c['name']}**\nM={c['mass']:.3f}, j={c['l']}, m={c['m']}")
        else:
            st.success("States match! Fine-tune phase/fractions.")

# ==========================================
# 4. MAIN INTERFACE
# ==========================================

left, right = st.columns([4, 5], gap="large")

with left:
    # --- GAME STATUS & SCORE GAUGE ---
    status_col1, status_col2 = st.columns([4, 1])
    
    with status_col1:
        rem = st.session_state.config['attempts'] - st.session_state.attempts_used
        st.subheader(f"🎯 Attempts Left: {rem}")
        
        if st.button("🚀 EVALUATE FIT", use_container_width=True, type="primary", disabled=not st.session_state.game_active):
            st.session_state.attempts_used += 1
            gm = AmplitudeModel(Mx_min=0.3, Mx_max=1.7, num_bins=200)
            for w in st.session_state.inventory:
                gm.add_wave({'mass': w['mass'], 'width': w['width']}, w['l'], w['m'], w['eps'], w['frac'], w['phase'])
            
            g_data = {a: gm.generate_moments(L_max=st.session_state.config['l_max']*2, alpha=a, include_zeros=True) for a in st.session_state.true_data.keys()}
            
            sse = 0.0
            for a in st.session_state.true_data:
                t_moms = st.session_state.true_data[a]
                g_moms = g_data.get(a, {})
                all_keys = set(t_moms.keys()).union(g_moms.keys())
                for k in all_keys:
                    sse += np.sum((t_moms.get(k, 0.0) - g_moms.get(k, 0.0))**2)
                    
            score = max(0, min(100, int(100 * (1.0 - sse/st.session_state.baseline))))
            st.session_state.history.append((g_data, score))
            
            if score >= 98 or st.session_state.attempts_used >= st.session_state.config['attempts']:
                st.session_state.game_active = False
            st.rerun()

    with status_col2:
        sc = st.session_state.history[-1][1] if st.session_state.history else 0
        st.markdown(f"""
            <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%;">
                <div style="font-size: 11px; margin-bottom: 2px; color: #888; font-weight: bold;">SCORE</div>
                <div style="height: 70px; width: 22px; background-color: #222; border-radius: 11px; position: relative; border: 1px solid #555; overflow: hidden;">
                    <div style="position: absolute; bottom: 0; width: 100%; height: {sc}%; background: linear-gradient(0deg, #D7191C, #FDAE61, #1A9641); transition: height 0.5s ease-in-out;"></div>
                </div>
                <div style="margin-top: 4px; font-weight: bold; font-size: 16px;">{sc}</div>
            </div>
        """, unsafe_allow_html=True)

    st.divider()

    # --- ADD/EDIT PANEL ---
    is_editing = st.session_state.edit_idx is not None
    label = "📝 Edit Partial Wave" if is_editing else "➕ Add New Partial Wave"
    
    with st.expander(label, expanded=True):
        if is_editing:
            target = st.session_state.inventory[st.session_state.edit_idx]
            d_m, d_w, d_l, d_m_val, d_e, d_f, d_p = target['mass'], target['width'], target['l'], target['m'], target['eps'], target['frac'], target['phase']
        else:
            d_m, d_w, d_l, d_m_val, d_e, d_f, d_p = 0.77, 0.15, 1, 0, 1, 0.3, 0.0

        c_par, c_dial = st.columns([2, 1])
        with c_par:
            r1c1, r1c2 = st.columns(2)
            im = r1c1.slider("Mass (GeV)", 0.1, 3.0, float(d_m), step=0.01, key="panel_mass")
            iw = r1c2.slider("Width (GeV)", 0.01, 1.0, float(d_w), step=0.01, key="panel_width")
            
            r2c1, r2c2 = st.columns(2)
            ij = r2c1.slider("Spin (j)", 0, 10, int(d_l), step=1, key="panel_j")
            
            m_opts = list(range(-ij, ij + 1))
            if len(m_opts) > 1:
                # Protection logic: if the user lowers J, safely snap m back to a valid range
                if 'panel_m_slider' in st.session_state and st.session_state.panel_m_slider not in m_opts:
                    st.session_state.panel_m_slider = 0
                    
                im_val = r2c2.select_slider(
                    "m-projection", 
                    options=m_opts, 
                    value=d_m_val if d_m_val in m_opts else 0, 
                    key="panel_m_slider"
                )
            else:
                im_val = 0
                r2c2.markdown("<br><span style='color:gray; font-size: 14px;'>m-projection locked at 0</span>", unsafe_allow_html=True)
            
            r3c1, r3c2 = st.columns(2)
            ifrac = r3c1.slider("Fraction", 0.0, 1.0, float(d_f), key="panel_frac")
            iphase = r3c2.slider("Phase", -3.14, 3.14, float(d_p), key="panel_phase")
            ieps = st.selectbox("eps", [1, -1], index=0 if d_e == 1 else 1, key="panel_eps") if st.session_state.config['polarized'] else 1

        with c_dial:
            st.pyplot(draw_m_dial(ij, im_val))

        # Render Edit/Cancel vs Add buttons
        if is_editing:
            bc1, bc2 = st.columns(2)
            if bc1.button("Update Wave", use_container_width=True, type="primary", key="panel_submit_btn"):
                entry = {'mass': im, 'width': iw, 'l': ij, 'm': im_val, 'eps': ieps, 'frac': ifrac, 'phase': iphase}
                st.session_state.inventory[st.session_state.edit_idx] = entry
                st.session_state.edit_idx = None
                st.rerun()
            if bc2.button("Cancel Edit", use_container_width=True):
                st.session_state.edit_idx = None
                st.rerun()
        else:
            if st.button("Add to Model", use_container_width=True, key="panel_submit_btn"):
                entry = {'mass': im, 'width': iw, 'l': ij, 'm': im_val, 'eps': ieps, 'frac': ifrac, 'phase': iphase}
                st.session_state.inventory.append(entry)
                st.rerun()

    # --- INVENTORY ---
    st.subheader("📋 Current Model")
    if len(st.session_state.inventory) > 0:
        st.caption("Adjusting sliders here does not cost an attempt. Click EVALUATE FIT above when ready!")
        
    for idx, w in enumerate(st.session_state.inventory):
        with st.container(border=True):
            cinfo, cacts = st.columns([4, 1])
            cinfo.write(f"**W{idx}**: j={w['l']}, m={w['m']} | Frac: {w['frac']:.2f}")
            eb, db = cacts.columns(2)
            
            # THE EDIT OVERRIDE LOGIC
            if eb.button("Edit", key=f"edit_btn_{idx}"):
                w_tgt = st.session_state.inventory[idx]
                st.session_state.panel_mass = float(w_tgt['mass'])
                st.session_state.panel_width = float(w_tgt['width'])
                st.session_state.panel_j = int(w_tgt['l'])
                if int(w_tgt['l']) > 0:
                    st.session_state.panel_m_slider = int(w_tgt['m'])
                st.session_state.panel_frac = float(w_tgt['frac'])
                st.session_state.panel_phase = float(w_tgt['phase'])
                if st.session_state.config['polarized']:
                    st.session_state.panel_eps = int(w_tgt['eps'])
                st.session_state.edit_idx = idx
                st.rerun()
                
            if db.button("🗑️", key=f"del_btn_{idx}"):
                if is_editing and st.session_state.edit_idx == idx:
                    st.session_state.edit_idx = None
                st.session_state.inventory.pop(idx)
                st.rerun()

with right:
    # --- RESULT REVEAL ---
    if not st.session_state.game_active:
        if any(h[1] >= 98 for h in st.session_state.history):
            st.balloons()
            st.success("🎉 Fit Match Found!")
        else: 
            st.error("💥 Truth Revealed Below")
        for w in st.session_state.true_waves:
            st.write(f"**{w['name']}**: M={w['mass']:.3f}, Γ={w['width']:.3f}, j={w['l']}, m={w['m']}, eps={w['eps']}")

    # --- PLOTTING ---
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
            sorted_keys = sorted(t_moms.keys())[:9]
            
            fig, axes = plt.subplots(3, 3, figsize=(10, 8))
            axes = axes.flatten()
            
            for i, ax in enumerate(axes):
                if i < len(sorted_keys):
                    K = sorted_keys[i]
                    ax.plot(st.session_state.Mx, t_moms[K], color='black', lw=5, alpha=0.8)
                    if st.session_state.history:
                        ax.plot(st.session_state.Mx, st.session_state.history[-1][0][alpha][K], color=color, lw=3, ls='--')
                    ax.set_title(f"H{K}")
                    ax.grid(True, linestyle='--', alpha=0.5)
                else: 
                    ax.axis('off')
                    
            plt.tight_layout()
            st.pyplot(fig, use_container_width=True)
