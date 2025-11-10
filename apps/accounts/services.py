#  apps/accounts/services.py
from __future__ import annotations

from typing import Dict

from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import User


def issue_tokens(user: User) -> Dict[str, str]:

    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}
