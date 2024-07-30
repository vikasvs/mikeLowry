import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json
from datetime import datetime, timedelta
import os

# Define the base directory for static files
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../static'))
os.makedirs(base_dir, exist_ok=True)

# Fetch historical data for the SPY ETF
market_ticker = 'SPY'
start_date = '1980-01-01'
market_data = yf.Ticker(market_ticker).history(start=start_date, interval='1d')
market_data.index = market_data.index.tz_convert(None)

# Calculate the 5% decline signal
market_data['5%_Decline'] = market_data['Close'].pct_change().rolling(window=5).sum()
market_data['Signal'] = np.where(market_data['5%_Decline'] < -0.05, 'Sell', 'Buy')
market_data['Signal'] = market_data['Signal'].shift(-1)
market_data.index = pd.to_datetime(market_data.index).normalize()
daily_signals = market_data[market_data['Signal'].isin(['Buy', 'Sell'])]
signals_dict = {date.strftime('%Y-%m-%d'): signal for date, signal in daily_signals['Signal'].items()}

def write_plotly_json(data, signals, inflection_points, filename, start_date, end_date):
    plotly_data = {
        'date': data.index.strftime('%Y-%m-%d').tolist(),
        'close': data['Close'].tolist(),
        'inflection_points': [{'date': date, 'signal': signal} for date, signal in inflection_points],
        'layout': {
            'xaxis': {
                'range': [start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')]
            },
            'yaxis': {
                'range': [data['Close'].min(), data['Close'].max()]
            }
        }
    }
    with open(filename, 'w') as json_file:
        json.dump(plotly_data, json_file, indent=4)

def find_inflection_points(signals):
    inflection_points = []
    prev_signal = None
    for date, signal in signals.items():
        if prev_signal is not None and signal != prev_signal:
            inflection_points.append((date, signal))
        prev_signal = signal
    return inflection_points

timeframes = {
    '3_Months': datetime.now() - timedelta(days=90),
    '1_Year': datetime.now() - timedelta(days=365),
    '5_Years': datetime.now() - timedelta(days=5*365)
}

for period, start_date in timeframes.items():
    filtered_data = market_data[(market_data.index >= start_date) & (market_data.index <= datetime.now())]
    inflection_points = find_inflection_points(signals_dict)
    filename = os.path.join(base_dir, f'2023_{period.replace(" ", "_")}_plotly.json')
    write_plotly_json(filtered_data, signals_dict, inflection_points, filename, start_date, datetime.now())
