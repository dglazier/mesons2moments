import pandas as pd

def moments_to_dataframe(Mx, moments):
    """
    Converts the generated moments dictionary into a Pandas DataFrame.
    Mx: Array of mass bins (independent variable).
    moments: Dictionary of {(L, M): intensity_array}.
    """
    # Initialize the data dictionary with our independent variable
    data = {'M_X_GeV': Mx}
    
    # Iterate through the generated moments and add them as columns.
    # We sort the keys so the columns appear in a logical order (H(0,0), H(1,0), H(1,1), etc.)
    sorted_keys = sorted(moments.keys(), key=lambda k: (k[0], k[1]))
    
    for (L, M) in sorted_keys:
        col_name = f"H({L},{M})"
        data[col_name] = moments[(L, M)]
        
    return pd.DataFrame(data)

def export_to_csv(df, filename="generated_moments.csv"):
    """
    Exports the DataFrame to a standard CSV file without the pandas index column.
    """
    df.to_csv(filename, index=False)
    print(f"✓ Data successfully exported to {filename}")
