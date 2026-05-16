"""
connectors/push.py — FCM Mobile Push Notification Connector
============================================================
Sends push notifications to procurement managers' phones via Firebase Cloud Messaging.

Setup:
  1. pip install firebase-admin
  2. Create Firebase project: https://console.firebase.google.com
  3. Download service account JSON → set FIREBASE_CREDENTIALS_PATH env var
  4. Mobile app subscribes to topic: "procurement_managers"

No-ops silently if FIREBASE_CREDENTIALS_PATH is not set.
"""
import os
import logging

logger = logging.getLogger(__name__)

FIREBASE_CONFIGURED = bool(os.environ.get("FIREBASE_CREDENTIALS_PATH"))


def push_to_mobile(shadow_id: int, vendor: str, amount: float, risk: float) -> bool:
    """
    Send a push notification to all devices subscribed to 'procurement_managers' topic.

    Returns True if sent successfully, False otherwise (no crash on failure).
    """
    if not FIREBASE_CONFIGURED:
        logger.debug(
            f"[Push] FIREBASE_CREDENTIALS_PATH not set — "
            f"skipping alert for shadow #{shadow_id}"
        )
        return False

    try:
        import firebase_admin
        from firebase_admin import messaging, credentials

        cred_path = os.environ["FIREBASE_CREDENTIALS_PATH"]
        if not firebase_admin._apps:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)

        msg = messaging.Message(
            notification=messaging.Notification(
                title=f"Shadow alert — ${amount:,.0f}",
                body=f"{vendor} | Risk {risk:.0%} | Tap to review"
            ),
            topic="procurement_managers",
            data={
                "shadow_id": str(shadow_id),
                "screen":    "ShadowDetail",
            }
        )
        messaging.send(msg)
        logger.info(f"[Push] FCM notification sent for shadow #{shadow_id}")
        return True

    except ImportError:
        logger.warning(
            "[Push] firebase-admin not installed. Run: pip install firebase-admin"
        )
        return False
    except Exception as e:
        logger.warning(f"[Push] FCM error: {e}")
        return False
