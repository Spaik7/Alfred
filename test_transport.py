#!/usr/bin/env python3
"""
Test script for transport functionality (car and public transit)
Run this on the Pi: python3 test_transport.py
"""

from functions import transport

print('=' * 60)
print('TRANSPORT TEST')
print('=' * 60)

# Test 1: Car/Traffic to Milan
print('\n1. Testing car traffic to Milan...')
result = transport.get_traffic_status(None, "Milan, Italy")
if result['success']:
    print(f'   ✅ Success!')
    print(f'      Duration: {result["duration_text"]}')
    print(f'      Distance: {result["distance_text"]}')
    print(f'      Traffic delay: {result["delay_minutes"]} minutes')
else:
    print(f'   ❌ Error: {result.get("error", "Unknown error")}')

# Test 2: Car/Traffic to Turin
print('\n2. Testing car traffic to Turin...')
result = transport.get_traffic_status(None, "Turin, Italy")
if result['success']:
    print(f'   ✅ Success!')
    print(f'      Duration: {result["duration_text"]}')
    print(f'      Distance: {result["distance_text"]}')
    print(f'      Traffic delay: {result["delay_minutes"]} minutes')
else:
    print(f'   ❌ Error: {result.get("error", "Unknown error")}')

# Test 3: Public transit to Milan
print('\n3. Testing public transit to Milan...')
result = transport.get_public_transit(None, "Milan, Italy")
if result['success']:
    print(f'   ✅ Success!')
    print(f'      Duration: {result["duration_text"]}')
    print(f'      Distance: {result["distance_text"]}')

    # Count transfers
    steps = result['steps']
    transit_count = sum(1 for s in steps if s.get('travel_mode') == 'TRANSIT')
    if transit_count > 1:
        transfers = transit_count - 1
        print(f'      Transfers: {transfers}')
    else:
        print(f'      Transfers: 0')

    # Show first transit line
    for step in steps:
        if step.get('travel_mode') == 'TRANSIT':
            transit = step.get('transit_details', {})
            line = transit.get('line', {}).get('short_name', 'Unknown')
            print(f'      First line: {line}')
            break
else:
    print(f'   ❌ Error: {result.get("error", "Unknown error")}')

# Test 4: Public transit to Turin
print('\n4. Testing public transit to Turin...')
result = transport.get_public_transit(None, "Turin, Italy")
if result['success']:
    print(f'   ✅ Success!')
    print(f'      Duration: {result["duration_text"]}')
    print(f'      Distance: {result["distance_text"]}')

    # Count transfers
    steps = result['steps']
    transit_count = sum(1 for s in steps if s.get('travel_mode') == 'TRANSIT')
    if transit_count > 1:
        transfers = transit_count - 1
        print(f'      Transfers: {transfers}')
    else:
        print(f'      Transfers: 0')

    # Show first transit line
    for step in steps:
        if step.get('travel_mode') == 'TRANSIT':
            transit = step.get('transit_details', {})
            line = transit.get('line', {}).get('short_name', 'Unknown')
            print(f'      First line: {line}')
            break
else:
    print(f'   ❌ Error: {result.get("error", "Unknown error")}')

print('\n' + '=' * 60)
