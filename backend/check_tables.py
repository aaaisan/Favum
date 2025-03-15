#!/usr/bin/env python3
"""
检查数据库中的表和记录
"""

import os
import mysql.connector
from mysql.connector import Error

try:
    connection = mysql.connector.connect(
        host=os.environ.get('MYSQL_HOST', 'localhost'),
        database=os.environ.get('MYSQL_DATABASE', 'forum_db'),
        user=os.environ.get('MYSQL_USER', 'aaaisan'),
        password=os.environ.get('MYSQL_PASSWORD', 'aaaisan78'),
        port=os.environ.get('MYSQL_PORT', '3306')
    )
    
    if connection.is_connected():
        print('Connected to MySQL database')
        cursor = connection.cursor()
        
        # 检查users表
        cursor.execute('SELECT COUNT(*) FROM users')
        users_count = cursor.fetchone()[0]
        print(f'Users count: {users_count}')
        
        if users_count > 0:
            cursor.execute('SELECT id, username, email, role FROM users LIMIT 5')
            users = cursor.fetchall()
            print("Sample users:")
            for user in users:
                print(f"  ID: {user[0]}, Username: {user[1]}, Email: {user[2]}, Role: {user[3]}")
        
        # 检查sections表
        cursor.execute('SELECT COUNT(*) FROM sections')
        sections_count = cursor.fetchone()[0]
        print(f'Sections count: {sections_count}')
        
        if sections_count > 0:
            cursor.execute('SELECT id, name FROM sections LIMIT 5')
            sections = cursor.fetchall()
            print("Sample sections:")
            for section in sections:
                print(f"  ID: {section[0]}, Name: {section[1]}")
        
        # 检查categories表
        cursor.execute('SELECT COUNT(*) FROM categories')
        categories_count = cursor.fetchone()[0]
        print(f'Categories count: {categories_count}')
        
        if categories_count > 0:
            cursor.execute('SELECT id, name FROM categories LIMIT 5')
            categories = cursor.fetchall()
            print("Sample categories:")
            for category in categories:
                print(f"  ID: {category[0]}, Name: {category[1]}")
        
        cursor.close()
except Error as e:
    print(f'Error: {e}')
finally:
    if 'connection' in locals() and connection.is_connected():
        connection.close()
        print('MySQL connection closed') 