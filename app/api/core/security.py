from jose import jwt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET")
ALGORITHM = os.getenv("ALGORITHM")

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(datetime.timezone.utc) + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM) 