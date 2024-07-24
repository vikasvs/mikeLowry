import os
import json
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.colors as mcolors

# Path to the directory containing the JSON files
json_directory = 'papers/buy_sell_dicts'

# Initialize a dictionary to hold the tally of "Buy" signals and inflection points
buy_tally = defaultdict(lambda: {'buy': 0, 'total': 0})
inflection_points_dict = {}

# Function to find inflection points in the signals
def find_inflection_points(signals):
    inflection_points = []
    prev_signal = None
    for date, signal in signals.items():
        if prev_signal is not None and signal != prev_signal:
            inflection_points.append((date, signal))
        prev_signal = signal
    return inflection_points

# Iterate over all JSON files in the directory
for filename in os.listdir(json_directory):
    if filename.endswith('.json'):
        filepath = os.path.join(json_directory, filename)
        with open(filepath, 'r') as file:
            signals = json.load(file)
            # Find inflection points
            inflection_points = find_inflection_points(signals)
            inflection_points_dict[filename] = inflection_points
            
            for date, signal in signals.items():
                buy_tally[date]['total'] += 1
                if signal == 'Buy':
                    buy_tally[date]['buy'] += 1

# Calculate the percentage of "Buy" signals for each date
buy_percentage = {date: (data['buy'] / data['total']) * 100 for date, data in buy_tally.items() if data['total'] > 0}

# Write the results to new JSON files
output_buy_percentage_filepath = 'buy_percentage.json'
with open(output_buy_percentage_filepath, 'w') as outfile:
    json.dump(buy_percentage, outfile, indent=4)

output_inflection_points_filepath = 'inflection_points.json'
with open(output_inflection_points_filepath, 'w') as outfile:
    json.dump(inflection_points_dict, outfile, indent=4)

# Load SPY data
spy_ticker = 'SPY'
spy_data = yf.Ticker(spy_ticker).history(start='2016-01-01', end='2024-06-30', interval='1d')
spy_data.index = spy_data.index.tz_convert(None)

# Calculate the 200-day Simple Moving Average (SMA)
spy_data['200_SMA'] = spy_data['Close'].rolling(window=200).mean()

# Adjust SPY data timestamps to match the buy_percentage_df date format
spy_data.index = spy_data.index.normalize()

# Create a DataFrame for the buy percentage
buy_percentage_df = pd.DataFrame(list(buy_percentage.items()), columns=['Date', 'Buy_Percentage'])
buy_percentage_df['Date'] = pd.to_datetime(buy_percentage_df['Date'])
buy_percentage_df.set_index('Date', inplace=True)

# Filter buy_percentage_df to match the spy_data date range if necessary
buy_percentage_df = buy_percentage_df.loc[(buy_percentage_df.index >= spy_data.index.min()) & (buy_percentage_df.index <= spy_data.index.max())]

# Merge SPY data with buy percentage data
merged_df = spy_data.join(buy_percentage_df, how='left')

# Define the timeframes to plot (last 8 years)
end_date = datetime.now().date()
start_date = end_date - timedelta(days=8*365)  # approximately 8 years

# Define different markers for each JSON file
markers = ['o', 's', 'D', '^', 'v', '<', '>', 'p', '*', 'h', 'H', 'x', 'd']

# Plot SPY data with Buy and Sell signals and color gradient for the timeframe
fig, ax = plt.subplots(figsize=(14, 7))
norm = mcolors.Normalize(vmin=0, vmax=100)
sm = plt.cm.ScalarMappable(cmap='RdYlGn', norm=norm)
sm.set_array([])

# Plot SPY Close price and 200-day SMA
ax.plot(merged_df.loc[start_date:end_date].index, merged_df.loc[start_date:end_date]['Close'], label='SPY', color='black', zorder=1)
ax.plot(merged_df.loc[start_date:end_date].index, merged_df.loc[start_date:end_date]['200_SMA'], label='200-day SMA', color='blue', linestyle='--', zorder=1)

# Plot color gradient for Buy percentage
for i in range(len(merged_df) - 1):
    if pd.notna(merged_df['Buy_Percentage'].iloc[i]):
        color = plt.cm.RdYlGn(norm(merged_df['Buy_Percentage'].iloc[i]))
        ax.plot(merged_df.index[i:i+2], merged_df['Close'].iloc[i:i+2], color=color, linewidth=2, zorder=1)

# Add inflection points for each JSON file
for idx, (filename, inflection_points) in enumerate(inflection_points_dict.items()):
    marker = markers[idx % len(markers)]  # Cycle through markers if there are more files than markers
    for date_str, signal in inflection_points:
        date = pd.to_datetime(date_str)
        if date in merged_df.index:
            price = merged_df.loc[date, 'Close']
            if signal == 'Buy':
                ax.scatter(date, price, color='green', edgecolor='black', linewidth=0.5, marker=marker, s=50, label=f'{filename} Buy' if idx == 0 else "", zorder=2)
            elif signal == 'Sell':
                ax.scatter(date, price, color='red', edgecolor='black', linewidth=0.5, marker=marker, s=50, label=f'{filename} Sell' if idx == 0 else "", zorder=2)

# Formatting the plot
plt.title(f'SPY with Buy and Sell Signals and Buy Percentage Color Gradient ({start_date} to {end_date})')
plt.xlabel('Date')
plt.ylabel('Price')
fig.colorbar(sm, ax=ax, label='Buy Percentage', orientation='vertical')
plt.legend()
plt.grid(True)
ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_minor_locator(mdates.MonthLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
plt.show()
