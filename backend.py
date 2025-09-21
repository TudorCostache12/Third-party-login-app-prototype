from fastapi import FastAPI, Request, Cookie, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
import httpx
import config
import jwt
from datetime import datetime, timedelta, timezone
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/login")
def login():
    authorize_url = (
        f"{config.AUTHORIZE_ENDPOINT}"
        f"?client_id={config.CLIENT_ID}"
        f"&response_type=code"
        f"&redirect_uri={config.REDIRECT_URI}"
        f"&response_mode=query"
        f"&scope={' '.join(config.SCOPES)}"
    )
    print(authorize_url)
    return RedirectResponse(authorize_url)

@app.get("/auth/callback")
async def auth_callback(request: Request, code: str = None, error: str = None):
    if error:
        return JSONResponse({"error": error})
    if not code:
        return JSONResponse({"error": "Authorization code missing"}, status_code=400)
        

    token_data = {
        "client_id": config.CLIENT_ID,
        "client_secret": config.CLIENT_SECRET,
        "code": code,
        "redirect_uri": config.REDIRECT_URI,
        "grant_type": "authorization_code",
    }

    async with httpx.AsyncClient() as client:
        token_resp = await client.post(config.TOKEN_ENDPOINT, data=token_data)
        
    if token_resp.status_code != 200:
        return JSONResponse({"error": "Failed to obtain token", "details": token_resp.text}, status_code=token_resp.status_code)

    tokens = token_resp.json()


    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    async with httpx.AsyncClient() as client:
        user_resp = await client.get("https://graph.microsoft.com/v1.0/me", headers=headers)

    if user_resp.status_code != 200:
        return JSONResponse({"error": "Failed to fetch user info", "details": user_resp.text}, status_code=user_resp.status_code)

    user_info = user_resp.json()


    payload_intern = {
        "sub": user_info.get("id"),
        "email": user_info.get("mail") or user_info.get("userPrincipalName"),
        "name": user_info.get("displayName"),
        "exp": datetime.now(timezone.utc) + timedelta(days=config.JWT_EXPIRE_DAYS),
    }
    jwt_token = jwt.encode(payload_intern, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)

    
    response =RedirectResponse(url = "http://localhost:4200/callback")

    response.set_cookie(
        key="session_token",
        value=jwt_token,
        httponly=True,
        secure=False, 
        samesite="lax"
    )
    return response
    

@app.get("/me")
async def get_me(session_token: str = Cookie(None)):
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        payload = jwt.decode(session_token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    return {
        "name": payload.get("name"),
        "email": payload.get("email")
    }

