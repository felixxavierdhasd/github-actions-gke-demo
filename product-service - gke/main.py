import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError

from database import get_db, engine
import models
import schemas
import auth


# ---------------------------
# DB INIT (NON-BLOCKING)
# ---------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    async def init_db():
        retries = 5
        for attempt in range(retries):
            try:
                models.Base.metadata.create_all(bind=engine)
                print("✅ Database connected and tables created")
                break
            except OperationalError:
                print(f"⏳ DB not ready (attempt {attempt + 1}/{retries}), retrying...")
                await asyncio.sleep(3)
        else:
            print("❌ DB not reachable after retries, continuing anyway")

    # Start DB initialization in background, do not block FastAPI startup
    asyncio.create_task(init_db())

    yield  # Server becomes ready immediately


app = FastAPI(title="Product Service", lifespan=lifespan)

# ---------------------------
# CORS Middleware
# ---------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# ---------------------------
# ROOT (Health Check)
# ---------------------------
@app.get("/")
def root():
    return {"status": "OK"}


# ---------------------------
# USER APIs
# ---------------------------
@app.post("/register", response_model=schemas.UserResponse)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing_user = (
        db.query(models.User).filter(models.User.username == user.username).first()
    )
    if existing_user:
        raise ValueError("User already exists")
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        role=models.UserRole.USER,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.post("/login", response_model=schemas.TokenResponse)
def login(user_login: schemas.UserLogin, db: Session = Depends(get_db)):
    user = (
        db.query(models.User)
        .filter(models.User.username == user_login.username)
        .first()
    )
    if not user or not auth.verify_password(user_login.password, user.hashed_password):
        raise ValueError("Invalid credentials")
    access_token = auth.create_access_token(data={"sub": user.id, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer", "user": user}


# ---------------------------
# PRODUCT APIs
# ---------------------------
@app.post("/products", response_model=schemas.ProductResponse)
def create_product(
    product: schemas.ProductCreate,
    admin: models.User = Depends(auth.require_admin),
    db: Session = Depends(get_db),
):
    db_product = models.Product(
        name=product.name,
        description=product.description,
        price=product.price,
        stock=product.stock,
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


@app.get("/products", response_model=list[schemas.ProductResponse])
def list_products(db: Session = Depends(get_db)):
    return db.query(models.Product).all()


@app.get("/products/{product_id}", response_model=schemas.ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise ValueError("Product not found")
    return product


@app.get("/health")
def health():
    return {"status": "healthy"}
