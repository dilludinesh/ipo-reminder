#!/usr/bin/env python3
"""Test script to verify Zerodha company name parsing fix."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import date
from ipo_reminder.sources.zerodha import get_zerodha_ipos_closing_today

def test_company_names():
    """Test that company names are properly formatted."""
    print("🧪 Testing Zerodha company name parsing...")

    # Use today's date for testing
    today = date.today()
    print(f"📅 Checking IPOs closing on: {today}")

    try:
        ipos = get_zerodha_ipos_closing_today(today)

        if not ipos:
            print("ℹ️  No IPOs found closing today")
            return

        print(f"✅ Found {len(ipos)} IPO(s) closing today:")
        print()

        for i, ipo in enumerate(ipos, 1):
            print(f"{i}. {ipo.name}")
            print(f"   Symbol: {ipo.symbol or 'N/A'}")
            print(f"   Price Range: {ipo.price_range or 'N/A'}")
            print(f"   Close Date: {ipo.close_date}")
            print()

        # Check for problematic patterns
        problematic_names = []
        for ipo in ipos:
            name_lower = ipo.name.lower()
            # Check for lowercase first letters (indicating incorrect parsing)
            if ipo.name and len(ipo.name) > 0 and ipo.name[0].islower():
                problematic_names.append(ipo.name)

        if problematic_names:
            print("⚠️  Found potentially problematic company names:")
            for name in problematic_names:
                print(f"   - {name}")
        else:
            print("✅ All company names appear properly formatted!")

    except Exception as e:
        print(f"❌ Error testing company names: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_company_names()
