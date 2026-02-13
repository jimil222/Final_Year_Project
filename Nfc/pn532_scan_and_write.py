"""
DEPRECATED: NFC write functionality.

This script previously implemented "Scan NFC & Write" to store the book name on the tag.
The project has been simplified to use ONLY the tag UID (no writing book names).

Now the always-on daemon `nfc_daemon.py` handles:
- Student issue/return
- Status lookups
- Add Book "Scan Tag" (via /nfc/scan)

If you run this script it will just print a message and exit.
"""
import os
import time
def main():
    print("NFC write flow is disabled.")
    print("Use nfc_daemon.py (always-on) for:")
    print("- Student issue/return")
    print("- Status lookups")
    print("- Add Book → Scan Tag (admin panel)")


if __name__ == "__main__":
    main()
