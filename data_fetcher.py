# fundamental_analyzer/data_fetcher.py

import yfinance as yf
import pandas as pd
from functools import lru_cache

@lru_cache(maxsize=10) # Cache results for the same ticker to avoid repeated API calls
def get_stock_data(ticker_symbol):
    """
    Fetches stock data for a given ticker symbol using yfinance.

    Args:
        ticker_symbol (str): The stock ticker symbol (e.g., 'AAPL').

    Returns:
        yf.Ticker object or None: The yfinance Ticker object if valid, else None.
    """
    try:
        stock = yf.Ticker(ticker_symbol)
        # Check if the ticker is valid by trying to access info
        if not stock.info or 'symbol' not in stock.info:
             print(f"Error: Could not find data for ticker '{ticker_symbol}'. It might be invalid.")
             return None
        print(f"Successfully fetched data for {ticker_symbol}")
        return stock
    except Exception as e:
        print(f"Error fetching data for {ticker_symbol}: {e}")
        return None

def get_financial_statement(stock, statement_type, years):
    """
    Fetches a specific financial statement (Income Statement, Balance Sheet, Cash Flow).

    Args:
        stock (yf.Ticker): The yfinance Ticker object.
        statement_type (str): 'income', 'balance', 'cashflow'.
        years (int): Number of years to fetch (Note: yfinance often returns ~4 years regardless).

    Returns:
        pd.DataFrame or None: DataFrame with financial statement data or None if error.
    """
    if not stock:
        return None
    try:
        if statement_type == 'income':
            statement = stock.income_stmt
        elif statement_type == 'balance':
            statement = stock.balance_sheet
        elif statement_type == 'cashflow':
            statement = stock.cashflow
        else:
            print(f"Error: Invalid statement type '{statement_type}'")
            return None

        if statement.empty:
            print(f"Warning: No {statement_type} statement data found for {stock.info.get('symbol', '')}.")
            return pd.DataFrame() # Return empty DataFrame

        # yfinance often returns 4 years max, select based on available columns
        num_available_years = statement.shape[1]
        years_to_fetch = min(years, num_available_years)
        return statement.iloc[:, :years_to_fetch]

    except Exception as e:
        print(f"Error fetching {statement_type} statement for {stock.info.get('symbol', '')}: {e}")
        return None

def get_key_metrics(stock):
    """
    Fetches key metrics and info for the stock.

    Args:
        stock (yf.Ticker): The yfinance Ticker object.

    Returns:
        dict or None: Dictionary with key metrics or None if error.
    """
    if not stock:
        return None
    try:
        info = stock.info
        # Add more error checking if specific keys are critical
        if not info:
             print(f"Warning: Could not fetch key metrics (.info) for {stock.info.get('symbol', '')}.")
             return None
        return info
    except Exception as e:
        print(f"Error fetching key metrics for {stock.info.get('symbol', '')}: {e}")
        return None

def get_historical_prices(stock, period="5y"):
    """
    Fetches historical stock prices.

    Args:
        stock (yf.Ticker): The yfinance Ticker object.
        period (str): Period string (e.g., "1y", "5y", "max").

    Returns:
        pd.DataFrame or None: DataFrame with historical price data or None if error.
    """
    if not stock:
        return None
    try:
        hist = stock.history(period=period)
        if hist.empty:
             print(f"Warning: Could not fetch historical prices for {stock.info.get('symbol', '')}.")
             return None
        return hist
    except Exception as e:
        print(f"Error fetching historical prices for {stock.info.get('symbol', '')}: {e}")
        return None

# Example Usage (for testing module directly)
if __name__ == '__main__':
    ticker = 'AAPL'
    years = 5
    stock_obj = get_stock_data(ticker)

    if stock_obj:
        print("\n--- Key Metrics ---")
        key_metrics = get_key_metrics(stock_obj)
        if key_metrics:
            print(f"Market Cap: {key_metrics.get('marketCap')}")
            print(f"P/E Ratio: {key_metrics.get('trailingPE')}")
            print(f"Forward P/E Ratio: {key_metrics.get('forwardPE')}")
            print(f"P/B Ratio: {key_metrics.get('priceToBook')}")
            # Print more metrics as needed

        print("\n--- Income Statement (Recent Years) ---")
        income_stmt = get_financial_statement(stock_obj, 'income', years)
        if income_stmt is not None:
            print(income_stmt.head())

        print("\n--- Balance Sheet (Recent Years) ---")
        balance_sheet = get_financial_statement(stock_obj, 'balance', years)
        if balance_sheet is not None:
            print(balance_sheet.head())

        print("\n--- Cash Flow (Recent Years) ---")
        cash_flow = get_financial_statement(stock_obj, 'cashflow', years)
        if cash_flow is not None:
            print(cash_flow.head())

        print("\n--- Historical Prices (Last 5 Years) ---")
        prices = get_historical_prices(stock_obj, period=f"{years}y")
        if prices is not None:
            print(prices.tail())