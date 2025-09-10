#!/usr/bin/env python3
import asyncio
import statistics
import time

import aiohttp


async def test_endpoint(session, url):
    start = time.time()
    try:
        async with session.get(url) as response:
            await response.text()
            return time.time() - start, response.status
    except Exception:
        return time.time() - start, 0


async def run_load_test(base_url="http://localhost:8000", num_requests=100):
    print(f"Running load test: {num_requests} requests")

    async with aiohttp.ClientSession() as session:
        # Test health endpoint
        tasks = [
            test_endpoint(session, f"{base_url}/health") for _ in range(num_requests)
        ]
        results = await asyncio.gather(*tasks)

        # Analyze results
        durations = [r[0] for r in results if r[1] == 200]
        failures = [r for r in results if r[1] != 200]

        print("\nResults:")
        print(f"Successful: {len(durations)}")
        print(f"Failed: {len(failures)}")
        if durations:
            print(f"Avg response time: {statistics.mean(durations):.3f}s")
            print(f"Min: {min(durations):.3f}s")
            print(f"Max: {max(durations):.3f}s")
            print(f"P95: {sorted(durations)[int(len(durations) * 0.95)]:.3f}s")


if __name__ == "__main__":
    asyncio.run(run_load_test())
