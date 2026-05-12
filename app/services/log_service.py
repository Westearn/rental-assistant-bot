from app.database.models import History
from app.services.utils import now_time


class LogService:

    def __init__(self, session):
        self.session = session

    async def log(self, user: str | None, action: str, apartment_id: int | None = None):
        self.session.add(
            History(
                user=user,
                apartment_id=apartment_id,
                action=action,
                created_at=now_time()))