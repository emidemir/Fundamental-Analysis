# fundamental_analyzer_pro/utils/export_utils.py

import pandas as pd
import re
from typing import Dict, Any, Union
from datetime import datetime

# Make sure openpyxl is installed (`pip install openpyxl`)
# It's usually required by pandas for .xlsx writing.

def _clean_excel_sheet_name(name: str) -> str:
    """
    Cleans a string to be used as a valid Excel sheet name.
    - Removes invalid characters.
    - Truncates to 31 characters.
    - Ensures it's not empty.

    Args:
        name (str): The proposed sheet name.

    Returns:
        str: A cleaned, valid Excel sheet name.
    """
    if not isinstance(name, str):
        name = str(name) # Attempt to convert non-strings

    # Remove invalid characters: []*/\?:
    # Also remove leading/trailing spaces which can cause issues
    cleaned_name = re.sub(r'[\[\]\*\/\\?\:]+', '', name).strip()

    # Truncate to Excel's limit
    truncated_name = cleaned_name[:31]

    # Ensure sheet name is not empty after cleaning
    if not truncated_name:
        return "Sheet" # Default name if cleaning results in empty string

    return truncated_name

def export_dict_to_excel(data_dict: Dict[str, Union[pd.DataFrame, pd.Series]], filename: str):
    """
    Exports a dictionary of pandas DataFrames or Series to an Excel file,
    with each dictionary key becoming a sheet name.

    Args:
        data_dict (Dict[str, Union[pd.DataFrame, pd.Series]]):
            Dictionary where keys are intended sheet names and values
            are the pandas DataFrames or Series to write.
        filename (str): The name (including path if necessary) of the
                        Excel file to create (e.g., 'output.xlsx').

    Raises:
        TypeError: If data_dict is not a dictionary or values are not DataFrames/Series.
        ImportError: If 'openpyxl' is not installed.
        Exception: Can raise various file I/O errors from pandas/openpyxl.
    """
    if not isinstance(data_dict, dict):
        raise TypeError("Input 'data_dict' must be a dictionary.")

    if not filename.lower().endswith((".xlsx", ".xls")):
        filename += ".xlsx"
        print(f"Warning: Filename did not end with .xlsx/.xls. Appending .xlsx: '{filename}'")

    print(f"[{datetime.now()}] Exporting data to Excel file: {filename}")

    try:
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            sheet_count = 0
            for sheet_name_raw, data in data_dict.items():
                if not isinstance(data, (pd.DataFrame, pd.Series)):
                    print(f"  - Skipping item '{sheet_name_raw}': Not a DataFrame or Series.")
                    continue

                if data.empty:
                    print(f"  - Skipping item '{sheet_name_raw}': DataFrame/Series is empty.")
                    continue

                # Clean the sheet name
                sheet_name_clean = _clean_excel_sheet_name(sheet_name_raw)

                print(f"  - Writing sheet: '{sheet_name_clean}' (from '{sheet_name_raw}')")

                # Convert Series to DataFrame before writing
                df_to_write = data.to_frame() if isinstance(data, pd.Series) else data

                try:
                    # Write data, include index by default
                    df_to_write.to_excel(writer, sheet_name=sheet_name_clean, index=True)
                    sheet_count += 1
                except Exception as sheet_error:
                    # Log error for specific sheet but continue if possible
                    print(f"  - ERROR writing sheet '{sheet_name_clean}'. Skipping. Details: {sheet_error}")

        if sheet_count > 0:
             print(f"[{datetime.now()}] Successfully wrote {sheet_count} sheet(s) to {filename}")
        else:
             print(f"[{datetime.now()}] Warning: No data was written to {filename} (all items were empty or invalid).")

    except ImportError:
        print("\nERROR: The 'openpyxl' library is required for writing .xlsx files.")
        print("Please install it using: pip install openpyxl")
        raise # Re-raise the import error
    except Exception as e:
        print(f"\nERROR: Failed to write Excel file '{filename}'. Details: {e}")
        raise # Re-raise the exception


# Example Usage (for testing the module directly)
if __name__ == "__main__":
    print("--- Testing export_dict_to_excel ---")

    # Create sample data
    df1 = pd.DataFrame({'Col A': [1, 2, 3], 'Col B': ['X', 'Y', 'Z']})
    s1 = pd.Series([10.1, 20.2, 30.3], name='Sample Series', index=['R1', 'R2', 'R3'])
    df_empty = pd.DataFrame()
    df_long_name = pd.DataFrame({'Value': [100]})
    df_invalid_chars = pd.DataFrame({'Check': [True, False]})

    sample_export_data = {
        "First Sheet": df1,
        "My Series Data": s1,
        "Empty Sheet": df_empty, # Should be skipped
        "This is a very long sheet name that will exceed Excel's limit": df_long_name, # Should be truncated
        "SheetWith[/\\*?:]Chars": df_invalid_chars, # Should be cleaned
        "Invalid Data Type": [1, 2, 3] # Should be skipped
    }

    test_filename = "test_export_util_output.xlsx"

    try:
        export_dict_to_excel(sample_export_data, test_filename)
        print(f"\nTest export completed. Check the file: '{test_filename}'")
        # Add manual check here or load file back if needed for automated tests
    except Exception as e:
        print(f"\nTest export failed: {e}")

    # Test invalid input
    print("\n--- Testing error handling ---")
    try:
         export_dict_to_excel("not a dictionary", "error_test.xlsx")
    except TypeError as te:
         print(f"Successfully caught expected TypeError: {te}")
    except Exception as e:
         print(f"Caught unexpected error during type error test: {e}")