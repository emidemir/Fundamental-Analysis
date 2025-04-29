# fundamental_analyzer/visualizer.py

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

plt.style.use('seaborn-v0_8-darkgrid') # Use a pleasant style

def plot_metric_trend(data, metric_name, title=None, ylabel=None, kind='line'):
    """
    Plots a single metric over time.

    Args:
        data (pd.Series): Data with index as time/period and values as the metric.
        metric_name (str): Name of the metric being plotted.
        title (str, optional): Plot title. Defaults to metric_name Trend.
        ylabel (str, optional): Y-axis label. Defaults to metric_name.
        kind (str): 'line' or 'bar'.
    """
    if data is None or data.empty or data.isnull().all():
        print(f"Skipping plot for {metric_name}: No data available.")
        return

    fig, ax = plt.subplots(figsize=(10, 5))

    # Data index is likely datetime, format for display
    try:
        # Convert index to Year if it's datetime-like
        if isinstance(data.index, pd.DatetimeIndex):
            plot_index = data.index.year
        else:
             plot_index = data.index # Assume it's already suitable (e.g., year numbers)
        plot_data = data.dropna() # Drop NaNs before plotting
        plot_index = plot_index[plot_data.index.isin(plot_data.index)] # Align index after dropna
    except Exception as e:
        print(f"Warning: Could not process index for plotting {metric_name}: {e}")
        plot_index = range(len(data)) # Fallback index
        plot_data = data.dropna()

    if plot_data.empty:
        print(f"Skipping plot for {metric_name}: No valid data points after dropping NaNs.")
        plt.close(fig) # Close the empty figure
        return

    if kind == 'line':
        ax.plot(plot_index, plot_data.values, marker='o', linestyle='-')
    elif kind == 'bar':
        ax.bar(plot_index, plot_data.values)
    else:
        print(f"Warning: Invalid plot kind '{kind}'. Using 'line'.")
        ax.plot(plot_index, plot_data.values, marker='o', linestyle='-')

    ax.set_title(title if title else f"{metric_name} Trend")
    ax.set_xlabel("Year" if isinstance(plot_index, (pd.Int64Index, pd.RangeIndex, pd.Index)) and not isinstance(plot_index, pd.DatetimeIndex) else "Period")
    ax.set_ylabel(ylabel if ylabel else metric_name)
    ax.grid(True)

    # Format y-axis for percentages if applicable
    if any(s in metric_name.lower() for s in ['margin', 'roe', 'roa', 'rate']):
         from matplotlib.ticker import PercentFormatter
         ax.yaxis.set_major_formatter(PercentFormatter(1.0))

    # Set x-axis ticks explicitly if using numerical index representing years
    if len(plot_index) > 1 and isinstance(plot_index, (pd.Int64Index, pd.RangeIndex, pd.Index)) and not isinstance(plot_index, pd.DatetimeIndex):
        ax.set_xticks(plot_index)
        ax.set_xticklabels(plot_index) # Ensure labels match ticks

    plt.xticks(rotation=45)
    plt.tight_layout()
    # plt.show() # Don't show automatically, let the main script control this

def display_plots():
    """ Shows all generated matplotlib plots. """
    plt.show()

def close_plots():
     """ Closes all open matplotlib figures. """
     plt.close('all')


# Example Usage (for testing module directly)
if __name__ == '__main__':
    # Create some sample data (e.g., ROE over 4 years)
    years = [2020, 2021, 2022, 2023]
    roe_data = pd.Series([0.15, 0.18, 0.17, 0.20], index=years)
    revenue_data = pd.Series([100e9, 120e9, 115e9, 140e9], index=years)
    revenue_data_with_nan = pd.Series([100e9, 120e9, np.nan, 140e9], index=years)


    plot_metric_trend(roe_data, "Return on Equity (ROE)", kind='line')
    plot_metric_trend(revenue_data, "Total Revenue", ylabel="Revenue ($ Billions)", kind='bar')
    # Test NaN handling
    plot_metric_trend(revenue_data_with_nan, "Revenue with NaN", ylabel="Revenue ($ Billions)", kind='bar')
    # Test no data
    plot_metric_trend(pd.Series(dtype=float), "Empty Metric")


    display_plots() # Show the plots when running the module directly