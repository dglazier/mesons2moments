# Technical Design Review: `pwa_particle_game.py`

## 1. Overall Objectives
The `pwa_particle_game.py` application is an interactive, web-based educational tool designed to gamify Partial Wave Analysis (PWA) in photoproduction. The primary objective is to train the user’s physics intuition regarding quantum mechanical angular interference. 

By challenging users to reconstruct a "secret" photoproduction cross-section, the game forces players to understand how different resonances (defined by mass, width, and $J^{PC}$) and their specific kinematic production mechanisms ($m$-projections, reflectivities, and phases) uniquely map to observable spherical harmonic moments. Rather than performing an automated algorithmic fit, the user acts as the fitter, learning to "read" Breit-Wigner phase motions and interference patterns by eye.

## 2. Theoretical & Data Foundations

### The Physics Formalism (Glazier & Mathieu)
The game engine acts as a digital twin of the theoretical formalism derived by Glazier and Mathieu. It completely bypasses numerical angular integration in favor of exact algebraic calculations:
* **Spin Density Matrix Elements (SDMEs):** The model correctly cross-mixes the $+m$ and $-m$ partial waves based on exact parity conservation rules. 
* **Polarized Observables:** The game explicitly models the four photoproduction intensity moments ($H^0, H^1, H^2, H^3$). It accurately reflects how natural ($\epsilon = +1$) and unnatural ($\epsilon = -1$) parity exchanges distinctively couple to linear and circular beam polarizations.
* **Complex Conjugate Ambiguity:** By enforcing strict physical constraints (e.g., $H^0, H^1$ are strictly real; $H^2, H^3$ are strictly imaginary), the engine perfectly demonstrates how polarized observables resolve phase ambiguities that plague unpolarized data.

### Particle Data Group (PDG) Integration
To ground the game in experimental reality, the application interfaces with the Scikit-HEP `particle` library. Instead of abstract sliders for mass and width, the game queries the live PDG database to build a realistic roster of mesons. 
* It filters physical states based on user-defined kinematic thresholds ($J_{max}$ and $M_{max}$).
* It extracts exact $J^{PC}$ quantum numbers to categorize resonances into physical nonets (e.g., pseudoscalars, vectors, tensors), applying a color-coded visual hierarchy to the UI.

## 3. Component Architecture & Function Roles

The application is structured into four main operational blocks: Visual Helpers, Core Engine, Initialization, and the Main UI Loop.

### Visual Helpers
* **`draw_m_dial(j, m)`:** Generates a Matplotlib polar plot acting as a visual compass, showing the user the alignment of the chosen spin-projection.
* **`draw_refl_viz(active_eps)`:** Generates a Cartesian visualization showing active exchange reflectivities (Natural vs. Unnatural parity exchange).
* **`get_particle_color(P, C, J)`:** Maps $J^{PC}$ quantum numbers to an HSL color space. Pseudoscalars are blue, vectors are red, scalars/tensors are green, and axials are purple. Depth/lightness scales with Spin $J$.

### Core Engine
* **`build_particle_pool(config)`:** Executes the PDG database query. It applies strict physics filters (charge = 0, is_meson = True) and dynamic kinematic cuts ($J \le J_{max}$, $M \le M_{max}$) to build the selectable roster.
* **`generate_secret_truth(config, pool)`:** The heart of the game logic. It instantiates an `AmplitudeModel`, injects a mandatory background wave ($f_0(500)$), and randomly selects additional resonances from the PDG pool. Crucially, it models physical asymmetries by randomizing the strength split between natural and unnatural reflectivities, assigning independent phases, and calculating the target $H^\alpha(LM)$ moments.
* **`AmplitudeModel` (External):** Evaluates the exact Clebsch-Gordan Racah formulas and bilinear SDME combinations to return mathematically perfect, noise-free moments.

### Initialization & State Management
* **`init_game(config)`:** Handles the reset protocol. It clears the user's active inventory, generates a fresh secret truth, resets the score history, and updates the Streamlit session state.

## 4. The Streamlit Subsystem

Streamlit is a reactive Python UI framework that reruns the entire script from top to bottom whenever a user interacts with a widget. This paradigm dictates how the game maintains state and processes inputs.

### State Persistence (`st.session_state`)
Because the script reruns on every click, local variables are destroyed. The game relies entirely on `st.session_state` to persist the game’s reality:
* `inventory`: A list of dictionaries tracking the user's currently active model (selected particles, strengths, and phases).
* `true_data`: The cached dictionary of target moments generated at the start of the level.
* `history`: Tracks the user's previous guesses and scores to draw the dashed lines on the plots.

### The UI Layout
The interface utilizes a wide 3-Column Dashboard architecture:
1. **The Roster (Left):** Renders the PDG pool as HTML styled cards. Clicking an "Add" button triggers a state mutation (appending to `inventory`) and a forced rerun (`st.rerun()`).
2. **The Active Model (Center):** Iterates over the `inventory`. It provides Streamlit slider widgets bound directly to the dictionary keys of the active particles. Changing a slider instantly updates the underlying dictionary.
3. **The Plotting Engine (Right):** Iterates through the generated moments and plots the mathematical shapes using Matplotlib. It dynamically adjusts the grid size (up to 4 columns wide) depending on how many moments $J_{max}$ requires.

### The Scoring Mechanism
When the "Evaluate Fit" button is pressed, the game instantiates a new `AmplitudeModel` based on the user's `inventory`. 
The scoring logic uses a **symmetric, moment-by-moment localized error function**:
$$\text{Score}_k = 1.0 - \frac{\sum (T_k - G_k)^2}{\sum T_k^2 + \sum G_k^2}$$
By filtering out empty moments and calculating the score independently per moment before averaging, the system prevents massively dominant unpolarized cross-sections ($H^0_{00}$) from masking critical errors in the delicate polarized interference terms.