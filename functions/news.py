#!/usr/bin/env python3
"""
News Functions for Alfred - Using NewsAPI
Get your free API key at: https://newsapi.org/
"""

import requests
from typing import Optional
import sys
from pathlib import Path

# Import from config.py
try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config import NEWS_API_KEY, NEWS_DEFAULT_COUNTRIES
except ImportError:
    NEWS_API_KEY = None
    NEWS_DEFAULT_COUNTRIES = ["it", "us"]

def get_top_headlines(country: str = "us", category: Optional[str] = None, count: int = 5) -> dict:
    """
    Get top news headlines

    Args:
        country: Country code (us, gb, it, etc.)
        category: Category (business, entertainment, health, science, sports, technology)
        count: Number of articles to return (max 100)

    Returns:
        dict with news articles
    """
    if not NEWS_API_KEY:
        return {
            "success": False,
            "error": "NewsAPI key not configured. Get one at https://newsapi.org/"
        }

    try:
        params = {
            "apiKey": NEWS_API_KEY,
            "country": country,
            "pageSize": min(count, 100)
        }

        if category:
            params["category"] = category

        response = requests.get(
            "https://newsapi.org/v2/top-headlines",
            params=params,
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()

            if data["status"] == "ok":
                articles = []
                for article in data.get("articles", []):
                    articles.append({
                        "title": article.get("title"),
                        "description": article.get("description"),
                        "source": article.get("source", {}).get("name"),
                        "author": article.get("author"),
                        "url": article.get("url"),
                        "published_at": article.get("publishedAt")
                    })

                return {
                    "success": True,
                    "total_results": data.get("totalResults", 0),
                    "articles": articles
                }
            else:
                return {
                    "success": False,
                    "error": data.get("message", "API error")
                }
        else:
            return {
                "success": False,
                "error": f"HTTP {response.status_code}"
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def search_news(query: str, language: str = "en", count: int = 5) -> dict:
    """
    Search for news articles

    Args:
        query: Search query
        language: Language code (en, it, etc.)
        count: Number of articles to return

    Returns:
        dict with search results
    """
    if not NEWS_API_KEY:
        return {
            "success": False,
            "error": "NewsAPI key not configured"
        }

    try:
        response = requests.get(
            "https://newsapi.org/v2/everything",
            params={
                "apiKey": NEWS_API_KEY,
                "q": query,
                "language": language,
                "pageSize": min(count, 100),
                "sortBy": "publishedAt"
            },
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()

            if data["status"] == "ok":
                articles = []
                for article in data.get("articles", []):
                    articles.append({
                        "title": article.get("title"),
                        "description": article.get("description"),
                        "source": article.get("source", {}).get("name"),
                        "url": article.get("url"),
                        "published_at": article.get("publishedAt")
                    })

                return {
                    "success": True,
                    "total_results": data.get("totalResults", 0),
                    "articles": articles
                }
            else:
                return {
                    "success": False,
                    "error": data.get("message", "API error")
                }
        else:
            return {
                "success": False,
                "error": f"HTTP {response.status_code}"
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def get_multi_country_headlines(countries: list = None, category: Optional[str] = None, count_per_country: int = 3) -> dict:
    """
    Get top headlines from multiple countries

    Args:
        countries: List of country codes (default: from config, ["it", "us"])
        category: Category filter (optional)
        count_per_country: Number of articles per country

    Returns:
        dict with combined news from all countries
    """
    if countries is None:
        countries = NEWS_DEFAULT_COUNTRIES

    if not NEWS_API_KEY:
        return {
            "success": False,
            "error": "NewsAPI key not configured"
        }

    all_articles = []
    total_results = 0

    for country in countries:
        result = get_top_headlines(country, category, count_per_country)
        if result["success"]:
            # Add country tag to each article
            for article in result["articles"]:
                article["country"] = country.upper()
            all_articles.extend(result["articles"])
            total_results += result["total_results"]

    if all_articles:
        return {
            "success": True,
            "countries": countries,
            "total_results": total_results,
            "articles": all_articles
        }
    else:
        return {
            "success": False,
            "error": "Could not fetch news from any country"
        }


if __name__ == '__main__':
    # Test functions
    print("News Functions Test\n" + "="*50)

    if not NEWS_API_KEY:
        print("\nNEWS_API_KEY not set!")
        print("Get your free API key at: https://newsapi.org/")
        print("Then set it: export NEWS_API_KEY='your_key_here'")
    else:
        print("\n1. Top Headlines (US):")
        news = get_top_headlines("us", count=3)
        if news["success"]:
            for i, article in enumerate(news["articles"], 1):
                print(f"\n   {i}. {article['title']}")
                print(f"      Source: {article['source']}")

        print("\n2. Technology News:")
        tech_news = get_top_headlines("us", category="technology", count=3)
        if tech_news["success"]:
            for i, article in enumerate(tech_news["articles"], 1):
                print(f"\n   {i}. {article['title']}")

        print("\n3. Search News:")
        search = search_news("artificial intelligence", count=2)
        if search["success"]:
            for i, article in enumerate(search["articles"], 1):
                print(f"\n   {i}. {article['title']}")
