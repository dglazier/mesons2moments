# PWA Moments Generator ⚛️

The **PWA Moments Generator** is a streamlined, interactive sandbox designed for rapid Partial Wave Analysis (PWA) modeling. It allows you to select physical meson resonances from the Particle Data Group (PDG) database and instantly generate the corresponding photoproduction intensity moments ($H^\alpha(L, M)$).

This application focuses strictly on data generation and visualization, automatically populating all allowed $m$-projections and reflectivities with randomized coupling strengths and phases.

---

## 🚀 How to Run the App

1. **Open your terminal** and navigate to the directory containing your project files.
2. **Activate your virtual environment** (if you aren't already in it):
   ```bash
   source pwa_env/bin/activate
   ```
3. **Launch the Streamlit application** by running:
   ```bash
   streamlit run pwa_generator.py
   ```
4. **Access the Web UI:** Streamlit will automatically open a new tab in your default web browser (usually at `http://localhost:8501`).

---

## 🛠️ How to Use the Generator

### 1. Configure Your Kinematics (Left Sidebar)
Before building your model, set the physical boundaries of your analysis in the left sidebar:
* **Max Spin (J):** Sets the highest spin allowed in your particle pool (determines the maximum $L_{max}$ calculated).
* **Max Mass (GeV):** Sets the energy window for both the particle pool and the generated plots.
* **Polarization Settings:** Choose whether to calculate polarized observables ($H^0, H^1, H^2, H^3$) and whether your generated waves should include both Natural ($\epsilon = +1$) and Unnatural ($\epsilon = -1$) parity exchanges.

### 2. Build Your Target Model
* Scroll through the **PDG Roster** column. The particles are dynamically fetched from the Scikit-HEP `particle` library, sorted by mass, and color-coded by their $J^{PC}$ nonet.
* Click on any particle card to add it to your **Selected Waves** inventory.
* *Note: To keep generation rapid, the app will automatically generate all valid $m$-projections and active reflectivities for every particle you select.*

### 3. Calculate Moments
* Click the primary **🚀 CALCULATE MOMENTS** button.
* The `AmplitudeModel` physics engine will instantly generate all non-zero interference moments based on exact Clebsch-Gordan algebraic cross-mixing.
* The results will be plotted in a dynamic grid on the right side of the screen. If polarization is enabled, use the tabs at the top of the plot area to switch between the $H^0$, $H^1$, $H^2$, and $H^3$ observables.

### 4. Export Your Data
* Once the moments are calculated, the **💾 DOWNLOAD CSV** button will appear.
* Clicking this will prompt your browser to download `pwa_moments.csv` directly to your local computer.
* This CSV contains only the mathematically non-zero moments (filtered down to a $< 10^{-13}$ tolerance limit) formatted cleanly with your mass bins as the independent variable.

---

## 🧹 Managing State
If your model becomes too cluttered or you want to start a completely fresh simulation, simply click the **🗑️ Clear Model** button in the sidebar to wipe your inventory and clear the plot cache.