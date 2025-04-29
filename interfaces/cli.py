# fundamental_analyzer_pro/interfaces/cli.py

import sys
import traceback # For more detailed error reporting if needed

# Assuming the 'professional' structure where 'main.py' is in the root
# Adjust imports based on how you run the script (e.g., using 'python -m')
try:
    # Assumes running with 'python -m fundamental_analyzer_pro.main'
    # Or that fundamental_analyzer_pro is in the PYTHONPATH
    from ..services.analysis_service import AnalysisService # Relative import
    from ..utils import export_utils, plotting_utils       # Relative imports
except ImportError:
    # Fallback for running cli.py directly (requires fundamental_analyzer_pro to be discoverable)
    # This might happen during development/testing if the parent isn't added to sys.path
    print("Warning: Could not perform relative imports. Attempting absolute imports.", file=sys.stderr)
    # Add parent directory to path to find siblings (services, utils)
    import os
    import sys
    PACKAGE_PARENT = '..'
    SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__))))
    sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))
    # Try absolute imports now - adjust 'fundamental_analyzer_pro' if your root folder name differs
    try:
        from fundamental_analyzer_pro.services.analysis_service import AnalysisService
        from fundamental_analyzer_pro.utils import export_utils, plotting_utils
    except ImportError as e:
        print(f"Fatal Error: Failed to import necessary modules. Ensure the project structure is correct and dependencies are installed. Details: {e}", file=sys.stderr)
        sys.exit(1)


def run_cli():
    """
    Runs the command-line interface for the fundamental analysis tool.
    """
    print("=" * 60)
    print(" Simple Stock Fundamental Analysis Tool (CLI Interface)")
    print("=" * 60)

    # Instantiate the core service - dependencies (like data provider)
    # would typically be injected here in a larger application.
    try:
        analyzer = AnalysisService()
    except Exception as e:
         print(f"Fatal Error: Could not initialize Analysis Service. {e}", file=sys.stderr)
         # traceback.print_exc() # Uncomment for detailed debug info
         sys.exit(1)

    while True:
        try:
            ticker = input("Enter the stock ticker symbol (e.g., AAPL, MSFT) or 'quit' to exit: ").strip().upper()
            if ticker == 'QUIT':
                break
            if not ticker:
                print("Ticker symbol cannot be empty.")
                continue

            print(f"\nAnalyzing {ticker}...")

            # --- Core Analysis Step ---
            success = analyzer.analyze_stock(ticker)

            if not success:
                # Error messages should ideally be printed by the service or logged
                print(f"Analysis failed for {ticker}. Please check the ticker or logs.")
                continue

            # --- Display Results ---
            summary = analyzer.get_summary_string()
            print(summary) # Assumes service provides a nicely formatted string

            # --- Optional Visualization ---
            show_plots = input("Do you want to see historical trend plots? (y/n): ").strip().lower()
            if show_plots == 'y':
                print("\nGenerating and displaying plots...")
                # The service might call the plotting utility directly
                analyzer.generate_and_display_plots()
                print("(Close plot windows to continue)")

            # --- Optional Export ---
            export_file = input("Do you want to export the results to Excel? (y/n): ").strip().lower()
            if export_file == 'y':
                default_filename = f"{ticker}_fundamental_analysis.xlsx"
                filename_input = input(f"Enter filename for export (default: {default_filename}): ").strip()
                filename = filename_input if filename_input else default_filename

                print(f"\nExporting data to {filename}...")
                try:
                    # Option 1: Service provides data, CLI calls exporter
                    # export_data = analyzer.get_export_data()
                    # export_utils.export_dict_to_excel(export_data, filename)

                    # Option 2: Service handles export internally (simpler for CLI)
                    analyzer.export_analysis(filename)

                    print(f"Data successfully exported to {filename}")
                except Exception as export_err:
                    print(f"Error exporting data to Excel: {export_err}")
                    # traceback.print_exc() # Uncomment for detailed debug info


        except KeyboardInterrupt:
            print("\nAnalysis interrupted by user.")
            break
        except Exception as e:
            print(f"\nAn unexpected error occurred:")
            print(f"Error Type: {type(e).__name__}")
            print(f"Error Details: {e}")
            # Uncomment for detailed debug info during development
            # print("\n--- Traceback ---")
            # traceback.print_exc()
            # print("--- End Traceback ---")
            print("Please try again or enter a different ticker.")

        print("\n" + "-" * 60)  # Separator for next analysis

    print("\nExiting Fundamental Analysis Tool. Goodbye!")

# This allows running the CLI directly for development/testing,
# although the intended entry point is usually main.py
if __name__ == "__main__":
    run_cli()