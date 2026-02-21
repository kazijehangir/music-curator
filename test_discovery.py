import asyncio
from src.services.discover import run_discovery

def run():
    print("Testing internal discovery logic directly...")
    result = run_discovery()
    print("Result:", result)

if __name__ == "__main__":
    run()
