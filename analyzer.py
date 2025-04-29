# fundamental_analyzer/analyzer.py

import pandas as pd
import numpy as np

from . import data_fetcher
from . import metrics
from . import visualizer
from . import exporter

class StockAnalyzer:
    """
    Analyzes a stock's fundamentals using data fetched from online sources.
    """
    def __init__(self, ticker, years=5):
        self.ticker = ticker.upper()
        self.years = years
        self.stock_obj = None
        self.key_stats = None
        self.income_stmt = None
        self.balance_sheet = None
        self.cash_flow = None
        self.historical_prices = None
        self.calculated_metrics = {}
        self.score = None
        self.score_details = {}
        self.analysis_summary = {}

    def fetch_data(self):
        """ Fetches all necessary data for the analysis. """
        print(f"\nFetching data for {self.ticker}...")
        self.stock_obj = data_fetcher.get_stock_data(self.ticker)
        if not self.stock_obj:
            return False # Stop if ticker is invalid

        self.key_stats = data_fetcher.get_key_metrics(self.stock_obj)
        self.income_stmt = data_fetcher.get_financial_statement(self.stock_obj, 'income', self.years)
        self.balance_sheet = data_fetcher.get_financial_statement(self.stock_obj, 'balance', self.years)
        self.cash_flow = data_fetcher.get_financial_statement(self.stock_obj, 'cashflow', self.years)
        self.historical_prices = data_fetcher.get_historical_prices(self.stock_obj, period=f"{self.years}y")

        # Basic check if essential data is missing
        if self.income_stmt is None or self.balance_sheet is None or self.cash_flow is None:
            print("Warning: Could not retrieve essential financial statements. Analysis may be incomplete.")
            # Decide if analysis should proceed or stop
            # return False
        return True

    def calculate_metrics(self):
        """ Calculates all fundamental metrics. """
        print("Calculating metrics...")
        if self.income_stmt is None or self.balance_sheet is None:
             print("Cannot calculate metrics without Income Statement and Balance Sheet.")
             return False

        # --- Current Metrics (mostly from key_stats or latest statements) ---
        current_metrics = {}
        valuation = metrics.calculate_valuation_metrics(self.key_stats)
        current_metrics.update(valuation)

        profitability = metrics.calculate_profitability_metrics(self.income_stmt, self.balance_sheet)
        current_metrics.update(profitability) # ROE, ROA, Margins for the most recent year

        liquidity = metrics.calculate_liquidity_metrics(self.balance_sheet)
        current_metrics.update(liquidity) # Current/Quick ratio for the most recent year

        efficiency = metrics.calculate_efficiency_metrics(self.income_stmt, self.balance_sheet)
        current_metrics.update(efficiency) # Turnovers for the most recent year

        solvency = metrics.calculate_solvency_metrics(self.balance_sheet, self.income_stmt)
        current_metrics.update(solvency) # D/E, Interest Coverage for most recent year

        self.calculated_metrics['current'] = current_metrics

        # --- Historical Metrics (requires iterating through statement columns) ---
        # This part needs the more complex historical calculation logic from metrics.py
        # For simplicity, we'll focus on plotting raw statement data instead of calculated historical ratios
        # Add historical calculation here if `calculate_historical_metric` is fully implemented.
        self.calculated_metrics['historical'] = self._extract_historical_trends()

        print("Metrics calculated.")
        return True

    def _extract_historical_trends(self):
        """ Extracts key line items from statements for historical trend plotting. """
        historical_trends = {}
        if self.income_stmt is not None and not self.income_stmt.empty:
            historical_trends['Revenue'] = self.income_stmt.loc['Total Revenue'].sort_index() # Sort by year ascending
            historical_trends['Net Income'] = self.income_stmt.loc['Net Income'].sort_index()
            if 'Gross Profit' in self.income_stmt.index:
                 historical_trends['Gross Profit'] = self.income_stmt.loc['Gross Profit'].sort_index()

        if self.balance_sheet is not None and not self.balance_sheet.empty:
             # Safely get Equity and Assets, trying alternative names
             equity_label = 'Stockholder Equity' if 'Stockholder Equity' in self.balance_sheet.index else 'Total Stockholder Equity'
             if equity_label in self.balance_sheet.index:
                  historical_trends['Total Equity'] = self.balance_sheet.loc[equity_label].sort_index()

             if 'Total Assets' in self.balance_sheet.index:
                  historical_trends['Total Assets'] = self.balance_sheet.loc['Total Assets'].sort_index()
             if 'Total Debt' in self.balance_sheet.index:
                 historical_trends['Total Debt'] = self.balance_sheet.loc['Total Debt'].sort_index()


        if self.cash_flow is not None and not self.cash_flow.empty:
             if 'Operating Cash Flow' in self.cash_flow.index:
                  historical_trends['Operating Cash Flow'] = self.cash_flow.loc['Operating Cash Flow'].sort_index()
             if 'Free Cash Flow' in self.cash_flow.index: # yfinance often has this
                  historical_trends['Free Cash Flow'] = self.cash_flow.loc['Free Cash Flow'].sort_index()

        # Convert index to year integers for cleaner plotting if they are datetime objects
        for key, series in historical_trends.items():
             if isinstance(series.index, pd.DatetimeIndex):
                  historical_trends[key].index = series.index.year

        return historical_trends


    def perform_scoring(self, simple=True):
        """
        Assigns a score based on financial health using a simple rule-based system.
        Green (Good), Yellow (Average), Red (Poor)
        """
        print("Performing scoring...")
        if not self.calculated_metrics.get('current'):
            print("Cannot perform scoring without calculated metrics.")
            self.score = "N/A"
            self.score_details = {}
            return

        metrics_dict = self.calculated_metrics['current']
        scores = {}
        points = 0
        possible_points = 0

        # --- Scoring Rules (Example Thresholds - adjust as needed!) ---

        # Profitability
        roe = metrics_dict.get('ROE', np.nan)
        if pd.notna(roe):
            possible_points += 2
            if roe > 0.15: scores['ROE'] = ('Green', f"{roe:.2%}"); points += 2
            elif roe > 0.05: scores['ROE'] = ('Yellow', f"{roe:.2%}"); points += 1
            else: scores['ROE'] = ('Red', f"{roe:.2%}")
        else: scores['ROE'] = ('N/A', 'Missing')

        net_margin = metrics_dict.get('Net Margin', np.nan)
        if pd.notna(net_margin):
            possible_points += 2
            if net_margin > 0.10: scores['Net Margin'] = ('Green', f"{net_margin:.2%}"); points += 2
            elif net_margin > 0.03: scores['Net Margin'] = ('Yellow', f"{net_margin:.2%}"); points += 1
            else: scores['Net Margin'] = ('Red', f"{net_margin:.2%}")
        else: scores['Net Margin'] = ('N/A', 'Missing')

        # Solvency
        de_ratio = metrics_dict.get('Debt/Equity', np.nan)
        if pd.notna(de_ratio):
            possible_points += 2
            if de_ratio < 0.5: scores['Debt/Equity'] = ('Green', f"{de_ratio:.2f}"); points += 2
            elif de_ratio < 1.0: scores['Debt/Equity'] = ('Yellow', f"{de_ratio:.2f}"); points += 1
            else: scores['Debt/Equity'] = ('Red', f"{de_ratio:.2f}")
        else: scores['Debt/Equity'] = ('N/A', 'Missing')

        int_cov = metrics_dict.get('Interest Coverage', np.nan)
        if pd.notna(int_cov):
             possible_points += 1
             if int_cov > 5: scores['Interest Coverage'] = ('Green', f"{int_cov:.2f}x"); points += 1
             elif int_cov > 2: scores['Interest Coverage'] = ('Yellow', f"{int_cov:.2f}x") # No points for yellow here
             else: scores['Interest Coverage'] = ('Red', f"{int_cov:.2f}x")
        else: scores['Interest Coverage'] = ('N/A', 'Missing')


        # Liquidity
        current_ratio = metrics_dict.get('Current Ratio', np.nan)
        if pd.notna(current_ratio):
            possible_points += 1
            if current_ratio > 1.5: scores['Current Ratio'] = ('Green', f"{current_ratio:.2f}"); points += 1
            elif current_ratio > 1.0: scores['Current Ratio'] = ('Yellow', f"{current_ratio:.2f}")
            else: scores['Current Ratio'] = ('Red', f"{current_ratio:.2f}")
        else: scores['Current Ratio'] = ('N/A', 'Missing')

        # Valuation (Lower P/E generally 'better', but highly context dependent)
        pe_ratio = metrics_dict.get('P/E', np.nan)
        if pd.notna(pe_ratio):
             possible_points += 1 # Low weight as 'good' P/E varies
             if pe_ratio < 15: scores['P/E Ratio'] = ('Green', f"{pe_ratio:.2f}"); points += 1
             elif pe_ratio < 25: scores['P/E Ratio'] = ('Yellow', f"{pe_ratio:.2f}")
             else: scores['P/E Ratio'] = ('Red', f"{pe_ratio:.2f}") # High P/E might indicate overvaluation or high growth
        else: scores['P/E Ratio'] = ('N/A', 'Missing')


        # --- Final Score Calculation ---
        if possible_points > 0:
             score_percentage = points / possible_points
             if score_percentage >= 0.75: self.score = "Green (Strong)"
             elif score_percentage >= 0.50: self.score = "Yellow (Average)"
             else: self.score = "Red (Weak)"
        else:
             self.score = "N/A (Insufficient Data)"

        self.score_details = scores
        print(f"Scoring complete. Overall: {self.score}")


    def generate_summary(self):
        """ Creates a dictionary summarizing the analysis. """
        self.analysis_summary = {
            'Ticker': self.ticker,
            'Company Name': self.key_stats.get('longName', 'N/A') if self.key_stats else 'N/A',
            'Sector': self.key_stats.get('sector', 'N/A') if self.key_stats else 'N/A',
            'Industry': self.key_stats.get('industry', 'N/A') if self.key_stats else 'N/A',
            'Overall Score': self.score,
            'Score Breakdown': self.score_details,
            'Key Metrics (Current)': self.calculated_metrics.get('current', {}),
            # Add more sections as needed
        }
        return self.analysis_summary

    def display_summary(self):
        """ Prints the analysis summary to the console. """
        summary = self.generate_summary()
        print("\n" + "="*50)
        print(f" Fundamental Analysis Report for: {summary['Ticker']} ({summary['Company Name']})")
        print(f" Sector: {summary['Sector']} | Industry: {summary['Industry']}")
        print("="*50)

        print(f"\nOverall Financial Health Score: {summary['Overall Score']}")
        print("--- Score Breakdown ---")
        if summary['Score Breakdown']:
            for metric, (rating, value) in summary['Score Breakdown'].items():
                print(f"  - {metric:<20}: {rating:<10} ({value})")
        else:
            print("  No scoring details available.")

        print("\n--- Key Metrics (Most Recent) ---")
        if summary['Key Metrics (Current)']:
             metrics_to_display = [
                  'P/E', 'Forward P/E', 'P/B', 'PEG', 'ROE', 'ROA',
                  'Net Margin', 'Gross Margin', 'Debt/Equity',
                  'Current Ratio', 'Quick Ratio', 'Interest Coverage',
                  'Asset Turnover', 'Inventory Turnover'
             ]
             for metric in metrics_to_display:
                  value = summary['Key Metrics (Current)'].get(metric)
                  if value is not None and pd.notna(value):
                       if isinstance(value, float):
                           # Format percentages nicely
                           if any(s in metric.lower() for s in ['margin', 'roe', 'roa', 'rate']):
                               print(f"  - {metric:<20}: {value:.2%}")
                           else:
                               print(f"  - {metric:<20}: {value:.2f}")
                       else:
                           print(f"  - {metric:<20}: {value}") # Should not happen often with calc metrics
                  else:
                       print(f"  - {metric:<20}: N/A")
        else:
             print("  No current metrics available.")

        print("\n" + "="*50)

    def plot_trends(self):
        """ Generates and displays plots for key historical trends. """
        print("\nGenerating plots...")
        visualizer.close_plots() # Close any previous plots

        historical_data = self.calculated_metrics.get('historical', {})
        plotted = False

        # Plot selected historical trends
        revenue = historical_data.get('Revenue')
        if revenue is not None and not revenue.empty:
            visualizer.plot_metric_trend(revenue, 'Total Revenue', kind='bar')
            plotted = True

        net_income = historical_data.get('Net Income')
        if net_income is not None and not net_income.empty:
            visualizer.plot_metric_trend(net_income, 'Net Income', kind='bar')
            plotted = True

        equity = historical_data.get('Total Equity')
        if equity is not None and not equity.empty:
             visualizer.plot_metric_trend(equity, 'Total Equity', kind='line')
             plotted = True

        fcf = historical_data.get('Free Cash Flow')
        if fcf is not None and not fcf.empty:
            visualizer.plot_metric_trend(fcf, 'Free Cash Flow', kind='line')
            plotted = True

        # Add plots for other calculated historical metrics if available

        if plotted:
            print("Displaying plots... Close plot windows to continue.")
            visualizer.display_plots()
        else:
            print("No historical data available to plot.")


    def export_to_excel(self, filename="fundamental_analysis_export.xlsx"):
        """ Exports the analysis results to an Excel file. """
        print(f"\nExporting data to {filename}...")
        data_to_export = {
            'Summary': pd.DataFrame([self.analysis_summary]), # Convert summary dict to DataFrame
            'Income Statement': self.income_stmt if self.income_stmt is not None else pd.DataFrame(),
            'Balance Sheet': self.balance_sheet if self.balance_sheet is not None else pd.DataFrame(),
            'Cash Flow': self.cash_flow if self.cash_flow is not None else pd.DataFrame(),
            'Key Metrics': pd.Series(self.calculated_metrics.get('current', {})).to_frame('Value'),
            'Historical Trends': pd.DataFrame(self.calculated_metrics.get('historical', {})),
        }
        try:
            exporter.export_dict_to_excel(data_to_export, filename)
            print(f"Data successfully exported to {filename}")
        except Exception as e:
            print(f"Error exporting data to Excel: {e}")