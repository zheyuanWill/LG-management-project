"""
Email Service — Async email sending via SMTP.

Disabled by default; set SMTP_ENABLED=true and configure SMTP_* env vars to enable.
"""
import logging
from typing import Optional, List
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger("email_service")


class EmailService:
    def __init__(self):
        from app.core.config import settings
        self.enabled = settings.SMTP_ENABLED
        self.host = settings.SMTP_HOST
        self.port = settings.SMTP_PORT
        self.user = settings.SMTP_USER
        self.password = settings.SMTP_PASSWORD
        self.from_addr = settings.SMTP_FROM or settings.SMTP_USER
        self.use_tls = settings.SMTP_USE_TLS

    async def send_email(
        self,
        to: str | List[str],
        subject: str,
        body: str,
        html: bool = False,
    ) -> bool:
        if not self.enabled:
            logger.info("Email disabled, skipping: to=%s subject=%s", to, subject)
            return False

        try:
            import aiosmtplib

            recipients = [to] if isinstance(to, str) else to
            msg = MIMEMultipart()
            msg["From"] = self.from_addr
            msg["To"] = ", ".join(recipients)
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "html" if html else "plain", "utf-8"))

            await aiosmtplib.send(
                msg,
                hostname=self.host,
                port=self.port,
                username=self.user,
                password=self.password,
                use_tls=self.use_tls,
            )
            logger.info("Email sent to %s: %s", recipients, subject)
            return True
        except Exception as e:
            logger.error("Failed to send email: %s", e)
            return False

    async def send_inquiry_email(self, supplier_email: str, supplier_name: str, inquiry_no: str, items_desc: str = ""):
        subject = f"询价函 - {inquiry_no}"
        body = (
            f"<p>尊敬的 {supplier_name}：</p>"
            f"<p>我司现有以下项目需要贵司报价，烦请查收：</p>"
            f"<p>{items_desc}</p>"
            f"<p>请于收到本函后3个工作日内回复报价，谢谢！</p>"
            f"<p>此致<br/>鲁顾国际贸易</p>"
        )
        return await self.send_email(supplier_email, subject, body, html=True)

    async def send_quote_email(self, customer_email: str, customer_name: str, quote_no: str, total_amount: str):
        subject = f"报价单 - {quote_no}"
        body = (
            f"<p>尊敬的 {customer_name}：</p>"
            f"<p>感谢贵司询价，我司报价单号 {quote_no}，总金额 {total_amount}。</p>"
            f"<p>详细报价单请见附件，如有疑问请随时联系。</p>"
            f"<p>此致<br/>鲁顾国际贸易</p>"
        )
        return await self.send_email(customer_email, subject, body, html=True)

    async def send_collection_reminder(self, customer_email: str, customer_name: str, contract_no: str, amount: str, overdue_days: int):
        subject = f"回款提醒 - {contract_no}"
        body = (
            f"<p>尊敬的 {customer_name}：</p>"
            f"<p>合同 {contract_no} 尚有款项 {amount} 已逾期 {overdue_days} 天，"
            f"烦请尽快安排付款，谢谢！</p>"
            f"<p>此致<br/>鲁顾国际贸易</p>"
        )
        return await self.send_email(customer_email, subject, body, html=True)


email_service = EmailService()
