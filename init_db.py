import sys
import os

# Ensure the current directory is in sys.path so we can import app modules
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)


from app.db.session import init_db
try:
    from app.worker import huey
except ImportError:
    huey = None

def main():
    print("🚀 Starting database initialization...")

    # 1. Initialize Main Database (hoshino.db)
    print("Checking Hoshino Main Database...")
    try:
        init_db()
        print("✅ Hoshino main database initialized successfully.")

        # Check and migrate columns
        from app.db.session import engine
        from sqlalchemy import inspect, text
        inspector = inspect(engine)
        columns = [c['name'] for c in inspector.get_columns('download_tasks')]
        if 'seeding_time' not in columns:
            print("⚠️ 'seeding_time' column missing in 'download_tasks'. Migrating...")
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE download_tasks ADD COLUMN seeding_time INTEGER DEFAULT -1"))
                conn.commit()
            print("✅ Migration 'add_seeding_time' completed.")

    except Exception as e:
        print(f"❌ Failed to initialize Hoshino main database: {e}")
        sys.exit(1)

    # 2. Initialize Huey Tasks Database (huey_tasks.db)
    print("Checking Huey Tasks Database...")
    if huey:
        try:
            # For SqliteHuey, the storage is initialized and tables are created upon instantiation
            # or we can explicitly call create_tables if available on the storage engine.
            if hasattr(huey.storage, 'create_tables'):
                huey.storage.create_tables()
                print("✅ Huey tasks database initialized successfully.")
            else:
                print("ℹ️  Huey storage does not require explicit table creation or is already handled.")
        except Exception as e:
            print(f"❌ Failed to initialize Huey tasks database: {e}")
            sys.exit(1)
    else:
        print("⚠️ Huey module not found, skipping Huey DB initialization.")

    print("🎉 All databases are ready!")

if __name__ == "__main__":
    main()
