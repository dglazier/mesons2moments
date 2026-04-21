import matplotlib.pyplot as plt
import math

def plot_moments(Mx, moments, max_rows=6, max_cols=4, title_prefix="Moments"):
    """
    Plots all generated moments on a grid. Automatically paginates.
    Does NOT call plt.show() so multiple calls can queue up canvases in the background.
    """
    sorted_keys = sorted(moments.keys(), key=lambda k: (k[0], k[1]))
    total_plots = len(sorted_keys)
    plots_per_canvas = max_rows * max_cols
    
    num_canvases = math.ceil(total_plots / plots_per_canvas)
    
    for canvas_idx in range(num_canvases):
        fig, axes = plt.subplots(max_rows, max_cols, figsize=(16, 12))
        axes = axes.flatten()
        
        start_idx = canvas_idx * plots_per_canvas
        
        for i in range(plots_per_canvas):
            ax = axes[i]
            global_idx = start_idx + i
            
            if global_idx < total_plots:
                L, M = sorted_keys[global_idx]
                ax.plot(Mx, moments[(L, M)], color='navy', lw=2)
                ax.set_title(f"H({L}, {M})", fontsize=12, fontweight='bold')
                ax.set_xlabel("Mass (GeV)")
                ax.grid(True, linestyle='--', alpha=0.6)
                ax.axhline(0, color='black', lw=1, alpha=0.8)
            else:
                ax.axis('off')
                
        plt.tight_layout()
        # Add the alpha label to the window title!
        fig.canvas.manager.set_window_title(f"{title_prefix} - Canvas {canvas_idx + 1} of {num_canvases}")

def show_all_plots():
    """
    Calls plt.show() once to display all generated canvases simultaneously.
    """
    plt.show()
