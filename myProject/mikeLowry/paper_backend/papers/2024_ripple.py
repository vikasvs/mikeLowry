import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import json

def get_52_week_low_status(ticker_symbol):
    print(f"Processing data for {ticker_symbol}")
    try:
        # Download historical data for the given ticker
        tick = yf.Ticker(ticker_symbol)
        tick_hist = tick.history(start="1980-01-01")
        
        # Check if data is empty
        if tick_hist.empty:
            print(f"No data found for {ticker_symbol}")
            return {}
        
        # Ensure index is timezone-naive
        tick_hist.index = tick_hist.index.tz_localize(None)
        
        # Calculate 52-week low
        tick_hist['52_Week_Low'] = tick_hist['Close'].rolling(window=252, min_periods=1).min()
        
        # Find the points where the Close price is equal to the 52-week low
        tick_hist['Is_52_Week_Low'] = (tick_hist['Close'] == tick_hist['52_Week_Low']).astype(int)
        
        # Create a dictionary to store the data
        low_status = {date.strftime('%Y-%m-%d'): status for date, status in zip(tick_hist.index, tick_hist['Is_52_Week_Low'])}
        
        return low_status
        
    except Exception as e:
        print(f"An error occurred: {e}")
        return {}

def query_ticker_at_date(all_ticker_data, query_date):
    # Convert the query_date to string format
    query_date_str = query_date.strftime('%Y-%m-%d')
    
    # Count tickers at their 52-week low on the query date
    low_count = sum(all_ticker_data[ticker].get(query_date_str, 0) for ticker in all_ticker_data if query_date_str in all_ticker_data[ticker])
    total_count = sum(1 for ticker in all_ticker_data if query_date_str in all_ticker_data[ticker])
    
    return low_count / total_count if total_count > 0 else 0

def fetch_sp500_tickers():
    """Fetches the list of S&P 500 tickers from Wikipedia."""
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    data = pd.read_html(url)
    sp500_table = data[0]
    return sp500_table['Symbol'].tolist()[:50]

def nyse_tickers():
    url = "https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main/nyse/nyse_tickers.txt"
    tickers_df = pd.read_csv(url, header=None)
    return tickers_df[0].tolist()

def write_dict_to_json(data_dict, filename):
    """Writes a dictionary to a JSON file."""
    with open(filename, 'w') as json_file:
        # Convert keys to string format
        str_data_dict = {str(key): value for key, value in data_dict.items()}
        json.dump(str_data_dict, json_file, indent=4)

# Fetch the list of S&P 500 tickers
tickers = fetch_sp500_tickers()
#tickers = nyse_tickers()  # Use NYSE tickers instead 

# Get the 52-week low status data for all tickers
all_ticker_data = {ticker: get_52_week_low_status(ticker) for ticker in tickers}

# Load SPY data
spy = yf.Ticker("SPY")
spy_hist = spy.history(start="2005-01-01")

# Ensure index is timezone-naive
spy_hist.index = spy_hist.index.tz_localize(None)

# Calculate the percentage of tickers at 52-week low for each trading day
percentages = []
dates = spy_hist.index
for date in dates:
    percentage = query_ticker_at_date(all_ticker_data, date)
    percentages.append(percentage)

# Create a DataFrame to store the results
percentages_df = pd.DataFrame({'Date': dates, 'Percentage': percentages}).set_index('Date')

# Identify "selling climax" and "extreme vulnerability" signals
percentages_df['Selling_Climax'] = percentages_df['Percentage'] >= 0.50
percentages_df['Extreme_Vulnerability'] = percentages_df['Percentage'] < 0.0003

# Create a signal dictionary
def create_signal_dict(percentages_df):
    signals = {}

    for date in percentages_df.index:
        if percentages_df.loc[date, 'Selling_Climax']:
            signals[date] = 'Sell'
        else:
            signals[date] = 'Buy'
    
    return signals

signal_dict = create_signal_dict(percentages_df)

# Function to query signal for a specific date
def query_signal(signal_dict, query_date):
    query_date = pd.to_datetime(query_date).tz_localize(None)
    if query_date in signal_dict:
        return signal_dict[query_date]
    else:
        # Find the last available date before the query date
        available_dates = [date for date in signal_dict.keys() if date <= query_date]
        if available_dates:
            last_date = max(available_dates)
            return signal_dict[last_date]
        else:
            return "Date not in data"

# Write the signal dictionary to a JSON file
write_dict_to_json(signal_dict, 'signal_dict.json')

# Plot the results
plt.figure(figsize=(14, 7))

# Plot SPY close price
plt.plot(spy_hist['Close'], label='SPY Close Price')

# Plot different percentage ranges in blocks of 10%
for pct in range(20, 71, 10):
    pct_range = (percentages_df['Percentage'] >= pct / 100) & (percentages_df['Percentage'] < (pct + 10) / 100)
    plt.scatter(percentages_df.index[pct_range], 
                spy_hist['Close'][spy_hist.index.isin(percentages_df.index[pct_range])], 
                label=f'{pct}-{pct + 9}%', marker='o')

# Plot extreme vulnerability signal
"""plt.scatter(percentages_df.index[percentages_df['Extreme_Vulnerability']], 
            spy_hist['Close'][spy_hist.index.isin(percentages_df.index[percentages_df['Extreme_Vulnerability']])], 
            color='red', label='Extreme Vulnerability', marker='o')"""

plt.title('SPY Close Price with Different Percentage Ranges and Extreme Vulnerability Signal')
plt.xlabel('Date')
plt.ylabel('Close Price (USD)')
plt.legend()
plt.grid(True)
plt.show()

# Example usage of the query_signal function
query_date = '2023-07-01'
signal = query_signal(signal_dict, query_date)
print(f"Signal on {query_date}: {signal}")

import json
def write_dict_to_json(data_dict, filename):
    """Writes a dictionary to a JSON file."""
    with open(filename, 'w') as json_file:
        # Convert keys to string format
        str_data_dict = {key.strftime('%Y-%m-%d'): value for key, value in data_dict.items()}
        json.dump(str_data_dict, json_file, indent=4)

write_dict_to_json(signal_dict, 'papers/buy_sell_dicts/2024_lows.json')