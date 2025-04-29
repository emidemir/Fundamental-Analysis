class FundamentalVisualizer:
    """Visualize key financial trends (e.g., revenue and net income) using matplotlib."""
    def __init__(self, analyzer: FundamentalAnalyzer):
        """
        Initialize the visualizer with a FundamentalAnalyzer instance.
        
        :param analyzer: An instance of FundamentalAnalyzer with computed data.
        """
        self.analyzer = analyzer

    def plot_revenue_trend(self):
        """Plot the revenue trend over the years."""
        if not self.analyzer.revenue_history:
            print("No revenue data available to plot.")
            return
        years = sorted(int(y) for y in self.analyzer.revenue_history.keys())
        values = [self.analyzer.revenue_history[str(year)] for year in years]
        plt.figure(figsize=(8, 5))
        plt.plot(years, values, marker='o', label='Revenue')
        plt.title(f"{self.analyzer.symbol} Revenue Trend")
        plt.xlabel("Year")
        plt.ylabel("Revenue")
        plt.xticks(years)  # show all years on x-axis
        plt.legend()
        plt.tight_layout()
        plt.show()

    def plot_net_income_trend(self):
        """Plot the net income trend over the years."""
        if not self.analyzer.net_income_history:
            print("No net income data available to plot.")
            return
        years = sorted(int(y) for y in self.analyzer.net_income_history.keys())
        values = [self.analyzer.net_income_history[str(year)] for year in years]
        plt.figure(figsize=(8, 5))
        plt.plot(years, values, marker='o', color='orange', label='Net Income')
        plt.title(f"{self.analyzer.symbol} Net Income Trend")
        plt.xlabel("Year")
        plt.ylabel("Net Income")
        plt.xticks(years)
        plt.legend()
        plt.tight_layout()
        plt.show()
