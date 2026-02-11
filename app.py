from flask import Flask, render_template
import yfinance as yf
import pandas_ta as ta
import pandas as pd
from datetime import datetime

app = Flask(__name__)

# Mapping tickers to descriptive names
TICKER_NAMES = {
    # US Market
    "VOO": "S&P 500 ETF", "QQQ": "Nasdaq 100", "IWM": "Russell 2000", "DIA": "Dow Jones Industrials",
    
    # Global Macro
    "EWJ": "MSCI Japan", "EWY": "MSCI South Korea", "EWG": "MSCI Germany", "INDA": "MSCI India",
    "MCHI": "MSCI China", "EWU": "MSCI United Kingdom", "EWZ": "MSCI Brazil", "EWW": "MSCI Mexico",
    "EWQ": "MSCI France", "FXI": "China Large-Cap", "EWH": "MSCI Hong Kong",
    
    # Thematic & Industry Sectors
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
            # Download 2 years of data for 52-week high/low and YTD calculations
            df = yf.download(ticker, period="2y", interval="1d", progress=False, auto_adjust=True)
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
            five_days_ago_close = df['Close'].iloc[-6]
            five_day_change = ((price - five_days_ago_close) / five_days_ago_close) * 100
            
            # YTD % Change
            current_year = datetime.now().year
            year_start_data = df[df.index >= f"{current_year}-01-01"]
            first_price_of_year = year_start_data['Close'].iloc[0]
            ytd_change = ((price - first_price_of_year) / first_price_of_year) * 100
            
            # 52-Week High/Low
            last_year_data = df.iloc[-252:]
            high_52 = last_year_data['High'].max()
            low_52 = last_year_data['Low'].min()
            
            rsi_val = float(latest['RSI'])
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
        except Exception as e:
            print(f"Error fetching {ticker}: {e}")
            continue
    return results

@app.route('/')
def index():
    # US Market Tickers
    us_tickers = ["VOO", "QQQ", "IWM", "DIA"]
    
    # Global Macro Tickers (Includes EWH)
    macro_tickers = ["EWJ", "EWY", "EWG", "INDA", "MCHI", "EWU", "EWZ", "EWW", "EWQ", "FXI", "EWH"]
    
    # Thematic & Industry Sectors
    sector_tickers = [
        "SMH", "MAGS", "RSP", "CIBR", "AIQ", "BOTZ", "LIT", "XOP", "GLD", "KRE", "ARKK",
        "ITA", "XLE", "IYZ", "XLP", "XLY", "IGV", "UFO"
    ]
    
    return render_template('index.html', 
                           us_data=get_stats(us_tickers), 
                           macro_data=get_stats(macro_tickers),
                           sector_data=get_stats(sector_tickers))

if __name__ == '__main__':
    app.run(debug=True)