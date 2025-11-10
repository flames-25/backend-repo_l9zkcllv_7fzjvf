import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from bson.objectid import ObjectId

from database import db, create_document, get_documents
from schemas import User, Listing

app = FastAPI(title="Book Marketplace API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helpers
class ObjectIdStr(BaseModel):
    id: str


def to_public(doc: dict):
    if not doc:
        return doc
    d = doc.copy()
    if "_id" in d:
        d["id"] = str(d.pop("_id"))
    return d


# Root and health
@app.get("/")
def read_root():
    return {"message": "Book Marketplace Backend running"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": "❌ Not Set",
        "database_name": "❌ Not Set",
        "connection_status": "Not Connected",
        "collections": [],
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set"
            response["database_name"] = getattr(db, "name", "✅ Connected")
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    # env check
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response


# Auth (very simple demo: SHA256 client-side hash expected)
class RegisterPayload(BaseModel):
    name: str
    email: EmailStr
    password_hash: str


class LoginPayload(BaseModel):
    email: EmailStr
    password_hash: str


@app.post("/api/auth/register")
def register(payload: RegisterPayload):
    # Check if user exists
    exists = db["user"].find_one({"email": payload.email}) if db else None
    if exists:
        raise HTTPException(status_code=400, detail="Email already registered")
    uid = create_document("user", User(name=payload.name, email=payload.email, password_hash=payload.password_hash))
    return {"id": uid, "name": payload.name, "email": payload.email}


@app.post("/api/auth/login")
def login(payload: LoginPayload):
    user = db["user"].find_one({"email": payload.email}) if db else None
    if not user or user.get("password_hash") != payload.password_hash:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    user_public = {"id": str(user["_id"]), "name": user.get("name"), "email": user.get("email")}
    return user_public


# Listings
class ListingCreate(BaseModel):
    title: str
    author: str
    isbn: Optional[str] = None
    price: float
    condition: str
    cover: Optional[str] = None
    description: Optional[str] = None
    seller_email: EmailStr


@app.post("/api/listings")
def create_listing(payload: ListingCreate):
    # ensure seller exists
    seller = db["user"].find_one({"email": payload.seller_email}) if db else None
    if not seller:
        raise HTTPException(status_code=400, detail="Seller not found")
    listing = Listing(**payload.model_dump())
    lid = create_document("listing", listing)
    return {"id": lid}


class ListingsQuery(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    isbn: Optional[str] = None


@app.get("/api/listings")
def list_listings(title: Optional[str] = None, author: Optional[str] = None, isbn: Optional[str] = None):
    filter_q = {}
    if title:
        filter_q["title"] = {"$regex": title, "$options": "i"}
    if author:
        filter_q["author"] = {"$regex": author, "$options": "i"}
    if isbn:
        filter_q["isbn"] = {"$regex": isbn, "$options": "i"}
    docs = get_documents("listing", filter_q)
    return [to_public(d) for d in docs]


@app.get("/api/listings/{listing_id}")
def get_listing(listing_id: str):
    try:
        doc = db["listing"].find_one({"_id": ObjectId(listing_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID")
    if not doc:
        raise HTTPException(status_code=404, detail="Not found")
    return to_public(doc)


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
