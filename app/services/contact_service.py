from sqlalchemy import select
from app.database.models import Contact


class ContactService:

    def __init__(self, session):
        self.session = session

    async def get_contacts(self, apartment_id: int):
        result = await self.session.execute(select(Contact).where(Contact.apartment_id == apartment_id).order_by(Contact.id))
        return result.scalars().all()