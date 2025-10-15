#!/usr/bin/env python3
"""
Test script for recipe search functionality
Run this on the Pi: python3 test_recipes.py
"""

from functions import food

print('=' * 60)
print('RECIPE SEARCH TEST')
print('=' * 60)

# Test 1: Search for pasta recipes
print('\n1. Searching for pasta recipes...')
result = food.search_recipes('pasta', count=3)
if result['success']:
    print(f'   ✅ Found {len(result["recipes"])} recipes')
    for recipe in result['recipes']:
        print(f'      - {recipe["name"]} ({recipe["area"]})')
else:
    print(f'   ❌ Error: {result.get("error", "Unknown error")}')

# Test 2: Search for chicken recipes
print('\n2. Searching for chicken recipes...')
result = food.search_recipes('chicken', count=3)
if result['success']:
    print(f'   ✅ Found {len(result["recipes"])} recipes')
    for recipe in result['recipes']:
        print(f'      - {recipe["name"]} ({recipe["area"]})')
else:
    print(f'   ❌ Error: {result.get("error", "Unknown error")}')

# Test 3: Random recipe
print('\n3. Getting random recipe...')
result = food.get_random_recipe()
if result['success']:
    recipe = result['recipe']
    print(f'   ✅ Random recipe: {recipe["name"]}')
    print(f'      Area: {recipe["area"]}')
    print(f'      Category: {recipe.get("category", "N/A")}')
else:
    print(f'   ❌ Error: {result.get("error", "Unknown error")}')

print('\n' + '=' * 60)
