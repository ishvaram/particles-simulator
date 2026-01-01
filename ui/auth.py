import os
import secrets
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

basic_security = HTTPBasic()

# TODO: credentials shouldn't be hardcoded, adding here for now
API_USERNAME = os.environ.get("API_USERNAME", "admin")
API_PASSWORD = os.environ.get("API_PASSWORD", "admin123")


def verify_basic_auth(credentials: HTTPBasicCredentials = Depends(basic_security)):
    correct_username = secrets.compare_digest(credentials.username, API_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, API_PASSWORD)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username
