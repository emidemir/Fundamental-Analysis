# fundamental_analyzer_pro/main.py

import sys
import traceback
import os

# --- Path Setup (Optional but can help in some execution environments) ---
# If running `python main.py` directly from the project root, this helps ensure
# modules within the 'fundamental_analyzer_pro' package are found.
# If running with `python -m fundamental_analyzer_pro.main`, this is usually not needed.
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    # print(f"Adding project root to sys.path: {project_root}") # Uncomment for debug
    sys.path.insert(0, project_root)
# --------------------------------------------------------------------------


def start_application():
    """
    Initializes and starts the command-line interface for the application.
    Handles top-level exceptions and import errors.
    """
    try:
        # Attempt to import the primary interface module
        # Use absolute import assuming 'fundamental_analyzer_pro' is the package name
        from fundamental_analyzer_pro.interfaces import cli
        print("Initializing Fundamental Analysis Tool...")

        # Run the main loop/function of the command-line interface
        cli.run_cli()

        print("\nFundamental Analysis Tool execution finished normally.")

    except ImportError as e:
        print(f"\nFATAL ERROR: Could not import required application modules.", file=sys.stderr)
        print(f"Import Error Details: {e}", file=sys.stderr)
        print("\nPlease ensure:", file=sys.stderr)
        print("  1. You are running this from the correct directory.", file=sys.stderr)
        print("  2. The project structure is intact (e.g., 'interfaces/cli.py' exists).", file=sys.stderr)
        print("  3. Dependencies are installed (`pip install -r requirements.txt`).", file=sys.stderr)
        print("  4. Consider running using `python -m fundamental_analyzer_pro.main` from the directory *containing* 'fundamental_analyzer_pro'.", file=sys.stderr)
        sys.exit(1) # Exit with an error code

    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully at the top level
        print("\n\nOperation cancelled by user (Ctrl+C). Exiting.", file=sys.stderr)
        sys.exit(0) # Exit cleanly

    except Exception as e:
        # Catch any other unexpected exceptions that weren't handled deeper down
        print(f"\nFATAL UNHANDLED ERROR encountered:", file=sys.stderr)
        print(f"Error Type: {type(e).__name__}", file=sys.stderr)
        print(f"Error Details: {e}", file=sys.stderr)
        print("\n--- Traceback ---", file=sys.stderr)
        # Print the full traceback to stderr for debugging
        traceback.print_exc(file=sys.stderr)
        print("--- End Traceback ---", file=sys.stderr)
        sys.exit(1) # Exit with an error code


# --- Standard Python Entry Point ---
if __name__ == "__main__":
    """
    This block executes only when the script is run directly
    (e.g., `python main.py` or `python -m fundamental_analyzer_pro.main`).
    """
    start_application()