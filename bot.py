from utils import lookup_country_by_code, find_country_in_message
from database import cursor
import re

def get_bot_response(message: str) -> str:
    msg = message.strip().lower()
    found_country = None

    # Try to detect country code
    m = re.search(r"\+?(\d{1,3})", msg)
    if m: found_country = lookup_country_by_code(m.group(1))

    # Try to detect country name if code not found
    if not found_country: 
        found_country = find_country_in_message(msg)
    if not found_country: 
        return "Specify a valid country name or country code."

    # Fetch records
    cursor.execute("SELECT * FROM ccrate WHERE country=%s ORDER BY addedTime DESC", (found_country,))
    records = cursor.fetchall()
    if not records: return f"No records found for {found_country}."

    # Build table
    header = f"{'Country':<10} | {'QualityDescription':<35} | {'Profile':<10} | {'BillingCycle':<12} | {'Rate':<5} | {'Status':<7}"
    lines = [header, "-"*len(header)]
    for r in records:
        lines.append(f"{r.get('country',''):<10} | {r.get('qualityDescription',''):<35} | {r.get('profile',''):<10} | {r.get('billingCycle',''):<12} | {r.get('rate',''):<5} | {r.get('status',''):<7}")
    return "\n".join(lines)
