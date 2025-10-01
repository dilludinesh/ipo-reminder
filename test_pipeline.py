#!/usr/bin/env python3
"""Test the full IPO reminder pipeline with company name fixes."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import date
from ipo_reminder.sources.zerodha import get_zerodha_ipos_closing_today
from ipo_reminder.sources.chittorgarh import IPOInfo

def test_full_pipeline():
    """Test the full pipeline from Zerodha to email format."""
    print("🧪 Testing full IPO reminder pipeline...")

    # Use today's date
    today = date.today()
    print(f"📅 Testing with date: {today}")

    try:
        # Get IPOs from Zerodha
        zerodha_ipos = get_zerodha_ipos_closing_today(today)

        if not zerodha_ipos:
            print("ℹ️  No IPOs found closing today")
            return

        print(f"✅ Found {len(zerodha_ipos)} IPO(s) from Zerodha")

        # Convert to IPOInfo format (like the main system does)
        ipos = []
        for z_ipo in zerodha_ipos:
            ipo = IPOInfo(
                name=z_ipo.name,
                detail_url=None,
                gmp_url=None,
                open_date=z_ipo.open_date,
                close_date=z_ipo.close_date,
                price_band=z_ipo.price_range,
                lot_size=None,
                recommendation=f"IPO closes today - Listing on {z_ipo.listing_date}"
            )
            ipos.append(ipo)

        # Format like the email system would
        from ipo_reminder.ipo_categorizer import format_personal_guide_email

        subject, body, html_body = format_personal_guide_email(today, ipos)

        print("\n📧 Email Preview:")
        print(f"Subject: {subject}")
        print(f"Body:\n{body}")

        # Check for proper company names
        problematic_names = []
        for ipo in ipos:
            name = ipo.name or ""
            if name and (name[0].islower() or any(char.isdigit() for char in name[:5])):
                problematic_names.append(name)

        if problematic_names:
            print(f"\n⚠️  Found potentially problematic names: {problematic_names}")
        else:
            print("\n✅ All company names appear properly formatted!")

        return True

    except Exception as e:
        print(f"❌ Error in pipeline test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_full_pipeline()
    if success:
        print("\n🎉 Pipeline test completed successfully!")
    else:
        print("\n❌ Pipeline test failed!")
