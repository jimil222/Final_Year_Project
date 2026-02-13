from fastapi import APIRouter, HTTPException, Depends
from app.core.db import db
from app.core.dependencies import get_current_student, get_current_admin
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix="/allocations", tags=["Allocations & Transactions"])


# ==================== Response Models ====================

class AllocationResponse(BaseModel):
  allocation_id: int
  user_id: int
  user_name: str
  user_email: str
  user_roll_no: Optional[str] = None
  user_department: Optional[str] = None
  book_id: int
  book_name: str
  book_author: Optional[str] = None
  admin_id: int
  status: str
  reserved_at: Optional[datetime]
  borrowed_at: Optional[datetime]
  returned_at: Optional[datetime]
  created_at: datetime


class TransactionResponse(BaseModel):
  transaction_id: int
  user_id: int
  user_name: str
  book_id: int
  book_name: str
  admin_id: int
  checkout_time: datetime
  due_date: datetime
  return_time: Optional[datetime]
  status: str
  created_at: datetime


# ==================== Allocation Endpoints ====================

@router.get("/my", response_model=List[AllocationResponse])
async def get_my_allocations(current_user=Depends(get_current_student)):
  """Get current student's allocations"""
  allocations = await db.userbookallocation.find_many(
    where={"user_id": current_user.user_id},
    include={"user": True, "book": True, "admin": True},
    order={"created_at": "desc"},
  )

  result: List[AllocationResponse] = []
  for alloc in allocations:
    result.append(
      {
        "allocation_id": alloc.allocation_id,
        "user_id": alloc.user_id,
        "user_name": alloc.user.name,
        "user_email": alloc.user.email,
        "user_roll_no": getattr(alloc.user, "roll_no", None),
        "user_department": getattr(alloc.user, "department", None),
        "book_id": alloc.book_id,
        "book_name": alloc.book.book_name,
        "book_author": alloc.book.author,
        "admin_id": alloc.admin_id,
        "status": alloc.status,
        "reserved_at": alloc.reserved_at,
        "borrowed_at": alloc.borrowed_at,
        "returned_at": alloc.returned_at,
        "created_at": alloc.created_at,
      }
    )

  return result


@router.get("/user/{user_id}", response_model=List[AllocationResponse])
async def get_user_allocations(user_id: int, current_admin=Depends(get_current_admin)):
  """Admin gets specific user's allocations"""
  allocations = await db.userbookallocation.find_many(
    where={"user_id": user_id},
    include={"user": True, "book": True, "admin": True},
    order={"created_at": "desc"},
  )

  result: List[AllocationResponse] = []
  for alloc in allocations:
    result.append(
      {
        "allocation_id": alloc.allocation_id,
        "user_id": alloc.user_id,
        "user_name": alloc.user.name,
        "user_email": alloc.user.email,
        "user_roll_no": getattr(alloc.user, "roll_no", None),
        "user_department": getattr(alloc.user, "department", None),
        "book_id": alloc.book_id,
        "book_name": alloc.book.book_name,
        "book_author": alloc.book.author,
        "admin_id": alloc.admin_id,
        "status": alloc.status,
        "reserved_at": alloc.reserved_at,
        "borrowed_at": alloc.borrowed_at,
        "returned_at": alloc.returned_at,
        "created_at": alloc.created_at,
      }
    )

  return result


@router.get("/all", response_model=List[AllocationResponse])
async def get_all_allocations(current_admin=Depends(get_current_admin)):
  """Admin gets all  allocations"""
  allocations = await db.userbookallocation.find_many(
    include={"user": True, "book": True, "admin": True},
    order={"created_at": "desc"},
    take=100,  # Limit to last 100
  )

  result: List[AllocationResponse] = []
  for alloc in allocations:
    result.append(
      {
        "allocation_id": alloc.allocation_id,
        "user_id": alloc.user_id,
        "user_name": alloc.user.name,
        "user_email": alloc.user.email,
        "user_roll_no": getattr(alloc.user, "roll_no", None),
        "user_department": getattr(alloc.user, "department", None),
        "book_id": alloc.book_id,
        "book_name": alloc.book.book_name,
        "book_author": alloc.book.author,
        "admin_id": alloc.admin_id,
        "status": alloc.status,
        "reserved_at": alloc.reserved_at,
        "borrowed_at": alloc.borrowed_at,
        "returned_at": alloc.returned_at,
        "created_at": alloc.created_at,
      }
    )

  return result


# ==================== Transaction Endpoints ====================

@router.get("/transactions/my", response_model=List[TransactionResponse])
async def get_my_transactions(current_user=Depends(get_current_student)):
  """Get current student's transaction history"""
  transactions = await db.transaction.find_many(
    where={"user_id": current_user.user_id},
    include={"user": True, "book": True, "admin": True},
    order={"checkout_time": "desc"},
  )

  result: List[TransactionResponse] = []
  for trans in transactions:
    result.append(
      {
        "transaction_id": trans.transaction_id,
        "user_id": trans.user_id,
        "user_name": trans.user.name,
        "book_id": trans.book_id,
        "book_name": trans.book.book_name,
        "admin_id": trans.admin_id,
        "checkout_time": trans.checkout_time,
        "due_date": trans.due_date,
        "return_time": trans.return_time,
        "status": trans.status,
        "created_at": trans.created_at,
      }
    )

  return result


@router.get("/transactions/book/{book_id}", response_model=List[TransactionResponse])
async def get_book_transactions(book_id: int, current_admin=Depends(get_current_admin)):
  """Admin gets transaction history for a specific book"""
  transactions = await db.transaction.find_many(
    where={"book_id": book_id},
    include={"user": True, "book": True, "admin": True},
    order={"checkout_time": "desc"},
  )

  result: List[TransactionResponse] = []
  for trans in transactions:
    result.append(
      {
        "transaction_id": trans.transaction_id,
        "user_id": trans.user_id,
        "user_name": trans.user.name,
        "book_id": trans.book_id,
        "book_name": trans.book.book_name,
        "admin_id": trans.admin_id,
        "checkout_time": trans.checkout_time,
        "due_date": trans.due_date,
        "return_time": trans.return_time,
        "status": trans.status,
        "created_at": trans.created_at,
      }
    )

  return result


@router.get("/transactions/overdue", response_model=List[TransactionResponse])
async def get_overdue_books(current_admin=Depends(get_current_admin)):
  """Admin gets all currently overdue books"""
  now = datetime.now()

  # Find transactions that are borrowed and past due date
  transactions = await db.transaction.find_many(
    where={
      "status": "BORROWED",
      "due_date": {"lt": now},
      "return_time": None,
    },
    include={"user": True, "book": True, "admin": True},
    order={"due_date": "asc"},
  )

  # Update their status to OVERDUE
  for trans in transactions:
    await db.transaction.update(
      where={"transaction_id": trans.transaction_id},
      data={"status": "OVERDUE"},
    )

  result: List[TransactionResponse] = []
  for trans in transactions:
    result.append(
      {
        "transaction_id": trans.transaction_id,
        "user_id": trans.user_id,
        "user_name": trans.user.name,
        "book_id": trans.book_id,
        "book_name": trans.book.book_name,
        "admin_id": trans.admin_id,
        "checkout_time": trans.checkout_time,
        "due_date": trans.due_date,
        "return_time": trans.return_time,
        "status": "OVERDUE",
        "created_at": trans.created_at,
      }
    )

  return result


@router.get("/transactions/all", response_model=List[TransactionResponse])
async def get_all_transactions(current_admin=Depends(get_current_admin)):
  """Admin gets all transactions"""
  transactions = await db.transaction.find_many(
    include={"user": True, "book": True, "admin": True},
    order={"checkout_time": "desc"},
    take=100,  # Limit to last 100
  )

  result: List[TransactionResponse] = []
  for trans in transactions:
    result.append(
      {
        "transaction_id": trans.transaction_id,
        "user_id": trans.user_id,
        "user_name": trans.user.name,
        "book_id": trans.book_id,
        "book_name": trans.book.book_name,
        "admin_id": trans.admin_id,
        "checkout_time": trans.checkout_time,
        "due_date": trans.due_date,
        "return_time": trans.return_time,
        "status": trans.status,
        "created_at": trans.created_at,
      }
    )

  return result

