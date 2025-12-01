from fastapi import Header, HTTPException, status, Depends, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from typing import Optional
import secrets
import ipaddress

from ratemate_app.core.config import settings

_basic = HTTPBasic()

def require_admin(credentials: HTTPBasicCredentials = Depends(_basic), admin_key: Optional[str] = Header(None), request: Request = None):
    if not admin_key or not settings.ADMIN_PANEL_KEY or not secrets.compare_digest(admin_key, settings.ADMIN_PANEL_KEY):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid admin key")
    if not settings.ADMIN_BASIC_USERNAME or not settings.ADMIN_BASIC_PASSWORD:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin basic auth not configured")
    if not secrets.compare_digest(credentials.username, settings.ADMIN_BASIC_USERNAME) or not secrets.compare_digest(credentials.password, settings.ADMIN_BASIC_PASSWORD):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin credentials")
    
    cidr = settings.model_fields.get('ADMIN_ALLOWED_CIDR') and settings.ADMIN_ALLOWED_CIDR
    if cidr:
        try:
            net = ipaddress.ip_network(cidr, strict=False)
            ip = ipaddress.ip_address(request.client.host) if request and request.client else None
            if ip and ip not in net:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access denied")
        except ValueError:
            pass

    