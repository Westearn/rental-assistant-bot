from sqlalchemy import select
from datetime import datetime, timedelta

from app.database.models import Apartment


class ApartmentService:

    def __init__(self, session):
        self.session = session

    async def get_apartments(self):
        result = await self.session.execute(select(Apartment).order_by(Apartment.id))
        return result.scalars().all()

    async def get_apartment(self, apartment_id: int):
        return await self.session.get(Apartment, apartment_id)
    
    async def process_monthly_billing(self, days_before: int):
        target_date = datetime.now() + timedelta(days=days_before)
        target_day = target_date.day

        query = select(Apartment).where(Apartment.due_day == target_day)
        result = await self.session.execute(query)

        return result.scalars().all()
    
    async def process_bill_rent(self, apartments: list[Apartment]):
        for apt in apartments:
            apt.debt += apt.rent

        await self.session.commit()
    
    async def get_overdue_apartments(self):
        now = datetime.now()
        day_1 = (now + timedelta(days=1)).day
        day_2 = (now + timedelta(days=2)).day

        query = select(Apartment).where(
            Apartment.debt > 0,
            Apartment.due_day != day_1,
            Apartment.due_day != day_2)
        result = await self.session.execute(query)

        return result.scalars().all()
        