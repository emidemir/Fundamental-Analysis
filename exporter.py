# fundamental_analyzer/exporter.py

import pandas as pd

def export_dict_to_excel(data_dict, filename):
    """
    Exports a dictionary of DataFrames/Series to an Excel file, each item as a sheet.

    Args:
        data_dict (dict): Dictionary where keys are sheet names and values are pandas DataFrames or Series.
        filename (str): The name of the Excel file to create.
    """
    if not filename.endswith(".xlsx"):
        filename += ".xlsx"

    try:
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            for sheet_name, data in data_dict.items():
                if isinstance(data, (pd.DataFrame, pd.Series)):
                    # Clean up sheet names (Excel limits length and chars)
                    clean_sheet_name = "".join(c for c in sheet_name if c.isalnum() or c in (' ', '_')).rstrip()
                    clean_sheet_name = clean_sheet_name[:31] # Max length for sheet names

                    if not data.empty:
                        # Convert Series to DataFrame for consistent writing
                        if isinstance(data, pd.Series):
                             df_to_write = data.to_frame()
                        else:
                             df_to_write = data

                        # Attempt to write, handle potential errors for specific sheets
                        try:
                             df_to_write.to_excel(writer, sheet_name=clean_sheet_name)
                             print(f"  - Writing sheet: {clean_sheet_name}")
                        except Exception as sheet_error:
                             print(f"  - Warning: Could not write sheet '{clean_sheet_name}'. Error: {sheet_error}")
                    else:
                         print(f"  - Skipping empty sheet: {clean_sheet_name}")
                else:
                     print(f"  - Skipping non-DataFrame/Series item: {sheet_name}")

    except Exception as e:
        print(f"Error creating Excel file '{filename}': {e}")
        raise # Re-raise the exception to be caught by the caller if needed

# Example Usage (for testing module directly)
if __name__ == '__main__':
    sample_data = {
        "Sheet 1": pd.DataFrame({'A': [1, 2], 'B': [3, 4]}),
        "Another Sheet": pd.Series([10, 20, 30], name="Values"),
        "Empty Data": pd.DataFrame(),
        "Invalid Sheet Name !@#$%^&*()_+": pd.DataFrame({'X': [0]})
    }
    try:
        export_dict_to_excel(sample_data, "test_export.xlsx")
        print("Test export successful.")
    except Exception as e:
        print(f"Test export failed: {e}")