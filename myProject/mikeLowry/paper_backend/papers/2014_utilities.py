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

# Fetch historical data for Utilities sector and the broader market
utilities_ticker = 'XLU'
market_ticker = 'SPY'
start_date = '1980-01-01'
utilities_data = yf.Ticker(utilities_ticker).history(start=start_date, interval='1d')
market_data = yf.Ticker(market_ticker).history(start=start_date, interval='1d')
utilities_data.index = utilities_data.index.tz_convert(None)
market_data.index = market_data.index.tz_convert(None)

df = pd.merge(utilities_data['Close'], market_data['Close'], left_index=True, right_index=True, suffixes=('_Utilities', '_Market'))
weekly_df = df.resample('W').last()
weekly_df['Relative_Strength'] = weekly_df['Close_Utilities'] / weekly_df['Close_Market']
weekly_df['4_Week_Rolling_RS'] = weekly_df['Relative_Strength'].pct_change(periods=4)
weekly_df['Signal'] = np.where(weekly_df['4_Week_Rolling_RS'] < 0, 'Buy', 'Sell')
df['Weekly_Signal'] = weekly_df['Signal'].reindex(df.index, method='ffill')
df.index = pd.to_datetime(df.index).normalize()
daily_signals = df[df['Weekly_Signal'].isin(['Buy', 'Sell'])]
signals_dict = {date.strftime('%Y-%m-%d'): signal for date, signal in daily_signals['Weekly_Signal'].items()}

def write_plotly_json(data, signals, inflection_points, filename, start_date, end_date):
    plotly_data = {
        'date': data.index.strftime('%Y-%m-%d').tolist(),
        'close': data['Close_Market'].tolist(),
        'inflection_points': [{'date': date, 'signal': signal} for date, signal in inflection_points],
        'layout': {
            'xaxis': {
                'range': [start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')]
            },
            'yaxis': {
                'range': [data['Close_Market'].min(), data['Close_Market'].max()]
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
    filtered_data = df[(df.index >= start_date) & (df.index <= datetime.now())]
    inflection_points = find_inflection_points(signals_dict)
    filename = os.path.join(base_dir, f'2014_{period.replace(" ", "_")}_plotly.json')
    write_plotly_json(filtered_data, signals_dict, inflection_points, filename, start_date, datetime.now())
