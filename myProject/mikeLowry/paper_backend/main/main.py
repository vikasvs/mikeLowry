import json
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.colors as mcolors
import os

# Path to the directory containing the JSON files
json_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'papers', 'buy_sell_dicts'))

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
output_buy_percentage_filepath = os.path.abspath(os.path.join(os.path.dirname(__file__), 'buy_percentage.json'))
with open(output_buy_percentage_filepath, 'w') as outfile:
    json.dump(buy_percentage, outfile, indent=4)

output_inflection_points_filepath = os.path.abspath(os.path.join(os.path.dirname(__file__), 'inflection_points.json'))
with open(output_inflection_points_filepath, 'w') as outfile:
    json.dump(inflection_points_dict, outfile, indent=4)

# Load SPY data
spy_ticker = 'SPY'
spy_data = yf.Ticker(spy_ticker).history(start='2009-01-01', end='2024-06-30', interval='1d')
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

# Define the timeframes to plot
timeframes = {
    '3 Months': timedelta(days=3*30),
    '1 Year': timedelta(days=365),
    '5 Years': timedelta(days=5*365)
}

# Define different markers for each JSON file
markers = ['o', 's', 'D', '^', 'v', '<', '>', 'p', '*', 'h', 'H', 'x', 'd']

# Plot SPY data with Buy and Sell signals and color gradient for each timeframe
for label, period in timeframes.items():
    fig, ax = plt.subplots(figsize=(14, 7))
    end_date = datetime.now().date()
    start_date = end_date - period

    # Calculate the scaling factor for marker size
    num_days = (end_date - start_date).days
    marker_size = max(20, min(200, 2000 / num_days))  # Adjust min and max sizes as necessary

    norm = mcolors.Normalize(vmin=0, vmax=100)
    sm = plt.cm.ScalarMappable(cmap='RdYlGn', norm=norm)
    sm.set_array([])

    # Filter data for the current timeframe
    filtered_df = merged_df.loc[start_date:end_date]
    if filtered_df.empty:
        print(f"No data available for {label}")
        continue

    # Plot SPY Close price and 200-day SMA
    ax.plot(filtered_df.index, filtered_df['Close'], label='SPY', color='black', zorder=1)
    ax.plot(filtered_df.index, filtered_df['200_SMA'], label='200-day SMA', color='blue', linestyle='--', zorder=1)

    # Plot color gradient for Buy percentage
    for i in range(len(filtered_df) - 1):
        if pd.notna(filtered_df['Buy_Percentage'].iloc[i]):
            color = plt.cm.RdYlGn(norm(filtered_df['Buy_Percentage'].iloc[i]))
            ax.plot(filtered_df.index[i:i+2], filtered_df['Close'].iloc[i:i+2], color=color, linewidth=2, zorder=1)

    # Add inflection points for each JSON file
    handles = []
    labels = []
    for idx, (filename, inflection_points) in enumerate(inflection_points_dict.items()):
        marker = markers[idx % len(markers)]  # Cycle through markers if there are more files than markers
        for date_str, signal in inflection_points:
            date = pd.to_datetime(date_str)
            if date in filtered_df.index:
                price = filtered_df.loc[date, 'Close']
                if signal == 'Buy':
                    ax.scatter(date, price, color='green', edgecolor='black', linewidth=0.5, marker=marker, s=marker_size, zorder=2)
                elif signal == 'Sell':
                    ax.scatter(date, price, color='red', edgecolor='black', linewidth=0.5, marker=marker, s=marker_size, zorder=2)
        # Add one handle per marker for the legend
        handles.append(ax.scatter([], [], color='black', marker=marker, s=marker_size, label=filename))
        labels.append(filename)

    # Formatting the plot
    plt.title(f'SPY with Buy and Sell Signals and Buy Percentage Color Gradient ({label})')
    plt.xlabel('Date')
    plt.ylabel('Price')
    fig.colorbar(sm, ax=ax, label='Buy Percentage', orientation='vertical')

    # Adjust x-axis formatting based on the timeframe
    if label == '3 Months':
        ax.xaxis.set_major_locator(mdates.WeekdayLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
        ax.xaxis.set_minor_locator(mdates.DayLocator())
    elif label == '1 Year':
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
        ax.xaxis.set_minor_locator(mdates.WeekdayLocator())
    else:
        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_minor_locator(mdates.MonthLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))

    plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
    plt.legend(handles=handles, labels=labels)
    plt.grid(True)

    # Save plot as PNG
    plot_filename = f'../../static/master_{label.replace(" ", "_")}.png'
    plt.savefig(plot_filename)
    plt.close(fig)
