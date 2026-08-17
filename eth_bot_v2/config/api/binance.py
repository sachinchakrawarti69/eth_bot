# ============================================================
# Binance API Configuration
# ============================================================

BASE_URL = "https://api.binance.com"

KLINES_ENDPOINT = "/api/v3/klines"

DEFAULT_SYMBOL = "ETHUSDT"
DEFAULT_INTERVAL = "1d"
DEFAULT_LIMIT = 1000

ORDERBOOK_ENDPOINT = "/api/v3/depth"

DEFAULT_ORDERBOOK_LIMIT = 100


def get_klines_url():
    return BASE_URL + KLINES_ENDPOINT


    # ============================================================
# Open Interest
# ============================================================

FUTURES_BASE_URL = "https://fapi.binance.com"

OPEN_INTEREST_ENDPOINT = "/fapi/v1/openInterest"

DEFAULT_SYMBOL = "ETHUSDT"


def get_open_interest_url():
    return FUTURES_BASE_URL + OPEN_INTEREST_ENDPOINT




    # ============================================================
# Funding Rate
# ============================================================

FUNDING_RATE_ENDPOINT = "/fapi/v1/fundingRate"


def get_funding_rate_url():
    return FUTURES_BASE_URL + FUNDING_RATE_ENDPOINT


# ============================================================
# Recent Trades
# ============================================================

TRADES_ENDPOINT = "/api/v3/trades"

DEFAULT_TRADES_LIMIT = 1000


def get_trades_url():
    return BASE_URL + TRADES_ENDPOINT


# ============================================================
# Liquidations (Force Orders)
# ============================================================

FORCE_ORDERS_ENDPOINT = "/dapi/v1/forceOrders"

DEFAULT_LIMIT = 100


def get_force_orders_url():
    return "https://dapi.binance.com" + FORCE_ORDERS_ENDPOINT