from sqlalchemy import select, desc
from app.database.models import MeterReading
from app.services.utils import now_time


class MeterReadingService:

    def __init__(self, session):
        self.session = session

    async def get_meters(self, apartment_id: int):
        result = await self.session.execute(
            select(MeterReading)
            .where(MeterReading.apartment_id == apartment_id)
            .order_by(desc(MeterReading.id))
            .limit(1))
        
        return result.scalars().one_or_none()

    async def save_reading(self, apartment_id: int, hot: int, cold: int, el: int):
        reading = MeterReading(
            apartment_id=apartment_id,
            hot_water=hot,
            cold_water=cold,
            electricity=el,
            created_at=now_time()
        )
        self.session.add(reading)