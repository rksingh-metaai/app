from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Annotated, Any
from datetime import datetime, timezone, timedelta
import uuid
import bcrypt
import jwt
import calendar

from emergentintegrations.llm.chat import LlmChat, UserMessage

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

JWT_SECRET = os.environ['JWT_SECRET']
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.environ.get('JWT_EXPIRE_MINUTES', '43200'))
EMERGENT_LLM_KEY = os.environ['EMERGENT_LLM_KEY']

app = FastAPI()
api_router = APIRouter(prefix="/api")
security = HTTPBearer(auto_error=False)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8')[:72], bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode('utf-8')[:72], hashed.encode('utf-8'))
    except Exception:
        return False


def create_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


async def get_current_user(
    creds: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)]
) -> dict:
    if creds is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(creds.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = await db.users.find_one({"id": user_id, "deleted_at": None})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class RegisterIn(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    language: str = "en"


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    name: str
    email: EmailStr
    language: str
    currency: str = "INR"


class AuthOut(BaseModel):
    token: str
    user: UserOut


class AccountCreate(BaseModel):
    name: str
    type: str = "bank"  # bank, cash, card, wallet, investment
    balance: float = 0.0
    color: Optional[str] = None


class AccountUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    balance: Optional[float] = None
    color: Optional[str] = None


class BillCreate(BaseModel):
    name: str
    amount: float
    category: str = "bills"
    frequency: str = "monthly"  # monthly, weekly, yearly
    due_day: int = 1  # day of month (1-31) for monthly/yearly
    due_weekday: int = 0  # 0=Mon..6=Sun for weekly
    due_month: int = 1  # 1-12 for yearly
    account_id: Optional[str] = None


class TransactionUpdate(BaseModel):
    account_id: Optional[str] = None
    title: str
    amount: float
    type: str
    category: str
    note: Optional[str] = None
    date: Optional[str] = None


class TransactionCreate(BaseModel):
    account_id: Optional[str] = None
    title: str
    amount: float
    type: str  # income or expense
    category: str
    note: Optional[str] = None
    date: Optional[str] = None


class BudgetCreate(BaseModel):
    name: str
    category: str
    limit: float
    period: str = "monthly"


class GoalCreate(BaseModel):
    name: str
    target: float
    saved: float = 0.0


class ChatIn(BaseModel):
    message: str


CATEGORY_META = {
    "food": {"icon": "food", "color": "#F97316"},
    "shopping": {"icon": "shopping", "color": "#8B5CF6"},
    "transport": {"icon": "transport", "color": "#0EA5E9"},
    "bills": {"icon": "bills", "color": "#EF4444"},
    "entertainment": {"icon": "entertainment", "color": "#EC4899"},
    "health": {"icon": "health", "color": "#14B8A6"},
    "salary": {"icon": "salary", "color": "#16A34A"},
    "investment": {"icon": "investment", "color": "#059669"},
    "groceries": {"icon": "groceries", "color": "#84CC16"},
    "other": {"icon": "other", "color": "#737373"},
}


def clean(doc: dict) -> dict:
    if doc and "_id" in doc:
        doc = {k: v for k, v in doc.items() if k != "_id"}
    return doc


# ---------------------------------------------------------------------------
# Seed helper
# ---------------------------------------------------------------------------
async def seed_user_data(user_id: str):
    acc1 = {
        "id": str(uuid.uuid4()), "user_id": user_id, "name": "HDFC Savings",
        "type": "bank", "balance": 84250.0, "color": "#059669",
        "created_at": now_utc(), "deleted_at": None,
    }
    acc2 = {
        "id": str(uuid.uuid4()), "user_id": user_id, "name": "Cash Wallet",
        "type": "cash", "balance": 5400.0, "color": "#F97316",
        "created_at": now_utc(), "deleted_at": None,
    }
    acc3 = {
        "id": str(uuid.uuid4()), "user_id": user_id, "name": "ICICI Credit Card",
        "type": "card", "balance": -12300.0, "color": "#8B5CF6",
        "created_at": now_utc(), "deleted_at": None,
    }
    await db.accounts.insert_many([acc1, acc2, acc3])

    txns = [
        ("Monthly Salary", 65000, "income", "salary", acc1["id"], 1),
        ("Big Bazaar Groceries", 3200, "expense", "groceries", acc1["id"], 2),
        ("Zomato Order", 640, "expense", "food", acc2["id"], 2),
        ("Uber Ride", 280, "expense", "transport", acc2["id"], 3),
        ("Electricity Bill", 1850, "expense", "bills", acc1["id"], 4),
        ("Netflix Subscription", 649, "expense", "entertainment", acc3["id"], 5),
        ("Amazon Shopping", 4499, "expense", "shopping", acc3["id"], 6),
        ("Pharmacy", 780, "expense", "health", acc2["id"], 7),
        ("Mutual Fund SIP", 5000, "expense", "investment", acc1["id"], 8),
        ("Freelance Project", 12000, "income", "salary", acc1["id"], 10),
        ("Swiggy Dinner", 520, "expense", "food", acc2["id"], 11),
        ("Petrol", 2000, "expense", "transport", acc1["id"], 12),
    ]
    docs = []
    for title, amt, typ, cat, aid, days_ago in txns:
        dt = datetime.now(timezone.utc) - timedelta(days=days_ago)
        docs.append({
            "id": str(uuid.uuid4()), "user_id": user_id, "account_id": aid,
            "title": title, "amount": float(amt), "type": typ, "category": cat,
            "note": None, "date": dt.isoformat(), "created_at": now_utc(), "deleted_at": None,
        })
    await db.transactions.insert_many(docs)

    budgets = [
        ("Food & Dining", "food", 8000, "monthly"),
        ("Shopping", "shopping", 6000, "monthly"),
        ("Transport", "transport", 4000, "monthly"),
        ("Groceries", "groceries", 5000, "monthly"),
    ]
    bdocs = [{
        "id": str(uuid.uuid4()), "user_id": user_id, "name": n, "category": c,
        "limit": float(l), "period": p, "created_at": now_utc(), "deleted_at": None,
    } for n, c, l, p in budgets]
    await db.budgets.insert_many(bdocs)

    goals = [
        ("Emergency Fund", 100000, 42000),
        ("Goa Vacation", 50000, 18500),
        ("New iPhone", 80000, 31000),
    ]
    gdocs = [{
        "id": str(uuid.uuid4()), "user_id": user_id, "name": n, "target": float(t),
        "saved": float(s), "created_at": now_utc(), "deleted_at": None,
    } for n, t, s in goals]
    await db.goals.insert_many(gdocs)

    bills = [
        ("House Rent", 15000, "bills", 5, acc1["id"]),
        ("Electricity Bill", 1800, "bills", 10, acc1["id"]),
        ("Internet / Broadband", 799, "bills", 15, acc1["id"]),
        ("Mobile Recharge", 299, "bills", 20, acc2["id"]),
    ]
    bill_docs = [{
        "id": str(uuid.uuid4()), "user_id": user_id, "name": n, "amount": float(a),
        "category": c, "due_day": d, "account_id": aid, "last_paid": None,
        "created_at": now_utc(), "deleted_at": None,
    } for n, a, c, d, aid in bills]
    await db.bills.insert_many(bill_docs)


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------
@api_router.get("/")
async def root():
    return {"message": "IndicFinance API"}


@api_router.post("/auth/register", response_model=AuthOut)
async def register(body: RegisterIn):
    email = body.email.lower()
    existing = await db.users.find_one({"email": email, "deleted_at": None})
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")
    user_id = str(uuid.uuid4())
    user = {
        "id": user_id, "name": body.name, "email": email,
        "hashed_password": hash_password(body.password),
        "language": body.language, "currency": "INR",
        "created_at": now_utc(), "deleted_at": None,
    }
    await db.users.insert_one(user)
    await seed_user_data(user_id)
    token = create_token(user_id)
    return AuthOut(token=token, user=UserOut(**user))


@api_router.post("/auth/login", response_model=AuthOut)
async def login(body: LoginIn):
    email = body.email.lower()
    user = await db.users.find_one({"email": email, "deleted_at": None})
    if not user or not verify_password(body.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    token = create_token(user["id"])
    return AuthOut(token=token, user=UserOut(**user))


@api_router.get("/auth/me", response_model=UserOut)
async def me(user: dict = Depends(get_current_user)):
    return UserOut(**user)


class UpdateLanguageIn(BaseModel):
    language: str


@api_router.put("/auth/language", response_model=UserOut)
async def update_language(body: UpdateLanguageIn, user: dict = Depends(get_current_user)):
    await db.users.update_one({"id": user["id"]}, {"$set": {"language": body.language}})
    user["language"] = body.language
    return UserOut(**user)


# ---------------------------------------------------------------------------
# Accounts
# ---------------------------------------------------------------------------
@api_router.get("/accounts")
async def get_accounts(user: dict = Depends(get_current_user)):
    accounts = await db.accounts.find({"user_id": user["id"], "deleted_at": None}).to_list(200)
    return [clean(a) for a in accounts]


@api_router.post("/accounts")
async def create_account(body: AccountCreate, user: dict = Depends(get_current_user)):
    acc = {
        "id": str(uuid.uuid4()), "user_id": user["id"], "name": body.name,
        "type": body.type, "balance": body.balance,
        "color": body.color or "#059669",
        "created_at": now_utc(), "deleted_at": None,
    }
    await db.accounts.insert_one(acc)
    return clean(acc)


@api_router.delete("/accounts/{account_id}")
async def delete_account(account_id: str, user: dict = Depends(get_current_user)):
    await db.accounts.update_one(
        {"id": account_id, "user_id": user["id"]}, {"$set": {"deleted_at": now_utc()}}
    )
    return {"ok": True}


@api_router.put("/accounts/{account_id}")
async def update_account(account_id: str, body: AccountUpdate, user: dict = Depends(get_current_user)):
    updates = {k: v for k, v in body.dict().items() if v is not None}
    if updates:
        await db.accounts.update_one(
            {"id": account_id, "user_id": user["id"], "deleted_at": None}, {"$set": updates}
        )
    acc = await db.accounts.find_one({"id": account_id, "user_id": user["id"]})
    return clean(acc) if acc else {"ok": True}


# ---------------------------------------------------------------------------
# Transactions
# ---------------------------------------------------------------------------
@api_router.get("/transactions")
async def get_transactions(
    user: dict = Depends(get_current_user),
    type: Optional[str] = None,
    category: Optional[str] = None,
):
    query: dict[str, Any] = {"user_id": user["id"], "deleted_at": None}
    if type:
        query["type"] = type
    if category:
        query["category"] = category
    txns = await db.transactions.find(query).sort("date", -1).to_list(500)
    return [clean(t) for t in txns]


@api_router.post("/transactions")
async def create_transaction(body: TransactionCreate, user: dict = Depends(get_current_user)):
    txn = {
        "id": str(uuid.uuid4()), "user_id": user["id"],
        "account_id": body.account_id, "title": body.title,
        "amount": abs(body.amount), "type": body.type,
        "category": body.category, "note": body.note,
        "date": body.date or now_utc(), "created_at": now_utc(), "deleted_at": None,
    }
    await db.transactions.insert_one(txn)
    # update account balance
    if body.account_id:
        delta = txn["amount"] if body.type == "income" else -txn["amount"]
        await db.accounts.update_one(
            {"id": body.account_id, "user_id": user["id"]}, {"$inc": {"balance": delta}}
        )
    return clean(txn)


@api_router.put("/transactions/{txn_id}")
async def update_transaction(txn_id: str, body: TransactionUpdate, user: dict = Depends(get_current_user)):
    old = await db.transactions.find_one({"id": txn_id, "user_id": user["id"], "deleted_at": None})
    if not old:
        raise HTTPException(status_code=404, detail="Transaction not found")
    # reverse old balance effect
    if old.get("account_id"):
        rev = -old["amount"] if old["type"] == "income" else old["amount"]
        await db.accounts.update_one({"id": old["account_id"]}, {"$inc": {"balance": rev}})
    new_amount = abs(body.amount)
    updates = {
        "account_id": body.account_id, "title": body.title, "amount": new_amount,
        "type": body.type, "category": body.category, "note": body.note,
        "date": body.date or old.get("date"),
    }
    await db.transactions.update_one({"id": txn_id}, {"$set": updates})
    # apply new balance effect
    if body.account_id:
        delta = new_amount if body.type == "income" else -new_amount
        await db.accounts.update_one(
            {"id": body.account_id, "user_id": user["id"]}, {"$inc": {"balance": delta}}
        )
    merged = {**old, **updates}
    return clean(merged)


@api_router.delete("/transactions/{txn_id}")
async def delete_transaction(txn_id: str, user: dict = Depends(get_current_user)):
    txn = await db.transactions.find_one({"id": txn_id, "user_id": user["id"], "deleted_at": None})
    if txn:
        await db.transactions.update_one({"id": txn_id}, {"$set": {"deleted_at": now_utc()}})
        if txn.get("account_id"):
            delta = -txn["amount"] if txn["type"] == "income" else txn["amount"]
            await db.accounts.update_one({"id": txn["account_id"]}, {"$inc": {"balance": delta}})
    return {"ok": True}


# ---------------------------------------------------------------------------
# Budgets & Goals
# ---------------------------------------------------------------------------
@api_router.get("/budgets")
async def get_budgets(user: dict = Depends(get_current_user)):
    budgets = await db.budgets.find({"user_id": user["id"], "deleted_at": None}).to_list(200)
    # compute spent this month per category
    start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    txns = await db.transactions.find({
        "user_id": user["id"], "type": "expense", "deleted_at": None,
        "date": {"$gte": start.isoformat()},
    }).to_list(1000)
    spent_by_cat: dict[str, float] = {}
    for t in txns:
        spent_by_cat[t["category"]] = spent_by_cat.get(t["category"], 0) + t["amount"]
    result = []
    for b in budgets:
        b = clean(b)
        b["spent"] = spent_by_cat.get(b["category"], 0)
        result.append(b)
    return result


@api_router.post("/budgets")
async def create_budget(body: BudgetCreate, user: dict = Depends(get_current_user)):
    b = {
        "id": str(uuid.uuid4()), "user_id": user["id"], "name": body.name,
        "category": body.category, "limit": body.limit, "period": body.period,
        "created_at": now_utc(), "deleted_at": None,
    }
    await db.budgets.insert_one(b)
    b = clean(b)
    b["spent"] = 0
    return b


@api_router.delete("/budgets/{budget_id}")
async def delete_budget(budget_id: str, user: dict = Depends(get_current_user)):
    await db.budgets.update_one(
        {"id": budget_id, "user_id": user["id"]}, {"$set": {"deleted_at": now_utc()}}
    )
    return {"ok": True}


@api_router.get("/goals")
async def get_goals(user: dict = Depends(get_current_user)):
    goals = await db.goals.find({"user_id": user["id"], "deleted_at": None}).to_list(200)
    return [clean(g) for g in goals]


@api_router.post("/goals")
async def create_goal(body: GoalCreate, user: dict = Depends(get_current_user)):
    g = {
        "id": str(uuid.uuid4()), "user_id": user["id"], "name": body.name,
        "target": body.target, "saved": body.saved,
        "created_at": now_utc(), "deleted_at": None,
    }
    await db.goals.insert_one(g)
    return clean(g)


class GoalAddIn(BaseModel):
    amount: float


@api_router.post("/goals/{goal_id}/add")
async def add_to_goal(goal_id: str, body: GoalAddIn, user: dict = Depends(get_current_user)):
    await db.goals.update_one(
        {"id": goal_id, "user_id": user["id"]}, {"$inc": {"saved": body.amount}}
    )
    g = await db.goals.find_one({"id": goal_id, "user_id": user["id"]})
    return clean(g)


@api_router.delete("/goals/{goal_id}")
async def delete_goal(goal_id: str, user: dict = Depends(get_current_user)):
    await db.goals.update_one(
        {"id": goal_id, "user_id": user["id"]}, {"$set": {"deleted_at": now_utc()}}
    )
    return {"ok": True}


# ---------------------------------------------------------------------------
# Dashboard summary
# ---------------------------------------------------------------------------
@api_router.get("/dashboard/summary")
async def dashboard_summary(user: dict = Depends(get_current_user)):
    accounts = await db.accounts.find({"user_id": user["id"], "deleted_at": None}).to_list(200)
    total_balance = sum(a["balance"] for a in accounts)

    start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_txns = await db.transactions.find({
        "user_id": user["id"], "deleted_at": None, "date": {"$gte": start.isoformat()},
    }).to_list(2000)

    income = sum(t["amount"] for t in month_txns if t["type"] == "income")
    expense = sum(t["amount"] for t in month_txns if t["type"] == "expense")

    by_cat: dict[str, float] = {}
    for t in month_txns:
        if t["type"] == "expense":
            by_cat[t["category"]] = by_cat.get(t["category"], 0) + t["amount"]

    spending = []
    for cat, amt in sorted(by_cat.items(), key=lambda x: -x[1]):
        meta = CATEGORY_META.get(cat, CATEGORY_META["other"])
        spending.append({"category": cat, "amount": amt, "color": meta["color"], "icon": meta["icon"]})

    recent = await db.transactions.find(
        {"user_id": user["id"], "deleted_at": None}
    ).sort("date", -1).to_list(5)

    return {
        "total_balance": total_balance,
        "income": income,
        "expense": expense,
        "savings": income - expense,
        "accounts_count": len(accounts),
        "spending_by_category": spending,
        "recent_transactions": [clean(t) for t in recent],
    }


# ---------------------------------------------------------------------------
# Bills (recurring reminders)
# ---------------------------------------------------------------------------
def _clamp_date(year: int, month: int, day: int):
    last = calendar.monthrange(year, month)[1]
    return datetime(year, month, min(day, last), tzinfo=timezone.utc).date()


def _prev_next_due(bill: dict):
    today = datetime.now(timezone.utc).date()
    freq = bill.get("frequency", "monthly")
    if freq == "weekly":
        wd = int(bill.get("due_weekday", 0)) % 7
        delta = (today.weekday() - wd) % 7
        prev_due = today - timedelta(days=delta)
        next_sched = prev_due + timedelta(days=7)
    elif freq == "yearly":
        dm = int(bill.get("due_month", 1))
        dd = int(bill.get("due_day", 1))
        this_year = _clamp_date(today.year, dm, dd)
        if this_year <= today:
            prev_due = this_year
            next_sched = _clamp_date(today.year + 1, dm, dd)
        else:
            prev_due = _clamp_date(today.year - 1, dm, dd)
            next_sched = this_year
    else:  # monthly
        dd = int(bill.get("due_day", 1))
        this_month = _clamp_date(today.year, today.month, dd)
        if this_month <= today:
            prev_due = this_month
            nm, ny = (today.month + 1, today.year) if today.month < 12 else (1, today.year + 1)
            next_sched = _clamp_date(ny, nm, dd)
        else:
            pm, py = (today.month - 1, today.year) if today.month > 1 else (12, today.year - 1)
            prev_due = _clamp_date(py, pm, dd)
            next_sched = this_month
    return prev_due, next_sched


def _bill_status(bill: dict):
    today = datetime.now(timezone.utc).date()
    prev_due, next_sched = _prev_next_due(bill)

    last_paid_date = None
    if bill.get("last_paid"):
        try:
            last_paid_date = datetime.fromisoformat(bill["last_paid"]).date()
        except Exception:
            last_paid_date = None

    created_date = today
    if bill.get("created_at"):
        try:
            created_date = datetime.fromisoformat(bill["created_at"]).date()
        except Exception:
            created_date = today

    paid_current = last_paid_date is not None and last_paid_date >= prev_due

    if paid_current:
        nd = next_sched
        paid = True
    elif prev_due <= today and prev_due >= created_date:
        nd = prev_due  # due today or overdue
        paid = False
    else:
        nd = next_sched
        paid = False

    days_until = (nd - today).days
    return nd.isoformat(), days_until, paid


def _decorate_bill(b: dict) -> dict:
    b = clean(b)
    nd, days_until, paid = _bill_status(b)
    b["next_due"] = nd
    b["days_until"] = days_until
    b["paid_this_month"] = paid
    return b


@api_router.get("/bills")
async def get_bills(user: dict = Depends(get_current_user)):
    bills = await db.bills.find({"user_id": user["id"], "deleted_at": None}).to_list(200)
    result = [_decorate_bill(b) for b in bills]
    result.sort(key=lambda x: x["days_until"])
    return result


@api_router.get("/bills/history")
async def bills_history(user: dict = Depends(get_current_user)):
    payments = await db.bill_payments.find(
        {"user_id": user["id"], "deleted_at": None}
    ).sort("paid_at", -1).to_list(200)
    return [clean(p) for p in payments]


def _bill_doc(body: BillCreate, user_id: str) -> dict:
    return {
        "name": body.name, "amount": body.amount, "category": body.category,
        "frequency": body.frequency if body.frequency in ("monthly", "weekly", "yearly") else "monthly",
        "due_day": max(1, min(31, body.due_day)),
        "due_weekday": max(0, min(6, body.due_weekday)),
        "due_month": max(1, min(12, body.due_month)),
        "account_id": body.account_id,
    }


@api_router.post("/bills")
async def create_bill(body: BillCreate, user: dict = Depends(get_current_user)):
    b = {
        "id": str(uuid.uuid4()), "user_id": user["id"],
        **_bill_doc(body, user["id"]),
        "last_paid": None, "created_at": now_utc(), "deleted_at": None,
    }
    await db.bills.insert_one(b)
    return _decorate_bill(b)


@api_router.put("/bills/{bill_id}")
async def update_bill(bill_id: str, body: BillCreate, user: dict = Depends(get_current_user)):
    await db.bills.update_one(
        {"id": bill_id, "user_id": user["id"], "deleted_at": None},
        {"$set": _bill_doc(body, user["id"])},
    )
    return {"ok": True}


@api_router.post("/bills/{bill_id}/pay")
async def pay_bill(bill_id: str, user: dict = Depends(get_current_user)):
    bill = await db.bills.find_one({"id": bill_id, "user_id": user["id"], "deleted_at": None})
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    paid_at = now_utc()
    await db.bills.update_one({"id": bill_id}, {"$set": {"last_paid": paid_at}})
    # log a transaction
    txn = {
        "id": str(uuid.uuid4()), "user_id": user["id"], "account_id": bill.get("account_id"),
        "title": bill["name"], "amount": float(bill["amount"]), "type": "expense",
        "category": bill.get("category", "bills"), "note": "Bill payment",
        "date": paid_at, "created_at": paid_at, "deleted_at": None,
    }
    await db.transactions.insert_one(txn)
    # record payment history
    account = await db.accounts.find_one({"id": bill.get("account_id")}) if bill.get("account_id") else None
    payment = {
        "id": str(uuid.uuid4()), "user_id": user["id"], "bill_id": bill_id,
        "name": bill["name"], "amount": float(bill["amount"]),
        "account_id": bill.get("account_id"),
        "account_name": account["name"] if account else None,
        "paid_at": paid_at, "created_at": paid_at, "deleted_at": None,
    }
    await db.bill_payments.insert_one(payment)
    if bill.get("account_id"):
        await db.accounts.update_one(
            {"id": bill["account_id"], "user_id": user["id"]}, {"$inc": {"balance": -float(bill["amount"])}}
        )
    return {"ok": True}


@api_router.delete("/bills/{bill_id}")
async def delete_bill(bill_id: str, user: dict = Depends(get_current_user)):
    await db.bills.update_one(
        {"id": bill_id, "user_id": user["id"]}, {"$set": {"deleted_at": now_utc()}}
    )
    return {"ok": True}


# ---------------------------------------------------------------------------
# Spending trends (month over month)
# ---------------------------------------------------------------------------
@api_router.get("/dashboard/trends")
async def spending_trends(user: dict = Depends(get_current_user)):
    now = datetime.now(timezone.utc)
    keys = []
    for i in range(5, -1, -1):
        mm = now.month - i
        yy = now.year
        while mm <= 0:
            mm += 12
            yy -= 1
        keys.append((yy, mm))

    txns = await db.transactions.find(
        {"user_id": user["id"], "deleted_at": None}
    ).to_list(5000)
    buckets = {(yy, mm): {"income": 0.0, "expense": 0.0} for (yy, mm) in keys}
    for t in txns:
        try:
            dt = datetime.fromisoformat(t["date"])
        except Exception:
            continue
        key = (dt.year, dt.month)
        if key in buckets and t["type"] in ("income", "expense"):
            buckets[key][t["type"]] += t["amount"]

    months = [
        {
            "year": yy,
            "month": mm,
            "income": buckets[(yy, mm)]["income"],
            "expense": buckets[(yy, mm)]["expense"],
        }
        for (yy, mm) in keys
    ]
    return {"months": months}


# ---------------------------------------------------------------------------
# AI Money Assistant
# ---------------------------------------------------------------------------
LANG_NAMES = {
    "en": "English", "hi": "Hindi", "ta": "Tamil",
    "te": "Telugu", "bn": "Bengali", "mr": "Marathi",
}


@api_router.get("/assistant/history")
async def assistant_history(user: dict = Depends(get_current_user)):
    msgs = await db.chat_messages.find(
        {"user_id": user["id"], "deleted_at": None}
    ).sort("created_at", 1).to_list(200)
    return [clean(m) for m in msgs]


@api_router.post("/assistant/chat")
async def assistant_chat(body: ChatIn, user: dict = Depends(get_current_user)):
    # Build financial context
    summary = await dashboard_summary(user)
    lang = LANG_NAMES.get(user.get("language", "en"), "English")

    top_spend = ", ".join(
        f"{s['category']}: ₹{int(s['amount'])}" for s in summary["spending_by_category"][:5]
    ) or "none"

    system = (
        f"You are Arth, a friendly and knowledgeable personal finance assistant inside the "
        f"IndicFinance app for an Indian user. All money is in Indian Rupees (₹). "
        f"IMPORTANT: Reply ONLY in {lang}. Keep replies concise (under 130 words), warm, "
        f"practical and specific to the user's data. Use short paragraphs or bullet points. "
        f"Do not use markdown headers.\n\n"
        f"User's current finances this month:\n"
        f"- Total balance across accounts: ₹{int(summary['total_balance'])}\n"
        f"- Income this month: ₹{int(summary['income'])}\n"
        f"- Expenses this month: ₹{int(summary['expense'])}\n"
        f"- Net savings this month: ₹{int(summary['savings'])}\n"
        f"- Top spending categories: {top_spend}\n"
    )

    # store user message
    user_msg = {
        "id": str(uuid.uuid4()), "user_id": user["id"], "role": "user",
        "content": body.message, "created_at": now_utc(), "deleted_at": None,
    }
    await db.chat_messages.insert_one(user_msg)

    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"assistant-{user['id']}",
            system_message=system,
        ).with_model("openai", "gpt-5.4")
        reply = await chat.send_message(UserMessage(text=body.message))
        reply_text = reply if isinstance(reply, str) else str(reply)
    except Exception as e:
        logger.error(f"AI assistant error: {e}")
        reply_text = "Sorry, I couldn't process that right now. Please try again."

    ai_msg = {
        "id": str(uuid.uuid4()), "user_id": user["id"], "role": "assistant",
        "content": reply_text, "created_at": now_utc(), "deleted_at": None,
    }
    await db.chat_messages.insert_one(ai_msg)
    return {"reply": reply_text, "message": clean(ai_msg)}


app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
