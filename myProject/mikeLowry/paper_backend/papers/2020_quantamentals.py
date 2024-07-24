import pandas as pd
import numpy as np
import yfinance as yf
import backtrader as bt
import logging

# Setting up the logger
logging.basicConfig(level=logging.INFO)

def fetch_sp500_tickers():
    """Fetches the list of S&P 500 tickers from Wikipedia."""
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    data = pd.read_html(url)
    sp500_table = data[0]
    return sp500_table['Symbol'].tolist()

def fetch_data(tickers, start, end):
    """Fetches historical price data from Yahoo Finance for a list of tickers."""
    data = yf.download(tickers, start=start, end=end, group_by='ticker')
    print("Data structure:\n", data.head())  # Debug statement to check data structure
    return data

def fetch_fundamental_data(tickers, data):
    """Fetches fundamental data for a list of tickers."""
    fundamental_data = {}
    for ticker in tickers:
        ticker_data = yf.Ticker(ticker)
        print("Ticker data:\n", ticker_data)  # Debug statement to check ticker data structure
        
        # Fetching fundamental data
        try:
            fundamentals = ticker_data.financials.T
            balance_sheet = ticker_data.balance_sheet.T
            cashflow = ticker_data.cashflow.T
        except AttributeError:
            # Handle case where financials data is not available
            continue
        
        # Fetching market data
        try:
            market_data = ticker_data.history(period='1d', start='2003-09-30', end='2019-09-30')
        except Exception as e:
            logging.warning(f"Failed to fetch market data for {ticker}: {str(e)}")
            continue
        
        # Calculating EV and other metrics
        if not fundamentals.empty and not balance_sheet.empty and not cashflow.empty:
            ev = balance_sheet.get('Total Capitalization', np.nan) - balance_sheet.get('Cash And Cash Equivalents', np.nan)
            ebit_ev = fundamentals.get('EBIT', np.nan) / ev
            ptos = ticker_data.info.get('priceToSalesTrailing12Months', np.nan)
            
            # Handling cases where specific metrics might not be available
            roe = fundamentals.get('Net Income Common Stockholders', np.nan) / balance_sheet.get('Common Stock Equity', np.nan)
            roic = fundamentals.get('Operating Income', np.nan) / (balance_sheet.get('Common Stock Equity', np.nan) + balance_sheet.get('Total Debt', np.nan))
            gross_profitability = fundamentals.get('Gross Profit', np.nan) / balance_sheet.get('Total Assets', np.nan)
            
            fundamental_data[ticker] = {
                'EBIT': fundamentals.get('EBIT', np.nan),
                'EV': ev,
                'Price/Sales': ptos,
                'ROE': roe,
                'ROIC': roic,
                'Gross Profitability': gross_profitability
            }
        else:
            logging.warning(f"Missing fundamental data for {ticker}")
    
    return fundamental_data

def calculate_fundamental_factors(data, tickers, fundamental_data):
    """Calculates fundamental factors for a list of tickers."""
    data_fundamental = data.copy()
    for ticker in tickers:
        if ticker in fundamental_data:
            data_fundamental[f'EBIT/EV_{ticker}'] = fundamental_data[ticker]['EBIT'] / fundamental_data[ticker]['EV']
            data_fundamental[f'Price/Sales_{ticker}'] = fundamental_data[ticker]['Price/Sales']
            data_fundamental[f'ROE_{ticker}'] = fundamental_data[ticker]['ROE']
            data_fundamental[f'ROIC_{ticker}'] = fundamental_data[ticker]['ROIC']
            data_fundamental[f'Gross Profitability_{ticker}'] = fundamental_data[ticker]['Gross Profitability']
    return data_fundamental

def calculate_technical_factors(data, tickers):
    """Calculates technical factors for a list of tickers."""
    data_technical = pd.DataFrame(index=data.index)
    for ticker in tickers:
        if ticker in data:
            data_technical[f'Momentum_6m_{ticker}'] = data[ticker]['Adj Close'].pct_change(126)  # 6 months momentum
            data_technical[f'Momentum_12m_{ticker}'] = data[ticker]['Adj Close'].pct_change(252)  # 12 months momentum
            data_technical[f'Volatility_{ticker}'] = data[ticker]['Adj Close'].rolling(window=252).std()  # 1 year rolling volatility
            data_technical[f'SMA_{ticker}'] = data[ticker]['Adj Close'].rolling(window=200).mean()  # 200-day simple moving average
    return data_technical

class QuantamentalsStrategy(bt.Strategy):
    params = (('rebalance_period', 30),)

    def __init__(self):
        self.rebalance_counter = 0
        self.data_close = {ticker: self.datas[i].close for i, ticker in enumerate(self.datas)}
        
        # Adding SMA indicator for SPY
        self.spy_sma = bt.indicators.SimpleMovingAverage(self.datas[0].close, period=100)

        # Track portfolio value and cash
        self.portfolio_value = []
        self.cash = []

    def next(self):
        if self.rebalance_counter % self.params.rebalance_period == 0:
            self.rebalance_portfolio()
        self.rebalance_counter += 1
        
        # Append portfolio value and cash to the lists
        self.portfolio_value.append(self.broker.getvalue())
        self.cash.append(self.broker.getcash())

    def rebalance_portfolio(self):
        scores = {}
        for data in self.datas:
            ticker = data._name
            if f'EBIT/EV_{ticker}' in self.data_close and f'ROIC_{ticker}' in self.data_close and f'Volatility_{ticker}' in self.data_close:
                ebit_ev = self.data_close[f'EBIT/EV_{ticker}'][0]
                roic = self.data_close[f'ROIC_{ticker}'][0]
                vol = self.data_close[f'Volatility_{ticker}'][0]

                if pd.notna(ebit_ev) and pd.notna(roic) and pd.notna(vol):
                    scores[ticker] = {
                        'Quality': roic,
                        'Value': ebit_ev,
                        'Volatility': vol
                    }

        # Ranking stocks based on Quality, Value, and Volatility
        quality_rank = {ticker: rank for rank, ticker in enumerate(sorted(scores, key=lambda x: scores[x]['Quality'], reverse=True), 1)}
        value_rank = {ticker: rank for rank, ticker in enumerate(sorted(scores, key=lambda x: scores[x]['Value'], reverse=True), 1)}
        volatility_rank = {ticker: rank for rank, ticker in enumerate(sorted(scores, key=lambda x: scores[x]['Volatility']), 1)}

        # Combining ranks to get a composite score
        combined_rank = {ticker: quality_rank[ticker] + value_rank[ticker] + volatility_rank[ticker] for ticker in scores}

        # Selecting top decile stocks
        top_decile_stocks = sorted(combined_rank, key=combined_rank.get)[:50]

        # Filtering top momentum stocks from the top decile stocks
        momentum_scores = {ticker: self.data_close[f'Momentum_6m_{ticker}'][0] for ticker in top_decile_stocks if pd.notna(self.data_close[f'Momentum_6m_{ticker}'][0])}
        top_momentum_stocks = sorted(momentum_scores, key=momentum_scores.get, reverse=True)[:20]

        # SPY (or similar market index) price and moving average
        spy_data = self.datas[0]
        spy_sma = self.spy_sma[0]
        spy_price = spy_data.close[0]

        # Rebalancing the portfolio based on the conditions
        for data in self.datas:
            ticker = data._name
            if spy_price > spy_sma and ticker in top_momentum_stocks:
                self.order_target_percent(data, target=1.0 / len(top_momentum_stocks))
            else:
                self.order_target_percent(data, target=0)

    def log_performance(self):
        print(f"Final Portfolio Value: {self.broker.getvalue()}")
        print(f"Final Cash Value: {self.broker.getcash()}")
        print(f"Total Returns: {self.broker.getvalue() / 1000000 - 1:.2%}")
        print("Trades Executed:")
        for trade in self._trades:
            print(trade)

    def stop(self):
        # Print performance when the strategy ends
        self.log_performance()

def main():
    # Step 1: Fetch and Prepare Data
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    table = pd.read_html(url, header=0)[0]
    tickers = table['Symbol'].tolist()[40:50]

    print(tickers)
    start_date = '2003-01-01'
    end_date = '2019-09-30'

    data = fetch_data(tickers, start_date, end_date)
    logging.info("Data fetched successfully")

    # Step 2: Fetch Fundamental Data
    fundamental_data = fetch_fundamental_data(tickers, data)
    logging.info("Fundamental data fetched successfully")

    # Step 3: Calculate Fundamental and Technical Factors
    data_fundamental = calculate_fundamental_factors(data, tickers, fundamental_data)
    data_technical = calculate_technical_factors(data, tickers)

    # Step 4: Combine Data
    combined_data = pd.concat([data_fundamental, data_technical], axis=1)

    print("start backtest")
    # Step 5: Backtesting with Backtrader
    cerebro = bt.Cerebro()
    for ticker in tickers:
        if ticker in combined_data:
            ticker_data = combined_data[ticker].dropna()
            if not ticker_data.empty:
                data_feed = bt.feeds.PandasData(dataname=ticker_data[['Open', 'High', 'Low', 'Close', 'Volume']])
                data_feed._name = ticker
                cerebro.adddata(data_feed)

    cerebro.addstrategy(QuantamentalsStrategy)
    start_cash = 1000000
    cerebro.broker.set_cash(start_cash)
    strategies = cerebro.run()
    first_strategy = strategies[0]

    # Accessing the final portfolio value
    final_portfolio_value = cerebro.broker.getvalue()
    print(f'Final Portfolio Value: {final_portfolio_value}')


if __name__ == '__main__':
    main()
