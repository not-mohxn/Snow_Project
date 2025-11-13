"""
death_birth_mongo.py

Simple Python module to manage Birth and Death records in MongoDB using pymongo.

Features:
- Connects to MongoDB (URI from env var MONGO_URI or default localhost)
- Defines collections: births, deaths
- Provides CRUD functions: create, read, update, delete, list, search
- Adds basic validation and indexes
- Example usage at bottom (under __main__)

Instructions:
1) Install dependency: pip install pymongo
2) Set environment variable MONGO_URI if not using default mongodb://localhost:27017
   e.g. export MONGO_URI="mongodb://user:pass@host:27017"
3) Run: python death_birth_mongo.py

Note: This is a starter template. Modify validation rules to match your local legal/format requirements.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
import os
import re

from pymongo import MongoClient, ASCENDING
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError

# ------------------ Configuration ------------------
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "civic_records")

# ------------------ Utilities ------------------

def connect_db(uri: str = MONGO_URI, db_name: str = DB_NAME):
    client = MongoClient(uri)
    db = client[db_name]
    # Ensure indexes
    ensure_indexes(db)
    return db


def ensure_indexes(db):
    # births: index on registration_no unique, and name, dob
    db.births.create_index([("registration_no", ASCENDING)], unique=True, name="idx_birth_regno")
    db.births.create_index([("name", ASCENDING)], name="idx_birth_name")
    db.births.create_index([("dob", ASCENDING)], name="idx_birth_dob")

    # deaths: index on registration_no unique, name, dod
    db.deaths.create_index([("registration_no", ASCENDING)], unique=True, name="idx_death_regno")
    db.deaths.create_index([("name", ASCENDING)], name="idx_death_name")
    db.deaths.create_index([("dod", ASCENDING)], name="idx_death_dod")

# ------------------ Validation ------------------

REGNO_RE = re.compile(r"^[A-Z0-9-]{3,50}$", re.I)
NAME_RE = re.compile(r"^[\w\s.'-]{2,150}$", re.U)


def validate_birth(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and coerce birth record fields. Raises ValueError on bad data."""
    out = {}
    reg = data.get("registration_no")
    if not reg or not REGNO_RE.match(str(reg)):
        raise ValueError("Invalid or missing registration_no")
    out["registration_no"] = str(reg).upper()

    name = data.get("name")
    if not name or not NAME_RE.match(name):
        raise ValueError("Invalid or missing name")
    out["name"] = name.strip()

    dob = data.get("dob")
    if isinstance(dob, str):
        try:
            dob = datetime.fromisoformat(dob)
        except Exception:
            raise ValueError("dob must be ISO date string or datetime")
    if not isinstance(dob, datetime):
        raise ValueError("Invalid or missing dob")
    out["dob"] = dob

    place = data.get("place")
    out["place"] = place.strip() if isinstance(place, str) else None

    sex = data.get("sex")
    out["sex"] = sex if sex in ("M", "F", "O", None) else None

    parents = data.get("parents") or {}
    out["parents"] = {
        "father": parents.get("father"),
        "mother": parents.get("mother"),
    }

    out["created_at"] = datetime.utcnow()
    return out


def validate_death(data: Dict[str, Any]) -> Dict[str, Any]:
    out = {}
    reg = data.get("registration_no")
    if not reg or not REGNO_RE.match(str(reg)):
        raise ValueError("Invalid or missing registration_no")
    out["registration_no"] = str(reg).upper()

    name = data.get("name")
    if not name or not NAME_RE.match(name):
        raise ValueError("Invalid or missing name")
    out["name"] = name.strip()

    dod = data.get("dod")
    if isinstance(dod, str):
        try:
            dod = datetime.fromisoformat(dod)
        except Exception:
            raise ValueError("dod must be ISO date string or datetime")
    if not isinstance(dod, datetime):
        raise ValueError("Invalid or missing dod")
    out["dod"] = dod

    place = data.get("place")
    out["place"] = place.strip() if isinstance(place, str) else None

    cause = data.get("cause")
    out["cause"] = cause.strip() if isinstance(cause, str) else None

    out["created_at"] = datetime.utcnow()
    return out

# ------------------ CRUD operations ------------------

class RecordsManager:
    def __init__(self, db):
        self.db = db
        self.births: Collection = db.births
        self.deaths: Collection = db.deaths

    # Create
    def create_birth(self, data: Dict[str, Any]) -> str:
        doc = validate_birth(data)
        try:
            res = self.births.insert_one(doc)
            return str(res.inserted_id)
        except DuplicateKeyError:
            raise ValueError("A birth record with this registration_no already exists")

    def create_death(self, data: Dict[str, Any]) -> str:
        doc = validate_death(data)
        try:
            res = self.deaths.insert_one(doc)
            return str(res.inserted_id)
        except DuplicateKeyError:
            raise ValueError("A death record with this registration_no already exists")

    # Read
    def get_birth_by_regno(self, regno: str) -> Optional[Dict[str, Any]]:
        return self.births.find_one({"registration_no": regno.upper()})

    def get_death_by_regno(self, regno: str) -> Optional[Dict[str, Any]]:
        return self.deaths.find_one({"registration_no": regno.upper()})

    # Update
    def update_birth(self, regno: str, updates: Dict[str, Any]) -> int:
        # Only allow some fields to be updated
        allowed = {"name", "place", "parents", "sex"}
        upd = {k: v for k, v in updates.items() if k in allowed}
        if not upd:
            raise ValueError("No updatable fields provided")
        res = self.births.update_one({"registration_no": regno.upper()}, {"$set": upd})
        return res.modified_count

    def update_death(self, regno: str, updates: Dict[str, Any]) -> int:
        allowed = {"name", "place", "cause"}
        upd = {k: v for k, v in updates.items() if k in allowed}
        if not upd:
            raise ValueError("No updatable fields provided")
        res = self.deaths.update_one({"registration_no": regno.upper()}, {"$set": upd})
        return res.modified_count

    # Delete
    def delete_birth(self, regno: str) -> int:
        res = self.births.delete_one({"registration_no": regno.upper()})
        return res.deleted_count

    def delete_death(self, regno: str) -> int:
        res = self.deaths.delete_one({"registration_no": regno.upper()})
        return res.deleted_count

    # List / Search
    def list_births(self, limit: int = 50) -> List[Dict[str, Any]]:
        return list(self.births.find().sort([("created_at", -1)]).limit(limit))

    def list_deaths(self, limit: int = 50) -> List[Dict[str, Any]]:
        return list(self.deaths.find().sort([("created_at", -1)]).limit(limit))

    def search_births(self, query: Dict[str, Any], limit: int = 50) -> List[Dict[str, Any]]:
        return list(self.births.find(query).limit(limit))

    def search_deaths(self, query: Dict[str, Any], limit: int = 50) -> List[Dict[str, Any]]:
        return list(self.deaths.find(query).limit(limit))

# ------------------ Example CLI usage ------------------

if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Manage birth and death records in MongoDB")
    parser.add_argument("action", choices=["create_birth", "create_death", "get_birth", "get_death", "list_births", "list_deaths", "delete_birth", "delete_death", "update_birth", "update_death"], help="Action to perform")
    parser.add_argument("data", nargs="?", help="JSON string or registration_no (for get/delete)")
    args = parser.parse_args()

    db = connect_db()
    mgr = RecordsManager(db)

    try:
        if args.action == "create_birth":
            payload = json.loads(args.data)
            _id = mgr.create_birth(payload)
            print("Inserted birth id:", _id)
        elif args.action == "create_death":
            payload = json.loads(args.data)
            _id = mgr.create_death(payload)
            print("Inserted death id:", _id)
        elif args.action == "get_birth":
            print(mgr.get_birth_by_regno(args.data))
        elif args.action == "get_death":
            print(mgr.get_death_by_regno(args.data))
        elif args.action == "list_births":
            print(json.dumps(mgr.list_births(), default=str, indent=2))
        elif args.action == "list_deaths":
            print(json.dumps(mgr.list_deaths(), default=str, indent=2))
        elif args.action == "delete_birth":
            print("deleted:", mgr.delete_birth(args.data))
        elif args.action == "delete_death":
            print("deleted:", mgr.delete_death(args.data))
        elif args.action == "update_birth":
            parts = args.data.split(None, 1)
            regno = parts[0]
            payload = json.loads(parts[1])
            print("modified:", mgr.update_birth(regno, payload))
        elif args.action == "update_death":
            parts = args.data.split(None, 1)
            regno = parts[0]
            payload = json.loads(parts[1])
            print("modified:", mgr.update_death(regno, payload))
    except Exception as e:
        print("Error:", str(e))

