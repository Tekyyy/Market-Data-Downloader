import pandas as pd

def add_diff(filepath):
    # Read the CSV
    df = pd.read_csv(filepath)

    # Add price difference column
    df['price_diff'] = df['price'].diff()

    # Save back to the SAME file
    df.to_csv(filepath, index=False)