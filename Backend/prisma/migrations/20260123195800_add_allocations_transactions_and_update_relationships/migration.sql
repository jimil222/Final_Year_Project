-- ============================================================================
-- DATA-PRESERVING MIGRATION (FROM BROKEN STATE)
-- Current state: shelves has columns but no primary key
-- This migration fixes and completes the schema update
-- ============================================================================

-- Step 1: Fix the shelves table - populate shelf_id from shelf_number for existing rows
UPDATE `shelves` SET `shelf_id` = CAST(`shelf_number` AS UNSIGNED) WHERE `shelf_id` = 0;

-- Step 2: Make shelf_id auto_increment and primary key
ALTER TABLE `shelves` MODIFY `shelf_id` BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY;

-- Step 3: Add unique constraint on shelf_number
CREATE UNIQUE INDEX `shelves_shelf_number_key` ON `shelves`(`shelf_number`);

-- Step 4: Add shelf_id column to books (will map from current shelf_number)
ALTER TABLE `books` ADD COLUMN `shelf_id` BIGINT NOT NULL DEFAULT 1 AFTER `nfc_tag_id`;

-- Step 5: Map books.shelf_id from books.shelf_number
UPDATE `books` b
SET b.`shelf_id` = (
    SELECT s.`shelf_id` 
    FROM `shelves` s 
    WHERE CAST(s.`shelf_number` AS UNSIGNED) = b.`shelf_number`
    LIMIT 1
);

-- Step 6: Drop the old shelf_number column from books
ALTER TABLE `books` DROP COLUMN `shelf_number`;

-- Step 7: Add timestamps to books table
ALTER TABLE `books`
    ADD COLUMN `created_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    ADD COLUMN `updated_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3);

-- Step 8: Update book status enum to include RESERVED
ALTER TABLE `books` 
    MODIFY `status` ENUM('AVAILABLE', 'RESERVED', 'BORROWED', 'MAINTENANCE') NOT NULL DEFAULT 'AVAILABLE';

-- Step 9: Add foreign key from books to shelves
ALTER TABLE `books` ADD CONSTRAINT `books_shelf_id_fkey` 
    FOREIGN KEY (`shelf_id`) REFERENCES `shelves`(`shelf_id`) 
    ON DELETE RESTRICT ON UPDATE CASCADE;

-- Step 10: Add updated_at to users table
ALTER TABLE `users` ADD COLUMN `updated_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3);

-- Step 11: Backup admin data
CREATE TEMPORARY TABLE `admin_backup` AS SELECT * FROM `admin`;

-- Step 12: Drop the old admin table
DROP TABLE `admin`;

-- Step 13: Create new admins table
CREATE TABLE `admins` (
    `admin_id` BIGINT NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(100) NOT NULL,
    `email` VARCHAR(150) NOT NULL,
    `password` VARCHAR(255) NOT NULL,
    `created_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    UNIQUE INDEX `admins_email_key`(`email`),
    PRIMARY KEY (`admin_id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Step 14: Migrate admin data
INSERT INTO `admins` (`name`, `email`, `password`, `created_at`)
SELECT `name`, `email`, `password`, `created_at` FROM `admin_backup`;

-- Step 15: Drop the temporary backup table
DROP TEMPORARY TABLE `admin_backup`;

-- Step 16: Create user_book_allocations table
CREATE TABLE `user_book_allocations` (
    `allocation_id` BIGINT NOT NULL AUTO_INCREMENT,
    `user_id` BIGINT NOT NULL,
    `book_id` BIGINT NOT NULL,
    `admin_id` BIGINT NOT NULL,
    `status` ENUM('RESERVED', 'BORROWED', 'RETURNED') NOT NULL,
    `reserved_at` DATETIME(3) NULL,
    `borrowed_at` DATETIME(3) NULL,
    `returned_at` DATETIME(3) NULL,
    `created_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    UNIQUE INDEX `user_book_allocations_book_id_key`(`book_id`),
    PRIMARY KEY (`allocation_id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Step 17: Create transactions table
CREATE TABLE `transactions` (
    `transaction_id` BIGINT NOT NULL AUTO_INCREMENT,
    `user_id` BIGINT NOT NULL,
    `book_id` BIGINT NOT NULL,
    `admin_id` BIGINT NOT NULL,
    `checkout_time` DATETIME(3) NOT NULL,
    `due_date` DATETIME(3) NOT NULL,
    `return_time` DATETIME(3) NULL,
    `status` ENUM('BORROWED', 'RETURNED', 'OVERDUE') NOT NULL,
    `created_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    PRIMARY KEY (`transaction_id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Step 18: Add foreign keys for user_book_allocations
ALTER TABLE `user_book_allocations` ADD CONSTRAINT `user_book_allocations_user_id_fkey` 
    FOREIGN KEY (`user_id`) REFERENCES `users`(`user_id`) 
    ON DELETE RESTRICT ON UPDATE CASCADE;

ALTER TABLE `user_book_allocations` ADD CONSTRAINT `user_book_allocations_book_id_fkey` 
    FOREIGN KEY (`book_id`) REFERENCES `books`(`book_id`) 
    ON DELETE RESTRICT ON UPDATE CASCADE;

ALTER TABLE `user_book_allocations` ADD CONSTRAINT `user_book_allocations_admin_id_fkey` 
    FOREIGN KEY (`admin_id`) REFERENCES `admins`(`admin_id`) 
    ON DELETE RESTRICT ON UPDATE CASCADE;

-- Step 19: Add foreign keys for transactions
ALTER TABLE `transactions` ADD CONSTRAINT `transactions_user_id_fkey` 
    FOREIGN KEY (`user_id`) REFERENCES `users`(`user_id`) 
    ON DELETE RESTRICT ON UPDATE CASCADE;

ALTER TABLE `transactions` ADD CONSTRAINT `transactions_book_id_fkey` 
    FOREIGN KEY (`book_id`) REFERENCES `books`(`book_id`) 
    ON DELETE RESTRICT ON UPDATE CASCADE;

ALTER TABLE `transactions` ADD CONSTRAINT `transactions_admin_id_fkey` 
    FOREIGN KEY (`admin_id`) REFERENCES `admins`(`admin_id`) 
    ON DELETE RESTRICT ON UPDATE CASCADE;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================
