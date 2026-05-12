from sqlalchemy import select, update
from app.database.models import Tariff


class TariffService:

    def __init__(self, session):
        self.session = session

    async def get_all_tariffs(self):
        # Запрашиваем все объекты из таблицы Tariff
        query = select(Tariff).order_by(Tariff.id)
        result = await self.session.execute(query)
        
        # scalars() превращает результат в список объектов
        return result.scalars().all()
    
    async def get_tariff(self, tariff_id: int):
        return await self.session.get(Tariff, tariff_id)
    
    async def update_tariff_value(self, tariff_id: int, new_value: float):
        # Обновление значения тарифа
        stmt = update(Tariff).where(Tariff.id == tariff_id).values(value=new_value)
        await self.session.execute(stmt)