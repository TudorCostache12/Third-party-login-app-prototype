import os
import json
from dotenv import load_dotenv

result = load_dotenv("OAuthClientData.env")
print (result)

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TENANT_ID = os.getenv("TENANT_ID")
REDIRECT_URI = os.getenv("REDIRECT_URI")
SCOPES = os.getenv("SCOPES").split(",")

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
AUTHORIZE_ENDPOINT = f"{AUTHORITY}/oauth2/v2.0/authorize"
TOKEN_ENDPOINT = f"{AUTHORITY}/oauth2/v2.0/token"


JWT_EXPIRE_DAYS = int(os.getenv("JWT_EXPIRE_DAYS"))
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")
JWT_SECRET = os.getenv("JWT_SECRET")
