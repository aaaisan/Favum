-- 创建数据库
CREATE DATABASE IF NOT EXISTS forum_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建用户并授权
CREATE USER IF NOT EXISTS 'forum_user'@'localhost' IDENTIFIED BY 'forum_password';
GRANT ALL PRIVILEGES ON forum_db.* TO 'forum_user'@'localhost';
FLUSH PRIVILEGES; 