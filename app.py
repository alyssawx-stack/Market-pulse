from flask import Flask, render_template
import yfinance as yf
import pandas_ta as ta
import pandas as pd
from datetime import datetime
import time  # Necessary for the small delay between fetches

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
            # Using 1y instead of 2y to stay within Render's memory limits
            df = yf.download(ticker, period="1y", interval="1d", progress=False, auto_adjust=True)
            
            if df.empty:
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
            first_price_of_year = year_start_data['Close