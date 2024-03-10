import ccxt
import ta
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import datetime
import configparser


config = configparser.ConfigParser()
config.read('config.ini')


def get_crypto_data(symbol, interval):
    # Replace with your actual API key and secret
    api_key = config['API_KEYS']['API_KEY']
    api_secret = config['API_KEYS']['API_SECRET']

    exchange = ccxt.binance({
        'apiKey': api_key,
        'secret': api_secret
    })

    # Fetch data based on symbol and interval
    data = exchange.fetch_ohlcv(symbol, timeframe=interval)
    # Convert data to NumPy array
    data_array = np.array(data)

    return data_array


def analyze_data(data):
    # Convert data to pandas DataFrame
    df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

    # Calculate RSI using ta library
    rsi = ta.momentum.rsi(df['close'])  # Use only close price for RSI

    # Calculate MACD
    macd_line = ta.trend.macd_diff(df['close'])  # MACD line (12-period EMA - 26-period EMA)
    signal_line = ta.trend.macd_signal(df['close'])  # Signal line (9-period EMA of MACD line)

    return {'rsi': rsi, 'macd_line': macd_line, 'signal_line': signal_line}



def generate_signal(analysis_result):
    # Generate a signal based on RSI
    # If RSI is above 70, consider it overbought and sell (signal = 0)
    # If RSI is below 30, consider it oversold and buy (signal = 1)
    signal = np.where(analysis_result['rsi'] > 70, 0, np.where(analysis_result['rsi'] < 30, 1, -1))
    return signal


def update_plot(frame):
    crypto_data = get_crypto_data("BTC/USDT", "1m")
    analysis_result = analyze_data(crypto_data)
    signal = generate_signal(analysis_result)

    timestamps = [datetime.datetime.fromtimestamp(ts / 1000) for ts in crypto_data[:, 0]]
    ax1.clear()
    ax1.plot(timestamps, crypto_data[:, 3], label='Close Price', color='black')
    ax1.set_title('Candlestick Chart')
    ax1.set_xlabel('Time')
    ax1.set_ylabel('Price')

    ax2.clear()
    ax2.plot(timestamps, analysis_result['rsi'], label='RSI', color='blue')
    ax2.axhline(y=70, color='r', linestyle='--', label='Overbought')
    ax2.axhline(y=30, color='g', linestyle='--', label='Oversold')
    ax2.set_title('RSI Indicator')
    ax2.set_xlabel('Time')
    ax2.set_ylabel('RSI')

    ax3 = ax2.twinx()
    ax3.plot(timestamps, analysis_result['macd_line'], label='MACD Line', color='orange')
    ax3.plot(timestamps, analysis_result['signal_line'], label='Signal Line', color='purple')
    ax3.set_ylabel('MACD')
    ax3.legend(loc='upper left')

    # Add signal markers
    ax1.plot([timestamps[i] for i in range(len(signal)) if signal[i] == 1], [crypto_data[:, 3][i] for i in range(len(signal)) if signal[i] == 1], '^', markersize=10, color='g', lw=0, label='Buy Signal')
    ax1.plot([timestamps[i] for i in range(len(signal)) if signal[i] == 0], [crypto_data[:, 3][i] for i in range(len(signal)) if signal[i] == 0], 'v', markersize=10, color='r', lw=0, label='Sell Signal')

    # Add signal markers for MACD
    ax3.plot([timestamps[i] for i in range(1, len(signal)) if signal[i] == 1 and signal[i-1] != 1],
             [analysis_result['macd_line'][i] for i in range(1, len(signal)) if signal[i] == 1 and signal[i-1] != 1],
             '^', markersize=10, color='g', lw=0, label='Buy Signal')
    ax3.plot([timestamps[i] for i in range(1, len(signal)) if signal[i] == 0 and signal[i-1] != 0],
             [analysis_result['macd_line'][i] for i in range(1, len(signal)) if signal[i] == 0 and signal[i-1] != 0],
             'v', markersize=10, color='r', lw=0, label='Sell Signal')

    ax1.legend()
    ax2.legend()

    ax1.xaxis.set_tick_params(rotation=0)


fig, (ax1, ax2) = plt.subplots(2, figsize=(12, 8))
ani = FuncAnimation(fig, update_plot, interval=15000, cache_frame_data=False) # Update every 5 seconds (5000 milliseconds)
plt.tight_layout()
plt.show()

