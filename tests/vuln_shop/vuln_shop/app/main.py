from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import Base, engine
from .routers import auth, orders, products
from . import seed

app = FastAPI(title="vuln_shop", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(orders.router)
app.include_router(products.router)


@app.on_event("startup")
def on_startup():
    seed.run()


@app.get("/")
def root():
    return {"service": "vuln_shop", "status": "running"}
