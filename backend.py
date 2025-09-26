from fastapi import FastAPI, Request, Cookie, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
import httpx, secrets, hashlib, base64, time
import config
import jwt
from datetime import datetime, timedelta, timezone
from fastapi.middleware.cors import CORSMiddleware
from jwt.algorithms import RSAAlgorithm
from starlette.middleware.base import BaseHTTPMiddleware

app = FastAPI()


#Implement middleware for intercepting every request/response.
#Requests taken only from port 4200 where Angular is running.
#Allows cookies and headers, every HTTP method and every tye of header.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[config.FRONTEND_LOGIN_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



_pkce_store = {} # dict containing key = state and value = {"verifier": verifier_value, "nonce": nonce_value}      
_sessions = {} # dict containing key = session_id and value = claims(scopes extracted from Microsoft user)  
_jwks = None # contains public keys necessary for validating the signature of id_token
_jwks_ts = 0 # timestamp for the latest update of the key set.



#generates code verifier for the PKCE flow
def gen_code_verifier():
    return base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode()


#generates code challange based on verifier passed as an argument
def code_challenge(verifier):
    h = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(h).rstrip(b"=").decode()



#returns the JWKS either from the OIDC provider (Microsoft) or from local cache if the timestamp < 1hr
async def fetch_jwks():
    global _jwks, _jwks_ts
    now = time.time()
    if _jwks and now - _jwks_ts < 3600:
        return _jwks
    async with httpx.AsyncClient() as c:
        cfg = await c.get(config.OIDC_CONFIG_URL)
        jwks_url = cfg.json()["jwks_uri"]
        r = await c.get(jwks_url)
        _jwks = r.json()
        _jwks_ts = now
        return _jwks



# Builds the authorization URL with the necessary info and redirects to the Microsoft Authorization endpoint for login
@app.get("/login")
def login():

    state = secrets.token_urlsafe(16)
    nonce = secrets.token_urlsafe(16)
    verifier = gen_code_verifier()
    challenge = code_challenge(verifier)
    _pkce_store[state] = {"verifier": verifier, "nonce": nonce}
    
    authorize_url = (
        f"{config.AUTHORIZE_ENDPOINT}"
        f"?client_id={config.CLIENT_ID}"
        f"&response_type=code"
        f"&redirect_uri={config.REDIRECT_URI}"
        f"&scope={' '.join(config.SCOPES)}"
        f"&state={state}"
        f"&code_challenge={challenge}"
        f"&code_challenge_method=S256"
        f"&nonce={nonce}"
    )
    print(authorize_url)
    return RedirectResponse(authorize_url)



# After being redirected from Microsoft, the function trades the code for necessary tokens.
# Extracts id_token and checks validity with Microsoft JWKS.
# Creates a valid session and stores it in cookie to redirect to frontend
@app.get("/auth/callback")
async def auth_callback(code: str = None, state: str = None, error: str = None):
    if error:
        return JSONResponse({"error": error}, status_code=400)
    data = _pkce_store.pop(state, None)
    if not code:
        return JSONResponse({"error": "Authorization code missing"}, status_code=400)
    if not data:
        return JSONResponse({"error": "invalid data"}, status_code=400)
        

    token_data = {
        "client_id": config.CLIENT_ID,
        "client_secret": config.CLIENT_SECRET, #not needed if the application allows public client flows(can be changed in Azure)
        "code": code,
        "redirect_uri": config.REDIRECT_URI,
        "grant_type": "authorization_code",
        "code_verifier": data["verifier"],
    }

    async with httpx.AsyncClient() as client:
        token_resp = await client.post(config.TOKEN_ENDPOINT, data=token_data)
        
    if token_resp.status_code != 200:
        return JSONResponse({"error": "Failed to obtain token", "details": token_resp.text}, status_code=token_resp.status_code)

    tokens = token_resp.json()
    id_token = tokens.get("id_token")
    if not id_token:
        return JSONResponse({"error": "No id_token received"}, status_code=400)


    try:
        jwks = await fetch_jwks()
        hdr = jwt.get_unverified_header(id_token)
        key = next(k for k in jwks["keys"] if k["kid"] == hdr["kid"])
        pub = RSAAlgorithm.from_jwk(key)
        claims = jwt.decode(id_token, pub, algorithms=["RS256"], audience=config.CLIENT_ID)
        if claims.get("nonce") != data["nonce"]:
            raise Exception("nonce mismatch")
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=401)

    session_id = secrets.token_urlsafe(32)
    _sessions[session_id] = claims

    
    response =RedirectResponse(url = config.CALLBACK_URL)

    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        secure=True, 
        samesite="none"
    )
    return response
    

# Verifies if session from cookie exists and is valid.
# Returns info about user back to frontend. 
@app.get("/me")
async def get_me(session_id: str = Cookie(None)):
    if not session_id or session_id not in _sessions:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return _sessions[session_id]

