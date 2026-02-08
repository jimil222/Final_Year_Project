"""
NFC tap handler: issue/return by book NFC only (no login).
NFC reader is always on; when a book is tapped we decide issue vs return from allocation status.
Also supports "scan for registration" so Add Book form can get NFC ID by scanning.
"""
from fastapi import APIRouter, HTTPException
from app.db import db
from app.books import (
    get_book_by_nfc,
    get_active_allocation,
    calculate_due_date,
)
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

router = APIRouter(prefix="/nfc", tags=["NFC"])

# In-memory store for last NFC scan (for Add Book form). Cleared when consumed.
_last_registration_scan: Optional[dict] = None
_REGISTRATION_SCAN_MAX_AGE_SECONDS = 120


def _normalize_uid(uid: str) -> str:
    return uid.strip().upper().replace(" ", "")


def _store_registration_scan(nfc_tag_id: str) -> None:
    global _last_registration_scan
    _last_registration_scan = {
        "nfc_tag_id": nfc_tag_id,
        "scanned_at": datetime.now().isoformat(),
    }


class NFCTapRequest(BaseModel):
    """Payload from NFC reader (UID = book's nfc_tag_id)."""
    nfc_tag_id: str


@router.post("/scan")
async def nfc_scan(request: NFCTapRequest):
    """
    Register an NFC scan for "Add Book" form. Call this when staff taps a tag
    to capture its UID (e.g. from a dedicated scan script or reader in scan mode).
    Frontend polls GET /nfc/last-scan to retrieve the UID.
    """
    uid = _normalize_uid(request.nfc_tag_id)
    if not uid:
        raise HTTPException(status_code=400, detail="nfc_tag_id is required")
    _store_registration_scan(uid)
    return {"message": "Scan stored", "nfc_tag_id": uid}


@router.get("/last-scan")
async def get_last_scan():
    """
    Return the most recent NFC scan stored for registration (Add Book).
    Intended for frontend: when user clicks "Scan NFC", poll this until a value appears.
    Returns and consumes the value (so one scan = one use).
    """
    global _last_registration_scan
    if _last_registration_scan is None:
        return {"nfc_tag_id": None, "scanned_at": None}
    scanned_at = _last_registration_scan.get("scanned_at")
    if scanned_at:
        try:
            t = datetime.fromisoformat(scanned_at.replace("Z", "+00:00"))
            t_naive = t.replace(tzinfo=None) if t.tzinfo else t
            age = (datetime.now() - t_naive).total_seconds()
            if age > _REGISTRATION_SCAN_MAX_AGE_SECONDS:
                _last_registration_scan = None
                return {"nfc_tag_id": None, "scanned_at": None}
        except Exception:
            pass
    out = _last_registration_scan
    _last_registration_scan = None
    return out


@router.post("/tap")
async def nfc_tap(request: NFCTapRequest):
    """
    Handle NFC tap at library: no login required.
    - If book is RESERVED → issue (complete borrow).
    - If book is BORROWED → return.
    - If book not found, UID is stored as last registration scan (for Add Book).
    """
    # Normalize UID (hex, uppercase, no spaces)
    uid = _normalize_uid(request.nfc_tag_id)

    if not uid:
        raise HTTPException(status_code=400, detail="nfc_tag_id is required")

    try:
        book = await get_book_by_nfc(uid)
    except HTTPException as e:
        if e.status_code == 404:
            _store_registration_scan(uid)
            raise HTTPException(
                status_code=404,
                detail="Book not found for this NFC tag. Register the book with this tag in the system.",
            )
        raise

    allocation = await get_active_allocation(book.book_id)

    if not allocation:
        raise HTTPException(
            status_code=400,
            detail="No active reservation or borrow for this book. Request and get it approved first, or the book is already returned.",
        )

    # ----- Issue: RESERVED → BORROWED -----
    if allocation.status == "RESERVED":
        checkout_time = datetime.now()
        due_date = calculate_due_date(checkout_time)

        await db.userbookallocation.update(
            where={"allocation_id": allocation.allocation_id},
            data={
                "status": "BORROWED",
                "borrowed_at": checkout_time,
            },
        )
        await db.book.update(
            where={"book_id": book.book_id},
            data={"status": "BORROWED"},
        )
        await db.transaction.create(
            data={
                "user_id": allocation.user_id,
                "book_id": book.book_id,
                "admin_id": allocation.admin_id,
                "checkout_time": checkout_time,
                "due_date": due_date,
                "status": "BORROWED",
            }
        )
        return {
            "action": "issue",
            "message": "Book issued successfully",
            "book_name": book.book_name,
            "student_name": allocation.user.name,
            "checkout_time": checkout_time.isoformat(),
            "due_date": due_date.isoformat(),
        }

    # ----- Return: BORROWED → AVAILABLE -----
    if allocation.status == "BORROWED":
        return_time = datetime.now()

        await db.userbookallocation.update(
            where={"allocation_id": allocation.allocation_id},
            data={
                "status": "RETURNED",
                "returned_at": return_time,
            },
        )
        await db.book.update(
            where={"book_id": book.book_id},
            data={"status": "AVAILABLE"},
        )

        transaction = await db.transaction.find_first(
            where={
                "book_id": book.book_id,
                "user_id": allocation.user_id,
                "return_time": None,
            },
            order={"checkout_time": "desc"},
        )
        was_overdue = False
        if transaction:
            was_overdue = return_time > transaction.due_date
            await db.transaction.update(
                where={"transaction_id": transaction.transaction_id},
                data={
                    "return_time": return_time,
                    "status": "OVERDUE" if was_overdue else "RETURNED",
                },
            )

        return {
            "action": "return",
            "message": "Book returned successfully",
            "book_name": book.book_name,
            "student_name": allocation.user.name,
            "return_time": return_time.isoformat(),
            "was_overdue": was_overdue,
        }

    raise HTTPException(
        status_code=400,
        detail=f"Cannot process tap: book allocation status is {allocation.status}. Only RESERVED (issue) or BORROWED (return) are allowed.",
    )
