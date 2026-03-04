"""Lambda handler for scheduled warranty expiry checks via CloudWatch Events."""

import os
import boto3

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.db import WARRANTIES_TABLE, PRODUCTS_TABLE, scan_table, get_item

from warranty_tracker import ReminderScheduler

ses_client = boto3.client("ses")
reminder_scheduler = ReminderScheduler(threshold_days=30)

SES_SENDER_EMAIL = os.environ.get("SES_SENDER_EMAIL", "noreply@warrantytracker.com")


def _get_product_name(product_id):
    """Look up a product name by ID."""
    item = get_item(PRODUCTS_TABLE, {"id": product_id})
    return item.get("name", "Unknown Product") if item else "Unknown Product"


def _send_ses_email(to_email, subject, body):
    """Send an email via Amazon SES."""
    try:
        ses_client.send_email(
            Source=SES_SENDER_EMAIL,
            Destination={"ToAddresses": [to_email]},
            Message={
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": {"Text": {"Data": body, "Charset": "UTF-8"}},
            },
        )
        print(f"SES email sent to {to_email}: {subject}")
    except Exception as e:
        print(f"SES email failed for {to_email}: {e}")


def check_expiring(event, context):
    """Scheduled function: scan all warranties, send SES email reminders.

    Triggered daily by CloudWatch Events.
    Sends email notifications via SES for warranties expiring within 30 days.
    """
    all_warranties = scan_table(WARRANTIES_TABLE)

    users = {}
    for w in all_warranties:
        uid = w.get("user_id")
        if uid:
            users.setdefault(uid, []).append(w)

    total_expiring = 0
    total_emails_sent = 0

    for user_id, warranties in users.items():
        expiring = reminder_scheduler.find_expiring_warranties(warranties)
        total_expiring += len(expiring)

        for w in expiring:
            product_name = _get_product_name(w.get("product_id", ""))
            w["product_name"] = product_name

            notification = reminder_scheduler.generate_notification(
                w, w.get("user_email", "")
            )

            print(f"Expiring warranty: user={user_id}, warranty={w.get('id')}, "
                  f"days_remaining={w.get('days_remaining')}, provider={w.get('provider')}")

            user_email = w.get("user_email")
            if user_email:
                _send_ses_email(user_email, notification["subject"], notification["body"])
                total_emails_sent += 1

    result = {
        "message": "Warranty expiry check completed",
        "total_warranties_scanned": len(all_warranties),
        "total_expiring": total_expiring,
        "total_emails_sent": total_emails_sent,
    }
    print(f"Reminder check result: {result}")
    return result
