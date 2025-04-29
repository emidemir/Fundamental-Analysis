# fundamental_analyzer/main.py

import sys
from .analyzer import StockAnalyzer

def run_analysis():
    """ Main function to run the fundamental analysis tool. """
    print("="*60)
    print(" Simple Stock Fundamental Analysis Tool")
    print("="*60)

    while True:
        ticker = input("Enter the stock ticker symbol (e.g., AAPL, MSFT) or 'quit' to exit: ").strip().upper()
        if ticker == 'QUIT':
            break
        if not ticker:
            print("Ticker symbol cannot be empty.")
            continue

        try:
             # Hardcoding years for simplicity, yfinance often limits this anyway for statements
             years = 5
             print(f"Analyzing {ticker} for the last available financial years (up to {years})...")

             analyzer = StockAnalyzer(ticker, years)

             # 1. Fetch Data
             if not analyzer.fetch_data():
                  print(f"Failed to fetch data for {ticker}. Please check the ticker symbol.")
                  continue # Ask for a new ticker

             # 2. Calculate Metrics
             if not analyzer.calculate_metrics():
                  print(f"Failed to calculate metrics for {ticker}. Analysis may be incomplete.")
                  # Decide if you want to continue or stop
                  # continue

             # 3. Perform Scoring
             analyzer.perform_scoring()

             # 4. Display Summary
             analyzer.display_summary()

             # 5. Visualization (Optional)
             show_plots = input("Do you want to see historical trend plots? (y/n): ").strip().lower()
             if show_plots == 'y':
                  analyzer.plot_trends()

             # 6. Export (Optional)
             export_file = input("Do you want to export the results to Excel? (y/n): ").strip().lower()
             if export_file == 'y':
                  default_filename = f"{ticker}_fundamental_analysis.xlsx"
                  filename = input(f"Enter filename for export (default: {default_filename}): ").strip()
                  if not filename:
                       filename = default_filename
                  analyzer.export_to_excel(filename)

        except KeyboardInterrupt:
            print("\nAnalysis interrupted by user.")
            break
        except Exception as e:
            print(f"\nAn unexpected error occurred during analysis for {ticker}:")
            print(f"Error Type: {type(e).__name__}")
            print(f"Error Details: {e}")
            # Optionally add more detailed traceback logging here for debugging
            # import traceback
            # traceback.print_exc()
            print("Please try again or enter a different ticker.")

        print("\n" + "-"*60) # Separator for next analysis

    print("\nExiting Fundamental Analysis Tool. Goodbye!")

if __name__ == "__main__":
    # This allows running the script directly
    # Add the parent directory to sys.path if running main.py directly for imports to work
    import os
    if __package__ is None:
          # If running as a script, adjust path to allow relative imports
          file_dir = os.path.dirname(os.path.abspath(__file__))
          parent_dir = os.path.dirname(file_dir)
          if parent_dir not in sys.path:
              sys.path.insert(0, parent_dir)
          # Now re-import using package context if necessary, or just run
          # from fundamental_analyzer.analyzer import StockAnalyzer # Example re-import
          run_analysis()
    else:
          # If imported as a module (e.g. python -m fundamental_analyzer.main)
          run_analysis()