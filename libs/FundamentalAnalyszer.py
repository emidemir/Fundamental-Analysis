class FundamentalAnalyzer:
    """Perform fundamental analysis for a given stock symbol using Yahoo Finance data."""
    def __init__(self, symbol: str, years: int):
        """
        Initialize the analyzer with a stock symbol and number of years for analysis.

        :param symbol: Stock ticker symbol (e.g., 'AAPL').
        :param years: Number of years of historical data to analyze.
        """
        self.symbol = symbol.upper().strip()
        self.years = years
        self.ticker = None
        # Data holders
        self.info = None
        self.financials = None         # Income statement (annual)
        self.balance_sheet = None      # Balance sheet (annual)
        self.cash_flow = None          # Cash flow statement (annual)
        # Results
        self.metrics = {}             # Dict to store calculated metrics
        self.revenue_history = {}     # Dict of {year: revenue} for trend
        self.net_income_history = {}  # Dict of {year: net income} for trend

    def fetch_data(self) -> bool:
        """
        Fetch financial data for the stock symbol using yfinance.
        Returns True if data fetched successfully, False otherwise.
        """
        try:
            self.ticker = yf.Ticker(self.symbol)
            # Fetch company info and financial statements
            self.info = self.ticker.info
            self.financials = self.ticker.financials
            self.balance_sheet = self.ticker.balance_sheet
            self.cash_flow = self.ticker.cashflow
        except Exception as e:
            print(f"Error fetching data for '{self.symbol}': {e}")
            return False

        # Ensure that we have some financial data
        if self.financials is None or self.financials.empty:
            print(f"No financial data available for symbol '{self.symbol}'.")
            return False
        return True

    def compute_metrics(self):
        """
        Compute key financial metrics based on fetched data.
        Stores results in the `metrics` dictionary and populates trend data.
        """
        # Determine how many years of data are available and adjust if needed
        num_years_available = self.financials.shape[1]  # number of columns (years) in financials
        years_to_use = min(self.years, num_years_available)
        if years_to_use < self.years:
            # Adjust if requested range exceeds available history
            print(f"Only {years_to_use} year(s) of data available for {self.symbol}.")
        # Slice the financial data to the requested number of years
        financials_slice = self.financials.iloc[:, :years_to_use]
        balance_sheet_slice = self.balance_sheet.iloc[:, :years_to_use] if self.balance_sheet is not None else None
        cash_flow_slice = self.cash_flow.iloc[:, :years_to_use] if self.cash_flow is not None else None

        # Helper to get a row from a DataFrame slice safely
        def get_series(dataframe, row_name):
            if dataframe is not None and not dataframe.empty and row_name in dataframe.index:
                return dataframe.loc[row_name]
            return None

        # Retrieve necessary financial figures (as pandas Series over years)
        net_income_series = get_series(financials_slice, 'Net Income') or get_series(financials_slice, 'Net Income Common Stockholders')
        revenue_series = get_series(financials_slice, 'Total Revenue') or get_series(financials_slice, 'Revenue')
        op_income_series = get_series(financials_slice, 'Operating Income') or get_series(financials_slice, 'Operating Income or Loss')
        total_equity_series = get_series(balance_sheet_slice, 'Total Stockholder Equity') or get_series(balance_sheet_slice, 'Total Equity')
        total_assets_series = get_series(balance_sheet_slice, 'Total Assets')
        total_liab_series = get_series(balance_sheet_slice, 'Total Liab')
        curr_assets_series = get_series(balance_sheet_slice, 'Total Current Assets')
        curr_liab_series = get_series(balance_sheet_slice, 'Total Current Liabilities')
        long_debt_series = get_series(balance_sheet_slice, 'Long Term Debt')
        short_debt_series = get_series(balance_sheet_slice, 'Short Long Term Debt') or get_series(balance_sheet_slice, 'Short Term Debt')
        cfo_series = get_series(cash_flow_slice, 'Total Cash From Operating Activities') or get_series(cash_flow_slice, 'Operating Cash Flow')
        capex_series = get_series(cash_flow_slice, 'Capital Expenditures')

        # Compute Free Cash Flow series: operating cash flow + capital expenditures (capex is usually negative)
        fcf_series = None
        if cfo_series is not None and capex_series is not None:
            fcf_series = cfo_series + capex_series

        # Convert series indices to ascending chronological order for trend analysis
        # (Original DataFrame columns are typically in descending order, latest year first)
        if revenue_series is not None:
            revenue_series = revenue_series.sort_index(axis=0)
        if net_income_series is not None:
            net_income_series = net_income_series.sort_index(axis=0)
        if op_income_series is not None:
            op_income_series = op_income_series.sort_index(axis=0)
        if fcf_series is not None:
            fcf_series = fcf_series.sort_index(axis=0)
        if total_equity_series is not None:
            total_equity_series = total_equity_series.sort_index(axis=0)
        if total_assets_series is not None:
            total_assets_series = total_assets_series.sort_index(axis=0)
        if total_liab_series is not None:
            total_liab_series = total_liab_series.sort_index(axis=0)
        if curr_assets_series is not None:
            curr_assets_series = curr_assets_series.sort_index(axis=0)
        if curr_liab_series is not None:
            curr_liab_series = curr_liab_series.sort_index(axis=0)
        if long_debt_series is not None:
            long_debt_series = long_debt_series.sort_index(axis=0)
        if short_debt_series is not None:
            short_debt_series = short_debt_series.sort_index(axis=0)

        # Identify the latest year (last element in each series after sorting ascending)
        # These will be used for calculating current metrics
        latest_net_income = net_income_series.iloc[-1] if net_income_series is not None else None
        latest_revenue = revenue_series.iloc[-1] if revenue_series is not None else None
        latest_op_income = op_income_series.iloc[-1] if op_income_series is not None else None
        latest_equity = total_equity_series.iloc[-1] if total_equity_series is not None else None
        latest_assets = total_assets_series.iloc[-1] if total_assets_series is not None else None
        latest_liab = total_liab_series.iloc[-1] if total_liab_series is not None else None
        latest_curr_assets = curr_assets_series.iloc[-1] if curr_assets_series is not None else None
        latest_curr_liab = curr_liab_series.iloc[-1] if curr_liab_series is not None else None
        latest_fcf = fcf_series.iloc[-1] if fcf_series is not None else None

        # Retrieve price and share data from info for market-based ratios
        current_price = None
        if self.info:
            current_price = self.info.get('currentPrice') or self.info.get('regularMarketPrice')
        shares_outstanding = self.info.get('sharesOutstanding') if self.info else None
        market_cap = self.info.get('marketCap') if self.info else None
        if market_cap is None and current_price and shares_outstanding:
            market_cap = current_price * shares_outstanding

        # Calculate metrics:
        # P/E Ratio = Price / EPS
        pe_ratio = None
        trailing_eps = self.info.get('trailingEps') if self.info else None
        if self.info:
            pe_ratio = self.info.get('trailingPE')
        if pe_ratio is None and current_price and trailing_eps is not None:
            # Avoid division by zero
            pe_ratio = current_price / trailing_eps if trailing_eps != 0 else None

        # EPS (Earnings per Share) – use trailing EPS if available, else derive from net income and shares
        eps = trailing_eps
        if eps is None and latest_net_income is not None and shares_outstanding:
            eps = latest_net_income / shares_outstanding

        # ROE = (Net Income / Shareholders' Equity) * 100%
        roe = None
        if latest_net_income is not None and latest_equity is not None and latest_equity != 0:
            roe = (latest_net_income / latest_equity) * 100

        # ROA = (Net Income / Total Assets) * 100%
        roa = None
        if latest_net_income is not None and latest_assets is not None and latest_assets != 0:
            roa = (latest_net_income / latest_assets) * 100

        # Debt/Equity = Total Debt or Liabilities / Equity
        de_ratio = None
        if latest_equity is not None and latest_equity != 0:
            if latest_liab is not None:
                de_ratio = latest_liab / latest_equity
            else:
                # If total liabilities not available, try using total debt (sum of long + short term debt)
                total_debt = None
                if long_debt_series is not None or short_debt_series is not None:
                    long_debt = long_debt_series.iloc[-1] if long_debt_series is not None else 0
                    short_debt = short_debt_series.iloc[-1] if short_debt_series is not None else 0
                    total_debt = (long_debt or 0) + (short_debt or 0)
                if total_debt is None and self.info:
                    total_debt = self.info.get('totalDebt')
                if total_debt is not None:
                    de_ratio = total_debt / latest_equity

        # Current Ratio = Total Current Assets / Total Current Liabilities
        current_ratio = None
        if latest_curr_assets is not None and latest_curr_liab is not None and latest_curr_liab != 0:
            current_ratio = latest_curr_assets / latest_curr_liab

        # Free Cash Flow (use latest year FCF if available, else try trailing from info)
        free_cash_flow = latest_fcf
        if free_cash_flow is None and self.info:
            free_cash_flow = self.info.get('freeCashflow')

        # Revenue Growth (year-over-year % change for latest year)
        revenue_growth = None
        if revenue_series is not None and revenue_series.size > 1:
            prev_revenue = revenue_series.iloc[-2]  # second to last (previous year)
            if prev_revenue is not None and prev_revenue != 0 and latest_revenue is not None:
                revenue_growth = ((latest_revenue - prev_revenue) / abs(prev_revenue)) * 100

        # Net Income Growth (year-over-year % change for latest year)
        net_income_growth = None
        if net_income_series is not None and net_income_series.size > 1:
            prev_net = net_income_series.iloc[-2]
            if prev_net is not None and prev_net != 0 and latest_net_income is not None:
                net_income_growth = ((latest_net_income - prev_net) / abs(prev_net)) * 100

        # Operating Margin = (Operating Income / Revenue) * 100%
        operating_margin = None
        if latest_op_income is not None and latest_revenue is not None and latest_revenue != 0:
            operating_margin = (latest_op_income / latest_revenue) * 100

        # Dividend Yield = (Annual Dividend per share / Price) * 100%
        dividend_yield = None
        if self.info:
            # yfinance provides dividend yield in decimal form if available
            if self.info.get('dividendYield') is not None:
                dividend_yield = self.info['dividendYield'] * 100
            elif self.info.get('trailingAnnualDividendYield') is not None:
                dividend_yield = self.info['trailingAnnualDividendYield'] * 100

        # Price-to-Book (P/B) = Price / (Equity per Share)
        pb_ratio = None
        if current_price and latest_equity is not None and shares_outstanding:
            book_value_per_share = latest_equity / shares_outstanding if shares_outstanding != 0 else None
            if book_value_per_share and book_value_per_share != 0:
                pb_ratio = current_price / book_value_per_share

        # Price-to-Sales (P/S) = Market Cap / Revenue
        ps_ratio = None
        if market_cap and latest_revenue and latest_revenue != 0:
            ps_ratio = market_cap / latest_revenue

        # Store metrics in dictionary
        self.metrics = {
            "P/E Ratio": pe_ratio,
            "EPS (TTM)": eps,
            "ROE (%)": roe,
            "ROA (%)": roa,
            "Debt/Equity": de_ratio,
            "Current Ratio": current_ratio,
            "Free Cash Flow": free_cash_flow,
            "Revenue Growth (%)": revenue_growth,
            "Net Income Growth (%)": net_income_growth,
            "Operating Margin (%)": operating_margin,
            "Dividend Yield (%)": dividend_yield,
            "P/B Ratio": pb_ratio,
            "P/S Ratio": ps_ratio
        }

        # Prepare trend data for output and visualization (store values per year)
        if revenue_series is not None:
            for date, value in revenue_series.iteritems():
                year_str = str(date)[:4]
                self.revenue_history[year_str] = value
        if net_income_series is not None:
            for date, value in net_income_series.iteritems():
                year_str = str(date)[:4]
                self.net_income_history[year_str] = value

        # *** Additional metrics can be added here in the future if needed ***

    def print_report(self):
        """Print the calculated metrics and trends to the console in a readable format."""
        years_used = min(self.years, self.financials.shape[1] if self.financials is not None else 0)
        print(f"\nFundamental Analysis for {self.symbol} (last {years_used} year(s))")
        print("=" * 50)
        # Print key metrics
        for metric, value in self.metrics.items():
            if metric.endswith("(%)"):
                # Format percentages
                if value is None:
                    print(f"{metric}: N/A")
                else:
                    print(f"{metric}: {value:.1f}%")
            elif metric in {"P/E Ratio", "Current Ratio", "Debt/Equity", "P/B Ratio", "P/S Ratio"}:
                # Format ratio values
                if value is None:
                    print(f"{metric}: N/A")
                else:
                    print(f"{metric}: {value:.2f}")
            elif metric == "EPS (TTM)":
                # Format EPS
                if value is None:
                    print(f"{metric}: N/A")
                else:
                    print(f"{metric}: {value:.2f}")
            elif metric == "Free Cash Flow":
                # Format large numbers for FCF
                if value is None:
                    print(f"{metric}: N/A")
                else:
                    print(f"{metric}: {self._format_number(value)}")
            else:
                # Default formatting for any other metrics
                print(f"{metric}: {value if value is not None else 'N/A'}")

        # Print revenue and net income trends by year
        if self.revenue_history or self.net_income_history:
            print("\nYearly Revenue and Net Income:")
            for year in sorted(set(list(self.revenue_history.keys()) + list(self.net_income_history.keys()))):
                rev = self.revenue_history.get(year)
                ni = self.net_income_history.get(year)
                rev_str = self._format_number(rev) if rev is not None else "N/A"
                ni_str = self._format_number(ni) if ni is not None else "N/A"
                print(f"{year}: Revenue = {rev_str}, Net Income = {ni_str}")
        print("=" * 50)

    def _format_number(self, value) -> str:
        """
        Format large numeric values with appropriate suffix (K, M, B, T).
        e.g., 1500000 -> '1.50M'
        """
        if value is None:
            return "N/A"
        try:
            value = float(value)
        except Exception:
            return str(value)
        sign = "-" if value < 0 else ""
        value = abs(value)
        if value >= 1e12:
            return f"{sign}{value/1e12:.2f}T"
        elif value >= 1e9:
            return f"{sign}{value/1e9:.2f}B"
        elif value >= 1e6:
            return f"{sign}{value/1e6:.2f}M"
        elif value >= 1e3:
            return f"{sign}{value/1e3:.2f}K"
        else:
            return f"{sign}{value:.2f}"
