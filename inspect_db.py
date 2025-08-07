#!/usr/bin/env python3
"""
Simple database inspection script
Run this after running tests to examine the data
"""

import sqlite3
import json
from pathlib import Path

def inspect_database():
    """Inspect the test database contents"""
    db_path = Path("database.db")
    
    if not db_path.exists():
        print("❌ Database file not found. Run the tests first.")
        return
    
    print("🔍 Inspecting database contents...")
    print("=" * 50)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print(f"📋 Found {len(tables)} tables:")
    for table in tables:
        table_name = table[0]
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"   - {table_name}: {count} records")
    
    print("\n" + "=" * 50)
    
    # Show documents
    print("📄 Documents:")
    cursor.execute("SELECT id, document_name, document_type, status, created_at FROM documents")
    documents = cursor.fetchall()
    for doc in documents:
        print(f"   - ID: {doc[0]}, Name: {doc[1]}, Type: {doc[2]}, Status: {doc[3]}")
    
    print("\n" + "=" * 50)
    
    # Show blocks
    print("🧱 Document Blocks:")
    cursor.execute("""
        SELECT b.id, b.block_type, b.block_order, b.content, d.document_name 
        FROM document_blocks b 
        JOIN documents d ON b.document_id = d.id 
        ORDER BY d.id, b.block_order
    """)
    blocks = cursor.fetchall()
    for block in blocks:
        content = json.loads(block[3]) if block[3] else {}
        print(f"   - Document: {block[4]}, Block: {block[1]} (order: {block[2]})")
        print(f"     Content: {content}")
    
    print("\n" + "=" * 50)
    
    # Show organizations and users
    print("🏢 Organizations:")
    cursor.execute("SELECT id, organization_name FROM organizations")
    orgs = cursor.fetchall()
    for org in orgs:
        print(f"   - ID: {org[0]}, Name: {org[1]}")
    
    print("\n👥 Users:")
    cursor.execute("SELECT id, name, email FROM users")
    users = cursor.fetchall()
    for user in users:
        print(f"   - ID: {user[0]}, Name: {user[1]}, Email: {user[2]}")
    
    conn.close()
    print("\n✅ Database inspection complete!")

if __name__ == "__main__":
    inspect_database() 