import pandas as pd
import os

def save_to_csv(data, filename="suppliers.csv"):
    """
    Save the extracted supplier data to a CSV file.
    """
    if not data:
        print("No data to save.")
        return

    df = pd.DataFrame(data)

    # Reorder columns for better readability if needed
    cols = ["Supplier Name", "Website", "Emails", "Phones", "Snippet"]
    df = df[[c for c in cols if c in df.columns]]

    try:
        df.to_csv(filename, index=False)
    except PermissionError:
        # File is locked — save with a different name
        base, ext = os.path.splitext(filename)
        filename = f"{base}_1{ext}"
        df.to_csv(filename, index=False)
        print(f"Original file was locked, saved as {filename}")

    print(f"Data saved to {filename}")
    return os.path.abspath(filename)
