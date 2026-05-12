from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import timedelta, timezone
from app.notifications.payment_tasks import notify_and_update_rent, late_payment_reminder


def setup_scheduler(bot):
    scheduler = AsyncIOScheduler(timezone=timezone(timedelta(hours=7)))
    # print(f"Текущее время в планировщике: {datetime.now(timezone(timedelta(hours=7)))}")
    
    # Добавляем задачу: каждый день в 09:00
    scheduler.add_job(
        notify_and_update_rent, 
        trigger="cron", 
        hour=9, 
        minute=0, 
        args=[bot])
    
    scheduler.add_job(
        late_payment_reminder, 
        trigger="cron", 
        hour=12, 
        minute=0, 
        args=[bot])
    
    return scheduler