"""Compatibility wrapper for the reference-state reset command."""

import asyncio

from reset_demo_state import reset_demo_state


if __name__ == "__main__":
    asyncio.run(reset_demo_state())
