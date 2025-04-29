# fundamental_analyzer_pro/models/analysis_report.py

from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple, Any # Any can be used for pandas Series if needed
from datetime import datetime
# import pandas as pd # Uncomment if storing Series/DataFrame directly

@dataclass
class AnalysisReport:
    """
    Represents the structured result of a fundamental stock analysis.

    Attributes:
        ticker (str): The stock ticker symbol analyzed.
        company_name (Optional[str]): Full name of the company.
        sector (Optional[str]): Sector the company belongs to.
        industry (Optional[str]): Industry the company belongs to.
        analysis_timestamp (datetime): When the analysis was performed.
        overall_score (str): The final calculated score/rating (e.g., "Green", "Yellow", "Red", "N/A").
        score_breakdown (Dict[str, Tuple[str, str]]):
            Detailed breakdown of the score components.
            Format: {metric_name: (rating_string, display_value_string)}
            Example: {'ROE': ('Green', '18.50%')}
        current_metrics (Dict[str, Optional[float]]):
            Dictionary of the most recently calculated key financial metrics.
            Format: {metric_name: value} where value is a float or None/NaN if unavailable.
            Example: {'P/E': 25.5, 'ROE': 0.185, 'Debt/Equity': None}
        # Optional: Include historical data if desired, but can make the object large.
        # historical_trends: Optional[Dict[str, pd.Series]] = None
        # financial_statements: Optional[Dict[str, pd.DataFrame]] = None # Raw statements usually kept separate
        error_message: Optional[str] = None # To store any error encountered during analysis
        # Add other relevant summary fields as needed
    """
    ticker: str
    analysis_timestamp: datetime = field(default_factory=datetime.now)
    company_name: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    overall_score: str = "N/A"
    score_breakdown: Dict[str, Tuple[str, str]] = field(default_factory=dict)
    current_metrics: Dict[str, Optional[float]] = field(default_factory=dict)
    error_message: Optional[str] = None
    # historical_trends: Optional[Dict[str, Any]] = field(default_factory=dict) # Use Any or pd.Series

    def __post_init__(self):
        # Example validation or post-processing, if needed
        if not self.ticker:
            raise ValueError("Ticker symbol cannot be empty.")
        self.ticker = self.ticker.upper() # Ensure ticker is uppercase

    def add_metric(self, name: str, value: Optional[float]):
        """Helper method to add a current metric."""
        self.current_metrics[name] = value

    def add_score_component(self, name: str, rating: str, display_value: str):
        """Helper method to add an item to the score breakdown."""
        self.score_breakdown[name] = (rating, display_value)

# Example Usage (for testing or demonstration)
if __name__ == "__main__":
    # Example of creating an AnalysisReport instance
    report = AnalysisReport(
        ticker="AAPL",
        company_name="Apple Inc.",
        sector="Technology",
        industry="Consumer Electronics",
        overall_score="Green (Strong)",
    )

    # Add metrics and score components
    report.add_metric("P/E", 28.5)
    report.add_metric("ROE", 0.45)
    report.add_metric("Debt/Equity", 1.5)
    report.add_metric("NonExistentMetric", None) # Example of missing metric

    report.add_score_component("ROE", "Green", "45.00%")
    report.add_score_component("Debt/Equity", "Yellow", "1.50")
    report.add_score_component("P/E Ratio", "Yellow", "28.50")

    # Add an error if something went wrong
    # report.error_message = "Could not fetch cash flow statement."

    print("--- Example Analysis Report ---")
    print(f"Ticker: {report.ticker}")
    print(f"Company: {report.company_name}")
    print(f"Timestamp: {report.analysis_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Score: {report.overall_score}")

    print("\nCurrent Metrics:")
    for name, value in report.current_metrics.items():
        display_val = f"{value:.2f}" if isinstance(value, float) else "N/A"
        print(f"  - {name}: {display_val}")

    print("\nScore Breakdown:")
    for name, (rating, value_str) in report.score_breakdown.items():
        print(f"  - {name}: {rating} ({value_str})")

    if report.error_message:
        print(f"\nError: {report.error_message}")

    # Demonstrate accessing data
    print(f"\nAccessing P/E directly: {report.current_metrics.get('P/E')}")