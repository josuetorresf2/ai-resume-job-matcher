from __future__ import annotations

import httpx

from .config import Settings


def _send_whatsapp_cloud_message(settings: Settings, phone_number: str, code: str) -> str | None:
    if not settings.whatsapp_cloud_access_token or not settings.whatsapp_cloud_phone_number_id:
        return None

    normalized_phone = phone_number.removeprefix("+")
    url = f"https://graph.facebook.com/{settings.whatsapp_cloud_api_version}/{settings.whatsapp_cloud_phone_number_id}/messages"
    response = httpx.post(
        url,
        headers={
            "Authorization": f"Bearer {settings.whatsapp_cloud_access_token}",
            "Content-Type": "application/json",
        },
        json={
            "messaging_product": "whatsapp",
            "to": normalized_phone,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": f"Your FairHire verification code is {code}.",
            },
        },
        timeout=10,
    )
    response.raise_for_status()
    return "sent"


def send_verification_message(settings: Settings, channel: str, phone_number: str, code: str) -> str:
    if channel == "email":
        return "placeholder"

    if channel == "whatsapp":
        whatsapp_cloud_status = _send_whatsapp_cloud_message(settings, phone_number, code)
        if whatsapp_cloud_status:
            return whatsapp_cloud_status

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
