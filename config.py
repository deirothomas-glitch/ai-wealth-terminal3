"""Configuration centrale de l'AI Wealth Terminal."""

APP_NAME = "AI Wealth Terminal"
APP_VERSION = "2.1.0"
CACHE_TTL = 300
DEFAULT_PERIOD = "6mo"
AVAILABLE_PERIODS = ["5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "max"]
AI_DEFAULT_MODEL = "gpt-5.6"
AI_TIMEOUT = 30.0
NEWS_CACHE_TTL = 900
MAX_AI_MESSAGES = 10
MAX_AI_QUESTION_LENGTH = 1000
MAX_NEWS = 5

MARKET_INDICES = {
    "S&P 500": "^GSPC", "NASDAQ": "^IXIC", "Dow Jones": "^DJI",
    "CAC 40": "^FCHI", "DAX": "^GDAXI", "FTSE 100": "^FTSE",
}
CRYPTO_ASSETS = {
    "Bitcoin": "BTC-USD", "Ethereum": "ETH-USD", "Solana": "SOL-USD",
    "BNB": "BNB-USD", "XRP": "XRP-USD",
}
DEFAULT_WATCHLIST = {
    "Actions": ["AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "TSLA"],
    "Cryptomonnaies": ["BTC-USD", "ETH-USD", "SOL-USD"],
    "ETF": ["SPY", "QQQ"],
}
