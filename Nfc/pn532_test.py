"""
NFC reader (always on): on book tap, POST UID to backend.
Backend decides: RESERVED → issue, BORROWED → return (no login).

Same tag can be scanned again after SAME_TAG_COOLDOWN_SECONDS so that after borrowing,
the user can return the same book by tapping again (backend enforces MIN_RETURN_TIME).
"""
import os
import time
import board
import busio
from adafruit_pn532.i2c import PN532_I2C

# Backend URL (e.g. http://localhost:8000 or http://<server-ip>:8000)
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000").rstrip("/")
NFC_TAP_URL = f"{BACKEND_URL}/nfc/tap"
# Same UID can be sent again after this many seconds (allows return after borrow with same tag).
SAME_TAG_COOLDOWN_SECONDS = float(os.environ.get("SAME_TAG_COOLDOWN_SECONDS", "3"))

try:
    import requests
except ImportError:
    requests = None


def send_tap(uid_hex: str) -> None:
    if not requests:
        print("Install 'requests' to send to backend: pip install requests")
        return
    try:
        r = requests.post(
            NFC_TAP_URL,
            json={"nfc_tag_id": uid_hex},
            timeout=5,
        )
        r.raise_for_status()
        data = r.json()
        action = data.get("action", "?")
        msg = data.get("message", "")
        book = data.get("book_name", "")
        student = data.get("student_name", "")
        print(f"  -> {action.upper()}: {msg} | Book: {book} | Student: {student}")
    except requests.exceptions.RequestException as e:
        if hasattr(e, "response") and e.response is not None:
            try:
                err = e.response.json()
                detail = err.get("detail", e.response.text)
            except Exception:
                detail = e.response.text
            if e.response.status_code == 404 and "Book not found" in str(detail):
                print(f"  -> (New book?) Scan saved for Add Book. Use 'Scan NFC' in the web app to capture this UID.")
            else:
                print(f"  -> Error: {detail}")
        else:
            print(f"  -> Error: {e}")


def main():
    i2c = busio.I2C(board.SCL, board.SDA)
    pn532 = PN532_I2C(i2c)
    pn532.SAM_configuration()

    print("NFC reader ready. Tap a book on the reader.")
    print(f"Backend: {BACKEND_URL}")
    if not requests:
        print("(requests not installed; UID will only be printed)")
    print()

    last_uid = None
    last_uid_time = None

    while True:
        uid = pn532.read_passive_target(timeout=0.5)
        if not uid:
            continue
        now = time.time()
        is_new_scan = (
            uid != last_uid
            or (last_uid_time is not None and (now - last_uid_time) >= SAME_TAG_COOLDOWN_SECONDS)
        )
        if is_new_scan:
            uid_hex = "".join([format(b, "02X") for b in uid])
            print(f"UID: {uid_hex}")
            send_tap(uid_hex)
            last_uid = uid
            last_uid_time = now
            time.sleep(1)


if __name__ == "__main__":
    main()
