# fundamental_analyzer_pro/utils/plotting_utils.py

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd
import numpy as np
from typing import Optional, Union, List
from datetime import datetime

# Apply a style globally for consistency
try:
    plt.style.use('seaborn-v0_8-darkgrid')
except OSError:
    # Fallback if seaborn styles aren't available
    plt.style.use('ggplot')
    print("Warning: 'seaborn-v0_8-darkgrid' style not found. Using 'ggplot'.")


def plot_metric_trend(data: pd.Series,
                      metric_name: str,
                      title: Optional[str] = None,
                      ylabel: Optional[str] = None,
                      kind: str = 'line'):
    """
    Generates a plot for a single metric's trend over time.

    Args:
        data (pd.Series): Data with index as time/period (e.g., years, datetime)
                          and values as the metric.
        metric_name (str): Name of the metric being plotted (used for default title/label).
        title (str, optional): Custom plot title. Defaults to f"{metric_name} Trend".
        ylabel (str, optional): Custom Y-axis label. Defaults to metric_name.
        kind (str): Type of plot ('line' or 'bar'). Defaults to 'line'.

    Returns:
        Optional[matplotlib.axes.Axes]: The Axes object of the generated plot, or None if plotting failed.
    """
    print(f"[{datetime.now()}] Generating plot for: {metric_name}")

    # --- Input Validation ---
    if data is None or not isinstance(data, pd.Series):
        print(f"  - Skipping plot for {metric_name}: Input data is not a valid pandas Series.")
        return None
    if data.empty:
        print(f"  - Skipping plot for {metric_name}: Input Series is empty.")
        return None

    # --- Data Preparation ---
    # Drop NaN values for plotting, as they create gaps or errors depending on plot type
    plot_data = data.dropna()
    if plot_data.empty:
        print(f"  - Skipping plot for {metric_name}: No valid data points after dropping NaNs.")
        return None

    # Determine index type for appropriate x-axis handling
    if isinstance(plot_data.index, pd.DatetimeIndex):
        # Use year for datetime index, ensure unique years if needed
        plot_index = plot_data.index.year
        xlabel = "Year"
        # If multiple data points per year exist after dropna, consider aggregation or different plotting approach
        # For simplicity here, assume index is reasonably unique per year or represents annual data
        if plot_index.duplicated().any():
             print(f"  - Warning for {metric_name}: Duplicate years found in index after dropna. Plot might overlay points.")
             # Potentially aggregate here if needed: plot_data = plot_data.groupby(plot_index).mean() # Example: mean
             # plot_index = plot_data.index # Update index after aggregation
    elif pd.api.types.is_numeric_dtype(plot_data.index):
        # Assume numeric index represents years or periods
        plot_index = plot_data.index
        xlabel = "Year / Period"
    else:
        # Use string representation for other index types
        plot_index = plot_data.index.astype(str)
        xlabel = "Period"

    # --- Plotting ---
    try:
        fig, ax = plt.subplots(figsize=(10, 5))

        if kind.lower() == 'line':
            ax.plot(plot_index, plot_data.values, marker='o', linestyle='-')
        elif kind.lower() == 'bar':
            ax.bar(plot_index, plot_data.values)
        else:
            print(f"  - Warning: Invalid plot kind '{kind}' for {metric_name}. Defaulting to 'line'.")
            ax.plot(plot_index, plot_data.values, marker='o', linestyle='-')

        # --- Formatting ---
        plot_title = title if title else f"{metric_name} Trend"
        plot_ylabel = ylabel if ylabel else metric_name
        ax.set_title(plot_title, fontsize=14, fontweight='bold')
        ax.set_xlabel(xlabel, fontsize=12)
        ax.set_ylabel(plot_ylabel, fontsize=12)

        # Format y-axis (e.g., percentages, currency)
        if '%' in plot_ylabel or any(s in metric_name.lower() for s in ['margin', 'roe', 'roa', 'rate', 'yield']):
            ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1.0))
        elif any(s in metric_name.lower() for s in ['revenue', 'income', 'profit', 'assets', 'equity', 'debt', 'flow', 'value', 'cap']):
            # Basic large number formatting (e.g., Billions)
            formatter = mticker.FuncFormatter(lambda x, p: format_large_number(x))
            ax.yaxis.set_major_formatter(formatter)


        # Set x-axis ticks explicitly if using numeric years to ensure all are shown
        # Check length > 1 to avoid issues with single data point plots
        if pd.api.types.is_numeric_dtype(plot_index) and len(plot_index) > 1:
            # Ensure ticks match the actual index values
            ax.set_xticks(plot_index.unique())
            ax.set_xticklabels(plot_index.unique()) # Use unique values for labels

        # Rotate x-axis labels if they are long or numerous
        plt.xticks(rotation=45, ha='right') # ha='right' aligns labels better after rotation

        ax.grid(True, which='major', linestyle='--', linewidth='0.5', color='grey')
        plt.tight_layout() # Adjust layout to prevent labels overlapping

        print(f"  - Successfully generated plot for {metric_name}")
        return ax # Return the Axes object

    except Exception as e:
        print(f"  - ERROR generating plot for {metric_name}: {e}")
        # Ensure the potentially created figure is closed if an error occurs mid-plot
        if 'fig' in locals():
             plt.close(fig)
        return None


def display_plots():
    """ Shows all generated matplotlib plots that haven't been shown yet. """
    if plt.get_fignums(): # Check if there are any figures to show
        print(f"[{datetime.now()}] Displaying generated plots...")
        try:
            plt.show()
            print(f"[{datetime.now()}] Plot windows closed by user.")
        except Exception as e:
            print(f"Error during plt.show(): {e}")
    else:
        print("No plots generated to display.")


def close_plots():
     """ Closes all open matplotlib figures. """
     open_figs = plt.get_fignums()
     if open_figs:
         print(f"[{datetime.now()}] Closing {len(open_figs)} plot window(s)...")
         plt.close('all')
     # else:
     #     print("No plot windows were open to close.")

def format_large_number(num: float, pos=None) -> str:
    """
    Formats a large number into a human-readable string (e.g., 1.2B, 500M, 10K).
    Helper function for matplotlib axis formatting.

    Args:
        num (float): The number to format.
        pos: Position (required by FuncFormatter, often unused).

    Returns:
        str: The formatted string representation.
    """
    if pd.isna(num):
        return 'N/A'
    if abs(num) >= 1e12:
        return f'{num / 1e12:.1f}T' # Trillions
    elif abs(num) >= 1e9:
        return f'{num / 1e9:.1f}B' # Billions
    elif abs(num) >= 1e6:
        return f'{num / 1e6:.1f}M' # Millions
    elif abs(num) >= 1e3:
        return f'{num / 1e3:.1f}K' # Thousands
    else:
        # Show smaller numbers with potentially 1 decimal place if not integer
        return f'{num:.1f}' if num != int(num) else f'{int(num)}'


# Example Usage (for testing the module directly)
if __name__ == "__main__":
    print("--- Testing plotting_utils ---")

    # Sample Data
    years = pd.to_datetime(['2020-12-31', '2021-12-31', '2022-12-31', '2023-12-31'])
    numeric_years = [2020, 2021, 2022, 2023]

    roe_data = pd.Series([0.15, 0.18, np.nan, 0.20], index=years, name="ROE")
    revenue_data = pd.Series([100e9, 120e9, 115e9, 140e9], index=numeric_years, name="Revenue")
    margin_data = pd.Series([0.25, 0.26, 0.24, 0.27], index=numeric_years, name="Gross Margin %")
    debt_data = pd.Series([50e9, 55e9, 52e9, 60e9], index=numeric_years, name="Total Debt")
    empty_data = pd.Series(dtype=float)
    nan_data = pd.Series([np.nan, np.nan], index=[2022, 2023])

    # Generate plots (they won't display until display_plots() is called)
    print("\nGenerating test plots:")
    plot_metric_trend(roe_data, "Return on Equity", kind='line')
    plot_metric_trend(revenue_data, "Total Revenue", kind='bar')
    plot_metric_trend(margin_data, "Gross Margin %", kind='line') # Test percentage formatting
    plot_metric_trend(debt_data, "Total Debt", kind='line') # Test large number formatting
    plot_metric_trend(empty_data, "Empty Data Series") # Test empty data handling
    plot_metric_trend(nan_data, "All NaN Data Series") # Test all NaN handling

    # Display all generated plots
    display_plots()

    # Test closing plots (useful in interactive sessions or loops)
    # close_plots()
    # print("\nPlots closed (if any were open).")