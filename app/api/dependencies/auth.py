from fastapi import Depends, HTTPException
from jose import JWTError, jwt
from app.core.security import JWT_SECRET, ALGORITHM

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")