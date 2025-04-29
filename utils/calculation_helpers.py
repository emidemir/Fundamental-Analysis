# fundamental_analyzer_pro/utils/calculation_helpers.py

import pandas as pd
import numpy as np
from typing import Optional, List, Union, Any

def safe_division(numerator: Optional[float], denominator: Optional[float]) -> float:
    """
    Safely divides two numbers, handling None, NaN, zero denominator, or non-numeric types.

    Args:
        numerator (Optional[float]): The number to be divided.
        denominator (Optional[float]): The number to divide by.

    Returns:
        float: The result of the division, or np.nan if division is not possible or invalid.
    """
    # Check for None or NaN first
    if numerator is None or denominator is None or pd.isna(numerator) or pd.isna(denominator):
        return np.nan

    # Attempt conversion to float in case inputs are strings representing numbers, etc.
    try:
        num = float(numerator)
        den = float(denominator)
    except (ValueError, TypeError):
        return np.nan # Cannot convert inputs to float

    # Check for zero denominator after conversion
    if den == 0:
        # Decide behavior: could return np.inf if num > 0, -np.inf if num < 0, or just NaN
        # Returning NaN is generally safer for financial ratios unless infinity is meaningful (e.g., coverage)
        # Specific handling for np.inf should be done in the calling metric function if needed.
        return np.nan
        # Example: return np.inf if num > 0 else (-np.inf if num < 0 else np.nan)

    return num / den

def get_value_from_df(df: Optional[pd.DataFrame],
                      row_labels: Union[str, List[str]],
                      col_index: int = 0,
                      allow_negative: bool = True) -> Optional[float]:
    """
    Safely retrieves a numeric value from a specific row and column of a DataFrame.
    Tries multiple row labels if a list is provided. Handles various data types.

    Args:
        df (Optional[pd.DataFrame]): The DataFrame to search in.
        row_labels (Union[str, List[str]]): The primary row label or a list of alternative labels to try.
        col_index (int): The column index (usually 0 for the most recent period).
        allow_negative (bool): If False, negative numeric values found are treated as invalid (returned as np.nan).

    Returns:
        Optional[float]: The numeric value found as a float, np.nan if found but was NaN,
                         or None if the row label doesn't exist or value cannot be converted to float.
                         Returns np.nan if allow_negative is False and the value is negative.
    """
    if df is None or df.empty or col_index >= df.shape[1] or col_index < 0:
        return None # Return None if DataFrame is invalid or index is out of bounds

    if isinstance(row_labels, str):
        labels_to_try = [row_labels]
    elif isinstance(row_labels, list):
        labels_to_try = row_labels
    else:
        # Invalid input type for row_labels
        return None

    value = None
    label_found = False
    for label in labels_to_try:
        if label in df.index:
            label_found = True
            try:
                # Use .iloc for potential integer-based indexing robustness if needed,
                # but .loc is standard for label-based lookup. iloc ensures position.
                raw_value = df.loc[label].iloc[col_index]

                # Check for explicit None or pandas NA types
                if raw_value is None or pd.isna(raw_value):
                    value = np.nan # Found label, but value is NaN/None
                    break

                # Attempt conversion to float
                numeric_value = float(raw_value)
                value = numeric_value # Successfully converted
                break # Stop searching once a valid value is found

            except (ValueError, TypeError, IndexError):
                 # Error during access or conversion, value remains None or its previous state (NaN)
                 # Continue to the next label if conversion failed for this one
                 continue
            except KeyError:
                 # Should not happen if label in df.index, but added for safety
                 continue

    # After loop:
    # value is float if conversion succeeded
    # value is np.nan if found but was NaN/None originally
    # value is None if label not found OR conversion failed for all found labels

    # If a label was found but resulted in None (e.g., conversion error on all attempts), return NaN
    if label_found and value is None:
        return np.nan

    # Apply allow_negative check only if value is a valid number
    if value is not None and pd.notna(value) and not allow_negative and value < 0:
        return np.nan # Treat unexpected negative values as invalid if specified

    return value # Return the float, np.nan, or None


def get_average_value_from_df(df: Optional[pd.DataFrame],
                              row_labels: Union[str, List[str]],
                              allow_negative: bool = True) -> Optional[float]:
    """
    Safely retrieves the average of the two most recent numeric values for a given row label(s).
    Handles cases with only one year of data or missing values.

    Args:
        df (Optional[pd.DataFrame]): The DataFrame containing financial statement data.
        row_labels (Union[str, List[str]]): The row label or list of alternative labels to look for.
        allow_negative (bool): Passed to get_value_from_df. If False, negative values
                                 won't be included in the average calculation.

    Returns:
        Optional[float]: The average value as a float, the single value if only one year is valid,
                         np.nan if values found were NaN, or None if the label wasn't found or
                         no numeric values could be retrieved.
    """
    latest_val = get_value_from_df(df, row_labels, 0, allow_negative)

    # Check if DataFrame exists and has at least 2 columns for averaging
    if df is None or df.shape[1] < 2:
        # Only one year or no data, return the single value found (which could be float, NaN, or None)
        return latest_val

    prior_val = get_value_from_df(df, row_labels, 1, allow_negative)

    # --- Averaging Logic ---
    latest_is_num = latest_val is not None and pd.notna(latest_val)
    prior_is_num = prior_val is not None and pd.notna(prior_val)

    if latest_is_num and prior_is_num:
        # Both values are valid numbers, return the average
        return (latest_val + prior_val) / 2.0
    elif latest_is_num:
        # Only the latest value is a valid number
        return latest_val
    elif prior_is_num:
        # Only the prior value is a valid number
        return prior_val
    else:
        # Neither value is a valid number. Return NaN if either original lookup returned NaN, else None.
        if pd.isna(latest_val) or pd.isna(prior_val):
             return np.nan
        else:
             return None


# Example Usage (for testing the module directly)
if __name__ == "__main__":
    print("--- Testing safe_division ---")
    print(f"10 / 2 = {safe_division(10, 2)}")
    print(f"10 / 0 = {safe_division(10, 0)}")
    print(f"0 / 5 = {safe_division(0, 5)}")
    print(f"10 / None = {safe_division(10, None)}")
    print(f"None / 2 = {safe_division(None, 2)}")
    print(f"10 / np.nan = {safe_division(10, np.nan)}")
    print(f"np.nan / 2 = {safe_division(np.nan, 2)}")
    print(f"10 / '2' = {safe_division(10, '2')}") # Handles string conversion
    print(f"'a' / 2 = {safe_division('a', 2)}")   # Handles invalid conversion

    print("\n--- Testing get_value_from_df ---")
    data = {
        '2023-12-31': [100, 200.5, -50, 'N/A', None, np.nan],
        '2022-12-31': [90, 190, -45, 10, 5, np.nan]
        }
    index = ['Revenue', 'Assets', 'Losses', 'BadData', 'Missing', 'ExplicitNaN']
    test_df = pd.DataFrame(data, index=index)
    print("Test DataFrame:")
    print(test_df)

    print(f"\nRevenue (2023): {get_value_from_df(test_df, 'Revenue', 0)}")
    print(f"Assets (2023): {get_value_from_df(test_df, 'Assets', 0)}")
    print(f"Losses (2023, allow_negative=True): {get_value_from_df(test_df, 'Losses', 0, allow_negative=True)}")
    print(f"Losses (2023, allow_negative=False): {get_value_from_df(test_df, 'Losses', 0, allow_negative=False)}") # Should be NaN
    print(f"BadData (2023): {get_value_from_df(test_df, 'BadData', 0)}") # Should be NaN (or None if stricter)
    print(f"Missing (2023): {get_value_from_df(test_df, 'Missing', 0)}") # Should be NaN
    print(f"ExplicitNaN (2023): {get_value_from_df(test_df, 'ExplicitNaN', 0)}") # Should be NaN
    print(f"NonExistent (2023): {get_value_from_df(test_df, 'NonExistent', 0)}") # Should be None
    print(f"Assets (2022): {get_value_from_df(test_df, 'Assets', 1)}")
    print(f"Assets (col 5 - out of bounds): {get_value_from_df(test_df, 'Assets', 5)}") # Should be None
    print(f"Trying list ['NotFound', 'Revenue'] (2023): {get_value_from_df(test_df, ['NotFound', 'Revenue'], 0)}") # Should find Revenue

    print("\n--- Testing get_average_value_from_df ---")
    print(f"Average Revenue: {get_average_value_from_df(test_df, 'Revenue')}") # (100+90)/2 = 95.0
    print(f"Average Assets: {get_average_value_from_df(test_df, 'Assets')}") # (200.5+190)/2 = 195.25
    print(f"Average Losses (allow_negative=True): {get_average_value_from_df(test_df, 'Losses', allow_negative=True)}") # (-50 + -45)/2 = -47.5
    print(f"Average Losses (allow_negative=False): {get_average_value_from_df(test_df, 'Losses', allow_negative=False)}") # Should be NaN
    print(f"Average BadData: {get_average_value_from_df(test_df, 'BadData')}") # Should be 10.0 (only 2022 is valid)
    print(f"Average Missing: {get_average_value_from_df(test_df, 'Missing')}") # Should be 5.0 (only 2022 is valid)
    print(f"Average ExplicitNaN: {get_average_value_from_df(test_df, 'ExplicitNaN')}") # Should be NaN
    print(f"Average NonExistent: {get_average_value_from_df(test_df, 'NonExistent')}") # Should be None

    # Test with only one column
    test_df_one_col = test_df[['2023-12-31']]
    print("\nTest DataFrame (One Column):")
    print(test_df_one_col)
    print(f"Average Revenue (1 col): {get_average_value_from_df(test_df_one_col, 'Revenue')}") # Should be 100.0
    print(f"Average NonExistent (1 col): {get_average_value_from_df(test_df_one_col, 'NonExistent')}") # Should be None