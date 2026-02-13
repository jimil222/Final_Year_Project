"""
NFC tap handler: issue/return by book NFC only (no login).
NFC reader is always on; when a book is tapped we decide issue vs return from allocation status.
Also supports "scan for registration" so Add Book form can get NFC ID by scanning.

Time constraint: return is allowed only after MIN_RETURN_TIME_SECONDS since borrow.
Atomic updates (update_many with status filter) prevent duplicate issue/return on rapid scans.
"""
import os
from fastapi import APIRouter, HTTPException, Depends
from app.db import db
from app.dependencies import get_current_admin
from app.books import (
    get_book_by_nfc,
    get_active_allocation,
    calculate_due_date,
)
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import math

router = APIRouter(prefix="/nfc", tags=["NFC"])

# Minimum seconds after borrow before the same tag can be used to return (prevents accidental double-tap).
MIN_RETURN_TIME_SECONDS = int(os.getenv("MIN_RETURN_TIME_SECONDS", "5"))

# In-memory store for last NFC scan (for Add Book form). Cleared when consumed.
_last_registration_scan: Optional[dict] = None
_REGISTRATION_SCAN_MAX_AGE_SECONDS = 120

# Add Book flow: pending write (book_name to write to tag) and write result (success/error).
# Key: normalized nfc_tag_id. Value: { "book_name": str, "created_at": iso } or { "success": bool, "error": str?, "created_at": iso }.
_pending_writes: dict = {}
_write_results: dict = {}
_PENDING_WRITE_MAX_AGE_SECONDS = 60
_WRITE_RESULT_MAX_AGE_SECONDS = 120


def _update_many_count(result) -> int:
    """Prisma update_many may return BatchQueryResult with .count or an int."""
    if result is None:
        return 0
    if isinstance(result, int):
        return result
    return getattr(result, "count", 0)


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


class SetPendingWriteRequest(BaseModel):
    """Admin sets pending write: book name to write to this tag after scan."""
    nfc_tag_id: str
    book_name: str


class WriteResultRequest(BaseModel):
    """NFC reader posts result of writing book name to tag."""
    nfc_tag_id: str
    success: bool
    error: Optional[str] = None


@router.post("/set-pending-write")
async def set_pending_write(body: SetPendingWriteRequest, current_admin=Depends(get_current_admin)):
    """
    Admin sets a pending write for Add Book flow. After the reader scans a tag and gets this
    book_name, it will write it to the tag and POST to /nfc/write-result.
    """
    uid = _normalize_uid(body.nfc_tag_id)
    if not uid:
        raise HTTPException(status_code=400, detail="nfc_tag_id is required")
    if not (body.book_name or "").strip():
        raise HTTPException(status_code=400, detail="book_name is required")
    book_name = body.book_name.strip()[:255]
    _pending_writes[uid] = {
        "book_name": book_name,
        "created_at": datetime.now().isoformat(),
    }
    return {"message": "Pending write set", "nfc_tag_id": uid, "book_name": book_name}


@router.get("/pending-write")
async def get_pending_write(nfc_tag_id: str):
    """
    NFC reader polls this after scanning a tag. Returns book_name to write to the tag, or 404.
    Consumes the pending write so it is only used once.
    """
    uid = _normalize_uid(nfc_tag_id)
    if not uid or uid not in _pending_writes:
        raise HTTPException(status_code=404, detail="No pending write for this tag")
    entry = _pending_writes.pop(uid)
    try:
        t = datetime.fromisoformat(entry["created_at"].replace("Z", "+00:00"))
        t_naive = t.replace(tzinfo=None) if t.tzinfo else t
        if (datetime.now() - t_naive).total_seconds() > _PENDING_WRITE_MAX_AGE_SECONDS:
            raise HTTPException(status_code=404, detail="Pending write expired")
    except Exception:
        pass
    return {"nfc_tag_id": uid, "book_name": entry["book_name"]}


@router.post("/write-result")
async def post_write_result(body: WriteResultRequest):
    """
    NFC reader posts the result of writing book name to the tag. Frontend polls GET /nfc/write-result.
    """
    uid = _normalize_uid(body.nfc_tag_id)
    if not uid:
        raise HTTPException(status_code=400, detail="nfc_tag_id is required")
    _write_results[uid] = {
        "success": body.success,
        "error": body.error,
        "created_at": datetime.now().isoformat(),
    }
    return {"message": "Write result stored", "nfc_tag_id": uid}


@router.get("/write-result")
async def get_write_result(nfc_tag_id: str):
    """
    Frontend polls this after setting pending write. Returns and consumes the result.
    """
    uid = _normalize_uid(nfc_tag_id)
    if not uid or uid not in _write_results:
        return {"nfc_tag_id": uid, "ready": False, "success": None, "error": None}
    entry = _write_results.pop(uid)
    try:
        t = datetime.fromisoformat(entry["created_at"].replace("Z", "+00:00"))
        t_naive = t.replace(tzinfo=None) if t.tzinfo else t
        if (datetime.now() - t_naive).total_seconds() > _WRITE_RESULT_MAX_AGE_SECONDS:
            return {"nfc_tag_id": uid, "ready": False, "success": None, "error": None}
    except Exception:
        pass
    return {
        "nfc_tag_id": uid,
        "ready": True,
        "success": entry["success"],
        "error": entry.get("error"),
    }


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

    # ----- Issue: RESERVED → BORROWED (atomic to prevent duplicate on rapid scan) -----
    if allocation.status == "RESERVED":
        checkout_time = datetime.now()
        due_date = calculate_due_date(checkout_time)

        result = await db.userbookallocation.update_many(
            where={
                "allocation_id": allocation.allocation_id,
                "status": "RESERVED",
            },
            data={
                "status": "BORROWED",
                "borrowed_at": checkout_time,
            },
        )
        if _update_many_count(result) == 0:
            raise HTTPException(
                status_code=409,
                detail="Book already issued or request was updated. Please do not scan again.",
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

    # ----- Return: BORROWED → AVAILABLE (time constraint + atomic to prevent duplicate) -----
    if allocation.status == "BORROWED":
        return_time = datetime.now()
        borrowed_at = allocation.borrowed_at or allocation.created_at
        if borrowed_at:
            # Normalize to naive datetime so subtraction works (DB may return timezone-aware)
            if getattr(borrowed_at, "tzinfo", None) is not None:
                borrowed_at = borrowed_at.replace(tzinfo=None)
            elapsed_seconds = (return_time - borrowed_at).total_seconds()
        else:
            elapsed_seconds = MIN_RETURN_TIME_SECONDS  # allow return if no timestamp
        if elapsed_seconds < MIN_RETURN_TIME_SECONDS:
            wait_seconds = math.ceil(MIN_RETURN_TIME_SECONDS - elapsed_seconds)
            raise HTTPException(
                status_code=400,
                detail=f"Please wait {wait_seconds} second(s) before returning this book (prevents accidental double-tap).",
            )

        result = await db.userbookallocation.update_many(
            where={
                "allocation_id": allocation.allocation_id,
                "status": "BORROWED",
            },
            data={
                "status": "RETURNED",
                "returned_at": return_time,
            },
        )
        if _update_many_count(result) == 0:
            raise HTTPException(
                status_code=409,
                detail="Book already returned. Please do not scan again.",
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


@router.post("/status")
async def nfc_status(request: NFCTapRequest):
    """
    Read-only status for a book by NFC tag (no state changes).
    Use this from the kiosk in STATUS mode to show current borrower and submit (due) date
    without issuing/returning the book.
    """
    uid = _normalize_uid(request.nfc_tag_id)
    if not uid:
        raise HTTPException(status_code=400, detail="nfc_tag_id is required")

    try:
        book = await get_book_by_nfc(uid)
    except HTTPException as e:
        if e.status_code == 404:
            # Reuse registration behavior so unknown tags can still be used in Add Book flow.
            _store_registration_scan(uid)
            raise HTTPException(
                status_code=404,
                detail="Book not found for this NFC tag. Register the book with this tag in the system.",
            )
        raise

    allocation = await get_active_allocation(book.book_id)

    # No active allocation: book is not currently reserved or borrowed.
    if not allocation:
        return {
            "action": "status",
            "message": "Book is not currently reserved or borrowed.",
            "book_name": book.book_name,
            "student_name": None,
            "book_status": book.status,
            "allocation_status": None,
            "due_date": None,
        }

    # Borrowed: show current borrower and due date.
    if allocation.status == "BORROWED":
        transaction = await db.transaction.find_first(
            where={
                "book_id": book.book_id,
                "user_id": allocation.user_id,
                "return_time": None,
            },
            order={"checkout_time": "desc"},
        )
        due_date = None
        if transaction and transaction.due_date:
            due_date = transaction.due_date.isoformat()
        else:
            # Fallback: approximate due date from allocation timestamps.
            base_time = allocation.borrowed_at or allocation.created_at
            if base_time:
                if getattr(base_time, "tzinfo", None) is not None:
                    base_time = base_time.replace(tzinfo=None)
                due_date = calculate_due_date(base_time).isoformat()

        return {
            "action": "status",
            "message": "Book is currently borrowed.",
            "book_name": book.book_name,
            "student_name": allocation.user.name,
            "book_status": book.status,
            "allocation_status": allocation.status,
            "due_date": due_date,
        }

    # Reserved or pending: show reservation info but no due date yet.
    if allocation.status in ("RESERVED", "PENDING"):
        return {
            "action": "status",
            "message": "Book is reserved and waiting for pickup."
            if allocation.status == "RESERVED"
            else "Book request is pending approval.",
            "book_name": book.book_name,
            "student_name": allocation.user.name,
            "book_status": book.status,
            "allocation_status": allocation.status,
            "due_date": None,
        }

    # Fallback: should not normally happen because get_active_allocation filters statuses.
    return {
        "action": "status",
        "message": f"Book status: {book.status}, allocation: {allocation.status}",
        "book_name": book.book_name,
        "student_name": allocation.user.name,
        "book_status": book.status,
        "allocation_status": allocation.status,
        "due_date": None,
    }
