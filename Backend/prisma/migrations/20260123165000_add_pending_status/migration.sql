-- Add PENDING status to AllocationStatus enum
ALTER TABLE `user_book_allocations` MODIFY `status` ENUM('PENDING', 'RESERVED', 'BORROWED', 'RETURNED') NOT NULL DEFAULT 'PENDING';
