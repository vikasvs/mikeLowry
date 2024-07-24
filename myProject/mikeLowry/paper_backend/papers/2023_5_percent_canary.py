import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import json

# Function to identify special decline conditions with a cooldown period
def identify_signals(symbol, cooldown=42, buy_dip_cooldown=42):
    # Fetch maximum historical data
    tick = yf.Ticker(symbol)
    data = tick.history(period="max")

    # Ensure index is timezone-naive
    data.index = data.index.tz_localize(None)

    # Calculate 52-week high, 5% decline, 50-day SMA, and 200-day SMA
    data['52_Week_High'] = data['Close'].rolling(window=252).max()
    data['5%_Decline'] = data['52_Week_High'] * 0.95
    data['50_SMA'] = data['Close'].rolling(window=50).mean()
    data['200_SMA'] = data['Close'].rolling(window=200).mean()

    special_declines = []
    buy_the_dip_signals = []
    last_confirmed_date = pd.Timestamp('1900-01-01')  # Ensuring timezone-naive
    last_buy_dip_date = pd.Timestamp('1900-01-01')  # Ensuring timezone-naive

    # Loop through the data
    for i in range(252, len(data) - cooldown):
        current_date = data.index[i]
        
        # Skip this iteration if we're within the cooldown period
        if (current_date - last_confirmed_date).days < cooldown:
            continue

        # Check if the current date is a 52-week high
        if data['Close'][i] == data['52_Week_High'][i]:
            # Look for a 5% decline within the next 15 trading days
            for j in range(i+1, i+16):
                if j >= len(data):
                    break
                if data['Close'][j] <= data['5%_Decline'][i]:
                    decline_index = data.index[j]

                    # Check for confirmation within 42 days after the decline
                    decline_window = data.loc[decline_index:decline_index + pd.DateOffset(days=cooldown)]
                    consecutive_below_sma = (decline_window['Close'] < decline_window['200_SMA']).rolling(window=2).sum()
                    
                    # Confirm the signal if there are two consecutive closes below the 200-day SMA
                    if (consecutive_below_sma >= 2).any():
                        special_declines.append(decline_index)
                        last_confirmed_date = decline_index
                        break

    # Loop through the data for Buy the Dip signals
    for i in range(252, len(data) - 15):
        current_date = data.index[i]
        
        # Skip this iteration if we're within the buy dip cooldown period
        if (current_date - last_buy_dip_date).days < buy_dip_cooldown:
            continue

        # Check if the current date is a 52-week high
        if data['Close'][i] == data['52_Week_High'][i]:
            # Look for a 5% decline over more than 15 trading days
            for j in range(i+16, len(data)):
                if data['Close'][j] <= data['5%_Decline'][i]:
                    # Validate that the decline happens when the 50-SMA is above the 200-SMA
                    if data['50_SMA'][j] > data['200_SMA'][j]:
                        decline_index = data.index[j]
                        buy_the_dip_signals.append(decline_index)
                        last_buy_dip_date = decline_index
                        break

    return data, special_declines, buy_the_dip_signals

# Function to plot signals for a specific timeframe
<<<<<<< HEAD
def plot_signals(data, special_declines, buy_the_dip_signals, start_date, end_date, title, period):
=======
def plot_signals(data, special_declines, buy_the_dip_signals, start_date, end_date, title):
>>>>>>> caf1f3c701afeb4ba6c7c28a79c9deba7f724787
    filtered_data = data[(data.index >= start_date) & (data.index <= end_date)]
    filtered_special_declines = [date for date in special_declines if start_date <= date <= end_date]
    filtered_buy_the_dip_signals = [date for date in buy_the_dip_signals if start_date <= date <= end_date]

    plt.figure(figsize=(14, 7))
    plt.plot(filtered_data.index, filtered_data['Close'], label='SPY', color='black')
    plt.plot(filtered_data.index, filtered_data['50_SMA'], label='50-Day SMA', color='green')
    plt.plot(filtered_data.index, filtered_data['200_SMA'], label='200-Day SMA', color='blue')

    for decline_date in filtered_special_declines:
        plt.scatter(decline_date, filtered_data.loc[decline_date]['Close'], color='red', zorder=5, label='Confirmed 5% Canary Signal' if decline_date == filtered_special_declines[0] else "")

    for dip_date in filtered_buy_the_dip_signals:
        plt.scatter(dip_date, filtered_data.loc[dip_date]['Close'], color='green', zorder=5, label='Buy the Dip Signal' if dip_date == filtered_buy_the_dip_signals[0] else "")

    plt.title(title)
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.legend()
    plt.grid(True)
<<<<<<< HEAD
    #plt.show()
    png_file = f'../../static/2023_{period.replace(" ", "_")}.png'
    plt.savefig(png_file)
=======
    plt.show()
>>>>>>> caf1f3c701afeb4ba6c7c28a79c9deba7f724787

# Function to create a signal dictionary
def create_signal_dict(data, special_declines, buy_the_dip_signals):
    signals = {}

    # Set initial state to 'Sell' (Cash)
    state = 'Sell'
    for date in data.index:
        if date in special_declines:
            state = 'Sell'
        elif date in buy_the_dip_signals:
            state = 'Buy'
        signals[date] = state

    return signals

# Function to query signal for a specific date
def query_signal(signal_dict, query_date):
    query_date = pd.to_datetime(query_date)
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

# Define the parameters
symbol = 'SPY'  # S&P 500 ETF as a proxy

# Identify special declines and Buy the Dip signals
data, special_declines, buy_the_dip_signals = identify_signals(symbol)

# Create signal dictionary
signal_dict = create_signal_dict(data, special_declines, buy_the_dip_signals)

# Define the timeframes
end_date = datetime.now().date()
end_date = pd.to_datetime(end_date)
start_date_5y = end_date - timedelta(days=1825)
start_date_1y = end_date - timedelta(days=365)
start_date_3m = end_date - timedelta(days=90)
start_date_1w = end_date - timedelta(days=7)

# Plot signals for different timeframes
"""plot_signals(data, special_declines, buy_the_dip_signals, start_date_1w, end_date, 'SPY with Signals (1 Week)')
"""
plot_signals(data, special_declines, buy_the_dip_signals, start_date_3m, end_date, 'SPY with Signals (3 Months)', '3 Months')
plot_signals(data, special_declines, buy_the_dip_signals, start_date_1y, end_date, 'SPY with Signals (1 Year)', '1 Year')
plot_signals(data, special_declines, buy_the_dip_signals, start_date_5y, end_date, 'SPY with Signals (5 Years)', '5 Years')

# Example usage of the query_signal function
query_date = '2023-07-01'
signal = query_signal(signal_dict, query_date)
print(f"Signal on {query_date}: {signal}")

# Function to write the dictionary to a JSON file
def write_dict_to_json(data_dict, filename):
    """Writes a dictionary to a JSON file."""
    with open(filename, 'w') as json_file:
        # Convert keys to string format
        str_data_dict = {key.strftime('%Y-%m-%d'): value for key, value in data_dict.items()}
        json.dump(str_data_dict, json_file, indent=4)

# Write the signal dictionary to a JSON file
write_dict_to_json(signal_dict, '../papers/buy_sell_dicts/2023_canary.json')
