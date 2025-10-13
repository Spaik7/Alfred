#!/usr/bin/env python3
"""
Food & Recipe Functions for Alfred
Using TheMealDB (free, no API key needed) and Spoonacular (requires API key)
"""

import requests
import sys
from pathlib import Path
from typing import Optional

# Import from config.py
try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config import SPOONACULAR_API_KEY
except ImportError:
    SPOONACULAR_API_KEY = None

def search_recipes(query: str, count: int = 5) -> dict:
    """
    Search for recipes by name or ingredient using TheMealDB (free)

    Args:
        query: Recipe name or main ingredient
        count: Number of results (Note: TheMealDB doesn't support limiting)

    Returns:
        dict with recipe results
    """
    try:
        # Try TheMealDB first (free, no key needed)
        response = requests.get(
            "https://www.themealdb.com/api/json/v1/1/search.php",
            params={"s": query},
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()

            if data.get("meals"):
                recipes = []
                for meal in data["meals"][:count]:
                    # Extract ingredients
                    ingredients = []
                    for i in range(1, 21):
                        ingredient = meal.get(f"strIngredient{i}")
                        measure = meal.get(f"strMeasure{i}")
                        if ingredient and ingredient.strip():
                            ingredients.append({
                                "ingredient": ingredient,
                                "measure": measure if measure else ""
                            })

                    recipes.append({
                        "id": meal["idMeal"],
                        "name": meal["strMeal"],
                        "category": meal.get("strCategory"),
                        "area": meal.get("strArea"),
                        "instructions": meal.get("strInstructions"),
                        "thumbnail": meal.get("strMealThumb"),
                        "ingredients": ingredients,
                        "youtube": meal.get("strYoutube"),
                        "source": meal.get("strSource")
                    })

                return {
                    "success": True,
                    "query": query,
                    "count": len(recipes),
                    "recipes": recipes
                }
            else:
                return {
                    "success": False,
                    "error": f"No recipes found for '{query}'"
                }

        return {
            "success": False,
            "error": "Failed to fetch recipes"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def get_random_recipe() -> dict:
    """
    Get a random recipe from TheMealDB

    Returns:
        dict with random recipe
    """
    try:
        response = requests.get(
            "https://www.themealdb.com/api/json/v1/1/random.php",
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()

            if data.get("meals"):
                meal = data["meals"][0]

                # Extract ingredients
                ingredients = []
                for i in range(1, 21):
                    ingredient = meal.get(f"strIngredient{i}")
                    measure = meal.get(f"strMeasure{i}")
                    if ingredient and ingredient.strip():
                        ingredients.append({
                            "ingredient": ingredient,
                            "measure": measure if measure else ""
                        })

                return {
                    "success": True,
                    "recipe": {
                        "id": meal["idMeal"],
                        "name": meal["strMeal"],
                        "category": meal.get("strCategory"),
                        "area": meal.get("strArea"),
                        "instructions": meal.get("strInstructions"),
                        "thumbnail": meal.get("strMealThumb"),
                        "ingredients": ingredients,
                        "youtube": meal.get("strYoutube")
                    }
                }

        return {
            "success": False,
            "error": "Failed to fetch random recipe"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def get_recipes_by_ingredient(ingredient: str) -> dict:
    """
    Find recipes by main ingredient

    Args:
        ingredient: Main ingredient (e.g., "chicken", "pasta")

    Returns:
        dict with recipe results
    """
    try:
        response = requests.get(
            "https://www.themealdb.com/api/json/v1/1/filter.php",
            params={"i": ingredient},
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()

            if data.get("meals"):
                recipes = []
                for meal in data["meals"]:
                    recipes.append({
                        "id": meal["idMeal"],
                        "name": meal["strMeal"],
                        "thumbnail": meal.get("strMealThumb")
                    })

                return {
                    "success": True,
                    "ingredient": ingredient,
                    "count": len(recipes),
                    "recipes": recipes
                }
            else:
                return {
                    "success": False,
                    "error": f"No recipes found with {ingredient}"
                }

        return {
            "success": False,
            "error": "Failed to fetch recipes"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def get_recipes_by_category(category: str) -> dict:
    """
    Get recipes by category

    Args:
        category: Category (e.g., "Seafood", "Vegetarian", "Dessert")

    Returns:
        dict with recipe results
    """
    try:
        response = requests.get(
            "https://www.themealdb.com/api/json/v1/1/filter.php",
            params={"c": category},
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()

            if data.get("meals"):
                recipes = []
                for meal in data["meals"]:
                    recipes.append({
                        "id": meal["idMeal"],
                        "name": meal["strMeal"],
                        "thumbnail": meal.get("strMealThumb")
                    })

                return {
                    "success": True,
                    "category": category,
                    "count": len(recipes),
                    "recipes": recipes
                }
            else:
                return {
                    "success": False,
                    "error": f"No recipes found in category {category}"
                }

        return {
            "success": False,
            "error": "Failed to fetch recipes"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


if __name__ == '__main__':
    # Test functions
    print("Food & Recipe Functions Test\n" + "="*50)

    print("\n1. Search Recipes (pasta):")
    recipes = search_recipes("pasta", count=3)
    if recipes["success"]:
        print(f"   Found {recipes['count']} recipes:")
        for i, recipe in enumerate(recipes["recipes"], 1):
            print(f"   {i}. {recipe['name']} ({recipe['area']} {recipe['category']})")
            print(f"      Ingredients: {len(recipe['ingredients'])}")

    print("\n2. Random Recipe:")
    random = get_random_recipe()
    if random["success"]:
        recipe = random["recipe"]
        print(f"   Name: {recipe['name']}")
        print(f"   Category: {recipe['category']} ({recipe['area']})")
        print(f"   Ingredients: {len(recipe['ingredients'])}")

    print("\n3. Recipes by Ingredient (chicken):")
    by_ingredient = get_recipes_by_ingredient("chicken")
    if by_ingredient["success"]:
        print(f"   Found {by_ingredient['count']} recipes with chicken")
        for i, recipe in enumerate(by_ingredient["recipes"][:3], 1):
            print(f"   {i}. {recipe['name']}")

    print("\n4. Recipes by Category (Dessert):")
    by_category = get_recipes_by_category("Dessert")
    if by_category["success"]:
        print(f"   Found {by_category['count']} dessert recipes")
        for i, recipe in enumerate(by_category["recipes"][:3], 1):
            print(f"   {i}. {recipe['name']}")
