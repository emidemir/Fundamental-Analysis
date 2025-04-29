# tests/test_cli.py

import unittest
from unittest.mock import patch, MagicMock, call
import io # To capture stdout
import sys

# Important: Adjust the import path based on your project structure and how you run tests
# This assumes 'tests' is outside 'fundamental_analyzer_pro' and you run tests from the project root
# Or that your test runner handles paths correctly.
try:
    from fundamental_analyzer_pro.interfaces import cli
    from fundamental_analyzer_pro.services.analysis_service import AnalysisService # Need to mock this class
    # We also mock the utility functions if the CLI calls them directly
    # from fundamental_analyzer_pro.utils import export_utils, plotting_utils
except ImportError:
    # If the above fails, you might need to adjust sys.path in your test setup
    # or configure your test runner (like pytest with __init__.py files or conftest.py)
     print("Error: Could not import modules for testing. Adjust paths if necessary.", file=sys.stderr)
     # Example path adjustment (use if needed):
     # import os
     # project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
     # sys.path.insert(0, project_root)
     # from fundamental_analyzer_pro.interfaces import cli
     # from fundamental_analyzer_pro.services.analysis_service import AnalysisService
     sys.exit(1) # Stop tests if imports fail


class TestCLI(unittest.TestCase):

    # Patch 'input' from builtins, the AnalysisService, and potentially utils
    # Patch the service CLASS so the constructor returns our mock instance
    @patch('builtins.input')
    @patch('fundamental_analyzer_pro.interfaces.cli.AnalysisService') # Patch where it's used
    @patch('sys.stdout', new_callable=io.StringIO) # Capture print output
    def test_quit_command(self, mock_stdout, mock_AnalysisService, mock_input):
        """ Test that entering 'quit' exits the loop immediately. """
        mock_input.side_effect = ['quit'] # Simulate user typing 'quit'
        mock_analyzer_instance = MagicMock()
        mock_AnalysisService.return_value = mock_analyzer_instance # Constructor returns our mock

        cli.run_cli()

        # Verify input was called once
        mock_input.assert_called_once_with("Enter the stock ticker symbol (e.g., AAPL, MSFT) or 'quit' to exit: ")
        # Verify the analyzer methods were NOT called
        mock_analyzer_instance.analyze_stock.assert_not_called()
        # Check output for welcome and goodbye messages
        output = mock_stdout.getvalue()
        self.assertIn("Simple Stock Fundamental Analysis Tool", output)
        self.assertIn("Exiting Fundamental Analysis Tool", output)

    @patch('builtins.input')
    @patch('fundamental_analyzer_pro.interfaces.cli.AnalysisService')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_empty_ticker_input(self, mock_stdout, mock_AnalysisService, mock_input):
        """ Test that empty input prompts again without analysis. """
        mock_input.side_effect = ['', 'quit'] # Empty input, then quit
        mock_analyzer_instance = MagicMock()
        mock_AnalysisService.return_value = mock_analyzer_instance

        cli.run_cli()

        # Verify input was called twice
        self.assertEqual(mock_input.call_count, 2)
        # Verify analysis was not attempted
        mock_analyzer_instance.analyze_stock.assert_not_called()
        # Check that the error message for empty ticker was printed
        self.assertIn("Ticker symbol cannot be empty.", mock_stdout.getvalue())

    @patch('builtins.input')
    @patch('fundamental_analyzer_pro.interfaces.cli.AnalysisService')
    # Assuming AnalysisService calls utils internally now:
    # @patch('fundamental_analyzer_pro.utils.plotting_utils.display_plots') # If CLI called it
    # @patch('fundamental_analyzer_pro.utils.export_utils.export_dict_to_excel') # If CLI called it
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_successful_analysis_no_plot_no_export(self, mock_stdout, mock_AnalysisService, mock_input):
        """ Test a successful analysis run without plotting or exporting. """
        ticker = 'AAPL'
        summary_output = f"Analysis Summary for {ticker}"
        mock_input.side_effect = [
            ticker, # Enter ticker
            'n',    # Don't show plots
            'n',    # Don't export
            'quit'  # Exit loop
        ]
        # Configure the mock AnalysisService instance
        mock_analyzer_instance = MagicMock(spec=AnalysisService) # Use spec for better mocking
        mock_analyzer_instance.analyze_stock.return_value = True # Simulate success
        mock_analyzer_instance.get_summary_string.return_value = summary_output
        mock_AnalysisService.return_value = mock_analyzer_instance # Constructor returns this mock

        cli.run_cli()

        # Verify interactions
        mock_analyzer_instance.analyze_stock.assert_called_once_with(ticker)
        mock_analyzer_instance.get_summary_string.assert_called_once()
        mock_analyzer_instance.generate_and_display_plots.assert_not_called() # Should not be called
        mock_analyzer_instance.export_analysis.assert_not_called()         # Should not be called

        # Verify prompts were made
        self.assertIn("Do you want to see historical trend plots? (y/n):", mock_input.call_args_list[1][0][0])
        self.assertIn("Do you want to export the results to Excel? (y/n):", mock_input.call_args_list[2][0][0])

        # Verify summary output
        self.assertIn(summary_output, mock_stdout.getvalue())

    @patch('builtins.input')
    @patch('fundamental_analyzer_pro.interfaces.cli.AnalysisService')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_successful_analysis_with_plot_and_export(self, mock_stdout, mock_AnalysisService, mock_input):
        """ Test successful analysis with plotting and exporting (default filename). """
        ticker = 'MSFT'
        summary_output = f"Analysis Summary for {ticker}"
        default_filename = f"{ticker}_fundamental_analysis.xlsx"
        mock_input.side_effect = [
            ticker, # Enter ticker
            'y',    # Show plots
            'y',    # Export
            '',     # Use default filename
            'quit'  # Exit loop
        ]
        mock_analyzer_instance = MagicMock(spec=AnalysisService)
        mock_analyzer_instance.analyze_stock.return_value = True
        mock_analyzer_instance.get_summary_string.return_value = summary_output
        mock_AnalysisService.return_value = mock_analyzer_instance

        cli.run_cli()

        # Verify interactions
        mock_analyzer_instance.analyze_stock.assert_called_once_with(ticker)
        mock_analyzer_instance.get_summary_string.assert_called_once()
        mock_analyzer_instance.generate_and_display_plots.assert_called_once() # Check plot call
        mock_analyzer_instance.export_analysis.assert_called_once_with(default_filename) # Check export call

        # Verify prompts
        self.assertIn("Do you want to see historical trend plots? (y/n):", mock_input.call_args_list[1][0][0])
        self.assertIn("Do you want to export the results to Excel? (y/n):", mock_input.call_args_list[2][0][0])
        self.assertIn(f"Enter filename for export (default: {default_filename}):", mock_input.call_args_list[3][0][0])

        # Verify output messages
        output = mock_stdout.getvalue()
        self.assertIn(summary_output, output)
        self.assertIn("Generating and displaying plots...", output)
        self.assertIn(f"Exporting data to {default_filename}...", output)
        # Assuming the service prints success on export, otherwise mock and check call
        # self.assertIn(f"Data successfully exported to {default_filename}", output) # This depends on where the message is printed

    @patch('builtins.input')
    @patch('fundamental_analyzer_pro.interfaces.cli.AnalysisService')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_analysis_failure(self, mock_stdout, mock_AnalysisService, mock_input):
        """ Test the CLI behavior when analysis service fails. """
        ticker = 'BADTICKER'
        mock_input.side_effect = [ticker, 'quit']
        mock_analyzer_instance = MagicMock(spec=AnalysisService)
        # Simulate analysis failure
        mock_analyzer_instance.analyze_stock.return_value = False
        # OR simulate an exception: mock_analyzer_instance.analyze_stock.side_effect = Exception("API Error")
        mock_AnalysisService.return_value = mock_analyzer_instance

        cli.run_cli()

        mock_analyzer_instance.analyze_stock.assert_called_once_with(ticker)
        # Ensure subsequent steps were not taken
        mock_analyzer_instance.get_summary_string.assert_not_called()
        mock_analyzer_instance.generate_and_display_plots.assert_not_called()
        mock_analyzer_instance.export_analysis.assert_not_called()
        # Check for failure message
        self.assertIn(f"Analysis failed for {ticker}", mock_stdout.getvalue())

    @patch('builtins.input')
    @patch('fundamental_analyzer_pro.interfaces.cli.AnalysisService')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_unexpected_exception_handling(self, mock_stdout, mock_AnalysisService, mock_input):
        """ Test that an unexpected exception during analysis is caught. """
        ticker = 'CRASHER'
        error_message = "Something broke unexpectedly!"
        mock_input.side_effect = [ticker, 'quit']
        mock_analyzer_instance = MagicMock(spec=AnalysisService)
        # Simulate an unexpected exception during analysis
        mock_analyzer_instance.analyze_stock.side_effect = RuntimeError(error_message)
        mock_AnalysisService.return_value = mock_analyzer_instance

        cli.run_cli()

        mock_analyzer_instance.analyze_stock.assert_called_once_with(ticker)
        # Check that the generic error message is printed
        output = mock_stdout.getvalue()
        self.assertIn("An unexpected error occurred:", output)
        self.assertIn(f"Error Type: RuntimeError", output) # Check type reported
        self.assertIn(f"Error Details: {error_message}", output) # Check details reported

# Allow running tests directly
if __name__ == '__main__':
    unittest.main()