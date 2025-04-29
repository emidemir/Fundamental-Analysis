# fundamental_analyzer_pro/services/metrics_service.py

import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, List, Union
from datetime import datetime

# --- Helper Functions ---

def _safe_division(numerator: Optional[float], denominator: Optional[float]) -> float:
    """ Safely divides two numbers, handling None, NaN, or zero denominator. """
    if numerator is None or denominator is None or pd.isna(numerator) or pd.isna(denominator) or denominator == 0:
        return np.nan
    try:
        return numerator / denominator
    except (TypeError, ValueError):
         # Handles cases where inputs might not be numeric after all checks
         return np.nan

def _get_value_from_df(df: Optional[pd.DataFrame],
                       row_labels: Union[str, List[str]],
                       col_index: int = 0,
                       allow_negative: bool = True) -> Optional[float]:
    """
    Safely retrieves a numeric value from a specific row and column of a DataFrame.
    Tries multiple row labels if a list is provided.

    Args:
        df (Optional[pd.DataFrame]): The DataFrame to search in.
        row_labels (Union[str, List[str]]): The primary row label or a list of alternative labels to try.
        col_index (int): The column index (0 for the most recent year).
        allow_negative (bool): If False, negative values are treated as invalid (NaN).

    Returns:
        Optional[float]: The numeric value found, or None if not found or not numeric.
                         Returns np.nan if explicitly NaN in the DataFrame.
    """
    if df is None or df.empty or col_index >= df.shape[1]:
        return None

    if isinstance(row_labels, str):
        labels_to_try = [row_labels]
    else:
        labels_to_try = row_labels

    value = None
    for label in labels_to_try:
        if label in df.index:
            try:
                raw_value = df.loc[label].iloc[col_index]
                # Check if it's NaN explicitly
                if pd.isna(raw_value):
                     value = np.nan
                     break # Found the label, but it's NaN
                # Try converting to float
                numeric_value = float(raw_value)
                value = numeric_value
                break # Found a valid numeric value for one of the labels
            except (ValueError, TypeError, IndexError):
                # Failed to convert or access, try next label
                continue

    if value is not None and not allow_negative and value < 0:
        return np.nan # Treat unexpected negative values as invalid if specified

    # If value is still None after trying all labels, it wasn't found
    # If value is np.nan, it was found but was NaN
    return value

def _get_average_value_from_df(df: Optional[pd.DataFrame],
                               row_labels: Union[str, List[str]],
                               allow_negative: bool = True) -> Optional[float]:
    """
    Safely retrieves the average of the two most recent values for a row.
    Handles cases with only one year of data. Tries multiple row labels.

    Args:
        df (Optional[pd.DataFrame]): The DataFrame.
        row_labels (Union[str, List[str]]): Row label(s) to look for.
        allow_negative (bool): If False, negative values are treated as invalid (NaN) for averaging.

    Returns:
        Optional[float]: The average value, or the single value if only one year, or None/NaN.
    """
    latest_val = _get_value_from_df(df, row_labels, 0, allow_negative)

    if df is None or df.shape[1] < 2: # Only one year or no data
        return latest_val # Return the single value (or None/NaN if not found)

    prior_val = _get_value_from_df(df, row_labels, 1, allow_negative)

    # Handle cases where one or both values are missing/NaN for averaging
    if latest_val is None or pd.isna(latest_val):
        return prior_val # Return prior year if latest is missing (might be None/NaN itself)
    if prior_val is None or pd.isna(prior_val):
        return latest_val # Return latest year if prior is missing

    # Both values are valid numbers
    return (latest_val + prior_val) / 2.0

# --- Metrics Service ---

class MetricsService:
    """
    Calculates various financial metrics based on provided financial statement data.
    Focuses on calculations for the most recent available period.
    """

    def calculate_all_current_metrics(self,
                                      income_stmt: Optional[pd.DataFrame],
                                      balance_sheet: Optional[pd.DataFrame],
                                      key_stats: Optional[Dict[str, Any]],
                                      cash_flow: Optional[pd.DataFrame]) -> Dict[str, Optional[float]]:
        """
        Calculates all supported metrics for the most recent period.

        Args:
            income_stmt (Optional[pd.DataFrame]): Income Statement data.
            balance_sheet (Optional[pd.DataFrame]): Balance Sheet data.
            key_stats (Optional[Dict[str, Any]]): Key statistics (from yf.info).
            cash_flow (Optional[pd.DataFrame]): Cash Flow statement data.

        Returns:
            Dict[str, Optional[float]]: Dictionary of calculated metrics.
                                        Keys are metric names, values are floats or np.nan.
        """
        print(f"[{datetime.now()}] MetricsService: Calculating current metrics...")
        all_metrics = {}

        # Calculate metrics by category
        all_metrics.update(self._calculate_profitability(income_stmt, balance_sheet))
        all_metrics.update(self._calculate_valuation(key_stats, balance_sheet))
        all_metrics.update(self._calculate_liquidity(balance_sheet))
        all_metrics.update(self._calculate_efficiency(income_stmt, balance_sheet))
        all_metrics.update(self._calculate_solvency(income_stmt, balance_sheet))

        print(f"[{datetime.now()}] MetricsService: Finished calculating metrics.")
        # Return only metrics that have a non-None value (NaN is acceptable)
        return {k: v for k, v in all_metrics.items() if v is not None}


    def _calculate_profitability(self, income_stmt, balance_sheet) -> Dict[str, Optional[float]]:
        """ Calculates ROE, ROA, Gross Margin, Net Margin. """
        metrics = {}

        # --- Inputs ---
        # Prefer trying multiple common names for robustness
        net_income = _get_value_from_df(income_stmt, ["Net Income", "NetIncome"], allow_negative=True) # Allow neg NI
        total_revenue = _get_value_from_df(income_stmt, ["Total Revenue", "Revenue", "Total Sales"], allow_negative=False)
        gross_profit = _get_value_from_df(income_stmt, ["Gross Profit", "GrossProfit"], allow_negative=True) # GP can be neg

        avg_equity = _get_average_value_from_df(balance_sheet, ["Stockholder Equity", "Total Stockholder Equity", "Total Equity Gross Minority Interest"], allow_negative=True) # Equity can be neg
        avg_assets = _get_average_value_from_df(balance_sheet, ["Total Assets", "TotalAssets"], allow_negative=False)

        # --- Calculations ---
        metrics['ROE'] = _safe_division(net_income, avg_equity)
        metrics['ROA'] = _safe_division(net_income, avg_assets)
        metrics['Gross Margin'] = _safe_division(gross_profit, total_revenue)
        metrics['Net Margin'] = _safe_division(net_income, total_revenue)

        return metrics

    def _calculate_valuation(self, key_stats, balance_sheet) -> Dict[str, Optional[float]]:
        """ Calculates P/E, P/B, PEG using key_stats primarily. """
        metrics = {}
        if key_stats is None:
            return metrics

        # Prioritize direct values from key_stats
        metrics['P/E'] = key_stats.get('trailingPE')
        metrics['Forward P/E'] = key_stats.get('forwardPE')
        metrics['P/B'] = key_stats.get('priceToBook')
        metrics['PEG'] = key_stats.get('pegRatio')

        # Fallback for P/B if not directly available
        if pd.isna(metrics.get('P/B')):
            market_cap = key_stats.get('marketCap')
            # Get latest equity value
            total_equity = _get_value_from_df(balance_sheet, ["Stockholder Equity", "Total Stockholder Equity", "Total Equity Gross Minority Interest"], 0, allow_negative=True)
            if market_cap is not None and total_equity is not None and total_equity != 0:
                metrics['P/B (Calculated)'] = _safe_division(float(market_cap), total_equity)
                # If P/B was NaN but we calculated it, replace the original P/B
                if pd.isna(metrics['P/B']):
                     metrics['P/B'] = metrics['P/B (Calculated)']

        # Convert None results from .get() to np.nan for consistency
        for k, v in metrics.items():
            if v is None:
                metrics[k] = np.nan
            try: # Ensure values are floats
                if pd.notna(v):
                    metrics[k] = float(v)
            except (ValueError, TypeError):
                 metrics[k] = np.nan # Mark as NaN if conversion fails

        return metrics


    def _calculate_liquidity(self, balance_sheet) -> Dict[str, Optional[float]]:
        """ Calculates Current Ratio, Quick Ratio. """
        metrics = {}

        # --- Inputs ---
        current_assets = _get_value_from_df(balance_sheet, ["Current Assets", "Total Current Assets"], 0, allow_negative=False)
        current_liabilities = _get_value_from_df(balance_sheet, ["Current Liabilities", "Total Current Liabilities"], 0, allow_negative=False)
        inventory = _get_value_from_df(balance_sheet, ["Inventory", "Inventories"], 0, allow_negative=False)
        # Treat missing inventory as 0 for Quick Ratio calculation
        inventory = inventory if inventory is not None and pd.notna(inventory) else 0.0

        # --- Calculations ---
        metrics['Current Ratio'] = _safe_division(current_assets, current_liabilities)

        quick_assets = None
        if current_assets is not None and pd.notna(current_assets):
            quick_assets = current_assets - inventory # Subtract inventory (even if 0)
        metrics['Quick Ratio'] = _safe_division(quick_assets, current_liabilities)

        return metrics

    def _calculate_efficiency(self, income_stmt, balance_sheet) -> Dict[str, Optional[float]]:
        """ Calculates Asset Turnover, Inventory Turnover. """
        metrics = {}

        # --- Inputs ---
        total_revenue = _get_value_from_df(income_stmt, ["Total Revenue", "Revenue", "Total Sales"], 0, allow_negative=False)
        cogs = _get_value_from_df(income_stmt, ["Cost Of Revenue", "Cost of Goods Sold", "Cost Of Goods And Services Sold"], 0, allow_negative=False) # COGS should be positive

        avg_assets = _get_average_value_from_df(balance_sheet, ["Total Assets", "TotalAssets"], allow_negative=False)
        avg_inventory = _get_average_value_from_df(balance_sheet, ["Inventory", "Inventories"], allow_negative=False)

        # --- Calculations ---
        metrics['Asset Turnover'] = _safe_division(total_revenue, avg_assets)
        # Use COGS for Inventory Turnover
        metrics['Inventory Turnover'] = _safe_division(cogs, avg_inventory)

        return metrics


    def _calculate_solvency(self, income_stmt, balance_sheet) -> Dict[str, Optional[float]]:
        """ Calculates Debt/Equity, Interest Coverage. """
        metrics = {}

        # --- Inputs for Debt/Equity ---
        # Define Total Debt carefully: Prefer 'Total Debt', fallback to LongTerm + ShortTerm/Current
        total_debt = _get_value_from_df(balance_sheet, ["Total Debt"], 0, allow_negative=False)

        if total_debt is None or pd.isna(total_debt):
             long_term_debt = _get_value_from_df(balance_sheet, ["Long Term Debt", "Long Term Debt Noncurrent"], 0, allow_negative=False)
             short_term_debt = _get_value_from_df(balance_sheet, ["Current Debt", "Short Term Debt", "Current Debt And Capital Lease Obligation", "Short Term Borrowings"], 0, allow_negative=False)
             # If only one is found, use it. If both, sum them. Treat missing as 0 for sum if one exists.
             ltd = long_term_debt if long_term_debt is not None and pd.notna(long_term_debt) else 0.0
             std = short_term_debt if short_term_debt is not None and pd.notna(short_term_debt) else 0.0
             if ltd > 0 or std > 0:
                  total_debt = ltd + std
             else:
                  total_debt = np.nan # Set back to NaN if neither component found

        total_equity = _get_value_from_df(balance_sheet, ["Stockholder Equity", "Total Stockholder Equity", "Total Equity Gross Minority Interest"], 0, allow_negative=True) # Equity can be negative

        # --- Inputs for Interest Coverage (EBIT / Interest Expense) ---
        interest_expense = _get_value_from_df(income_stmt, ["Interest Expense", "Interest Expense Net"], 0, allow_negative=True) # Interest expense often negative on IS
        # EBIT = Earnings Before Interest and Taxes
        ebit = _get_value_from_df(income_stmt, ["EBIT", "Earnings Before Interest And Taxes"], 0, allow_negative=True)

        if ebit is None or pd.isna(ebit):
            # Calculate EBIT if not directly available: Net Income + Interest + Taxes
            net_income = _get_value_from_df(income_stmt, ["Net Income", "NetIncome"], 0, allow_negative=True)
            # Tax Provision can be positive or negative (benefit)
            tax_provision = _get_value_from_df(income_stmt, ["Tax Provision", "Income Tax Expense Benefit", "Income Tax Expense"], 0, allow_negative=True)

            # Ensure components are valid numbers before calculation
            if (net_income is not None and pd.notna(net_income) and
                interest_expense is not None and pd.notna(interest_expense) and
                tax_provision is not None and pd.notna(tax_provision)):
                # EBIT calculation: NI + Taxes + Interest (use absolute value of interest expense if it's negative on IS)
                # Note: Tax Provision is subtracted on IS to get NI, so add it back.
                # Interest Expense is often subtracted (shown negative), so subtract the negative (add it back).
                # Check IS structure: If Interest Exp is positive, subtract it from EBT to get Pretax Income.
                # Assuming Interest Expense is subtracted (negative or positive value shown):
                ebit = net_income + tax_provision + abs(interest_expense) # Check your specific IS source format
                # Alternative if EBIT is not directly available and IS structure is Pretax Income:
                # pre_tax_income = _get_value_from_df(income_stmt, ["Pretax Income", ...], 0)
                # if pre_tax_income is not None and interest_expense is not None:
                #     ebit = pre_tax_income + abs(interest_expense)

            else:
                 ebit = np.nan # Cannot calculate EBIT

        # --- Calculations ---
        metrics['Debt/Equity'] = _safe_division(total_debt, total_equity)
        # Use absolute value of interest expense in denominator
        abs_interest_expense = abs(interest_expense) if interest_expense is not None and pd.notna(interest_expense) else None
        metrics['Interest Coverage'] = _safe_division(ebit, abs_interest_expense)
        # Handle case where interest expense is zero or negligible but EBIT is positive (Infinite coverage)
        if pd.notna(ebit) and ebit > 0 and abs_interest_expense == 0:
             metrics['Interest Coverage'] = np.inf

        return metrics


# Example Usage (for testing the service directly)
if __name__ == "__main__":
    print("Testing MetricsService...")
    # Requires fetching data first to test realistically
    # Use DataProviderService for testing
    try:
        from data_provider_service import DataProviderService
    except ImportError:
        print("Could not import DataProviderService for testing. Run from project root or adjust paths.")
        DataProviderService = None # Avoid crashing if import fails

    if DataProviderService:
        provider = DataProviderService()
        metrics_calc = MetricsService()
        test_ticker = 'MSFT'
        print(f"\nFetching data for {test_ticker} to test metrics calculation...")
        data = provider.fetch_all_data(test_ticker)

        if data:
            calculated_metrics = metrics_calc.calculate_all_current_metrics(
                income_stmt=data.get('income_stmt'),
                balance_sheet=data.get('balance_sheet'),
                key_stats=data.get('key_stats'),
                cash_flow=data.get('cash_flow') # Pass cash flow even if not used by current calcs
            )
            print(f"\n--- Calculated Metrics for {test_ticker} ---")
            if calculated_metrics:
                for name, value in calculated_metrics.items():
                     display_val = f"{value:.4f}" if isinstance(value, (float, np.floating)) and pd.notna(value) else str(value)
                     print(f"  - {name:<25}: {display_val}")
            else:
                print("No metrics were calculated (likely due to missing data).")
        else:
            print(f"Could not fetch data for {test_ticker}, cannot test metrics calculation.")

    else:
         print("Skipping realistic test as DataProviderService could not be imported.")
         # Add mock DataFrame tests here if needed
         print("\nTesting with dummy data (example):")
         dummy_metrics = MetricsService()._calculate_profitability(None, None) # Example call with no data
         print(f"Profitability with no data: {dummy_metrics}")