from flask import Flask, render_template
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import time

app = Flask(__name__)

# Full mapping for ticker descriptions
TICKER_NAMES = {
    "VOO": "S&P 500 ETF", "QQQ": "Nasdaq 100", "IWM": "Russell 2000", "DIA": "Dow Jones Industrials",
    "EWJ": "MSCI Japan", "EWY": "MSCI South Korea", "EWG": "MSCI Germany", "INDA": "MSCI India",
    "MCHI": "MSCI China", "EWU": "MSCI United Kingdom", "EWZ": "MSCI Brazil", "EWW": "MSCI Mexico",
    "EWQ": "MSCI France", "FXI": "China Large-Cap", "EWH": "MSCI Hong Kong",
    "SMH": "Semiconductors", "MAGS": "Magnificent 7", "RSP": "S&P 500 Equal Weight",
    "CIBR": "Cybersecurity", "AIQ": "Artificial Intelligence", "BOTZ": "Robotics & AI",
    "LIT": "Lithium & Battery Tech", "XOP": "Oil & Gas Exploration", "GLD": "Gold Shares",
    "KRE": "Regional Banking", "ARKK": "Innovation ETF",
    "ITA": "Aerospace & Defense", "XLE": "Energy Sector", "IYZ": "Telecommunications",
    "XLP": "Consumer Staples", "XLY": "Consumer Discretionary", "IGV": "Software Sector",
    "UFO": "Space Industry"
}

def calculate_rsi(series, period=14):
    """Calculates RSI manually to save memory/prevent Numba crashes"""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def get_stats(tickers):
    results = []
    for ticker in tickers:
        try:
            # Download 1 year of data (needed for 200-day Moving Average)
            df = yf.download(ticker, period="1y", interval="1d", progress=False, auto_adjust=True)
            if df.empty or len(df) < 200:
                continue
            
            # Clean column names if they are MultiIndex
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            # Technical Indicators (Manual calculation = Less RAM usage)
            df['MA20'] = df['Close'].rolling(window=20).mean()
            df['MA50'] = df['Close'].rolling(window=50).mean()
            df['MA200'] = df['Close'].rolling(window=200).mean()
            df['RSI'] = calculate_rsi(df['Close'])

            latest = df.iloc[-1]
            price = float(latest['Close'])
            
            # Daily % Change
            prev_close = df['Close'].iloc[-2]
            daily_change = ((price - prev_close) / prev_close) * 100
            
            # 5-Day % Change
            five_days_ago = df['Close'].iloc[-6] if len(df) > 6 else df['Close'].iloc[0]
            five_day_change = ((price - five_days_ago) / five_days_ago) * 100
            
            # YTD % Change
            current_year = datetime.now().year
            ytd_start_data = df[df.index >= f"{current_year}-01-01"]
            ytd_start_price = ytd_start_data['Close'].iloc[0] if not ytd_start_data.empty else df['Close'].iloc[0]
            ytd_change = ((price - ytd_start_price) / ytd_start_price) * 100

            # RSI Status
            rsi_val = float(latest['RSI']) if not pd.isna(latest['RSI']) else 50
            status = "Neutral"
            if rsi_val > 70: status = "Overbought"
            elif rsi_val < 30: status = "Oversold"

            results.append({
                "ticker": ticker,
                "name": TICKER_NAMES.get(ticker, ticker),
                "price": round(price, 2),
                "daily_change": round(daily_change, 2),
                "five_day_change": round(five_day_change, 2),
                "ytd_change": round(ytd_change, 2),
                "range_52": f"{round(df['Low'].min(), 2)} - {round(df['High'].max(), 2)}",
                "rsi": round(rsi_val, 1),
                "status": status,
                "ma20": "Y" if price > float(latest['MA20']) else "N",
                "ma50": "Y" if price > float(latest['MA50']) else "N",
                "ma200": "Y" if price > float(latest['MA200']) else "N"
            })
            # Small delay to be polite to the Yahoo Finance API
            time.sleep(0.1)
        except Exception as e:
            print(f"Error fetching {ticker}: {e}")
            continue
    return results

@app.route('/')
def index():
    # US Market Tickers
    us_tickers = ["VOO", "QQQ", "IWM", "DIA"]
    
    # Global Macro Tickers
    macro_tickers = ["EWJ", "EWY", "EWG", "INDA", "MCHI", "EWU", "EWZ", "EWW", "EWQ", "FXI", "EWH"]
    
    # Thematic Sectors (All added back!)
    sector_tickers = [
        "SMH", "MAGS", "RSP", "CIBR", "AIQ", "BOTZ", "LIT", "XOP", "GLD", 
        "KRE", "ARKK", "ITA", "XLE", "IYZ", "XLP", "XLY", "IGV", "UFO"
    ]
    
    return render_template('index.html', 
                           us_data=get_stats(us_tickers), 
                           macro_data=get_stats(macro_tickers),
                           sector_data=get_stats(sector_tickers))

if __name__ == '__main__':
    app.run(debug=True)