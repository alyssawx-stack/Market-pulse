from flask import Flask, render_template
import yfinance as yf
import pandas_ta as ta
import pandas as pd
from datetime import datetime
import time

app = Flask(__name__)

# Full mapping for all your tickers (kept for when you want to add them back)
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

def get_stats(tickers):
    results = []
    for ticker in tickers:
        try:
            # 1y period is optimal for Render's free memory limit
            df = yf.download(ticker, period="1y", interval="1d", progress=False, auto_adjust=True)
            
            if df.empty or len(df) < 200:
                continue
            
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            # Technical Indicators
            df['RSI'] = ta.rsi(df['Close'], length=14)
            df['MA20'] = ta.sma(df['Close'], length=20)
            df['MA50'] = ta.sma(df['Close'], length=50)
            df['MA200'] = ta.sma(df['Close'], length=200)

            latest = df.iloc[-1]
            price = float(latest['Close'])
            
            # Daily % Change
            prev_close = df['Close'].iloc[-2]
            daily_change = ((price - prev_close) / prev_close) * 100
            
            # 5-Day % Change
            five_days_ago_close = df['Close'].iloc[-6] if len(df) > 6 else df['Close'].iloc[0]
            five_day_change = ((price - five_days_ago_close) / five_days_ago_close) * 100
            
            # YTD % Change
            current_year = datetime.now().year
            year_start_data = df[df.index >= f"{current_year}-01-01"]
            first_price_of_year = year_start_data['Close'].iloc[0] if not year_start_data.empty else df['Close'].iloc[0]
            ytd_change = ((price - first_price_of_year) / first_price_of_year) * 100
            
            high_52 = df['High'].max()
            low_52 = df['Low'].min()
            
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
                "range_52": f"{round(low_52, 2)} - {round(high_52, 2)}",
                "rsi": round(rsi_val, 1),
                "status": status,
                "ma20": "Y" if price > float(latest['MA20']) else "N",
                "ma50": "Y" if price > float(latest['MA50']) else "N",
                "ma200": "Y" if price > float(latest['MA200']) else "N"
            })
            time.sleep(0.5) # Prevents hitting the API too hard/fast
        except Exception as e:
            print(f"Error fetching {ticker}: {e}")
            continue
    return results

@app.route('/')
def index():
    # STARTING SMALL: We only load 8 total tickers to ensure the 512MB RAM isn't exceeded.
    # Once this works and is stable, you can add your thematic sectors back here!
    us_tickers = ["VOO", "QQQ", "IWM", "DIA"]
    macro_tickers = ["EWJ", "EWY", "EWG", "MCHI"]
    sector_tickers = [] 
    
    return render_template('index.html', 
                           us_data=get_stats(us_tickers), 
                           macro_data=get_stats(macro_tickers),
                           sector_data=get_stats(sector_tickers))

if __name__ == '__main__':
    app.run(debug=True)