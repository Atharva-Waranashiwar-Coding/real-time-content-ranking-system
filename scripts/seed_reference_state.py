"""Compatibility wrapper for the reference-state seed command."""

import asyncio

from seed_demo_state import seed_demo_state


if __name__ == "__main__":
    asyncio.run(seed_demo_state())
