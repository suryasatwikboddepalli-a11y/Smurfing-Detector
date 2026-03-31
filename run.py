#!/usr/bin/env python
"""
Smurfing Hunter - Entry Point
Wrapper script to run the money laundering detection system
"""

import sys
import os

# Add src to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

try:
    from smurfing_hunter.core.smurfing_hunter import main
except ImportError as e:
    print(f"Error importing smurfing_hunter: {e}")
    print("Ensure you are running this script from the project root directory.")
    sys.exit(1)

if __name__ == "__main__":
    main()
