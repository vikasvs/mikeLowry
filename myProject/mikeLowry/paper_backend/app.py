from flask import Flask, render_template
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

app = Flask(__name__)

def generate_dummy_data():
    # Generate dates for the past year
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    dates = pd.date_range(start=start_date, end=end_date, freq='B')  # Business days only

    # Generate dummy closing prices
    np.random.seed(0)
    close_prices = np.random.uniform(low=350, high=450, size=len(dates))

    # Generate 50-day SMA and 200-day SMA
    sma_50 = pd.Series(close_prices).rolling(window=50).mean().to_numpy()
    sma_200 = pd.Series(close_prices).rolling(window=200).mean().to_numpy()

    # Generate dummy signals
    signals = np.random.choice([None, 'Confirmed 5% Canary Signal', 'Buy the Dip Signal'], size=len(dates))

    # Create a DataFrame
    data = {
        'Date': dates,
        'Close': close_prices,
        '50-SMA': sma_50,
        '200-SMA': sma_200,
        'Signal': signals
    }
    df = pd.DataFrame(data)
    return df

def plot_spy_data(df):
    # Plot data
    plt.figure(figsize=(14, 7))
    plt.plot(df['Date'], df['Close'], label='SPY', color='black')
    plt.plot(df['Date'], df['50-SMA'], label='50-Day SMA', color='green')
    plt.plot(df['Date'], df['200-SMA'], label='200-Day SMA', color='blue')

    # Add signals
    for _, row in df.iterrows():
        if row['Signal'] == 'Confirmed 5% Canary Signal':
            plt.scatter(row['Date'], row['Close'], color='red', label='Confirmed 5% Canary Signal', s=100)
        elif row['Signal'] == 'Buy the Dip Signal':
            plt.scatter(row['Date'], row['Close'], color='green', label='Buy the Dip Signal', s=100)

    # Avoid duplicate labels in legend
    handles, labels = plt.gca().get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    plt.legend(by_label.values(), by_label.keys())

    plt.title('SPY with Signals (Past Year)')
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.grid(True)

    # Save plot to file
    plt.savefig('static/images/plot.png')
    plt.close()

@app.route('/')
def index():
    # Generate dummy data
    df = generate_dummy_data()
    plot_spy_data(df)
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
