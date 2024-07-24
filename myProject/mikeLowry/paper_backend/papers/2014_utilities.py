import yfinance as yf
import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Fetch historical data for Utilities sector and the broader market
utilities_ticker = 'XLU'
market_ticker = 'SPY'

# Fetch data from 1980-01-01 to the present
start_date = '1980-01-01'

# Download the data using the .history() method with a daily interval
utilities_data = yf.Ticker(utilities_ticker).history(start=start_date, interval='1d')
market_data = yf.Ticker(market_ticker).history(start=start_date, interval='1d')

# Remove timezone information
utilities_data.index = utilities_data.index.tz_convert(None)
market_data.index = market_data.index.tz_convert(None)

# Merge the dataframes on the Date column
df = pd.merge(utilities_data['Close'], market_data['Close'], left_index=True, right_index=True, suffixes=('_Utilities', '_Market'))

# Resample data to weekly intervals
weekly_df = df.resample('W').last()

# Calculate the 4-week relative strength of Utilities to the Market
weekly_df['Relative_Strength'] = weekly_df['Close_Utilities'] / weekly_df['Close_Market']
weekly_df['4_Week_Rolling_RS'] = weekly_df['Relative_Strength'].pct_change(periods=4)  # 4 weeks

# Generate signals: Buy Market if RS > 0, else Sell (Hold Utilities)
weekly_df['Signal'] = np.where(weekly_df['4_Week_Rolling_RS'] < 0, 'Buy', 'Sell')

# Map the weekly signals back to the daily data
df['Weekly_Signal'] = weekly_df['Signal'].reindex(df.index, method='ffill')

# Ensure the index is in datetime format and timezone-naive
df.index = pd.to_datetime(df.index).normalize()

# Only keep 'Buy' and 'Sell' signals
daily_signals = df[df['Weekly_Signal'].isin(['Buy', 'Sell'])]

# Convert the signals into a dictionary for easy querying
signals_dict = {date.strftime('%Y-%m-%d'): signal for date, signal in daily_signals['Weekly_Signal'].items()}

# Function to query the strategy signal from the dictionary
def query_signal(date):
    date_str = pd.to_datetime(date).strftime('%Y-%m-%d')
    # Find the most recent available date in the dictionary before the given date
    available_dates = [d for d in signals_dict.keys() if d <= date_str]
    if available_dates:
        last_date = max(available_dates)
        print(f"Date not in dataset. Using the last available date: {last_date}")
        return signals_dict[last_date]
    else:
        return 'Date not in dataset'

# Example usage with dictionary
print(query_signal('2021-01-01'))
print(query_signal('2022-01-01'))

# Function to write the dictionary to a JSON file
def write_dict_to_json(data_dict, filename):
    with open(filename, 'w') as json_file:
        json.dump(data_dict, json_file, indent=4)

# Write the signals dictionary to a JSON file
write_dict_to_json(signals_dict, 'papers/buy_sell_dicts/2014_utilities.json')

# Define timeframes
end_date = pd.to_datetime(datetime.now().date())
timeframes = {
    '3 Months': end_date - timedelta(days=90),
    '1 Year': end_date - timedelta(days=365),
    '5 Years': end_date - timedelta(days=5 * 365)
}

# Plot SPY data with Buy and Sell signals for specified timeframes
for period, start_date in timeframes.items():
    plt.figure(figsize=(14, 7))
    plt.plot(market_data.loc[start_date:end_date].index, market_data.loc[start_date:end_date]['Close'], label='SPY', color='black')

    # Add Buy and Sell signals as colored segments
    period_df = df.loc[start_date:end_date]
    for i in range(1, len(period_df)):
        if period_df['Weekly_Signal'].iloc[i] == 'Buy':
            plt.plot(period_df.index[i-1:i+1], period_df['Close_Market'].iloc[i-1:i+1], color='green')
        elif period_df['Weekly_Signal'].iloc[i] == 'Sell':
            plt.plot(period_df.index[i-1:i+1], period_df['Close_Market'].iloc[i-1:i+1], color='red')

    plt.title(f'SPY with Buy and Sell Signals ({period})')
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.legend()
    plt.grid(True)
    plt.show()
