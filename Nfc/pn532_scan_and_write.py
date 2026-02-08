"""
Add Book flow: scan NFC tag → get tagId → backend gives book_name to write → write book name to tag → re-read to verify → post result.

Run this when adding a new book. In the admin panel: fill book name, click "Scan NFC & Write", then tap the tag.
Flow: 1) This script reads UID and POSTs to /nfc/scan. 2) Frontend gets tagId and calls set-pending-write. 3) This script
polls GET /nfc/pending-write; when it gets book_name, writes it to the tag (NTAG2xx user blocks, 4 bytes per block),
re-reads to verify, then POSTs /nfc/write-result. 4) Frontend polls write-result and then saves the book to the DB.

Requires: adafruit-circuitpython-pn532, requests. Use NTAG213/215/216 tags (not Mifare Classic).
"""
import os
import time
from typing import Optional, Tuple
import board
import busio
from adafruit_pn532.i2c import PN532_I2C

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000").rstrip("/")
NFC_SCAN_URL = f"{BACKEND_URL}/nfc/scan"
NFC_PENDING_WRITE_URL = f"{BACKEND_URL}/nfc/pending-write"
NFC_WRITE_RESULT_URL = f"{BACKEND_URL}/nfc/write-result"
SAME_TAG_COOLDOWN_SECONDS = float(os.environ.get("SAME_TAG_COOLDOWN_SECONDS", "3"))
# NTAG2xx user data starts at block 4. Each block is 4 bytes. We use up to 14 blocks (56 bytes) for book name.
NTAG_USER_START_BLOCK = 4
NTAG_MAX_BOOK_NAME_BYTES = 56
# Re-acquire tag between block writes to avoid connection drop (PN532 can lose tag after first write).
DELAY_BETWEEN_BLOCK_WRITES_SEC = 0.08
WRITE_REACQUIRE_TIMEOUT_SEC = 0.5

try:
    import requests
except ImportError:
    requests = None


def _uid_hex(uid: bytes) -> str:
    return "".join([format(b, "02X") for b in uid])


def send_scan(uid_hex: str) -> bool:
    if not requests:
        return False
    try:
        r = requests.post(NFC_SCAN_URL, json={"nfc_tag_id": uid_hex}, timeout=5)
        r.raise_for_status()
        return True
    except Exception:
        return False


def fetch_pending_write(uid_hex: str) -> Optional[str]:
    """GET pending write for this tag. Returns book_name or None."""
    if not requests:
        return None
    try:
        r = requests.get(NFC_PENDING_WRITE_URL, params={"nfc_tag_id": uid_hex}, timeout=5)
        if r.status_code != 200:
            return None
        data = r.json()
        return data.get("book_name")
    except Exception:
        return None


def post_write_result(uid_hex: str, success: bool, error: Optional[str] = None) -> None:
    if not requests:
        return
    try:
        requests.post(
            NFC_WRITE_RESULT_URL,
            json={"nfc_tag_id": uid_hex, "success": success, "error": error},
            timeout=5,
        )
    except Exception as e:
        print(f"  -> Failed to post write result: {e}")


def _reacquire_tag(pn532: PN532_I2C, expected_uid: bytes, timeout: float = WRITE_REACQUIRE_TIMEOUT_SEC) -> bool:
    """Re-detect the tag so PN532 has it selected. Returns True if tag with expected_uid is present."""
    uid = pn532.read_passive_target(timeout=timeout)
    if uid is None:
        return False
    return uid == expected_uid


def write_book_name_to_tag(pn532: PN532_I2C, uid: bytes, book_name: str) -> Tuple[bool, Optional[str]]:
    """
    Write book name to NTAG2xx user area (blocks 4+), 4 bytes per block.
    Re-acquires the tag before and between writes to avoid connection drop.
    Returns (success, error_message).
    """
    data_bytes = book_name.encode("utf-8", errors="replace")[:NTAG_MAX_BOOK_NAME_BYTES]
    # Pad to multiple of 4
    remainder = len(data_bytes) % 4
    if remainder:
        data_bytes += b"\x00" * (4 - remainder)
    blocks = [data_bytes[i : i + 4] for i in range(0, len(data_bytes), 4)]
    if not blocks:
        return False, "Book name empty"
    try:
        # Re-acquire tag before first write (tag may have been re-placed after the long poll).
        if not _reacquire_tag(pn532, uid, timeout=2.0):
            return False, "Tag not detected. Keep tag on reader and try again."
        time.sleep(0.05)
        for i, block in enumerate(blocks):
            block_num = NTAG_USER_START_BLOCK + i
            # ntag2xx_write_block expects 4 bytes
            if len(block) != 4:
                block = block + b"\x00" * (4 - len(block))
            if not pn532.ntag2xx_write_block(block_num, bytearray(block)):
                return False, f"Write failed at block {block_num}"
            time.sleep(DELAY_BETWEEN_BLOCK_WRITES_SEC)
            # Re-acquire before next write to keep connection (avoids "Write failed at block N").
            if i + 1 < len(blocks) and not _reacquire_tag(pn532, uid):
                return False, f"Tag lost at block {block_num}. Keep tag on reader."
        # Verify: re-acquire then re-read first block
        if not _reacquire_tag(pn532, uid):
            return False, "Tag lost during verify."
        read_back = pn532.ntag2xx_read_block(NTAG_USER_START_BLOCK)
        if read_back is None:
            return False, "Re-read failed"
        # read_back may be 4 bytes or have leading 0x00 per docs
        if isinstance(read_back, (bytes, bytearray)) and len(read_back) >= 4:
            first_block = bytes(read_back[:4])
        else:
            first_block = bytes(read_back) if read_back else b""
        if first_block != blocks[0]:
            return False, "Verify failed: read-back mismatch"
        return True, None
    except Exception as e:
        return False, str(e)


def main():
    i2c = busio.I2C(board.SCL, board.SDA)
    pn532 = PN532_I2C(i2c)
    pn532.SAM_configuration()

    print("Add Book: Scan & Write mode. Tap a tag (admin panel: Add Book → Scan NFC & Write).")
    print(f"Backend: {BACKEND_URL}")
    if not requests:
        print("Install 'requests' to talk to backend: pip install requests")
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
        if not is_new_scan:
            continue

        uid_hex = _uid_hex(uid)
        print(f"UID: {uid_hex}")

        # 1) Notify backend so frontend can get tagId
        if send_scan(uid_hex):
            print("  -> Scan sent. Waiting for book name from admin panel...")
        else:
            print("  -> Scan send failed. Is backend reachable?")
            last_uid = uid
            last_uid_time = now
            time.sleep(1)
            continue

        # 2) Poll for pending write (frontend sets it after getting tagId)
        book_name = None
        for _ in range(40):  # ~20 seconds
            book_name = fetch_pending_write(uid_hex)
            if book_name:
                break
            time.sleep(0.5)

        if not book_name:
            print("  -> No book name received (timeout). Tap again after clicking 'Scan NFC & Write' in the form.")
            last_uid = uid
            last_uid_time = now
            time.sleep(1)
            continue

        # 3) Tag must still be on reader. Write book name to tag.
        print(f"  -> Writing '{book_name[:40]}{'...' if len(book_name) > 40 else ''}' to tag. Keep tag on reader.")
        success, err = write_book_name_to_tag(pn532, uid, book_name)
        if success:
            print("  -> Write OK. Re-read verified.")
            post_write_result(uid_hex, True)
        else:
            print(f"  -> Write failed: {err}")
            post_write_result(uid_hex, False, err)

        last_uid = uid
        last_uid_time = now
        time.sleep(1)


if __name__ == "__main__":
    main()
