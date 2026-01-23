/*
  Warnings:

  - The primary key for the `books` table will be changed. If it partially fails, the table could be left without primary key constraint.
  - You are about to drop the column `created_at` on the `books` table. All the data in the column will be lost.
  - You are about to drop the column `department` on the `books` table. All the data in the column will be lost.
  - You are about to alter the column `status` on the `books` table. The data in that column could be lost. The data in that column will be cast from `VarChar(191)` to `Enum(EnumId(0))`.
  - A unique constraint covering the columns `[nfc_tag_id]` on the table `books` will be added. If there are existing duplicate values, this will fail.
  - Added the required column `nfc_tag_id` to the `books` table without a default value. This is not possible if the table is not empty.
  - Added the required column `shelf_number` to the `books` table without a default value. This is not possible if the table is not empty.

*/
-- AlterTable
ALTER TABLE `books` DROP PRIMARY KEY,
    DROP COLUMN `created_at`,
    DROP COLUMN `department`,
    ADD COLUMN `nfc_tag_id` VARCHAR(100) NOT NULL,
    ADD COLUMN `shelf_number` BIGINT NOT NULL,
    MODIFY `book_id` BIGINT NOT NULL AUTO_INCREMENT,
    MODIFY `book_name` VARCHAR(255) NOT NULL,
    MODIFY `author` VARCHAR(255) NULL,
    MODIFY `status` ENUM('AVAILABLE', 'BORROWED', 'MAINTENANCE') NOT NULL DEFAULT 'AVAILABLE',
    ADD PRIMARY KEY (`book_id`);

-- CreateTable
CREATE TABLE `shelves` (
    `shelf_number` BIGINT NOT NULL,

    PRIMARY KEY (`shelf_number`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateIndex
CREATE UNIQUE INDEX `books_nfc_tag_id_key` ON `books`(`nfc_tag_id`);

-- AddForeignKey
ALTER TABLE `books` ADD CONSTRAINT `books_shelf_number_fkey` FOREIGN KEY (`shelf_number`) REFERENCES `shelves`(`shelf_number`) ON DELETE RESTRICT ON UPDATE CASCADE;
