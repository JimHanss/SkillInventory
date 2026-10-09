"""Create demo skills explicitly; existing skills are never overwritten."""

from sqlalchemy.orm import Session

from skill_inventory.db import get_engine
from skill_inventory.seed import seed

if __name__ == "__main__":
    with Session(get_engine()) as session:
        seed(session)
    print("Demo skills are ready; existing skills were preserved.")
