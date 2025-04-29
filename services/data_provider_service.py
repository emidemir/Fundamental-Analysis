# fundamental_analyzer_pro/services/data_provider_service.py

import yfinance as yf
import pandas as pd
from typing import Optional, Dict, Any
from functools import lru_cache
from datetime import datetime

# Cache Ticker objects to avoid repeated network calls for the same ticker quickly
# Adjust maxsize based on expected usage patterns
@lru_cache(maxsize=32)
def _get_cached_ticker(ticker_symbol: str) -> Optional[yf.Ticker]:
    """
    Internal function to get and cache the yf.Ticker object.
    Checks for basic validity.

    Args:
        ticker_symbol (str): The stock ticker symbol.

    Returns:
        Optional[yf.Ticker]: The yfinance Ticker object if valid and found, else None.
    """
    print(f"[{datetime.now()}] Requesting yf.Ticker object for: {ticker_symbol}")
    try:
        stock = yf.Ticker(ticker_symbol)
        # Accessing .info forces yfinance to fetch data.
        # Check if essential info is present. If not, ticker might be delisted or invalid.
        if not stock.info or 'symbol' not in stock.info or stock.info.get('quoteType') == 'MUTUALFUND':
            # Added check for mutual funds as they often lack statement data
            if stock.info.get('quoteType') == 'MUTUALFUND':
                 print(f"Warning: Ticker '{ticker_symbol}' appears to be a Mutual Fund. Financial statement analysis may not apply.")
                 # Decide if you want to proceed or block mutual funds. Let's proceed but warn.
                 # return None # Uncomment to block mutual funds
            else:
                 print(f"Error: Could not validate ticker '{ticker_symbol}' or fetch basic info. It might be invalid or delisted.")
                 return None
        print(f"[{datetime.now()}] Successfully obtained and validated yf.Ticker for {stock.info.get('symbol', ticker_symbol)}")
        return stock
    except Exception as e:
        # Catches network errors, unexpected API responses etc.
        print(f"Error creating/validating yfinance Ticker object for {ticker_symbol}: {e}")
        return None

class DataProviderService:
    """
    Provides financial data for a given stock ticker using yfinance.
    Handles data fetching, basic validation, and error handling.
    """

    def fetch_all_data(self, ticker: str, years: int = 5, history_period: str = "5y") -> Optional[Dict[str, Any]]:
        """
        Fetches all required financial data for a given ticker.

        Args:
            ticker (str): The stock ticker symbol (e.g., 'AAPL').
            years (int): Number of years of statement data to attempt to fetch.
                         Note: yfinance typically provides ~4 years maximum.
            history_period (str): Period string for historical prices (e.g., "1y", "5y", "max").

        Returns:
            Optional[Dict[str, Any]]: A dictionary containing the fetched data:
                'ticker_requested': Original ticker requested.
                'ticker_yf': Symbol confirmed by yfinance.
                'key_stats': Dictionary of key statistics from yf.info.
                'income_stmt': DataFrame of the Income Statement.
                'balance_sheet': DataFrame of the Balance Sheet.
                'cash_flow': DataFrame of the Cash Flow Statement.
                'historical_prices': DataFrame of historical stock prices.
                Returns None if the ticker is fundamentally invalid or basic info cannot be fetched.
                Individual components within the dict might be empty DataFrames/dicts if specific data is unavailable.
        """
        ticker = ticker.upper()
        print(f"[{datetime.now()}] DataProviderService: Fetching all data for {ticker}...")

        stock_object = _get_cached_ticker(ticker)

        if stock_object is None:
            print(f"[{datetime.now()}] DataProviderService: Failed to get valid Ticker object for {ticker}. Aborting fetch.")
            return None # Cannot proceed without a valid Ticker object

        # If ticker was potentially redirected (e.g., 'FB' -> 'META'), use the one from .info
        ticker_yf = stock_object.info.get('symbol', ticker)
        print(f"Processing data for symbol: {ticker_yf}")

        results = {
            'ticker_requested': ticker,
            'ticker_yf': ticker_yf,
            'key_stats': {},
            'income_stmt': pd.DataFrame(),
            'balance_sheet': pd.DataFrame(),
            'cash_flow': pd.DataFrame(),
            'historical_prices': pd.DataFrame()
        }

        # 1. Fetch Key Stats (we already have this from validation)
        results['key_stats'] = stock_object.info if stock_object.info else {}
        if not results['key_stats']:
             print(f"Warning: Could not retrieve key_stats (stock.info) for {ticker_yf}.")

        # 2. Fetch Financial Statements
        statement_types = {
            'income_stmt': 'Income Statement',
            'balance_sheet': 'Balance Sheet',
            'cash_flow': 'Cash Flow'
        }
        for key, name in statement_types.items():
            print(f"Fetching {name}...")
            try:
                if key == 'income_stmt': statement = stock_object.income_stmt
                elif key == 'balance_sheet': statement = stock_object.balance_sheet
                elif key == 'cash_flow': statement = stock_object.cashflow
                else: continue # Should not happen

                if not statement.empty:
                    # Select up to 'years' available columns
                    num_available = statement.shape[1]
                    years_to_fetch = min(years, num_available)
                    results[key] = statement.iloc[:, :years_to_fetch]
                    print(f"Successfully fetched {name} ({results[key].shape[1]} years).")
                else:
                    print(f"Warning: No {name} data found for {ticker_yf}.")
                    results[key] = pd.DataFrame() # Ensure it's an empty DataFrame

            except Exception as e:
                print(f"Error fetching {name} for {ticker_yf}: {e}")
                results[key] = pd.DataFrame() # Return empty DataFrame on error

        # 3. Fetch Historical Prices
        print(f"Fetching Historical Prices (period: {history_period})...")
        try:
            hist = stock_object.history(period=history_period)
            if not hist.empty:
                results['historical_prices'] = hist
                print(f"Successfully fetched historical prices (records: {len(hist)}).")
            else:
                 print(f"Warning: No historical price data found for {ticker_yf} for period {history_period}.")
                 results['historical_prices'] = pd.DataFrame()
        except Exception as e:
            print(f"Error fetching historical prices for {ticker_yf}: {e}")
            results['historical_prices'] = pd.DataFrame()

        print(f"[{datetime.now()}] DataProviderService: Finished fetching data for {ticker}.")
        return results

# Example Usage (for testing the service directly)
if __name__ == "__main__":
    print("Testing DataProviderService...")
    provider = DataProviderService()
    test_tickers = ['AAPL', 'MSFT', 'GOOGL', 'NONEXISTENTTICKER', 'BF-B'] # Include a non-existent one and one with '.'/'/'

    for t in test_tickers:
        print("\n" + "="*30)
        print(f"Testing with ticker: {t}")
        print("="*30)
        data = provider.fetch_all_data(t)

        if data:
            print(f"\nData fetched for: {data['ticker_yf']} (Requested: {data['ticker_requested']})")
            print(f"Key Stats Snippet: Market Cap = {data['key_stats'].get('marketCap', 'N/A')}, P/E = {data['key_stats'].get('trailingPE', 'N/A')}")
            print(f"Income Statement Columns: {list(data['income_stmt'].columns) if not data['income_stmt'].empty else 'Empty'}")
            print(f"Balance Sheet Columns: {list(data['balance_sheet'].columns) if not data['balance_sheet'].empty else 'Empty'}")
            print(f"Cash Flow Columns: {list(data['cash_flow'].columns) if not data['cash_flow'].empty else 'Empty'}")
            print(f"Historical Prices Shape: {data['historical_prices'].shape if not data['historical_prices'].empty else 'Empty'}")
            # Test cache - request again
            print(f"\nRequesting {t} again (should use cache)...")
            data_cached = provider.fetch_all_data(t)
            if data_cached:
                 print("Second request successful (cache likely used if no 'Requesting yf.Ticker' message appeared).")
        else:
            print(f"\nFailed to fetch data for {t}.")

    # Demonstrate cache status (optional)
    print("\nCache Info:")
    print(_get_cached_ticker.cache_info())