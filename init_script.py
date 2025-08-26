# init_script.py
import sys
import subprocess
from cli.errors import handle_error

def run_migrations():
    """Run database migrations with proper error handling."""
    try:
        # Alembic migration command
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        handle_error(f"Migration failed: {e.stderr.strip()}")
        sys.exit(1)
    except Exception as e:
        handle_error(f"Unexpected error while running migrations: {e}")
        sys.exit(1)


if __name__ == "__main__":
    print("Running database initialization...")
    run_migrations()
    print("Database ready.")
