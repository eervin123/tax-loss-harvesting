import yfinance as yf
import pandas as pd

# Data Download and Preparation
eth = yf.download("ETH-USD", period="5y", interval="1d", auto_adjust=True)
eth.to_csv("ETH-daily.csv")

spy = yf.download("SPY", period="5y", interval="1d", auto_adjust=True)
spy.to_csv("SPY-daily.csv")

btc = yf.download("BTC-USD", period="5y", interval="1d", auto_adjust=True)
btc.to_csv("BTC-daily.csv")