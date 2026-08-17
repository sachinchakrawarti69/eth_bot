# ============================================================
# Deribit API
# ============================================================

BASE_URL = "https://www.deribit.com/api/v2"

GET_INSTRUMENTS = "/public/get_instruments"

GET_BOOK_SUMMARY = "/public/get_book_summary_by_instrument"

CURRENCY = "ETH"


def get_instruments_url():
    return BASE_URL + GET_INSTRUMENTS


def get_book_summary_url():
    return BASE_URL + GET_BOOK_SUMMARY

GET_ORDER_BOOK = "/public/get_order_book"


def get_order_book_url():
    return BASE_URL + GET_ORDER_BOOK