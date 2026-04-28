import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib as mpl
import random
import sys
from particle import Particle
from amplitude_model import AmplitudeModel

# ---------------------------------------------------------
# ENGINE & SCORING LOGIC
# ---------------------------------------------------------
def setup_game():
    print("="*65)
    print(" ⚙️  PWA GAME SETTINGS ⚙️")
    print("="*65)
    config = {}
    try:
        val = input("  Target number of waves (default 3): ").strip()
        config['num_waves'] = int(val) if val else 3
        val = input("  Evaluation attempts (default 5): ").strip()
        config['attempts'] = int(val) if val else 5
        val = input("  Max partial wave spin (l_max) (default 2): ").strip()
        config['l_max'] = int(val) if val else 2
    except ValueError:
        config['num_waves'], config['attempts'], config['l_max'] = 3, 5, 2
        
    pol = input("  Include polarized observables? [y/N]: ").strip().lower()
    config['polarized'] = pol in ['y', 'yes']
    return config

def generate_secret_truth(config):
    model = AmplitudeModel(Mx_min=0.3, Mx_max=1.7, num_bins=300)
    true_waves_info = []
    
    mesons = Particle.findall(lambda p:
        p.pdgid.is_meson and p.charge == 0 and p.J is not None and
        p.mass is not None and p.width is not None and
        400 < p.mass < 1650 and p.width > 10 and int(p.J) <= config['l_max']
    )
    pool = [{'name': p.name, 'mass': p.mass/1000.0, 'width': p.width/1000.0, 'l': int(p.J)} for p in mesons]
    
    weights = [random.uniform(0.2, 0.5)] + [random.uniform(0.1, 0.4) for _ in range(config['num_waves'] - 1)]
    norm_fracs = [w / sum(weights) for w in weights]
    
    # Background
    model.add_wave({'mass': 0.500, 'width': 0.400, 'name': 'f_0(500)'}, 0, 0, 1, norm_fracs[0], 0.0)
    true_waves_info.append({'name': 'f_0(500)', 'mass': 0.500, 'width': 0.400, 'l': 0, 'm': 0, 'eps': 1})
    
    for i in range(config['num_waves'] - 1):
        w = random.choice(pool)
        m, e = random.choice(range(-w['l'], w['l'] + 1)), (random.choice([1, -1]) if config['polarized'] else 1)
        model.add_wave({'mass': w['mass'], 'width': w['width'], 'name': w['name']}, w['l'], m, e, norm_fracs[i+1], random.uniform(-3.14, 3.14))
        true_waves_info.append({'name': w['name'], 'mass': w['mass'], 'width': w['width'], 'l': w['l'], 'm': m, 'eps': e})
    
    obs_L = config['l_max'] * 2
    alphas = [0, 1, 2, 3] if config['polarized'] else [0]
    return model.Mx, {a: model.generate_moments(L_max=obs_L, alpha=a, include_zeros=True) for a in alphas}, true_waves_info

# ---------------------------------------------------------
# VISUALS & INTERFACE
# ---------------------------------------------------------
def update_plot(fig, axes, Mx, true_data, guess_history, attempt, score, config):
    # Modern Colormap API (Fixed Deprecation)
    plasma_map = mpl.colormaps['plasma']
    
    # Map score to color
    try:
        num_score = float(score)
        color = plasma_map(num_score / 100.0)
    except:
        color = 'magenta' # Default for N/A
    
    for ax in axes: 
        ax.clear()
        ax.axis('off')
    
    targets = [(0,(0,0)), (0,(1,0)), (0,(2,0)), (0,(3,0)), (0,(4,0)), (2,(1,1)), (2,(2,1)), (2,(3,1)), (2,(4,1))] if config['polarized'] else [(0, (L,M)) for L in range(5) for M in range(L+1)][:9]
    
    for i, (a, (L, M)) in enumerate(targets):
        if i >= 9 or L > config['l_max'] * 2: continue
        ax = axes[i]
        ax.axis('on')
        
        t_val = true_data.get(a, {}).get((L, M), np.zeros_like(Mx))
        # Label added to truth to prevent legend error
        ax.plot(Mx, t_val, color='black', lw=6, alpha=0.9, zorder=1, label="Truth")
        
        for old_g, _ in guess_history[:-1]:
            h_val = old_g.get(a, {}).get((L, M), np.zeros_like(Mx))
            ax.plot(Mx, h_val, color='grey', lw=1.5, ls=':', alpha=0.3, zorder=2)
            
        if guess_history:
            curr_g, _ = guess_history[-1]
            g_val = curr_g.get(a, {}).get((L, M), np.zeros_like(Mx))
            ax.plot(Mx, g_val, color=color, lw=4, ls='--', label=f"Guess (Score: {score})" if i==0 else "", zorder=3)
            
        ax.set_title(f"H^{a}({L}, {M})", fontsize=10, fontweight='bold')
        # Legend only called if labels were actually created
        if i == 0: ax.legend(fontsize='x-small', loc='upper right')

    plt.tight_layout()
    fig.canvas.draw()
    plt.pause(0.1)

def print_inv(inv, pol):
    print("\n" + "-"*30)
    print(" [CURRENT INVENTORY]")
    header = " ID | Mass | Width | l | m " + ("| eps " if pol else "") + "| Frac | Phase"
    print(header + "\n" + "-"*len(header))
    for i, w in enumerate(inv):
        s = f" {i:>2} | {w['mass']:.2f} | {w['width']:.2f} | {w['l']} | {w['m']:>2} "
        if pol: s += f"| {w['eps']:>3} "
        print(s + f"| {w['frac']:.2f} | {w['phase']:.2f}")

def play_game():
    config = setup_game()
    Mx, true_data, true_waves = generate_secret_truth(config)
    baseline = sum(sum(np.sum(arr**2) for arr in true_data[a].values()) for a in true_data)
    
    plt.ion()
    fig, axes = plt.subplots(3, 3, figsize=(12, 8))
    update_plot(fig, axes.flatten(), Mx, true_data, [], 0, "N/A", config)
    
    inv, history, attempts = [], [], 0
    current_score = "N/A"
    
    while attempts < config['attempts']:
        # Clear terminal screen (optional, uncomment if preferred)
        # print("\033[H\033[J") 
        
        print(f"\n{'='*20} STATUS BAR {'='*20}")
        print(f" ATTEMPTS USED: {attempts}/{config['attempts']}  |  CURRENT SCORE: {current_score}/100")
        print("="*52)
        
        print_inv(inv, config['polarized'])
        cmd = input(f"\n[add, edit, remove, hint, eval, exit]: ").lower().strip()
        
        if cmd == 'exit': break
        elif cmd == 'hint':
            m = [w for w in true_waves if (w['mass'], w['l'], w['m']) not in [(g['mass'], g['l'], g['m']) for g in inv]]
            if m: 
                c = random.choice(m)
                print(f"💡 Missing: {c['name']} (M={c['mass']:.3f}, W={c['width']:.3f}, l={c['l']}, m={c['m']})")
        elif cmd in ['add', 'edit']:
            try:
                if cmd == 'edit':
                    idx = int(input("Index to edit: "))
                else:
                    idx = len(inv)
                print("Input: mass, width, l, m, " + ("eps, " if config['polarized'] else "") + "frac, phase")
                p = [float(x.strip()) for x in input("Values: ").split(',')]
                wave = {
                    'mass': p[0], 'width': p[1], 'l': int(p[2]), 'm': int(p[3]), 
                    'eps': int(p[4]) if config['polarized'] else 1, 
                    'frac': p[5 if config['polarized'] else 4], 
                    'phase': p[6 if config['polarized'] else 5]
                }
                if cmd == 'edit': inv[idx] = wave
                else: inv.append(wave)
            except: print("❌ Input Error. Ensure 7 values (pol) or 6 values (unpol).")
        elif cmd == 'remove':
            try: inv.pop(int(input("Index to remove: ")))
            except: print("❌ Invalid Index.")
        elif cmd == 'eval':
            attempts += 1
            gm = AmplitudeModel(Mx_min=0.3, Mx_max=1.7, num_bins=300)
            for w in inv: 
                gm.add_wave({'mass': w['mass'], 'width': w['width']}, w['l'], w['m'], w['eps'], w['frac'], w['phase'])
            
            g_data = {a: gm.generate_moments(L_max=config['l_max']*2, alpha=a, include_zeros=True) for a in true_data.keys()}
            sse = sum(sum(np.sum((true_data[a].get(k,0)-g_data[a].get(k,0))**2) for k in true_data[a].keys()) for a in true_data.keys())
            
            current_score = max(0, min(100, int(100 * (1 - sse/baseline))))
            history.append((g_data, current_score))
            
            update_plot(fig, axes.flatten(), Mx, true_data, history, attempts, current_score, config)
            
            if current_score >= 98: 
                print("\n🌟🌟🌟 PERFECT FIT! YOU WIN! 🌟🌟🌟")
                break
            else:
                print(f"\n📊 Evaluated! New Score: {current_score}")
            
    print("\n--- THE TRUTH ---")
    for w in true_waves: 
        print(f"{w['name']} | M={w['mass']:.3f} | W={w['width']:.3f} | l={w['l']} | m={w['m']} | eps={w['eps']}")
    
    plt.ioff()
    plt.show()

if __name__ == "__main__": 
    play_game()
