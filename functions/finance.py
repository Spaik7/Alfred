#!/usr/bin/env python3
"""
Finance Functions for Alfred - Stocks and Cryptocurrency
Using free APIs: Yahoo Finance Alternative and CoinGecko
"""

import requests
from typing import Optional

def get_stock_price(symbol: str) -> dict:
    """
    Get current stock price using free API

    Args:
        symbol: Stock symbol (e.g., "AAPL", "GOOGL", "TSLA")

    Returns:
        dict with stock information
    """
    try:
        # Using Twelve Data free API (no key needed for basic quotes)
        # Alternative: Alpha Vantage (requires free API key)
        response = requests.get(
            f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}",
            params={"interval": "1d", "range": "1d"},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()

            if "chart" in data and "result" in data["chart"] and data["chart"]["result"]:
                result = data["chart"]["result"][0]
                meta = result["meta"]
                quote = result["indicators"]["quote"][0]

                current_price = meta.get("regularMarketPrice")
                previous_close = meta.get("previousClose")

                if current_price and previous_close:
                    change = current_price - previous_close
                    change_percent = (change / previous_close) * 100

                    return {
                        "success": True,
                        "symbol": symbol.upper(),
                        "name": meta.get("longName", symbol),
                        "price": round(current_price, 2),
                        "currency": meta.get("currency", "USD"),
                        "previous_close": round(previous_close, 2),
                        "change": round(change, 2),
                        "change_percent": round(change_percent, 2),
                        "market_state": meta.get("marketState", "REGULAR")
                    }

        return {
            "success": False,
            "error": f"Could not fetch data for {symbol}"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def get_crypto_price(coin_id: str = "bitcoin") -> dict:
    """
    Get cryptocurrency price using CoinGecko API (free, no key needed)

    Args:
        coin_id: Coin ID (e.g., "bitcoin", "ethereum", "cardano")

    Returns:
        dict with crypto information
    """
    try:
        response = requests.get(
            f"https://api.coingecko.com/api/v3/simple/price",
            params={
                "ids": coin_id,
                "vs_currencies": "usd,eur",
                "include_24hr_change": "true",
                "include_market_cap": "true"
            },
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()

            if coin_id in data:
                coin_data = data[coin_id]

                return {
                    "success": True,
                    "coin_id": coin_id,
                    "price_usd": coin_data.get("usd"),
                    "price_eur": coin_data.get("eur"),
                    "change_24h": round(coin_data.get("usd_24h_change", 0), 2),
                    "market_cap_usd": coin_data.get("usd_market_cap")
                }

        return {
            "success": False,
            "error": f"Could not fetch data for {coin_id}"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def get_multiple_crypto_prices(coin_ids: list) -> dict:
    """
    Get multiple cryptocurrency prices at once

    Args:
        coin_ids: List of coin IDs (e.g., ["bitcoin", "ethereum"])

    Returns:
        dict with multiple crypto prices
    """
    try:
        coins_param = ",".join(coin_ids)

        response = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={
                "ids": coins_param,
                "vs_currencies": "usd",
                "include_24hr_change": "true"
            },
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()

            results = {}
            for coin_id in coin_ids:
                if coin_id in data:
                    results[coin_id] = {
                        "price_usd": data[coin_id].get("usd"),
                        "change_24h": round(data[coin_id].get("usd_24h_change", 0), 2)
                    }

            return {
                "success": True,
                "prices": results
            }

        return {
            "success": False,
            "error": "Could not fetch crypto prices"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def convert_currency(amount: float, from_currency: str = "USD", to_currency: str = "EUR") -> dict:
    """
    Convert currency using free exchange rate API

    Args:
        amount: Amount to convert
        from_currency: Source currency code
        to_currency: Target currency code

    Returns:
        dict with conversion result
    """
    try:
        # Using exchangerate-api.com (free tier: 1500 requests/month)
        response = requests.get(
            f"https://api.exchangerate-api.com/v4/latest/{from_currency.upper()}",
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()

            if to_currency.upper() in data["rates"]:
                rate = data["rates"][to_currency.upper()]
                converted_amount = amount * rate

                return {
                    "success": True,
                    "amount": amount,
                    "from_currency": from_currency.upper(),
                    "to_currency": to_currency.upper(),
                    "exchange_rate": round(rate, 4),
                    "converted_amount": round(converted_amount, 2)
                }

        return {
            "success": False,
            "error": "Currency conversion failed"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


if __name__ == '__main__':
    # Test functions
    print("Finance Functions Test\n" + "="*50)

    print("\n1. Stock Price (AAPL):")
    stock = get_stock_price("AAPL")
    if stock["success"]:
        print(f"   {stock['name']} ({stock['symbol']})")
        print(f"   Price: ${stock['price']} {stock['currency']}")
        print(f"   Change: ${stock['change']} ({stock['change_percent']}%)")

    print("\n2. Crypto Price (Bitcoin):")
    crypto = get_crypto_price("bitcoin")
    if crypto["success"]:
        print(f"   Bitcoin")
        print(f"   Price: ${crypto['price_usd']} USD / €{crypto['price_eur']} EUR")
        print(f"   24h Change: {crypto['change_24h']}%")

    print("\n3. Multiple Cryptos:")
    cryptos = get_multiple_crypto_prices(["bitcoin", "ethereum"])
    if cryptos["success"]:
        for coin, data in cryptos["prices"].items():
            print(f"   {coin}: ${data['price_usd']} ({data['change_24h']}%)")

    print("\n4. Currency Conversion (100 USD to EUR):")
    conversion = convert_currency(100, "USD", "EUR")
    if conversion["success"]:
        print(f"   {conversion['amount']} {conversion['from_currency']} = {conversion['converted_amount']} {conversion['to_currency']}")
        print(f"   Exchange Rate: {conversion['exchange_rate']}")
