"""
DEPRECATED MODULE
-----------------
This file exists only for backward compatibility.

All logic is delegated to memory.py.
DO NOT add new logic here.
"""

from memory import SupabaseMemory  # Re-export hardened implementation

__all__ = ["SupabaseMemory"]