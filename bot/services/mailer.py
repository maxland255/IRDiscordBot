import jinja2
import logging
import aiosmtplib

from pathlib import Path
from datetime import datetime

from email.message import EmailMessage
from email.utils import formatdate

from bot.core.config import get_settings

logger = logging.getLogger(__name__)


class VerificationMailer:
    def __init__(self):
        self.settings = get_settings()

        self.template_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(searchpath=Path("bot/templates"))
        )

    async def send_verification_code_email(self, guild_name: str, to_email: str, code: str) -> bool:
        """
        Send a verification code email to the specified email address.
        Return True if the email was sent successfully, False otherwise.
        :param guild_name: The guild name
        :param to_email:
        :param code:
        :return:
        """

        print(code)

        return True

        template = self.template_env.get_template("verification_email.html")
        html_content = template.render(
            guild_name=guild_name,
            code=code,
            current_year=datetime.now().year
        )

        msg = EmailMessage()
        msg["From"] = self.settings.SMTP_SENDER_EMAIL
        msg["To"] = to_email
        msg["Subject"] = f"Your Verification Code for {guild_name}"
        msg["Date"] = formatdate(localtime=False)

        msg.add_alternative(html_content, subtype='html')

        msg.set_content(
            f"Hello,\n\n"
            f"Your verification code for {guild_name} is: {code}\n\n"
            f"Please enter this code in the verification prompt to complete your verification.\n\n"
            f"If you did not request this code, please ignore this email.\n\n"
            f"Thank you,\n"
            f"{guild_name} Team"
        )

        try:
            if self.settings.SMTP_USE_TLS and self.settings.SMTP_START_TLS:
                raise ValueError("Both SMTP_USE_TLS and SMTP_START_TLS cannot be True at the same time.")

            await aiosmtplib.send(
                msg,
                hostname=self.settings.SMTP_HOST,
                port=self.settings.SMTP_PORT,
                username=self.settings.SMTP_USERNAME,
                password=self.settings.SMTP_PASSWORD,
                use_tls=self.settings.SMTP_USE_TLS,
                start_tls=self.settings.SMTP_START_TLS,
            )
            logger.info(f"Verification email sent to {to_email} for guild {guild_name}.")
            return True
        except Exception as e:
            logger.error(f"Failed to send verification email to {to_email} for guild {guild_name}.", exc_info=e)
            return False
