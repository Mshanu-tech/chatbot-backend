import re
from database import cursor

def lookup_country_by_code(code: str) -> str | None:
    cursor.execute(
        "SELECT DISTINCT country FROM ccrate WHERE countryCode IN (%s,%s)", 
        (f"+{code}", code)
    )
    rows = cursor.fetchall()
    return rows[0]["country"] if rows else None

def find_country_in_message(msg_lower: str) -> str | None:
    cursor.execute("SELECT DISTINCT country FROM ccrate")
    for c in [r["country"] for r in cursor.fetchall()]:
        if c.lower() in msg_lower:
            return c
    return None
