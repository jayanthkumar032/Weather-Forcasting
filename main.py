# main.py (with JWT and Google OAuth)
from fastapi import FastAPI, Form, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import create_engine, Column, Integer, String, or_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from passlib.hash import bcrypt
from dotenv import load_dotenv
from authlib.integrations.starlette_client import OAuth
from jose import JWTError, jwt
import requests, os, datetime
from starlette.middleware.sessions import SessionMiddleware


# Load environment variables
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).resolve().parent / ".env"
print("🟡 Loading .env from:", env_path)
load_dotenv(dotenv_path=env_path)

# Google OAuth setup
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
oauth = OAuth()
oauth.register(
    name='google',
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)
print("✅ GOOGLE_CLIENT_ID loaded:", GOOGLE_CLIENT_ID)


# Constants
SECRET_KEY = os.getenv("SECRET_KEY", "supersecret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Database setup
DATABASE_URL = "sqlite:///./users.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# User model
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=True)
    mobile = Column(String, unique=True, nullable=True)
    password = Column(String, nullable=True)  # nullable for OAuth users

Base.metadata.create_all(bind=engine)

# FastAPI app setup
app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# JWT setup
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

def create_access_token(data: dict, expires_delta: datetime.timedelta = None):
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + (expires_delta or datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).filter_by(email=email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user



# Weather API
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
if not WEATHER_API_KEY:
    raise Exception("WEATHER_API_KEY not set")

# Routes
@app.get("/")
def root():
    return {"message": "Backend running with JWT and OAuth ✅"}

@app.post("/signup")
def signup(email: str = Form(None), mobile: str = Form(None), password: str = Form(...), db: Session = Depends(get_db)):
    if not email and not mobile:
        raise HTTPException(status_code=400, detail="Email or mobile required")
    existing = db.query(User).filter(or_(User.email == email, User.mobile == mobile)).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    hashed_pw = bcrypt.hash(password)
    user = User(email=email, mobile=mobile, password=hashed_pw)
    db.add(user)
    db.commit()
    return {"message": "User registered successfully"}

@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    email_or_mobile = form_data.username
    password = form_data.password
    user = db.query(User).filter(or_(User.email == email_or_mobile, User.mobile == email_or_mobile)).first()
    if not user or not user.password or not bcrypt.verify(password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}

@app.get("/auth/google")
async def auth_google(request: Request):
    redirect_uri = request.url_for('auth_google_callback')
    return await oauth.google.authorize_redirect(request, redirect_uri)

@app.get("/auth/google/callback")
async def auth_google_callback(request: Request, db: Session = Depends(get_db)):
    token = await oauth.google.authorize_access_token(request)
    user_info = token.get("userinfo")
    email = user_info.get("email")
    user = db.query(User).filter_by(email=email).first()
    if not user:
        user = User(email=email)
        db.add(user)
        db.commit()
    jwt_token = create_access_token({"sub": email})
    return RedirectResponse(url=f"http://localhost:8501?token={jwt_token}&email={email}")

@app.get("/weather")
def get_weather(city: str):
    url = f"http://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q={city}"
    res = requests.get(url)
    if res.status_code != 200:
        detail = res.json().get("error", {}).get("message", "City not found")
        raise HTTPException(status_code=404, detail=detail)
    data = res.json()
    return {
        "city": data["location"]["name"],
        "country": data["location"]["country"],
        "temp_c": data["current"]["temp_c"],
        "condition": data["current"]["condition"]["text"],
        "icon": data["current"]["condition"]["icon"],
        "humidity": data["current"]["humidity"],
        "pressure": data["current"]["pressure_mb"],
        "wind_kph": data["current"]["wind_kph"]
    }
