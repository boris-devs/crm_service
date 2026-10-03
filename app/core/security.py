import secrets
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.core.config import Settings, get_settings

_basic = HTTPBasic(auto_error=False, realm="Mini CRM")


def require_admin(
    credentials: Annotated[HTTPBasicCredentials | None, Depends(_basic)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    if not settings.admin_password:
        return
    valid = credentials is not None and (
        secrets.compare_digest(credentials.username.encode(), settings.admin_username.encode())
        & secrets.compare_digest(credentials.password.encode(), settings.admin_password.encode())
    )
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
            headers={"WWW-Authenticate": 'Basic realm="Mini CRM"'},
        )
