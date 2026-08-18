
import logging

logger = logging.getLogger(__name__)

def send_push_notification(user_id: str, title: str, body: str) -> None:
    
    logger.info('[TASK] Push notification → %s | %s: %s', user_id, title, body)

def send_email_notification(user_email: str, subject: str, body: str) -> None:
    
    logger.info('[TASK] Email → %s | Subject: %s', user_email, subject)
