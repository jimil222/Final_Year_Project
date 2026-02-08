"""
Use when adding a new book: run this, then tap the book's NFC tag.
The UID is sent to POST /nfc/scan so the Add Book form (polling GET /nfc/last-scan) can fill the NFC ID field.
"""
import os
import time
import board
import busio
from adafruit_pn532.i2c import PN532_I2C

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000").rstrip("/")
NFC_SCAN_URL = f"{BACKEND_URL}/nfc/scan"

try:
    import requests
except ImportError:
    requests = None


def send_scan(uid_hex: str) -> None:
    if not requests:
        print("Install 'requests': pip install requests")
        return
    try:
        r = requests.post(
            NFC_SCAN_URL,
            json={"nfc_tag_id": uid_hex},
            timeout=5,
        )
        r.raise_for_status()
        print(f"  -> Scan stored. Use 'Scan NFC' in Add Book form to fill the field.")
    except requests.exceptions.RequestException as e:
        if hasattr(e, "response") and e.response is not None:
            try:
                err = e.response.json()
                detail = err.get("detail", e.response.text)
            except Exception:
                detail = e.response.text
            print(f"  -> Error: {detail}")
        else:
            print(f"  -> Error: {e}")


def main():
    i2c = busio.I2C(board.SCL, board.SDA)
    pn532 = PN532_I2C(i2c)
    pn532.SAM_configuration()

    print("Scan-for-registration mode. Tap the book's NFC tag (Add Book form should be open).")
    print(f"Backend: {BACKEND_URL}")
    print()
    if not requests:
        print("(install requests to send to backend)")
    last_uid = None
    while True:
        uid = pn532.read_passive_target(timeout=0.5)
        if uid and uid != last_uid:
            uid_hex = "".join([format(b, "02X") for b in uid])
            print(f"UID: {uid_hex}")
            send_scan(uid_hex)
            last_uid = uid
            time.sleep(1)


if __name__ == "__main__":
    main()
