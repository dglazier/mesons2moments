import pandas as pd

def moments_to_dataframe(Mx, moments):
    """
    Converts the generated moments dictionary into a Pandas DataFrame.
    Automatically detects if the input is from the old unpolarized engine 
    or the new polarized engine.
    
    Mx: Array of mass bins (independent variable).
    moments: Dictionary of either {(L, M): array} OR {alpha: {(L, M): array}}.
    """
    data = {'M_X_GeV': Mx}
    
    if not moments:
        return pd.DataFrame(data)
        
    # Check the first key to determine the dictionary structure
    first_key = list(moments.keys())[0]
    
    if isinstance(first_key, tuple):
        # --- OLD FORMAT (Flat Dictionary) ---
        # e.g. moments = {(0,0): array, (1,0): array}
        sorted_keys = sorted(moments.keys(), key=lambda k: (k[0], k[1]))
        
        for (L, M) in sorted_keys:
            col_name = f"H({L},{M})"
            data[col_name] = moments[(L, M)]
            
    else:
        # --- NEW FORMAT (Nested Polarized Dictionary) ---
        # e.g. moments = {0: {(0,0): array}, 1: {(0,0): array}}
        for alpha, sub_moments in moments.items():
            sorted_keys = sorted(sub_moments.keys(), key=lambda k: (k[0], k[1]))
            
            for (L, M) in sorted_keys:
                col_name = f"H{alpha}({L},{M})"
                data[col_name] = sub_moments[(L, M)]
                
    return pd.DataFrame(data)

def export_to_csv(df, filename="generated_moments.csv"):
    """
    Exports the DataFrame to a standard CSV file without the pandas index column.
    """
    df.to_csv(filename, index=False)
    print(f"✓ Data successfully exported to {filename}")
