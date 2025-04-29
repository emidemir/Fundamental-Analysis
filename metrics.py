# fundamental_analyzer/metrics.py

import pandas as pd
import numpy as np

def safe_division(numerator, denominator):
    """ Safely divides two numbers, handling potential zero denominator or NaN values. """
    if denominator is None or pd.isna(denominator) or denominator == 0:
        return np.nan
    if numerator is None or pd.isna(numerator):
        return np.nan # Or 0 depending on context, NaN indicates data wasn't available
    return numerator / denominator

def get_metric(data, metric_name, default=np.nan):
    """ Safely retrieves a metric from a pandas Series or DataFrame row. """
    if data is None or metric_name not in data.index:
        # print(f"Warning: Metric '{metric_name}' not found in data.")
        return default
    value = data.loc[metric_name]
    return value if pd.notna(value) else default

def calculate_profitability_metrics(income_stmt, balance_sheet):
    """ Calculates ROE, ROA, Gross Margin, Net Margin. """
    metrics = {}
    if income_stmt is None or income_stmt.empty or balance_sheet is None or balance_sheet.empty:
        return metrics # Cannot calculate without data

    # Use the most recent year's data (first column)
    latest_income = income_stmt.iloc[:, 0]
    latest_balance = balance_sheet.iloc[:, 0]
    prev_balance = balance_sheet.iloc[:, 1] if balance_sheet.shape[1] > 1 else latest_balance # Handle case with only 1 year

    # Extract necessary values safely
    net_income = get_metric(latest_income, 'Net Income', default=0) # Assume 0 if missing for calc continuity
    total_revenue = get_metric(latest_income, 'Total Revenue')
    gross_profit = get_metric(latest_income, 'Gross Profit')

    total_equity_latest = get_metric(latest_balance, 'Stockholder Equity') # yfinance often uses 'Stockholder Equity'
    if pd.isna(total_equity_latest):
        total_equity_latest = get_metric(latest_balance, 'Total Stockholder Equity') # Try alternative name
    total_assets_latest = get_metric(latest_balance, 'Total Assets')

    total_equity_prev = get_metric(prev_balance, 'Stockholder Equity')
    if pd.isna(total_equity_prev):
         total_equity_prev = get_metric(prev_balance, 'Total Stockholder Equity')
    total_assets_prev = get_metric(prev_balance, 'Total Assets')

    # Calculate average equity and assets
    avg_equity = (total_equity_latest + total_equity_prev) / 2 if pd.notna(total_equity_latest) and pd.notna(total_equity_prev) else total_equity_latest
    avg_assets = (total_assets_latest + total_assets_prev) / 2 if pd.notna(total_assets_latest) and pd.notna(total_assets_prev) else total_assets_latest

    # Calculate metrics
    metrics['ROE'] = safe_division(net_income, avg_equity)
    metrics['ROA'] = safe_division(net_income, avg_assets)
    metrics['Gross Margin'] = safe_division(gross_profit, total_revenue)
    metrics['Net Margin'] = safe_division(net_income, total_revenue)

    return {k: v for k, v in metrics.items() if pd.notna(v)} # Filter out NaN results


def calculate_valuation_metrics(key_stats):
    """ Calculates P/E, P/B, PEG based on current data from key_stats. """
    metrics = {}
    if key_stats is None:
        return metrics

    metrics['P/E'] = key_stats.get('trailingPE', np.nan)
    metrics['Forward P/E'] = key_stats.get('forwardPE', np.nan)
    metrics['P/B'] = key_stats.get('priceToBook', np.nan)
    metrics['PEG'] = key_stats.get('pegRatio', np.nan) # Often available directly

    # Alternative P/B calculation if not directly available
    if pd.isna(metrics['P/B']) and 'marketCap' in key_stats and 'enterpriseValue' not in key_stats: # Crude check if book value might be derived
        # This requires balance sheet data, which isn't passed here.
        # Needs integration in the main analyzer class if direct P/B is unavailable.
        pass

    return {k: v for k, v in metrics.items() if pd.notna(v)}

def calculate_liquidity_metrics(balance_sheet):
    """ Calculates Current Ratio, Quick Ratio. """
    metrics = {}
    if balance_sheet is None or balance_sheet.empty:
        return metrics

    latest_balance = balance_sheet.iloc[:, 0]

    current_assets = get_metric(latest_balance, 'Current Assets') # Common name
    if pd.isna(current_assets):
        current_assets = get_metric(latest_balance, 'Total Current Assets') # Alternative name
    current_liabilities = get_metric(latest_balance, 'Current Liabilities') # Common name
    if pd.isna(current_liabilities):
        current_liabilities = get_metric(latest_balance, 'Total Current Liabilities') # Alternative name

    inventory = get_metric(latest_balance, 'Inventory', default=0) # Assume 0 if missing

    metrics['Current Ratio'] = safe_division(current_assets, current_liabilities)
    quick_assets = current_assets - inventory if pd.notna(current_assets) else np.nan
    metrics['Quick Ratio'] = safe_division(quick_assets, current_liabilities)

    return {k: v for k, v in metrics.items() if pd.notna(v)}

def calculate_efficiency_metrics(income_stmt, balance_sheet):
    """ Calculates Asset Turnover, Inventory Turnover. """
    metrics = {}
    if income_stmt is None or income_stmt.empty or balance_sheet is None or balance_sheet.empty:
        return metrics

    latest_income = income_stmt.iloc[:, 0]
    latest_balance = balance_sheet.iloc[:, 0]
    prev_balance = balance_sheet.iloc[:, 1] if balance_sheet.shape[1] > 1 else latest_balance

    total_revenue = get_metric(latest_income, 'Total Revenue')
    cogs = get_metric(latest_income, 'Cost Of Revenue') # yfinance uses 'Cost Of Revenue'
    if pd.isna(cogs):
        cogs = get_metric(latest_income, 'Cost of Goods Sold') # Try alternative

    total_assets_latest = get_metric(latest_balance, 'Total Assets')
    total_assets_prev = get_metric(prev_balance, 'Total Assets')
    avg_assets = (total_assets_latest + total_assets_prev) / 2 if pd.notna(total_assets_latest) and pd.notna(total_assets_prev) else total_assets_latest

    inventory_latest = get_metric(latest_balance, 'Inventory', default=0)
    inventory_prev = get_metric(prev_balance, 'Inventory', default=0)
    avg_inventory = (inventory_latest + inventory_prev) / 2 if inventory_latest is not None and inventory_prev is not None else inventory_latest

    metrics['Asset Turnover'] = safe_division(total_revenue, avg_assets)
    metrics['Inventory Turnover'] = safe_division(cogs, avg_inventory) # Use COGS for inventory turnover

    return {k: v for k, v in metrics.items() if pd.notna(v)}


def calculate_solvency_metrics(balance_sheet, income_stmt):
    """ Calculates Debt/Equity, Interest Coverage. """
    metrics = {}
    if balance_sheet is None or balance_sheet.empty or income_stmt is None or income_stmt.empty:
        return metrics

    latest_balance = balance_sheet.iloc[:, 0]
    latest_income = income_stmt.iloc[:, 0]

    # Debt can be tricky (Short term + Long term? Total Liabilities?)
    # Using Total Debt if available, else Long Term Debt. Be explicit about definition.
    total_debt = get_metric(latest_balance, 'Total Debt', default=np.nan)
    if pd.isna(total_debt):
        long_term_debt = get_metric(latest_balance, 'Long Term Debt', default=0)
        short_term_debt = get_metric(latest_balance, 'Current Debt', default=0) # yfinance might use 'Current Debt' or similar
        if pd.isna(short_term_debt):
             short_term_debt = get_metric(latest_balance, 'Short Term Debt', default=0)

        # If only long-term is found, use that. If both, sum. If neither, can't calc.
        if pd.notna(long_term_debt) or pd.notna(short_term_debt):
             total_debt = (long_term_debt if pd.notna(long_term_debt) else 0) + \
                          (short_term_debt if pd.notna(short_term_debt) else 0)
        else: # Try Total Liabilities as a proxy if no debt found (less ideal)
            # total_debt = get_metric(latest_balance, 'Total Liabilities Net Minority Interest', default=np.nan)
            pass # Decide if proxy is acceptable, here we default to NaN


    total_equity = get_metric(latest_balance, 'Stockholder Equity')
    if pd.isna(total_equity):
        total_equity = get_metric(latest_balance, 'Total Stockholder Equity')

    # Interest Coverage = EBIT / Interest Expense
    ebit = get_metric(latest_income, 'EBIT') # Earnings Before Interest and Taxes
    if pd.isna(ebit): # Calculate if not directly available
        net_income = get_metric(latest_income, 'Net Income', default=0)
        interest_expense = get_metric(latest_income, 'Interest Expense', default=0)
        tax_expense = get_metric(latest_income, 'Tax Provision', default=0) # yfinance uses 'Tax Provision'
        if pd.isna(tax_expense):
            tax_expense = get_metric(latest_income, 'Income Tax Expense', default=0)

        if pd.notna(net_income) and pd.notna(interest_expense) and pd.notna(tax_expense):
             ebit = net_income + interest_expense + tax_expense # Check calculation logic based on statement structure

    interest_expense = get_metric(latest_income, 'Interest Expense', default=np.nan) # Get it again for division

    metrics['Debt/Equity'] = safe_division(total_debt, total_equity)
    # Ensure interest expense is treated as positive for ratio calculation if it's negative on IS
    metrics['Interest Coverage'] = safe_division(ebit, abs(interest_expense)) if pd.notna(interest_expense) and interest_expense !=0 else np.inf if ebit > 0 else np.nan


    return {k: v for k, v in metrics.items() if pd.notna(v)}

def calculate_historical_metric(statement_data, balance_sheet_data, metric_func):
    """Calculates a metric across multiple years using rolling data."""
    historical_metrics = pd.Series(dtype=float)
    if statement_data is None or statement_data.empty or balance_sheet_data is None or balance_sheet_data.empty:
        return historical_metrics

    num_years = statement_data.shape[1]
    for i in range(num_years):
        # Need data for year i and potentially year i+1 (for averages)
        current_year_stmt = statement_data.iloc[:, i:i+1] # Keep as DataFrame
        current_year_bal = balance_sheet_data.iloc[:, i:i+1]

        # Provide previous year's balance sheet if needed for averages
        prev_year_bal = balance_sheet_data.iloc[:, i+1:i+2] if i + 1 < num_years else None

        # Reconstruct temporary dataframes for the metric function (expects specific structure)
        temp_income = current_year_stmt if 'Income' in str(metric_func) else None # Hacky way to know which stmt is needed
        temp_balance = pd.concat([current_year_bal, prev_year_bal], axis=1) if prev_year_bal is not None else current_year_bal

        # Call the appropriate metric calculation function
        # This part is complex because metric funcs expect specific inputs
        # A better design might pass DataFrames directly to metric funcs and let them handle slicing
        # Simplified approach: Calculate only for the most recent year for now in main analyzer
        # Or redesign metric functions to take year index `i`
        pass # Placeholder - historical calculation needs careful implementation based on metric dependencies

    # Example: Simplified historical ROE (requires redesigning metric function)
    # def calculate_roe_for_year(income_stmt_col, balance_col, prev_balance_col): ...
    # for i in range(num_years):
    #     year = statement_data.columns[i]
    #     income_col = income_stmt.iloc[:, i]
    #     balance_col = balance_sheet.iloc[:, i]
    #     prev_balance_col = balance_sheet.iloc[:, i+1] if i+1 < num_years else balance_col
    #     roe = calculate_roe_for_year(income_col, balance_col, prev_balance_col)
    #     historical_metrics[year] = roe

    return historical_metrics # Return empty for now