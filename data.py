import yfinance as yf
def get_stock_history(symbol, period="1mo"):
    ticker = yf.Ticker(symbol)
    return ticker.history(period=period)    

def get_stock_info(symbol):
    ticker = yf.Ticker(symbol)
    return ticker.info 
