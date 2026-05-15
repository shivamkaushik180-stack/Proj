import json
import os
from pathlib import Path
from django.conf import settings
from django.utils import timezone
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from datetime import timedelta


# ─────────────────────────────────────────────
# CONFIG FILE
# ─────────────────────────────────────────────

ADMIN_CONFIG_FILE = Path(settings.BASE_DIR) / "admin_config.json"


# ─────────────────────────────────────────────
# PIN SAVE / LOAD
# ─────────────────────────────────────────────

def save_admin_pin(pin):
    """Save admin PIN securely in file"""
    try:
        config = {
            "ADMIN_PIN": pin,
            "updated_at": timezone.now().isoformat()
        }

        ADMIN_CONFIG_FILE.write_text(json.dumps(config, indent=2))

        # optional file permission (ignore on Windows)
        try:
            os.chmod(ADMIN_CONFIG_FILE, 0o600)
        except:
            pass

        return True

    except Exception as e:
        print("Error saving admin PIN:", e)
        return False


def load_admin_pin():
    """Load admin PIN from file"""
    try:
        if ADMIN_CONFIG_FILE.exists():
            with open(ADMIN_CONFIG_FILE, "r") as f:
                data = json.load(f)
                return data.get("ADMIN_PIN")
    except Exception as e:
        print("Error loading admin PIN:", e)

    return getattr(settings, "ADMIN_PIN", "123456")


# ─────────────────────────────────────────────
# ADMIN PIN DECORATOR
# ─────────────────────────────────────────────

def admin_pin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        if not request.session.get('admin_pin_verified'):
            messages.error(request, "Admin PIN required")