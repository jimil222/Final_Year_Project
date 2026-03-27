import os
import math
import logging
from fastapi import APIRouter, HTTPException, Depends, status
from app.db import db
from app.dependencies import get_current_student, get_current_admin, get_current_user
from app.email_service import send_book_approval_email
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta

router = APIRouter(prefix="/books", tags=["Books"])
logger = logging.getLogger(__name__)

# Minimum seconds after borrow before return is allowed (prevents accidental double-tap).
MIN_RETURN_TIME_SECONDS = int(os.getenv("MIN_RETURN_TIME_SECONDS", "5"))


def _update_many_count(result) -> int:
    """Prisma update_many may return BatchQueryResult with .count or an int."""
    if result is None:
        return 0
    if isinstance(result, int):
        return result
    return getattr(result, "count", 0)

# ==================== Request/Response Models ====================

class BookResponse(BaseModel):
    book_id: int
    book_name: str
    author: Optional[str]
    nfc_tag_id: str
    shelf_id: int
    status: str
    allocation: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

class NFCRequest(BaseModel):
    nfc_tag_id: str

class AllocationResponse(BaseModel):
    allocation_id: int
    user_id: int
    book_id: int
    admin_id: int
    status: str
    reserved_at: Optional[datetime]
    borrowed_at: Optional[datetime]
    returned_at: Optional[datetime]
    created_at: datetime


class CreateBookRequest(BaseModel):
    book_name: str
    author: Optional[str] = None
    nfc_tag_id: str
    shelf_id: Optional[int] = None


class ShelfResponse(BaseModel):
    shelf_id: int
    shelf_number: str
    coordinate_x: int
    coordinate_y: int


class ShelfCapacityResponse(BaseModel):
    shelf_id: int
    shelf_number: str
    book_count: int
    capacity: int
    available: bool


class AdminBookInventoryResponse(BaseModel):
    book_id: int
    book_name: str
    author: Optional[str]
    nfc_tag_id: str
    shelf_id: int
    status: str
    allocation_id: Optional[int] = None
    allocation_user_name: Optional[str] = None
    allocation_user_email: Optional[str] = None
    allocation_status: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class PendingRequestResponse(BaseModel):
    allocation_id: int
    user_id: int
    user_name: str
    user_email: str
    user_department: Optional[str] = None
    book_id: int
    book_name: str
    book_author: Optional[str] = None
    created_at: datetime
    requested_at: Optional[datetime] = None

# ==================== Helper Functions ====================

def calculate_due_date(checkout_time: datetime, days: int = 6) -> datetime:
    """Calculate due date (default 6 days from checkout)"""
    return checkout_time + timedelta(days=days)

async def get_book_by_id(book_id: int):
    """Get book or raise 404"""
    book = await db.book.find_unique(where={"book_id": book_id})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book

async def get_book_by_nfc(nfc_tag_id: str):
    """Get book by NFC tag or raise 404"""
    uid = (nfc_tag_id or "").strip().upper().replace(" ", "")
    if not uid:
        raise HTTPException(status_code=400, detail="nfc_tag_id is required")
    book = await db.book.find_unique(where={"nfc_tag_id": uid})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found with this NFC tag")
    return book

async def get_active_allocation(book_id: int):
    """Get active allocation for a book (PENDING, RESERVED or BORROWED). RETURNED rows are ignored."""
    return await db.userbookallocation.find_first(
        where={
            "book_id": book_id,
            "status": {"in": ["PENDING", "RESERVED", "BORROWED"]}
        },
        include={"user": True, "admin": True}
    )


async def get_returned_allocation_for_book(book_id: int):
    """Get the RETURNED allocation row for a book (for reuse on new request). One book has at most one allocation row (unique book_id)."""
    return await db.userbookallocation.find_first(
        where={"book_id": book_id, "status": "RETURNED"},
        order={"returned_at": "desc"},
    )


async def find_available_shelf():
    """Find first shelf with < 5 books. Each shelf can hold max 5 books."""
    shelves = await db.shelf.find_many(order={"shelf_id": "asc"})
    
    for shelf in shelves:
        book_count = await db.book.count(where={"shelf_id": shelf.shelf_id})
        if book_count < 5:
            return shelf
    
    raise HTTPException(
        status_code=400,
        detail="No shelf has available capacity. Each shelf can hold max 5 books."
    )


# ==================== Endpoints ====================

@router.get("/shelves", response_model=List[ShelfResponse])
async def list_shelves(current_user=Depends(get_current_user)):
    """List all shelves (for Add Book dropdown)."""
    shelves = await db.shelf.find_many(order={"shelf_id": "asc"})
    return [
        {"shelf_id": s.shelf_id, "shelf_number": s.shelf_number, "coordinate_x": s.coordinate_x, "coordinate_y": s.coordinate_y}
        for s in shelves
    ]


@router.get("/shelves/capacity", response_model=List[ShelfCapacityResponse])
async def get_shelf_capacity(current_user=Depends(get_current_user)):
    """Get shelf capacity info (books per shelf, max 5 each)."""
    shelves = await db.shelf.find_many(order={"shelf_id": "asc"})
    result = []
    
    for shelf in shelves:
        book_count = await db.book.count(where={"shelf_id": shelf.shelf_id})
        available = book_count < 5
        
        result.append({
            "shelf_id": shelf.shelf_id,
            "shelf_number": shelf.shelf_number,
            "book_count": book_count,
            "capacity": 5,
            "available": available
        })
    
    return result


@router.post("/", response_model=BookResponse)
async def create_book(body: CreateBookRequest, current_admin=Depends(get_current_admin)):
    """Admin adds a new book. Use NFC scan (GET /nfc/last-scan) to get nfc_tag_id. Shelf auto-assigns if not provided."""
    book_name = (body.book_name or "").strip()
    if not book_name:
        raise HTTPException(status_code=400, detail="book_name is required")
    uid = body.nfc_tag_id.strip().upper().replace(" ", "")
    if not uid:
        raise HTTPException(status_code=400, detail="nfc_tag_id is required (scan the book's NFC tag)")
    existing = await db.book.find_unique(where={"nfc_tag_id": uid})
    if existing:
        raise HTTPException(status_code=400, detail=f"A book is already registered with this NFC tag: {uid}")
    
    # Auto-select shelf if not provided
    if body.shelf_id:
        shelf = await db.shelf.find_unique(where={"shelf_id": body.shelf_id})
        if not shelf:
            raise HTTPException(status_code=400, detail="Invalid shelf_id")
        # Check capacity if manually selected
        book_count = await db.book.count(where={"shelf_id": body.shelf_id})
        if book_count >= 5:
            raise HTTPException(status_code=400, detail=f"Shelf {shelf.shelf_number} is full (5/5 books). Please select another shelf.")
    else:
        # Auto-select first available shelf with capacity
        shelf = await find_available_shelf()
    book = await db.book.create(
        data={
            "book_name": book_name,
            "author": (body.author or "").strip() or None,
            "nfc_tag_id": uid,
            "shelf_id": shelf.shelf_id,
            "status": "AVAILABLE",
        }
    )
    return {
        "book_id": book.book_id,
        "book_name": book.book_name,
        "author": book.author,
        "nfc_tag_id": book.nfc_tag_id,
        "shelf_id": book.shelf_id,
        "status": book.status,
        "allocation": None,
        "created_at": book.created_at,
        "updated_at": book.updated_at,
    }


@router.get("/", response_model=List[BookResponse])
async def list_books(current_user=Depends(get_current_user)):
    """List all books with their allocation status"""
    books = await db.book.find_many(
        include={
            "shelf": True,
            "allocations": {
                "where": {"status": {"in": ["PENDING", "RESERVED", "BORROWED"]}},
                "include": {"user": True, "admin": True}
            }
        },
        order={"book_id": "asc"}
    )
    
    result = []
    for book in books:
        allocation = None
        if book.allocations and len(book.allocations) > 0:
            alloc = book.allocations[0]
            allocation = {
                "allocation_id": alloc.allocation_id,
                "user_name": alloc.user.name,
                "user_email": alloc.user.email,
                "status": alloc.status,
                "reserved_at": alloc.reserved_at,
                "borrowed_at": alloc.borrowed_at
            }
        
        result.append({
            "book_id": book.book_id,
            "book_name": book.book_name,
            "author": book.author,
            "nfc_tag_id": book.nfc_tag_id,
            "shelf_id": book.shelf_id,
            "status": book.status,
            "allocation": allocation,
            "created_at": book.created_at,
            "updated_at": book.updated_at
        })
    
    return result


@router.get("/admin/inventory", response_model=List[AdminBookInventoryResponse])
async def get_book_inventory(
    status: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_admin=Depends(get_current_admin)
):
    """
    Admin endpoint: Get all books with optional status and search filters.
    """
    where_clause = {}

    if status:
        valid_statuses = ["AVAILABLE", "RESERVED", "BORROWED", "MAINTENANCE"]
        status_values = [s.strip().upper() for s in status.split(",") if s.strip()]
        if not status_values:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        invalid = [s for s in status_values if s not in valid_statuses]
        if invalid:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        if len(status_values) == 1:
            where_clause["status"] = status_values[0]
        else:
            where_clause["status"] = {"in": status_values}

    books = await db.book.find_many(
        where=where_clause,
        include={
            "allocations": {
                "where": {"status": {"in": ["PENDING", "RESERVED", "BORROWED"]}},
                "include": {"user": True},
            },
        },
        order={"book_id": "asc"},
        skip=skip,
        take=limit,
    )

    result = []
    for book in books:
        if search:
            search_lower = search.lower()
            if not (
                (book.book_name and search_lower in book.book_name.lower()) or
                (book.author and search_lower in book.author.lower())
            ):
                continue

        allocation_id = None
        allocation_user_name = None
        allocation_user_email = None
        allocation_status = None

        if book.allocations and len(book.allocations) > 0:
            alloc = book.allocations[0]
            allocation_id = alloc.allocation_id
            allocation_user_name = alloc.user.name
            allocation_user_email = alloc.user.email
            allocation_status = alloc.status

        result.append({
            "book_id": book.book_id,
            "book_name": book.book_name,
            "author": book.author,
            "nfc_tag_id": book.nfc_tag_id,
            "shelf_id": book.shelf_id,
            "status": book.status,
            "allocation_id": allocation_id,
            "allocation_user_name": allocation_user_name,
            "allocation_user_email": allocation_user_email,
            "allocation_status": allocation_status,
            "created_at": book.created_at,
            "updated_at": book.updated_at,
        })

    return result


@router.get("/admin/pending-requests", response_model=List[PendingRequestResponse])
async def get_pending_requests(
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_admin=Depends(get_current_admin)
):
    """
    Admin endpoint: Get pending book requests awaiting approval.
    """
    allocations = await db.userbookallocation.find_many(
        where={"status": "PENDING"},
        include={"user": True, "book": True},
        order={"created_at": "desc"},
        skip=skip,
        take=limit,
    )

    result = []
    for alloc in allocations:
        if search:
            search_lower = search.lower()
            if not (
                (alloc.user.name and search_lower in alloc.user.name.lower()) or
                (alloc.user.email and search_lower in alloc.user.email.lower()) or
                (alloc.book.book_name and search_lower in alloc.book.book_name.lower())
            ):
                continue

        result.append({
            "allocation_id": alloc.allocation_id,
            "user_id": alloc.user_id,
            "user_name": alloc.user.name,
            "user_email": alloc.user.email,
            "user_department": getattr(alloc.user, "department", None),
            "book_id": alloc.book_id,
            "book_name": alloc.book.book_name,
            "book_author": alloc.book.author,
            "created_at": alloc.created_at,
            "requested_at": alloc.created_at,
        })

    return result


@router.get("/nfc/{nfc_tag_id}")
async def get_book_by_nfc_tag(nfc_tag_id: str, current_user=Depends(get_current_user)):
    """Get a book by NFC UID for scan inventory and NFC workflows."""
    book = await get_book_by_nfc(nfc_tag_id)
    return {
        "id": book.book_id,
        "book_id": book.book_id,
        "title": book.book_name,
        "book_name": book.book_name,
        "author": book.author,
        "status": (book.status or "").lower(),
        "shelf_number": book.shelf_id,
        "nfc_tag_id": book.nfc_tag_id,
        "created_at": book.created_at,
        "updated_at": book.updated_at,
    }

@router.get("/{book_id}", response_model=BookResponse)
async def get_book(book_id: int, current_user=Depends(get_current_user)):
    """Get book details with allocation info"""
    book = await db.book.find_unique(
        where={"book_id": book_id},
        include={
            "shelf": True,
            "allocations": {
                "where": {"status": {"in": ["PENDING", "RESERVED", "BORROWED"]}},
                "include": {"user": True}
            }
        }
    )
    
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    allocation = None
    if book.allocations and len(book.allocations) > 0:
        alloc = book.allocations[0]
        allocation = {
            "allocation_id": alloc.allocation_id,
            "user_name": alloc.user.name,
            "status": alloc.status,
            "reserved_at": alloc.reserved_at,
            "borrowed_at": alloc.borrowed_at
        }
    
    return {
        "book_id": book.book_id,
        "book_name": book.book_name,
        "author": book.author,
        "nfc_tag_id": book.nfc_tag_id,
        "shelf_id": book.shelf_id,
        "status": book.status,
        "allocation": allocation,
        "created_at": book.created_at,
        "updated_at": book.updated_at
    }

@router.post("/{book_id}/request", response_model=AllocationResponse)
async def request_book(book_id: int, current_user=Depends(get_current_student)):
    """Student requests a book. Book must be AVAILABLE. Reuses RETURNED allocation row if present (unique book_id)."""
    book = await get_book_by_id(book_id)
    
    if book.status != "AVAILABLE":
        raise HTTPException(
            status_code=400,
            detail=f"Book is not available (current status: {book.status})"
        )
    
    existing_active = await get_active_allocation(book_id)
    if existing_active:
        raise HTTPException(
            status_code=400,
            detail=f"Book is already {existing_active.status.lower()} by another user"
        )
    
    admin = await db.admin.find_first()
    if not admin:
        raise HTTPException(status_code=500, detail="No admin available")
    
    # Reuse RETURNED allocation row if present (so unique book_id is not violated). Atomic update to prevent double-assign.
    returned_row = await get_returned_allocation_for_book(book_id)
    if returned_row:
        result = await db.userbookallocation.update_many(
            where={
                "allocation_id": returned_row.allocation_id,
                "status": "RETURNED",  # only claim if still RETURNED (concurrent request may have taken it)
            },
            data={
                "user_id": current_user.user_id,
                "admin_id": admin.admin_id,
                "status": "PENDING",
                "reserved_at": None,
                "borrowed_at": None,
                "returned_at": None,
            },
        )
        if _update_many_count(result) == 0:
            raise HTTPException(status_code=409, detail="Book was just requested by someone else. Please refresh and try again.")
        allocation = await db.userbookallocation.find_unique(where={"allocation_id": returned_row.allocation_id})
    else:
        allocation = await db.userbookallocation.create(
            data={
                "user_id": current_user.user_id,
                "book_id": book_id,
                "admin_id": admin.admin_id,
                "status": "PENDING",
                "reserved_at": None,
            }
        )
    
    # Book status stays AVAILABLE until admin approves
    # No book status update here
    
    return {
        "allocation_id": allocation.allocation_id,
        "user_id": allocation.user_id,
        "book_id": allocation.book_id,
        "admin_id": allocation.admin_id,
        "status": allocation.status,
        "reserved_at": allocation.reserved_at,
        "borrowed_at": allocation.borrowed_at,
        "returned_at": allocation.returned_at,
        "created_at": allocation.created_at
    }

@router.post("/borrow", response_model=dict)
async def borrow_book(request: NFCRequest, current_user=Depends(get_current_student)):
    """Student borrows a reserved book via NFC tap (RESERVED → BORROWED)"""
    book = await get_book_by_nfc(request.nfc_tag_id)
    
    # Check if book is reserved
    if book.status != "RESERVED":
        raise HTTPException(
            status_code=400,
            detail=f"Book must be RESERVED to borrow (current status: {book.status})"
        )
    
    # Get the active allocation
    allocation = await get_active_allocation(book.book_id)
    if not allocation:
        raise HTTPException(status_code=400, detail="No active reservation found for this book")
    
    # Verify the current user is the one who reserved it
    if allocation.user_id != current_user.user_id:
        raise HTTPException(
            status_code=403,
            detail="This book is reserved by another user"
        )
    
    # Atomic update: only one request can move RESERVED → BORROWED (prevents duplicate on rapid scan).
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
    
    # Create transaction record
    transaction = await db.transaction.create(
        data={
            "user_id": current_user.user_id,
            "book_id": book.book_id,
            "admin_id": allocation.admin_id,
            "checkout_time": checkout_time,
            "due_date": due_date,
            "status": "BORROWED"
        }
    )
    
    return {
        "message": "Book borrowed successfully",
        "book_name": book.book_name,
        "checkout_time": checkout_time,
        "due_date": due_date,
        "transaction_id": transaction.transaction_id
    }

@router.post("/return", response_model=dict)
async def return_book(request: NFCRequest, current_user=Depends(get_current_student)):
    """Student returns a borrowed book via NFC tap. State: BORROWED → AVAILABLE. Book is immediately available for reassignment; allocation is set to RETURNED (borrower fields cleared from active view)."""
    book = await get_book_by_nfc(request.nfc_tag_id)
    
    # Check if book is borrowed
    if book.status != "BORROWED":
        raise HTTPException(
            status_code=400,
            detail=f"Book must be BORROWED to return (current status: {book.status})"
        )
    
    # Get the active allocation
    allocation = await get_active_allocation(book.book_id)
    if not allocation:
        raise HTTPException(status_code=400, detail="No active borrowing found for this book")
    
    # Verify the current user is the one who borrowed it
    if allocation.user_id != current_user.user_id:
        raise HTTPException(
            status_code=403,
            detail="This book is borrowed by another user"
        )

    # Allow return only after MIN_RETURN_TIME_SECONDS since borrow (prevents accidental double-tap).
    return_time = datetime.now()
    borrowed_at = allocation.borrowed_at or allocation.created_at
    if borrowed_at:
        if getattr(borrowed_at, "tzinfo", None) is not None:
            borrowed_at = borrowed_at.replace(tzinfo=None)
        elapsed_seconds = (return_time - borrowed_at).total_seconds()
    else:
        elapsed_seconds = MIN_RETURN_TIME_SECONDS
    if elapsed_seconds < MIN_RETURN_TIME_SECONDS:
        wait_seconds = math.ceil(MIN_RETURN_TIME_SECONDS - elapsed_seconds)
        raise HTTPException(
            status_code=400,
            detail=f"Please wait {wait_seconds} second(s) before returning this book (prevents accidental double-tap).",
        )

    # Atomic update: only one request can move BORROWED → RETURNED (prevents duplicate on rapid scan).
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
            "user_id": current_user.user_id,
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
        "message": "Book returned successfully",
        "book_name": book.book_name,
        "return_time": return_time,
        "was_overdue": was_overdue,
    }

@router.post("/{book_id}/approve-request", response_model=dict)
async def approve_request(book_id: int, current_admin=Depends(get_current_admin)):
    """Admin approves a book request (PENDING → RESERVED, book becomes RESERVED)"""
    book = await get_book_by_id(book_id)
    
    # Find PENDING allocation for this book
    allocation = await db.userbookallocation.find_first(
        where={
            "book_id": book_id,
            "status": "PENDING"
        },
        include={"user": True}
    )
    
    if not allocation:
        raise HTTPException(status_code=400, detail="No pending request found for this book")
    
    # Check if book is still available
    if book.status != "AVAILABLE":
        raise HTTPException(
            status_code=400,
            detail=f"Book is no longer available (current status: {book.status})"
        )
    
    # Update allocation: PENDING → RESERVED
    issue_time = datetime.now()
    return_time = calculate_due_date(issue_time)

    await db.userbookallocation.update(
        where={"allocation_id": allocation.allocation_id},
        data={
            "status": "RESERVED",
            "admin_id": current_admin.admin_id,
            "reserved_at": issue_time
        }
    )
    
    # Update book status: AVAILABLE → RESERVED
    await db.book.update(
        where={"book_id": book_id},
        data={"status": "RESERVED"}
    )

    try:
        await send_book_approval_email(
            to_email=allocation.user.email,
            user_name=allocation.user.name,
            book_name=book.book_name,
            author=book.author,
            issue_datetime=issue_time,
            return_datetime=return_time,
        )
    except Exception as exc:
        # Email failure should not fail approval.
        logger.warning("Failed to send approval email for book_id=%s: %s", book_id, exc)
    
    return {
        "message": "Request approved successfully",
        "book_name": book.book_name,
        "allocated_to": allocation.user.email,
        "issue_date_time": issue_time,
        "return_due_date_time": return_time,
        "approved_by": current_admin.email
    }

@router.post("/{book_id}/reject-request", response_model=dict)
async def reject_request(book_id: int, current_admin=Depends(get_current_admin)):
    """Admin rejects a book request (PENDING → Deleted, book stays AVAILABLE)"""
    book = await get_book_by_id(book_id)
    
    # Find PENDING allocation
    allocation = await db.userbookallocation.find_first(
        where={
            "book_id": book_id,
            "status": "PENDING"
        },
        include={"user": True}
    )
    
    if not allocation:
        raise HTTPException(status_code=400, detail="No pending request found for this book")
    
    # Delete the allocation record
    # This effectively rejects it and frees up the user to request other books, 
    # and keeps the book AVAILABLE for others.
    await db.userbookallocation.delete(
        where={"allocation_id": allocation.allocation_id}
    )
    
    # Book status is already AVAILABLE, so no change needed to book table
    
    return {
        "message": "Request rejected successfully",
        "book_name": book.book_name,
        "rejected_user": allocation.user.email
    }
