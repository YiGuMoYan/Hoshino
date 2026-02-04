"""
Database migration script to add 'renamed' field to rss_items table.
Run this with: python scripts/add_renamed_field.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import engine
from sqlalchemy import text

def migrate():
    print("Adding 'renamed' column to rss_items table...")
    
    with engine.connect() as conn:
        # Check if column already exists
        result = conn.execute(text("PRAGMA table_info(rss_items)"))
        columns = [row[1] for row in result]
        
        if 'renamed' in columns:
            print("✅ Column 'renamed' already exists, skipping migration")
            return
        
        # Add the column
        conn.execute(text("ALTER TABLE rss_items ADD COLUMN renamed BOOLEAN DEFAULT 0"))
        conn.commit()
        print("✅ Successfully added 'renamed' column")
        
        # Update existing rows to set renamed=0
        conn.execute(text("UPDATE rss_items SET renamed = 0 WHERE renamed IS NULL"))
        conn.commit()
        print("✅ Updated existing rows")

if __name__ == "__main__":
    migrate()
