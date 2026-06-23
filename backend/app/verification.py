from __future__ import annotations

import httpx

from .config import Settings


def send_verification_message(settings: Settings, channel: str, phone_number: str, code: str) -> str:
    if channel == "email":
        return "placeholder"

    from_number = settings.twilio_whatsapp_from if channel == "whatsapp" else settings.twilio_sms_from
    if not settings.twilio_account_sid or not settings.twilio_auth_token or not from_number:
        return "placeholder"

    to_number = f"whatsapp:{phone_number}" if channel == "whatsapp" else phone_number
    message_from = from_number if channel == "sms" else from_number
    url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.twilio_account_sid}/Messages.json"
    response = httpx.post(
        url,
        data={
            "From": message_from,
            "To": to_number,
            "Body": f"Your FairHire verification code is {code}.",
        },
        auth=(settings.twilio_account_sid, settings.twilio_auth_token),
        timeout=10,
    )
    response.raise_for_status()
    return "sent"
