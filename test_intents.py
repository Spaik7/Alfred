#!/usr/bin/env python3
"""Quick test script for intents without full alfred.py"""
from intents import parse_intent
import json

print("="*60)
print("Alfred Intent Parser - Debug Mode")
print("="*60)
print("Type commands to test intent parsing. Type 'quit' to exit.\n")

while True:
    try:
        command = input("You: ").strip()
        if not command:
            continue
        if command.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break
        
        result = parse_intent(command)
        print(f"\n📋 Intent: {result['intent']}")
        print(f"🌍 Language: {result['language']}")
        print(f"✅ Confidence: {result['confidence']}")
        if result['parameters']:
            print(f"📦 Parameters: {json.dumps(result['parameters'], indent=2)}")
        print(f"🔐 Requires PIN: {result['requires_pin']}")
        print()
        
    except KeyboardInterrupt:
        print("\nGoodbye!")
        break
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
