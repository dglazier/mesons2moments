import numpy as np
from particle import Particle
import physics_engine as pe

def dump_available_mesons():
    """
    Helper function to print all valid meson strings from the PDG database.
    """
    print("\n" + "="*65)
    print(" ERROR: PARTICLE NOT FOUND.")
    print(" Here is the list of valid meson strings in the PDG database:")
    print("="*65)
    
    mesons = Particle.findall(lambda p: p.pdgid.is_meson)
    
    for p in mesons:
        if p.name and p.mass is not None:
            mass_gev = p.mass / 1000.0
            print(f"String: '{p.name:<18}' | Mass: {mass_gev:>6.3f} GeV | PDG ID: {int(p.pdgid)}")
            
    print("="*65 + "\n")

class PartialWave:
    def __init__(self, name_or_dict, l, m, epsilon, fraction, phase, m1, m2):
        """
        Initializes a partial wave state.
        name_or_dict: Exact string, fuzzy string, PDG ID (int), or custom dict.
        l, m: Partial wave spin and spin projection.
        """
        self.l = l
        self.m = m
        self.epsilon = epsilon
        self.fraction = fraction
        self.phase = phase
        self.m1 = m1
        self.m2 = m2

        if isinstance(name_or_dict, str):
            particles = Particle.findall(name_or_dict)
            if not particles:
                particles = Particle.findall(lambda p: p.name is not None and name_or_dict in p.name)
                
            if not particles:
                dump_available_mesons()
                raise ValueError(f"Particle string '{name_or_dict}' not found. See valid list above.")
            
            p = particles[0]
            self.mass = p.mass / 1000.0
            self.width = (p.width / 1000.0) if p.width is not None else 0.0
            self.name = p.name
            
        elif isinstance(name_or_dict, int):
            try:
                p = Particle.from_pdgid(name_or_dict)
                self.mass = p.mass / 1000.0
                self.width = (p.width / 1000.0) if p.width is not None else 0.0
                self.name = p.name
            except Exception:
                dump_available_mesons()
                raise ValueError(f"PDG ID {name_or_dict} not found. See valid list above.")
                
        elif isinstance(name_or_dict, dict):
            self.mass = name_or_dict.get('mass')
            self.width = name_or_dict.get('width')
            self.name = name_or_dict.get('name', 'CustomState')
            if self.mass is None or self.width is None:
                raise ValueError("Custom particle dictionary must contain 'mass' and 'width' in GeV.")
        else:
            raise TypeError("name_or_dict must be a PDG string, integer PDG ID, or a dictionary.")

    def get_shape(self, M_X):
        return pe.relativistic_breit_wigner(
            M_X, self.mass, self.width, self.l, self.m1, self.m2
        )
