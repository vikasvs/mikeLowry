import yfinance as yf
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
import os
from collections import defaultdict

# Define the base directory for static files
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../static'))
# Create static directory if it doesn't exist
os.makedirs(base_dir, exist_ok=True)

# Fetch historical data for SPY
spy_ticker = 'SPY'
start_date = '1980-01-01'
spy_data = yf.Ticker(spy_ticker).history(start=start_date, interval='1d')
spy_data.index = spy_data.index.tz_convert(None)

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

# Load signals from JSON files
json_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'papers', 'buy_sell_dicts'))
for filename in os.listdir(json_directory):
    if filename.endswith('.json'):
        filepath = os.path.join(json_directory, filename)
        with open(filepath, 'r') as file:
            signals = json.load(file)
            inflection_points = find_inflection_points(signals)
            inflection_points_dict[filename] = inflection_points

            for date, signal in signals.items():
                buy_tally[date]['total'] += 1
                if signal == 'Buy':
                    buy_tally[date]['buy'] += 1

# Calculate the percentage of "Buy" signals for each date
buy_percentage = {date: (data['buy'] / data['total']) * 100 for date, data in buy_tally.items() if data['total'] > 0}

# Create a DataFrame for the buy percentage
buy_percentage_df = pd.DataFrame(list(buy_percentage.items()), columns=['Date', 'Buy_Percentage'])
buy_percentage_df['Date'] = pd.to_datetime(buy_percentage_df['Date'])
buy_percentage_df.set_index('Date', inplace=True)

# Adjust SPY data timestamps to match the buy_percentage_df date format
spy_data.index = spy_data.index.normalize()

# Merge SPY data with buy percentage data
spy_data['200_SMA'] = spy_data['Close'].rolling(window=200).mean()
merged_df = spy_data.join(buy_percentage_df, how='left')

# Define the timeframes to plot
timeframes = {
    '3_Months': timedelta(days=3*30),
    '1_Year': timedelta(days=365),
    '5_Years': timedelta(days=5*365)
}

def write_plotly_json(data, inflection_points, filename, start_date, end_date):
    plotly_data = {
        'date': data.index.strftime('%Y-%m-%d').tolist(),
        'close': data['Close'].tolist(),
        'buy_percentage': data['Buy_Percentage'].tolist(),
        'inflection_points': [{'date': date, 'signal': signal} for date, signal in inflection_points],
        'layout': {
            'xaxis': {
                'range': [start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')],
                'title': 'Date'
            },
            'yaxis': {
                'range': [data['Close'].min(), data['Close'].max()],
                'title': 'Price'
            },
            'coloraxis': {
                'colorbar': {
                    'title': 'Buy Percentage'
                }
            }
        }
    }
    with open(filename, 'w') as json_file:
        json.dump(plotly_data, json_file, indent=4)

for label, period in timeframes.items():
    end_date = datetime.now().date()
    start_date = end_date - period

    # Filter data for the current timeframe
    filtered_data = merged_df.loc[start_date:end_date]
    inflection_points = find_inflection_points(buy_tally)
    filename = os.path.join(base_dir, f'master_{label.replace(" ", "_")}_plotly.json')
    write_plotly_json(filtered_data, inflection_points, filename, start_date, end_date)

# Plot SPY data with Buy and Sell signals and color gradient for each timeframe
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.dates as mdates

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
    markers = ['o', 's', 'D', '^', 'v', '<', '>', 'p', '*', 'h', 'H', 'x', 'd']
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
    if label == '3_Months':
        ax.xaxis.set_major_locator(mdates.WeekdayLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
        ax.xaxis.set_minor_locator(mdates.DayLocator())
    elif label == '1_Year':
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
    plot_filename = os.path.join(base_dir, f'master_{label.replace(" ", "_")}.png')
    plt.savefig(plot_filename)
    plt.close(fig)
