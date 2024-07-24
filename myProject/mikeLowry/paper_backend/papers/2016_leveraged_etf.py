import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import numpy as np
import json

def fetch_data(symbol, start_date):
    tick = yf.Ticker(symbol)
    data = tick.history(start=start_date)
    data.index = data.index.tz_localize(None)
    data['Returns'] = data['Close'].pct_change()  # Calculate returns immediately
    return data

def calculate_leverage_rotation(spy_data):
    spy_data['200_MA'] = spy_data['Close'].rolling(window=200, min_periods=1).mean()  # Adjust rolling to allow less periods

    # Strategy: Buy when SPY > 200 MA, Sell (cash) when SPY < 200 MA
    spy_data['Signal'] = np.where(spy_data['Close'] > spy_data['200_MA'], 'Buy', 'Sell')
    
    return spy_data

def plot_signals(spy_data, start_date, end_date, title, period):
    # Filter data for the specified period
    plot_data = spy_data.loc[start_date:end_date]

    plt.figure(figsize=(14, 7))
    plt.plot(plot_data.index, plot_data['Close'], label='SPY Close Price', color='blue')
    plt.plot(plot_data.index, plot_data['200_MA'], label='200-Day Moving Average', color='orange', linestyle='--')
    
    buy_signals = plot_data[plot_data['Signal'] == 'Buy']
    sell_signals = plot_data[plot_data['Signal'] == 'Sell']
    plt.scatter(buy_signals.index, buy_signals['Close'], marker='^', color='green', label='Buy Signal', alpha=1)
    plt.scatter(sell_signals.index, sell_signals['Close'], marker='v', color='red', label='Sell Signal', alpha=1)

    plt.title(title)
    plt.xlabel('Date')
    plt.ylabel('SPY Close Price')
    plt.legend()
    plt.grid(True)
    #plt.show()
 
    png_file = f'../../static/2016_{period.replace(" ", "_")}.png'
    plt.savefig(png_file)

def write_dict_to_json(data_dict, filename):
    """Writes a dictionary to a JSON file."""
    with open(filename, 'w') as json_file:
        # Convert keys to string format
        str_data_dict = {key.strftime('%Y-%m-%d'): value for key, value in data_dict.items()}
        json.dump(str_data_dict, json_file, indent=4)

# Load data for SPY
symbol_spy = 'SPY'
spy_data = fetch_data(symbol_spy, '1980-01-01')

# Calculate signals
spy_data = calculate_leverage_rotation(spy_data)

# Generate signal dictionary
signal_dict = {}
for date in spy_data.index:
    signal_dict[date] = spy_data.loc[date, 'Signal']

# Write signals to JSON file
<<<<<<< HEAD
write_dict_to_json(signal_dict, '../papers/buy_sell_dicts/2016_leverage.json')
=======
write_dict_to_json(signal_dict, 'papers/buy_sell_dicts/2016_leverage.json')
>>>>>>> caf1f3c701afeb4ba6c7c28a79c9deba7f724787

# Define the end date and timeframes for plotting
end_date = pd.to_datetime(datetime.now().date())
timeframes = {
    '3 Months': (end_date - timedelta(days=90), end_date),
    '1 Year': (end_date - timedelta(days=365), end_date),
    '5 Years': (end_date - timedelta(days=5 * 365), end_date)  # Adjust for leap years if necessary
}

# Plot for each timeframe
for period, (start_date, end_date) in timeframes.items():
<<<<<<< HEAD
    plot_signals(spy_data, start_date, end_date, f'SPY Buy and Sell Signals ({period})', period)
=======
    plot_signals(spy_data, start_date, end_date, f'SPY Buy and Sell Signals ({period})')
>>>>>>> caf1f3c701afeb4ba6c7c28a79c9deba7f724787
