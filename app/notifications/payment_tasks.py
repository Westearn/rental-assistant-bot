from app.database.db import SessionLocal
from app.services.apartment_service import ApartmentService
from app.services.log_service import LogService
from app.config import settings


async def notify_and_update_rent(bot):
    async with SessionLocal() as session:
        service = ApartmentService(session)
        logService = LogService(session)

        billing_list = await service.process_monthly_billing(days_before=2)

        if not billing_list:
            return

        await service.process_bill_rent(billing_list)        

        report = "📊 *Ежедневный отчет по начислениям:*\n\n"
        for apt in billing_list:
            report += (
                f"🏠 *Объект:* {apt.address}\n"
                f"📅 *Срок оплаты:* через 2 дня ({apt.due_day}-е число)\n"
                f"💰 *Начислено:* {apt.rent} ₽\n"
                f"📈 *Текущий долг:* {apt.debt} ₽\n"
                f"────────────────────\n")
            
            await logService.log(
                action=f"{apt.address}: Произведено начисление арендной платы {apt.rent} ₽ в сумму долга. Текущий долг: {apt.debt} ₽")

        for admin_id in settings.admins:
            try:
                await bot.send_message(
                    chat_id=admin_id, 
                    text=report,
                    parse_mode="Markdown")
            except Exception:
                continue


async def late_payment_reminder(bot):
    async with SessionLocal() as session:
        service = ApartmentService(session)

        overdue_list = await service.get_overdue_apartments()

        if not overdue_list:
            return

        report = "📊 *Ежедневный отчет по должникам:*\n\n"
        for apt in overdue_list:
            report += (
                f"🏠 *Объект:* {apt.address}\n"
                f"📅 *Срок оплаты:* {apt.due_day}-е число\n"
                f"📈 *Текущий долг:* {apt.debt} ₽\n"
                f"────────────────────\n")
            
        for admin_id in settings.admins:
            try:
                await bot.send_message(
                    chat_id=admin_id, 
                    text=report,
                    parse_mode="Markdown")
            except Exception:
                continue