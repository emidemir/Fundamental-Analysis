# fundamental_analyzer_pro/services/analysis_service.py

import pandas as pd
import numpy as np
from datetime import datetime
import traceback # For detailed error logging

# --- Dependency Imports ---
# Use try-except for flexibility during development/testing if paths differ
try:
    # Assumes running via main.py or test runner that sets up paths
    from .data_provider_service import DataProviderService
    from .metrics_service import MetricsService
    from ..models.analysis_report import AnalysisReport
    from ..utils import plotting_utils, export_utils # Assuming utils are siblings of models/services
except ImportError:
    # Fallback for potentially running file directly or path issues
    print("Warning: analysis_service.py failed relative imports. Attempting absolute.")
    # This part might need adjustment based on your exact project root and PYTHONPATH
    try:
        from fundamental_analyzer_pro.services.data_provider_service import DataProviderService
        from fundamental_analyzer_pro.services.metrics_service import MetricsService
        from fundamental_analyzer_pro.models.analysis_report import AnalysisReport
        from fundamental_analyzer_pro.utils import plotting_utils, export_utils
    except ImportError as e:
        print(f"FATAL ERROR in analysis_service.py: Cannot import dependencies. Check paths and structure. {e}")
        raise # Re-raise the error to prevent the service from being unusable

# --- Constants (Example Thresholds for Scoring) ---
# These should ideally be configurable or part of a separate config module
ROE_THRESHOLDS = {'green': 0.15, 'yellow': 0.05}
NET_MARGIN_THRESHOLDS = {'green': 0.10, 'yellow': 0.03}
DE_RATIO_THRESHOLDS = {'green': 0.6, 'yellow': 1.2} # Lower is better
CURRENT_RATIO_THRESHOLDS = {'green': 1.8, 'yellow': 1.0} # Higher is better
INTEREST_COVERAGE_THRESHOLDS = {'green': 5.0, 'yellow': 2.0} # Higher is better
PE_RATIO_THRESHOLDS = {'green': 15, 'yellow': 25} # Lower is often better (context dependent)

class AnalysisService:
    """
    Orchestrates the fundamental analysis of a stock.
    Uses DataProviderService for data fetching and MetricsService for calculations.
    Produces an AnalysisReport.
    """

    def __init__(self, data_provider=None, metrics_calculator=None):
        """
        Initializes the AnalysisService.

        Args:
            data_provider (DataProviderService, optional): Instance for fetching data. Defaults to a new DataProviderService().
            metrics_calculator (MetricsService, optional): Instance for calculating metrics. Defaults to a new MetricsService().
        """
        self.data_provider = data_provider or DataProviderService()
        self.metrics_calculator = metrics_calculator or MetricsService()
        self.current_report: Optional[AnalysisReport] = None
        # Store raw data temporarily if needed for export/plotting
        self._raw_data: Optional[dict] = None
        self._historical_trends: Optional[dict] = None

    def analyze_stock(self, ticker: str) -> bool:
        """
        Performs the full fundamental analysis for a given ticker symbol.

        Fetches data, calculates metrics, performs scoring, and compiles the report.
        Stores the result in self.current_report.

        Args:
            ticker (str): The stock ticker symbol.

        Returns:
            bool: True if the analysis was completed successfully (even if data is partial),
                  False if a critical error occurred (e.g., cannot fetch basic data).
        """
        self.current_report = None # Reset previous report
        self._raw_data = None
        self._historical_trends = None
        analysis_error = None
        print(f"[{datetime.now()}] Starting analysis for {ticker.upper()}...")

        try:
            # 1. Fetch Data
            print("Fetching data...")
            raw_data = self.data_provider.fetch_all_data(ticker)
            if not raw_data or not raw_data.get('key_stats'): # Require at least key_stats
                analysis_error = f"Failed to fetch essential data for {ticker}. Ticker might be invalid or API unavailable."
                print(f"Error: {analysis_error}")
                self.current_report = AnalysisReport(ticker=ticker, error_message=analysis_error)
                return False
            self._raw_data = raw_data
            print("Data fetched successfully.")

            # Extract key info for the report early
            key_stats = raw_data.get('key_stats', {})
            company_name = key_stats.get('longName')
            sector = key_stats.get('sector')
            industry = key_stats.get('industry')

            # 2. Calculate Metrics
            print("Calculating metrics...")
            income_stmt = raw_data.get('income_stmt')
            balance_sheet = raw_data.get('balance_sheet')
            cash_flow = raw_data.get('cash_flow')

            calculated_metrics = self.metrics_calculator.calculate_all_current_metrics(
                income_stmt=income_stmt,
                balance_sheet=balance_sheet,
                key_stats=key_stats,
                cash_flow=cash_flow # Pass cash flow if needed by metric service
            )
            print("Metrics calculated.")

            # 3. Perform Scoring
            print("Performing scoring...")
            overall_score, score_breakdown = self._perform_scoring(calculated_metrics)
            print(f"Scoring complete. Overall: {overall_score}")

            # 4. Extract Historical Trends (for plotting/export)
            self._historical_trends = self._extract_historical_trends(income_stmt, balance_sheet, cash_flow)

            # 5. Compile Report
            print("Compiling report...")
            self.current_report = AnalysisReport(
                ticker=ticker,
                company_name=company_name,
                sector=sector,
                industry=industry,
                overall_score=overall_score,
                score_breakdown=score_breakdown,
                current_metrics=calculated_metrics,
                analysis_timestamp=datetime.now()
                # historical_trends=self._historical_trends # Optionally add to report object
            )
            print(f"[{datetime.now()}] Analysis for {ticker} completed successfully.")
            return True

        except Exception as e:
            analysis_error = f"An unexpected error occurred during analysis for {ticker}: {e}"
            print(f"Error: {analysis_error}")
            # Log the full traceback for debugging purposes
            print("\n--- Traceback ---")
            traceback.print_exc()
            print("--- End Traceback ---\n")
            # Create a report indicating the error
            self.current_report = AnalysisReport(
                ticker=ticker,
                error_message=analysis_error,
                overall_score="Error",
                company_name=key_stats.get('longName') if 'key_stats' in locals() else None # Try to get name if fetched
            )
            return False # Indicate failure

    def _perform_scoring(self, metrics_dict: dict) -> Tuple[str, dict]:
        """
        Assigns a score based on financial health using predefined thresholds.

        Args:
            metrics_dict (dict): Dictionary of calculated metrics.

        Returns:
            Tuple[str, dict]: (Overall score string, score breakdown dictionary)
        """
        if not metrics_dict:
            return "N/A (No Metrics)", {}

        scores = {}
        points = 0
        possible_points = 0

        def rate_metric(metric_name, value, thresholds, higher_is_better=True):
            nonlocal points, possible_points
            rating, display_val = "N/A", "Missing"
            points_added = 0
            is_valid = value is not None and pd.notna(value)

            if is_valid:
                # Format display value (handle percentages)
                is_percentage = any(s in metric_name.lower() for s in ['margin', 'roe', 'roa', 'rate'])
                display_val = f"{value:.2%}" if is_percentage else f"{value:.2f}"

                possible_points += 2 # Max 2 points per scored metric
                green = thresholds['green']
                yellow = thresholds['yellow']

                if higher_is_better:
                    if value >= green: rating, points_added = "Green", 2
                    elif value >= yellow: rating, points_added = "Yellow", 1
                    else: rating = "Red"
                else: # Lower is better (e.g., D/E, P/E)
                    if value <= green: rating, points_added = "Green", 2
                    elif value <= yellow: rating, points_added = "Yellow", 1
                    else: rating = "Red"
            else:
                 # Don't count missing metrics towards possible points if we require them
                 # Decide if a missing metric counts against the score or not.
                 # Here, we just mark it N/A and don't add to possible_points unless required.
                 pass

            scores[metric_name] = (rating, display_val)
            return points_added

        # Apply scoring rules - ADD MORE METRICS HERE
        points += rate_metric('ROE', metrics_dict.get('ROE'), ROE_THRESHOLDS, higher_is_better=True)
        points += rate_metric('Net Margin', metrics_dict.get('Net Margin'), NET_MARGIN_THRESHOLDS, higher_is_better=True)
        points += rate_metric('Debt/Equity', metrics_dict.get('Debt/Equity'), DE_RATIO_THRESHOLDS, higher_is_better=False)
        points += rate_metric('Current Ratio', metrics_dict.get('Current Ratio'), CURRENT_RATIO_THRESHOLDS, higher_is_better=True)
        points += rate_metric('Interest Coverage', metrics_dict.get('Interest Coverage'), INTEREST_COVERAGE_THRESHOLDS, higher_is_better=True)
        # P/E is context-dependent, scoring it simply might be misleading
        # points += rate_metric('P/E', metrics_dict.get('P/E'), PE_RATIO_THRESHOLDS, higher_is_better=False)

        # Determine overall score
        if possible_points > 0:
            score_percentage = points / possible_points
            if score_percentage >= 0.75: overall_score = "Green (Strong)"
            elif score_percentage >= 0.50: overall_score = "Yellow (Average)"
            else: overall_score = "Red (Weak)"
        else:
            overall_score = "N/A (Insufficient Data)"

        return overall_score, scores

    def _extract_historical_trends(self, income_stmt, balance_sheet, cash_flow):
        """ Extracts key line items from statements for historical trend plotting. """
        historical_trends = {}
        try:
            # Safely extract data, handling potential missing statements or line items
            if income_stmt is not None and not income_stmt.empty:
                if 'Total Revenue' in income_stmt.index:
                    historical_trends['Revenue'] = income_stmt.loc['Total Revenue'].sort_index()
                if 'Net Income' in income_stmt.index:
                    historical_trends['Net Income'] = income_stmt.loc['Net Income'].sort_index()
                # Add Gross Profit, Operating Income etc. if desired

            if balance_sheet is not None and not balance_sheet.empty:
                equity_label = next((label for label in ['Stockholder Equity', 'Total Stockholder Equity'] if label in balance_sheet.index), None)
                if equity_label:
                    historical_trends['Total Equity'] = balance_sheet.loc[equity_label].sort_index()
                if 'Total Assets' in balance_sheet.index:
                    historical_trends['Total Assets'] = balance_sheet.loc['Total Assets'].sort_index()
                debt_label = next((label for label in ['Total Debt', 'Long Term Debt'] if label in balance_sheet.index), None)
                if debt_label:
                     historical_trends['Total Debt'] = balance_sheet.loc[debt_label].sort_index()

            if cash_flow is not None and not cash_flow.empty:
                op_cf_label = next((label for label in ['Operating Cash Flow', 'Total Cash From Operating Activities'] if label in cash_flow.index), None)
                if op_cf_label:
                     historical_trends['Operating Cash Flow'] = cash_flow.loc[op_cf_label].sort_index()
                fcf_label = next((label for label in ['Free Cash Flow'] if label in cash_flow.index), None)
                if fcf_label:
                    historical_trends['Free Cash Flow'] = cash_flow.loc[fcf_label].sort_index()

            # Convert index to year integers for cleaner plotting if they are datetime objects
            for key, series in historical_trends.items():
                if isinstance(series.index, pd.DatetimeIndex):
                    historical_trends[key].index = series.index.year

        except Exception as e:
            print(f"Warning: Error extracting historical trends: {e}")
            # Continue without historical trends if extraction fails

        return historical_trends

    def get_summary_string(self) -> str:
        """
        Formats the current analysis report into a readable string summary.

        Returns:
            str: A formatted string summary, or an error message if no report is available.
        """
        if not self.current_report:
            return "No analysis report available. Please run analyze_stock() first."
        if self.current_report.error_message:
            return f"Analysis Error for {self.current_report.ticker}: {self.current_report.error_message}"

        report = self.current_report
        summary = []
        sep = "=" * 50
        summary.append(sep)
        summary.append(f" Fundamental Analysis Report for: {report.ticker} ({report.company_name or 'N/A'})")
        summary.append(f" Sector: {report.sector or 'N/A'} | Industry: {report.industry or 'N/A'}")
        summary.append(f" Analysis Timestamp: {report.analysis_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        summary.append(sep)

        summary.append(f"\nOverall Financial Health Score: {report.overall_score}")
        summary.append("--- Score Breakdown ---")
        if report.score_breakdown:
            for metric, (rating, value) in report.score_breakdown.items():
                summary.append(f"  - {metric:<20}: {rating:<10} ({value})")
        else:
            summary.append("  No scoring details available.")

        summary.append("\n--- Key Metrics (Most Recent) ---")
        if report.current_metrics:
             metrics_to_display = [ # Define order and selection
                  'P/E', 'Forward P/E', 'P/B', 'PEG', 'ROE', 'ROA',
                  'Net Margin', 'Gross Margin', 'Debt/Equity',
                  'Current Ratio', 'Quick Ratio', 'Interest Coverage',
                  'Asset Turnover', 'Inventory Turnover' # Add more as needed
             ]
             displayed_count = 0
             for metric in metrics_to_display:
                  value = report.current_metrics.get(metric)
                  if value is not None and pd.notna(value):
                       displayed_count += 1
                       is_percentage = any(s in metric.lower() for s in ['margin', 'roe', 'roa', 'rate'])
                       display_val = f"{value:.2%}" if is_percentage else f"{value:.2f}"
                       summary.append(f"  - {metric:<20}: {display_val}")
                  # else: # Optionally show N/A for metrics that weren't calculated
                  #     summary.append(f"  - {metric:<20}: N/A")
             if displayed_count == 0:
                  summary.append("  No key metrics data available.")
        else:
             summary.append("  No key metrics calculated.")

        summary.append("\n" + sep)
        return "\n".join(summary)

    def generate_and_display_plots(self):
        """ Generates and displays plots for key historical trends using plotting_utils. """
        if not self._historical_trends:
            print("No historical data available to plot.")
            return

        plotting_utils.close_plots() # Close previous plots if any
        plotted = False

        trends_to_plot = { # Define which trends to plot and how
            'Revenue': {'kind': 'bar', 'title': 'Total Revenue Trend'},
            'Net Income': {'kind': 'bar', 'title': 'Net Income Trend'},
            'Total Equity': {'kind': 'line', 'title': 'Total Equity Trend'},
            'Free Cash Flow': {'kind': 'line', 'title': 'Free Cash Flow Trend'},
            'Operating Cash Flow': {'kind': 'line', 'title': 'Operating Cash Flow Trend'},
            'Total Debt': {'kind': 'line', 'title': 'Total Debt Trend'},
        }

        for key, config in trends_to_plot.items():
            data_series = self._historical_trends.get(key)
            if data_series is not None and not data_series.empty:
                try:
                    plotting_utils.plot_metric_trend(
                        data_series,
                        metric_name=key,
                        title=config.get('title', f"{key} Trend"),
                        kind=config.get('kind', 'line')
                    )
                    plotted = True
                except Exception as plot_err:
                    print(f"Warning: Could not plot {key}. Error: {plot_err}")

        if plotted:
            plotting_utils.display_plots()
        else:
            print("No valid historical trends found to plot.")

    def export_analysis(self, filename: str):
        """
        Exports the current analysis results (summary, metrics, raw data) to an Excel file.

        Args:
            filename (str): The path/name for the output Excel file.

        Raises:
            ValueError: If no analysis report is available to export.
            Exception: If the export process fails (relayed from export_utils).
        """
        if not self.current_report:
            raise ValueError("No analysis report available to export. Run analyze_stock first.")
        if self.current_report.error_message:
            print(f"Warning: Exporting report for {self.current_report.ticker} which contains an error: {self.current_report.error_message}")
            # Decide if you want to prevent export on error or allow exporting the error state

        report_data = {
            # Convert report object fields to DataFrames/Series for Excel
            "Summary": pd.DataFrame([self.current_report.__dict__]).drop(columns=['score_breakdown', 'current_metrics'], errors='ignore').T, # Transpose for readability
            "Score Breakdown": pd.DataFrame(self.current_report.score_breakdown.items(), columns=['Metric', 'Rating/Value']),
            "Key Metrics": pd.Series(self.current_report.current_metrics, name="Value").to_frame(),
            "Historical Trends": pd.DataFrame(self._historical_trends) if self._historical_trends else pd.DataFrame(),
            # Include raw statements if available and desired
            "Income Statement": self._raw_data.get('income_stmt', pd.DataFrame()),
            "Balance Sheet": self._raw_data.get('balance_sheet', pd.DataFrame()),
            "Cash Flow": self._raw_data.get('cash_flow', pd.DataFrame())
        }

        # Clean up empty dataframes before export
        data_to_export = {k: v for k, v in report_data.items() if not (isinstance(v, (pd.DataFrame, pd.Series)) and v.empty)}

        if not data_to_export:
             print("No data available to export.")
             return

        try:
            export_utils.export_dict_to_excel(data_to_export, filename)
        except Exception as e:
            print(f"Error during Excel export process: {e}")
            raise # Re-raise to allow CLI to handle/report

# Example of direct usage (mainly for testing the service itself)
if __name__ == "__main__":
    print("Testing AnalysisService...")
    service = AnalysisService()
    ticker_to_test = 'AAPL' # Use a common ticker

    success = service.analyze_stock(ticker_to_test)

    if success:
        print("\n--- Analysis Summary ---")
        print(service.get_summary_string())

        print("\n--- Generating Plots ---")
        service.generate_and_display_plots() # Will pop up plots

        try:
            print("\n--- Exporting Data ---")
            service.export_analysis(f"{ticker_to_test}_service_test_export.xlsx")
            print("Export test successful.")
        except Exception as ex:
            print(f"Export test failed: {ex}")
    else:
        print(f"\nAnalysis failed for {ticker_to_test}.")
        if service.current_report:
             print(f"Error details: {service.current_report.error_message}")