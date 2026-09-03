import os
from fastapi import FastAPI, Request, Form, HTTPException, UploadFile, File, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, Table
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime, timedelta
from pathlib import Path
import secrets, hashlib, os, json, shutil, re, csv, io

BASE_DIR = Path(__file__).resolve().parent
DB_URL = os.getenv('DATABASE_URL', f"sqlite:///{BASE_DIR/'punembaruar.db'}")
if DB_URL.startswith('postgres://'):
    DB_URL = 'postgresql+psycopg://' + DB_URL[len('postgres://'):]
elif DB_URL.startswith('postgresql://') and '+psycopg' not in DB_URL:
    DB_URL = 'postgresql+psycopg://' + DB_URL[len('postgresql://'):]
engine = create_engine(DB_URL, connect_args={"check_same_thread": False} if DB_URL.startswith('sqlite') else {})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

professional_categories = Table(
    'professional_categories', Base.metadata,
    Column('professional_id', ForeignKey('professionals.id'), primary_key=True),
    Column('category_id', ForeignKey('categories.id'), primary_key=True)
)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    phone = Column(String(32), unique=True, nullable=False, index=True)
    role = Column(String(20), default='client')
    created_at = Column(DateTime, default=datetime.utcnow)
    requests = relationship('ServiceRequest', back_populates='client')

class OTPCode(Base):
    __tablename__ = 'otp_codes'
    id = Column(Integer, primary_key=True)
    phone = Column(String(32), index=True, nullable=False)
    code_hash = Column(String(128), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)

class Category(Base):
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    slug = Column(String(120), unique=True, nullable=False)
    parent_id = Column(Integer, ForeignKey('categories.id'), nullable=True)
    active = Column(Boolean, default=False)
    approval_status = Column(String(40), default='APPLICATION')
    verification_level = Column(String(40), default='UNVERIFIED')
    responsible_person = Column(String(160), nullable=True)
    nipt = Column(String(80), nullable=True)
    business_address = Column(String(255), nullable=True)
    maps_url = Column(String(500), nullable=True)
    verification_notes = Column(Text, nullable=True)
    physical_visit = Column(Boolean, default=False)
    professionals = relationship('Professional', secondary=professional_categories, back_populates='categories')

class Professional(Base):
    __tablename__ = 'professionals'
    id = Column(Integer, primary_key=True)
    name = Column(String(160), nullable=False)
    phone = Column(String(32), unique=True, nullable=False)
    whatsapp = Column(String(32), nullable=False)
    professional_type = Column(String(40), default='business')
    city = Column(String(80), nullable=False)
    zone = Column(String(120), nullable=True)
    description = Column(Text, nullable=True)
    verified = Column(Boolean, default=False)
    founding_member = Column(Boolean, default=True)
    rating = Column(Float, default=0)
    plan = Column(String(30), default='FREE')
    active = Column(Boolean, default=True)
    response_rate = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    categories = relationship('Category', secondary=professional_categories, back_populates='professionals')
    offers = relationship('Offer', back_populates='professional')

class Vehicle(Base):
    __tablename__ = 'vehicles'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    make = Column(String(80))
    model = Column(String(80))
    year = Column(String(10))
    engine = Column(String(80))
    fuel = Column(String(40))

class ServiceRequest(Base):
    __tablename__ = 'requests'
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)
    request_type = Column(String(60), nullable=False)
    description = Column(Text, nullable=False)
    city = Column(String(80), nullable=False)
    zone = Column(String(120), nullable=True)
    vehicle_make = Column(String(80), nullable=True)
    vehicle_model = Column(String(80), nullable=True)
    vehicle_year = Column(String(10), nullable=True)
    vehicle_engine = Column(String(80), nullable=True)
    vehicle_fuel = Column(String(40), nullable=True)
    urgency = Column(String(40), nullable=True)
    preferred_timing = Column(String(80), nullable=True)
    mileage = Column(String(30), nullable=True)
    symptom = Column(String(80), nullable=True)
    warning_light = Column(String(120), nullable=True)
    part_name = Column(String(160), nullable=True)
    part_code = Column(String(120), nullable=True)
    part_condition_preference = Column(String(40), nullable=True)
    status = Column(String(30), default='RECEIVING_OFFERS')
    source = Column(String(60), default='direct')
    created_at = Column(DateTime, default=datetime.utcnow)
    client = relationship('User', back_populates='requests')
    offers = relationship('Offer', back_populates='request', cascade='all, delete-orphan')

class Offer(Base):
    __tablename__ = 'offers'
    id = Column(Integer, primary_key=True)
    request_id = Column(Integer, ForeignKey('requests.id'), nullable=False)
    professional_id = Column(Integer, ForeignKey('professionals.id'), nullable=False)
    price = Column(Float, nullable=True)
    price_from = Column(Float, nullable=True)
    price_to = Column(Float, nullable=True)
    brand = Column(String(120), nullable=True)
    condition = Column(String(40), nullable=True)
    in_stock = Column(Boolean, nullable=True)
    warranty = Column(String(120), nullable=True)
    delivery = Column(Boolean, nullable=True)
    quote_type = Column(String(40), nullable=True)
    diagnostic_fee = Column(Float, nullable=True)
    labor_price = Column(Float, nullable=True)
    parts_price = Column(Float, nullable=True)
    estimated_time = Column(String(80), nullable=True)
    appointment_note = Column(String(160), nullable=True)
    earliest_appointment = Column(String(120), nullable=True)
    parts_type = Column(String(80), nullable=True)
    includes_vat = Column(Boolean, nullable=True)
    message = Column(Text, nullable=True)
    status = Column(String(30), default='SENT')
    created_at = Column(DateTime, default=datetime.utcnow)
    request = relationship('ServiceRequest', back_populates='offers')
    professional = relationship('Professional', back_populates='offers')

class Notification(Base):
    __tablename__ = 'notifications'
    id = Column(Integer, primary_key=True)
    professional_id = Column(Integer, ForeignKey('professionals.id'), nullable=False)
    request_id = Column(Integer, ForeignKey('requests.id'), nullable=False)
    channel = Column(String(30), default='whatsapp')
    status = Column(String(30), default='queued')
    payload = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)



class RequestMedia(Base):
    __tablename__ = 'request_media'
    id = Column(Integer, primary_key=True)
    request_id = Column(Integer, ForeignKey('requests.id'), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    media_type = Column(String(40), default='image')
    created_at = Column(DateTime, default=datetime.utcnow)

class ProfessionalMedia(Base):
    __tablename__ = 'professional_media'
    id = Column(Integer, primary_key=True)
    professional_id = Column(Integer, ForeignKey('professionals.id'), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    media_type = Column(String(40), default='image')
    created_at = Column(DateTime, default=datetime.utcnow)

class AuthSession(Base):
    __tablename__ = 'auth_sessions'
    id = Column(Integer, primary_key=True)
    token = Column(String(160), unique=True, index=True, nullable=False)
    phone = Column(String(32), index=True, nullable=False)
    role = Column(String(20), nullable=False)
    user_id = Column(Integer, nullable=True)
    professional_id = Column(Integer, nullable=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True)
    request_id = Column(Integer, ForeignKey('requests.id'), nullable=False, index=True)
    sender_role = Column(String(20), nullable=False)
    sender_id = Column(Integer, nullable=False)
    body = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Review(Base):
    __tablename__ = 'reviews'
    id = Column(Integer, primary_key=True)
    request_id = Column(Integer, ForeignKey('requests.id'), unique=True, nullable=False)
    client_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    professional_id = Column(Integer, ForeignKey('professionals.id'), nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class VerificationEvidence(Base):
    __tablename__ = 'verification_evidence'
    id = Column(Integer, primary_key=True)
    professional_id = Column(Integer, ForeignKey('professionals.id'), index=True)
    evidence_type = Column(String(40), nullable=False)  # PHOTO / VIDEO / DOCUMENT / OTHER
    file_url = Column(String(600), nullable=False)
    label = Column(String(160), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Report(Base):
    __tablename__ = 'reports'
    id = Column(Integer, primary_key=True)
    reporter_phone = Column(String(40), nullable=True)
    target_type = Column(String(40), nullable=False)  # professional/request/offer/message
    target_id = Column(Integer, nullable=False)
    reason = Column(String(120), nullable=False)
    details = Column(Text, nullable=True)
    status = Column(String(30), default='OPEN')
    created_at = Column(DateTime, default=datetime.utcnow)

class JobOutcome(Base):
    __tablename__ = 'job_outcomes'
    id = Column(Integer, primary_key=True)
    request_id = Column(Integer, ForeignKey('requests.id'), index=True)
    offer_id = Column(Integer, ForeignKey('offers.id'), nullable=True)
    outcome = Column(String(40), nullable=False)  # COMPLETED / NO_SHOW / CANCELLED / DISPUTED
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class NotificationEvent(Base):
    __tablename__ = 'notification_events'
    id = Column(Integer, primary_key=True)
    user_type = Column(String(30), nullable=False)  # CLIENT / PROFESSIONAL
    user_id = Column(Integer, nullable=False, index=True)
    channel = Column(String(30), default='WHATSAPP')
    event_type = Column(String(50), nullable=False)  # NEW_REQUEST/NEW_OFFER/OFFER_ACCEPTED/UNREAD_CHAT/JOB_CONFIRMATION/REVIEW
    request_id = Column(Integer, nullable=True, index=True)
    job_id = Column(Integer, nullable=True, index=True)
    status = Column(String(30), default='QUEUED')
    grouped_count = Column(Integer, default=1)
    payload = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime, nullable=True)

class JobConfirmation(Base):
    __tablename__ = 'job_confirmations'
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, nullable=False, index=True)
    party_type = Column(String(30), nullable=False)  # CLIENT / PROFESSIONAL
    party_id = Column(Integer, nullable=False)
    answer = Column(String(30), nullable=False)  # YES / NO / STILL_IN_PROGRESS
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class ManagedCategory(Base):
    __tablename__ = 'managed_categories'
    id = Column(Integer, primary_key=True)
    name = Column(String(120), unique=True, nullable=False, index=True)
    slug = Column(String(140), unique=True, nullable=False, index=True)
    category_type = Column(String(40), default='AUTOMOTIVE')
    priority = Column(Integer, default=100)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class TrialCreditLedger(Base):
    __tablename__ = 'trial_credit_ledger'
    id = Column(Integer, primary_key=True)
    professional_id = Column(Integer, ForeignKey('professionals.id'), index=True)
    request_id = Column(Integer, ForeignKey('requests.id'), index=True)
    action = Column(String(30), nullable=False)  # CONSUMED / REFUNDED
    reason = Column(String(160), nullable=True)
    admin_note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class RequestTrustReview(Base):
    __tablename__ = 'request_trust_reviews'
    id = Column(Integer, primary_key=True)
    request_id = Column(Integer, ForeignKey('requests.id'), unique=True, index=True)
    status = Column(String(30), default='PENDING')  # PENDING/VALID/FAKE/SPAM/DUPLICATE
    admin_note = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)

class AppSetting(Base):
    __tablename__ = 'app_settings'
    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(String(500), nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

Base.metadata.create_all(engine)
UPLOAD_DIR = BASE_DIR/'uploads'
UPLOAD_DIR.mkdir(exist_ok=True)

app = FastAPI(title='PunëMbaruar', version='1.6.0-render-ready')
app.mount('/static', StaticFiles(directory=BASE_DIR), name='static')
templates = Jinja2Templates(directory=str(BASE_DIR/'templates'))
security = HTTPBasic(auto_error=False)

def require_admin(credentials: HTTPBasicCredentials | None = Depends(security)):
    expected_user = os.getenv('ADMIN_USERNAME')
    expected_pass = os.getenv('ADMIN_PASSWORD')
    if not expected_user or not expected_pass:
        return True  # local DEV mode only
    if not credentials or not (secrets.compare_digest(credentials.username, expected_user) and secrets.compare_digest(credentials.password, expected_pass)):
        raise HTTPException(status_code=401, detail='Admin authentication required', headers={'WWW-Authenticate':'Basic'})
    return True


def normalize_phone(phone: str) -> str:
    p = ''.join(ch for ch in phone if ch.isdigit() or ch == '+')
    if p.startswith('06'):
        p = '+355' + p[1:]
    if p.startswith('355'):
        p = '+' + p
    return p


DEFAULT_SETTINGS = {
    'matching_batch_size': '20',
    'matching_max_professionals': '60',
    'matching_same_city_required': 'true',
    'whatsapp_enabled': 'false',
    'platform_name': 'PunëMbaruar',
}

def seed_settings():
    db = SessionLocal()
    try:
        for key, value in DEFAULT_SETTINGS.items():
            if not db.query(AppSetting).filter(AppSetting.key == key).first():
                db.add(AppSetting(key=key, value=value))
        db.commit()
    finally:
        db.close()

def setting(db, key: str, default=None):
    row = db.query(AppSetting).filter(AppSetting.key == key).first()
    return row.value if row else default

def setting_int(db, key: str, default: int):
    try: return int(setting(db, key, str(default)))
    except Exception: return default

def setting_bool(db, key: str, default: bool=False):
    return str(setting(db, key, str(default).lower())).lower() in ('1','true','yes','on')

def match_score(req, p):
    score = 0.0
    if p.city == req.city: score += 60
    if req.zone and p.zone and req.zone.strip().lower() == p.zone.strip().lower(): score += 20
    score += min((p.rating or 0) * 3, 15)
    if p.verified: score += 4
    if p.founding_member: score += 1
    if p.plan == 'PRO': score += 2
    elif p.plan == 'BUSINESS': score += 3
    return round(score, 2)

seed_settings()

def seed_categories():
    seed = [
        ('Makina','makina',None),
        ('Shërbime','sherbime',None),
        ('Servis / Riparim','servis-riparim','makina'),
        ('Pjesë këmbimi','pjese-kembimi','makina'),
        ('Diagnostikim','diagnostikim','makina'),
        ('Autoelektrik','autoelektrik','makina'),
        ('Goma / Gomisteri','gomisteri','makina'),
        ('Kondicioner Makine','kondicioner-makine','makina'),
        ('Karroceri / Bojë','karroceri-boje','makina'),
        ('Hidraulik','hidraulik','sherbime'),
        ('Elektricist','elektricist','sherbime'),
        ('Kondicioner','kondicioner','sherbime'),
        ('Bojaxhi','bojaxhi','sherbime'),
        ('Pastrim','pastrim','sherbime'),
        ('Montime','montime','sherbime'),
    ]
    db = SessionLocal()
    try:
        if db.query(Category).count(): return
        by_slug = {}
        for name, slug, parent_slug in seed:
            parent = by_slug.get(parent_slug)
            c = Category(name=name, slug=slug, parent_id=parent.id if parent else None)
            db.add(c); db.flush(); by_slug[slug] = c
        db.commit()
    finally: db.close()
seed_categories()


def queue_matching_notifications(db, req: ServiceRequest):
    cat = db.query(Category).get(req.category_id)
    q = db.query(Professional).join(professional_categories).filter(
        professional_categories.c.category_id == req.category_id,
        Professional.active == True,
    )
    if setting_bool(db, 'matching_same_city_required', True):
        q = q.filter(Professional.city == req.city)
    pros = q.all()
    pros = sorted(pros, key=lambda p: match_score(req, p), reverse=True)
    batch_size = max(1, setting_int(db, 'matching_batch_size', 20))
    max_pros = max(batch_size, setting_int(db, 'matching_max_professionals', 60))
    selected = pros[:min(batch_size, max_pros)]
    for pro in selected:
        payload = {
            'to': pro.whatsapp,
            'template': 'new_request',
            'request_id': req.id,
            'match_score': match_score(req, pro),
            'text': f"Kërkesë e re në PunëMbaruar: {cat.name} • {req.city}. {req.description[:120]}",
            'offer_url': f"/o/{req.id}/{pro.id}",
        }
        db.add(Notification(professional_id=pro.id, request_id=req.id, payload=json.dumps(payload, ensure_ascii=False)))
    db.commit()
    return selected

@app.get('/', response_class=HTMLResponse)
def home(request: Request):
    db = SessionLocal()
    try:
        cats = db.query(Category).filter(Category.parent_id != None, Category.active == True).all()
        return templates.TemplateResponse('index.html', {'request': request, 'categories': cats})
    finally: db.close()

@app.get('/health')
def health(): return {'ok': True, 'service': 'PunëMbaruar API'}

class OTPStart(BaseModel):
    phone: str

@app.post('/api/auth/otp/start')
def otp_start(data: OTPStart):
    phone = normalize_phone(data.phone)
    if len(phone) < 8: raise HTTPException(400, 'Numër telefoni i pavlefshëm')
    code = f"{secrets.randbelow(1000000):06d}"
    db = SessionLocal()
    try:
        db.add(OTPCode(phone=phone, code_hash=hashlib.sha256(code.encode()).hexdigest(), expires_at=datetime.utcnow()+timedelta(minutes=5)))
        db.commit()
    finally: db.close()
    # DEV ONLY: return code. In production send via SMS and omit dev_code.
    return {'ok': True, 'phone': phone, 'dev_code': code, 'expires_in_seconds': 300}

class OTPVerify(BaseModel):
    phone: str
    code: str
    name: str = 'Klient'

@app.post('/api/auth/otp/verify')
def otp_verify(data: OTPVerify):
    phone = normalize_phone(data.phone)
    db = SessionLocal()
    try:
        row = db.query(OTPCode).filter(OTPCode.phone==phone, OTPCode.used==False).order_by(OTPCode.id.desc()).first()
        if not row or row.expires_at < datetime.utcnow(): raise HTTPException(400, 'Kodi ka skaduar ose nuk ekziston')
        if hashlib.sha256(data.code.encode()).hexdigest() != row.code_hash: raise HTTPException(400, 'Kodi i pasaktë')
        row.used = True
        user = db.query(User).filter(User.phone==phone).first()
        if not user:
            user = User(name=data.name.strip() or 'Klient', phone=phone)
            db.add(user); db.flush()
        db.commit()
        token = secrets.token_urlsafe(32)
        db.add(AuthSession(token=token, phone=phone, role='client', user_id=user.id, expires_at=datetime.utcnow()+timedelta(days=30)))
        db.commit()
        return {'ok': True, 'user': {'id': user.id, 'name': user.name, 'phone': user.phone}, 'token': token, 'dashboard_url': '/client'}
    finally: db.close()

class RequestCreate(BaseModel):
    name: str
    phone: str
    category_slug: str
    request_type: str
    description: str
    city: str
    zone: str | None = None
    vehicle_make: str | None = None
    vehicle_model: str | None = None
    vehicle_year: str | None = None
    vehicle_engine: str | None = None
    vehicle_fuel: str | None = None
    urgency: str | None = None
    preferred_timing: str | None = None
    mileage: str | None = None
    symptom: str | None = None
    warning_light: str | None = None
    part_name: str | None = None
    part_code: str | None = None
    part_condition_preference: str | None = None
    source: str = 'direct'

@app.post('/api/requests')
def create_request(data: RequestCreate):
    db = SessionLocal()
    try:
        phone = normalize_phone(data.phone)
        user = db.query(User).filter(User.phone==phone).first()
        if not user:
            user = User(name=data.name.strip(), phone=phone)
            db.add(user); db.flush()
        cat = db.query(Category).filter(Category.slug==data.category_slug, Category.active==True).first()
        if not cat: raise HTTPException(400, 'Kategori e pavlefshme')
        req = ServiceRequest(client_id=user.id, category_id=cat.id, request_type=data.request_type,
            description=data.description.strip(), city=data.city, zone=data.zone,
            vehicle_make=data.vehicle_make, vehicle_model=data.vehicle_model,
            vehicle_year=data.vehicle_year, vehicle_engine=data.vehicle_engine, vehicle_fuel=data.vehicle_fuel,
            urgency=data.urgency, preferred_timing=data.preferred_timing,
            mileage=data.mileage, symptom=data.symptom, warning_light=data.warning_light,
            part_name=data.part_name, part_code=data.part_code,
            part_condition_preference=data.part_condition_preference, source=data.source)
        db.add(req); db.flush(); db.commit(); db.refresh(req)
        matched = queue_matching_notifications(db, req)
        return {'ok': True, 'request_id': req.id, 'matched_professionals': len(matched), 'status': req.status}
    finally: db.close()

class ProfessionalCreate(BaseModel):
    name: str
    phone: str
    whatsapp: str
    professional_type: str = 'business'
    city: str
    zone: str | None = None
    category_slugs: list[str]
    description: str | None = None

@app.post('/api/professionals')
def create_professional(data: ProfessionalCreate):
    db = SessionLocal()
    try:
        phone = normalize_phone(data.phone); wa = normalize_phone(data.whatsapp)
        if db.query(Professional).filter(Professional.phone==phone).first(): raise HTTPException(409, 'Ky numër është regjistruar')
        cats = db.query(Category).filter(Category.slug.in_(data.category_slugs)).all()
        if not cats: raise HTTPException(400, 'Zgjidh të paktën një kategori')
        pro = Professional(name=data.name.strip(), phone=phone, whatsapp=wa,
            professional_type=data.professional_type, city=data.city, zone=data.zone,
            description=data.description, categories=cats)
        db.add(pro); db.commit(); db.refresh(pro)
        return {'ok': True, 'professional_id': pro.id, 'founding_member': pro.founding_member}
    finally: db.close()

@app.get('/api/requests/{request_id}')
def get_request(request_id: int):
    db = SessionLocal()
    try:
        r = db.query(ServiceRequest).get(request_id)
        if not r: raise HTTPException(404, 'Kërkesa nuk u gjet')
        return {'id': r.id, 'description': r.description, 'city': r.city, 'zone': r.zone, 'status': r.status,
                'vehicle': {'make': r.vehicle_make, 'model': r.vehicle_model, 'year': r.vehicle_year, 'engine': r.vehicle_engine},
                'offers': [{'id':o.id,'professional':o.professional.name,'price':o.price,'message':o.message,'status':o.status} for o in r.offers]}
    finally: db.close()

class OfferCreate(BaseModel):
    professional_id: int
    price: float | None = None
    price_from: float | None = None
    price_to: float | None = None
    brand: str | None = None
    condition: str | None = None
    in_stock: bool | None = None
    warranty: str | None = None
    delivery: bool | None = None
    quote_type: str | None = None
    diagnostic_fee: float | None = None
    labor_price: float | None = None
    parts_price: float | None = None
    estimated_time: str | None = None
    appointment_note: str | None = None
    earliest_appointment: str | None = None
    parts_type: str | None = None
    includes_vat: bool | None = None
    message: str | None = None

@app.post('/api/requests/{request_id}/offers')
def create_offer(request_id: int, data: OfferCreate):
    db = SessionLocal()
    try:
        req = db.query(ServiceRequest).get(request_id); pro = db.query(Professional).get(data.professional_id)
        if not req or not pro: raise HTTPException(404, 'Kërkesa ose profesionisti nuk u gjet')
        exists = db.query(Offer).filter(Offer.request_id==request_id, Offer.professional_id==pro.id).first()
        if exists: raise HTTPException(409, 'Ke dërguar tashmë ofertë për këtë kërkesë')
        offer = Offer(request_id=request_id, professional_id=pro.id, price=data.price,
            price_from=data.price_from, price_to=data.price_to, brand=data.brand, condition=data.condition,
            in_stock=data.in_stock, warranty=data.warranty, delivery=data.delivery, quote_type=data.quote_type,
            diagnostic_fee=data.diagnostic_fee, labor_price=data.labor_price, parts_price=data.parts_price,
            estimated_time=data.estimated_time, appointment_note=data.appointment_note,
            earliest_appointment=data.earliest_appointment, parts_type=data.parts_type,
            includes_vat=data.includes_vat, message=data.message)
        db.add(offer); db.commit(); db.refresh(offer)
        return {'ok': True, 'offer_id': offer.id}
    finally: db.close()

@app.post('/api/offers/{offer_id}/accept')
def accept_offer(request: Request, offer_id: int):
    db = SessionLocal()
    try:
        offer = db.query(Offer).get(offer_id)
        if not offer: raise HTTPException(404, 'Oferta nuk u gjet')
        sess = get_session_from_request(request, db) if 'get_session_from_request' in globals() else None
        if sess and (sess.role != 'client' or sess.user_id != offer.request.client_id):
            raise HTTPException(403, 'Vetëm klienti i kërkesës mund ta pranojë ofertën')
        offer.status='ACCEPTED'; offer.request.status='OFFER_SELECTED'
        for other in offer.request.offers:
            if other.id != offer.id and other.status == 'SENT': other.status = 'NOT_SELECTED'
        db.commit(); return {'ok': True, 'request_id': offer.request_id}
    finally: db.close()

@app.get('/o/{request_id}/{professional_id}', response_class=HTMLResponse)
def offer_page(request: Request, request_id: int, professional_id: int):
    db = SessionLocal()
    try:
        r = db.query(ServiceRequest).get(request_id); p = db.query(Professional).get(professional_id)
        if not r or not p: raise HTTPException(404)
        return templates.TemplateResponse('offer.html', {'request':request,'r':r,'p':p})
    finally: db.close()

@app.get('/api/professionals/{professional_id}/dashboard')
def pro_dashboard(professional_id: int):
    db = SessionLocal()
    try:
        p = db.query(Professional).get(professional_id)
        if not p: raise HTTPException(404, 'Profesionisti nuk u gjet')
        offers = db.query(Offer).filter(Offer.professional_id==p.id).all()
        won = [o for o in offers if o.status=='ACCEPTED']
        revenue = sum((o.price or o.price_from or 0) for o in won)
        notifications = db.query(Notification).filter(Notification.professional_id==p.id).count()
        return {'professional': p.name, 'requests_received': notifications, 'offers_sent': len(offers), 'jobs_won': len(won), 'declared_value': revenue, 'rating': p.rating}
    finally: db.close()

@app.get('/api/admin/overview')
def admin_overview(_: bool = Depends(require_admin)):
    db = SessionLocal()
    try:
        return {
            'users': db.query(User).count(), 'professionals': db.query(Professional).count(),
            'requests': db.query(ServiceRequest).count(), 'offers': db.query(Offer).count(),
            'whatsapp_queue': db.query(Notification).filter(Notification.status=='queued').count()
        }
    finally: db.close()

@app.get('/api/notifications/queue')
def notification_queue(_: bool = Depends(require_admin)):
    db = SessionLocal()
    try:
        rows=db.query(Notification).order_by(Notification.id.desc()).limit(100).all()
        return [{'id':n.id,'professional_id':n.professional_id,'request_id':n.request_id,'channel':n.channel,'status':n.status,'payload':json.loads(n.payload or '{}')} for n in rows]
    finally: db.close()


def get_session_from_request(request: Request, db):
    token = request.cookies.get('pm_session') or request.headers.get('X-PM-Session')
    if not token:
        return None
    row = db.query(AuthSession).filter(AuthSession.token==token).first()
    if not row or row.expires_at < datetime.utcnow():
        return None
    return row

@app.post('/api/auth/session')
def create_browser_session(data: OTPVerify):
    phone = normalize_phone(data.phone)
    db = SessionLocal()
    try:
        row = db.query(OTPCode).filter(OTPCode.phone==phone, OTPCode.used==False).order_by(OTPCode.id.desc()).first()
        if not row or row.expires_at < datetime.utcnow(): raise HTTPException(400, 'Kodi ka skaduar ose nuk ekziston')
        if hashlib.sha256(data.code.encode()).hexdigest() != row.code_hash: raise HTTPException(400, 'Kodi i pasaktë')
        row.used = True
        user = db.query(User).filter(User.phone==phone).first()
        pro = db.query(Professional).filter(Professional.phone==phone).first()
        role = 'professional' if pro else 'client'
        if not user and not pro:
            user = User(name=data.name.strip() or 'Klient', phone=phone)
            db.add(user); db.flush()
        token = secrets.token_urlsafe(32)
        db.add(AuthSession(token=token, phone=phone, role=role, user_id=user.id if user else None, professional_id=pro.id if pro else None, expires_at=datetime.utcnow()+timedelta(days=30)))
        db.commit()
        response = JSONResponse({'ok':True,'role':role,'dashboard_url':'/professional' if role=='professional' else '/client'})
        response.set_cookie('pm_session', token, max_age=2592000, httponly=True, samesite='lax')
        return response
    finally: db.close()

@app.post('/api/auth/logout')
def logout(request: Request):
    db=SessionLocal()
    try:
        session=get_session_from_request(request,db)
        if session: db.delete(session); db.commit()
    finally: db.close()
    response=JSONResponse({'ok':True})
    response.delete_cookie('pm_session')
    return response

@app.get('/login', response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse('login.html', {'request':request})

@app.get('/client', response_class=HTMLResponse)
def client_page(request: Request):
    db=SessionLocal()
    try:
        sess=get_session_from_request(request,db)
        if not sess or sess.role!='client' or not sess.user_id:
            return RedirectResponse('/login?next=/client',303)
        user=db.query(User).get(sess.user_id)
        requests=db.query(ServiceRequest).filter(ServiceRequest.client_id==user.id).order_by(ServiceRequest.id.desc()).all()
        vehicles=db.query(Vehicle).filter(Vehicle.user_id==user.id).order_by(Vehicle.id.desc()).all()
        return templates.TemplateResponse('client_dashboard.html',{'request':request,'user':user,'requests_list':requests,'vehicles':vehicles})
    finally: db.close()

@app.get('/professional', response_class=HTMLResponse)
def professional_page(request: Request):
    db=SessionLocal()
    try:
        sess=get_session_from_request(request,db)
        if not sess or sess.role!='professional' or not sess.professional_id:
            return RedirectResponse('/login?next=/professional',303)
        p=db.query(Professional).get(sess.professional_id)
        notes=db.query(Notification).filter(Notification.professional_id==p.id).order_by(Notification.id.desc()).all()
        offers=db.query(Offer).filter(Offer.professional_id==p.id).order_by(Offer.id.desc()).all()
        won=[o for o in offers if o.status=='ACCEPTED']
        revenue=sum((o.price or o.price_from or 0) for o in won)
        media=db.query(ProfessionalMedia).filter(ProfessionalMedia.professional_id==p.id).order_by(ProfessionalMedia.id.desc()).all()
        return templates.TemplateResponse('professional_dashboard.html',{'request':request,'p':p,'notes':notes,'offers':offers,'won':len(won),'revenue':revenue,'media':media})
    finally: db.close()

@app.get('/request/{request_id}', response_class=HTMLResponse)
def request_detail(request: Request, request_id:int):
    db=SessionLocal()
    try:
        sess=get_session_from_request(request,db)
        r=db.query(ServiceRequest).get(request_id)
        if not r: raise HTTPException(404,'Kërkesa nuk u gjet')
        if not sess: return RedirectResponse('/login',303)
        allowed=(sess.role=='client' and sess.user_id==r.client_id) or (sess.role=='professional' and sess.professional_id and db.query(Notification).filter(Notification.request_id==r.id,Notification.professional_id==sess.professional_id).first())
        if not allowed: raise HTTPException(403,'Nuk ke akses te kjo kërkesë')
        messages=db.query(Message).filter(Message.request_id==r.id).order_by(Message.id.asc()).all()
        accepted=next((o for o in r.offers if o.status=='ACCEPTED'),None)
        review=db.query(Review).filter(Review.request_id==r.id).first()
        media=db.query(RequestMedia).filter(RequestMedia.request_id==r.id).order_by(RequestMedia.id.desc()).all()
        return templates.TemplateResponse('request_detail.html',{'request':request,'r':r,'sess':sess,'messages':messages,'accepted':accepted,'review':review,'media':media})
    finally: db.close()

class MessageCreate(BaseModel):
    body: str

@app.post('/api/requests/{request_id}/messages')
def send_message(request: Request, request_id:int, data:MessageCreate):
    db=SessionLocal()
    try:
        sess=get_session_from_request(request,db)
        if not sess: raise HTTPException(401,'Duhet të hysh')
        r=db.query(ServiceRequest).get(request_id)
        if not r: raise HTTPException(404,'Kërkesa nuk u gjet')
        if sess.role=='client' and sess.user_id!=r.client_id: raise HTTPException(403,'Pa akses')
        if sess.role=='professional':
            if not db.query(Notification).filter(Notification.request_id==r.id,Notification.professional_id==sess.professional_id).first(): raise HTTPException(403,'Pa akses')
        body=data.body.strip()
        if not body: raise HTTPException(400,'Mesazhi është bosh')
        sender_id=sess.user_id if sess.role=='client' else sess.professional_id
        m=Message(request_id=r.id,sender_role=sess.role,sender_id=sender_id,body=body)
        db.add(m)
        db.commit(); db.refresh(m)
        return {'ok':True,'id':m.id,'created_at':m.created_at.isoformat()}
    finally: db.close()

@app.post('/api/requests/{request_id}/complete')
def complete_request(request:Request, request_id:int):
    db=SessionLocal()
    try:
        sess=get_session_from_request(request,db)
        r=db.query(ServiceRequest).get(request_id)
        if not sess or not r or sess.role!='client' or sess.user_id!=r.client_id: raise HTTPException(403,'Pa akses')
        if r.status not in ('OFFER_SELECTED','IN_PROGRESS'): raise HTTPException(400,'Kërkesa nuk mund të përfundohet në këtë status')
        r.status='COMPLETED'; db.commit(); return {'ok':True}
    finally: db.close()

class ReviewCreate(BaseModel):
    rating:int
    comment:str|None=None

@app.post('/api/requests/{request_id}/review')
def create_review(request:Request, request_id:int, data:ReviewCreate):
    db=SessionLocal()
    try:
        sess=get_session_from_request(request,db)
        r=db.query(ServiceRequest).get(request_id)
        if not sess or not r or sess.role!='client' or sess.user_id!=r.client_id: raise HTTPException(403,'Pa akses')
        if r.status!='COMPLETED': raise HTTPException(400,'Puna duhet të jetë e përfunduar')
        if not 1<=data.rating<=5: raise HTTPException(400,'Rating duhet 1–5')
        if db.query(Review).filter(Review.request_id==r.id).first(): raise HTTPException(409,'Review është dërguar')
        accepted=db.query(Offer).filter(Offer.request_id==r.id,Offer.status=='ACCEPTED').first()
        if not accepted: raise HTTPException(400,'Nuk ka ofertë të pranuar')
        rev=Review(request_id=r.id,client_id=r.client_id,professional_id=accepted.professional_id,rating=data.rating,comment=(data.comment or '').strip() or None)
        db.add(rev); r.status='REVIEWED'; db.flush()
        ratings=[x.rating for x in db.query(Review).filter(Review.professional_id==accepted.professional_id).all()]
        p=db.query(Professional).get(accepted.professional_id); p.rating=round(sum(ratings)/len(ratings),2)
        db.commit(); return {'ok':True,'rating':p.rating}
    finally: db.close()

@app.get('/admin', response_class=HTMLResponse)
def admin_page(request: Request, _: bool = Depends(require_admin)):
    db=SessionLocal()
    try:
        overview={
            'users':db.query(User).count(),'professionals':db.query(Professional).count(),
            'requests':db.query(ServiceRequest).count(),'offers':db.query(Offer).count(),
            'queued':db.query(Notification).filter(Notification.status=='queued').count(),
            'reviews':db.query(Review).count()
        }
        pros=db.query(Professional).order_by(Professional.id.desc()).limit(50).all()
        reqs=db.query(ServiceRequest).order_by(ServiceRequest.id.desc()).limit(50).all()
        notes=db.query(Notification).order_by(Notification.id.desc()).limit(50).all()
        cats=db.query(Category).filter(Category.parent_id!=None).order_by(Category.id).all()
        stats=admin_stats_payload(db) if 'admin_stats_payload' in globals() else {}
        settings={k:setting(db,k,v) for k,v in DEFAULT_SETTINGS.items()}
        return templates.TemplateResponse('admin.html',{'request':request,'overview':overview,'pros':pros,'reqs':reqs,'notes':notes,'cats':cats,'stats':stats,'settings':settings})
    finally: db.close()

class CategoryCreate(BaseModel):
    name:str
    slug:str
    parent_slug:str

@app.post('/api/admin/categories')
def admin_create_category(data:CategoryCreate, _: bool = Depends(require_admin)):
    db=SessionLocal()
    try:
        if db.query(Category).filter(Category.slug==data.slug.strip()).first(): raise HTTPException(409,'Slug ekziston')
        parent=db.query(Category).filter(Category.slug==data.parent_slug).first()
        if not parent: raise HTTPException(400,'Kategoria prind nuk u gjet')
        c=Category(name=data.name.strip(),slug=data.slug.strip(),parent_id=parent.id,active=False)
        db.add(c);db.commit();db.refresh(c);return {'ok':True,'id':c.id}
    finally:db.close()

@app.post('/api/admin/professionals/{professional_id}/verify')
def admin_verify_professional(professional_id:int, _: bool = Depends(require_admin)):
    db=SessionLocal()
    try:
        p=db.query(Professional).get(professional_id)
        if not p: raise HTTPException(404,'Profesionisti nuk u gjet')
        p.verified=True;db.commit();return {'ok':True}
    finally:db.close()

@app.post('/api/admin/notifications/{notification_id}/mark-sent')
def admin_mark_notification_sent(notification_id:int, _: bool = Depends(require_admin)):
    db=SessionLocal()
    try:
        n=db.query(Notification).get(notification_id)
        if not n: raise HTTPException(404,'Njoftimi nuk u gjet')
        n.status='sent';db.commit();return {'ok':True}
    finally:db.close()


# ---------- V1.0 additions: garage, media, public profiles, matching ----------
class VehicleCreate(BaseModel):
    make: str
    model: str
    year: str | None = None
    engine: str | None = None
    fuel: str | None = None

@app.post('/api/garage')
def garage_add(request: Request, data: VehicleCreate):
    db = SessionLocal()
    try:
        sess = get_session_from_request(request, db)
        if not sess or sess.role != 'client' or not sess.user_id:
            raise HTTPException(401, 'Duhet të hysh si klient')
        v = Vehicle(user_id=sess.user_id, make=data.make.strip(), model=data.model.strip(), year=data.year, engine=data.engine, fuel=data.fuel)
        db.add(v); db.commit(); db.refresh(v)
        return {'ok': True, 'vehicle_id': v.id}
    finally:
        db.close()

@app.delete('/api/garage/{vehicle_id}')
def garage_delete(request: Request, vehicle_id: int):
    db = SessionLocal()
    try:
        sess = get_session_from_request(request, db)
        v = db.query(Vehicle).get(vehicle_id)
        if not sess or not v or sess.user_id != v.user_id:
            raise HTTPException(403, 'Pa akses')
        db.delete(v); db.commit()
        return {'ok': True}
    finally:
        db.close()

def safe_filename(name: str) -> str:
    base = os.path.basename(name or 'file')
    base = re.sub(r'[^A-Za-z0-9._-]+', '_', base)
    return base[:120] or 'file'

@app.post('/api/requests/{request_id}/media')
async def upload_request_media(request: Request, request_id: int, file: UploadFile = File(...)):
    db = SessionLocal()
    try:
        sess = get_session_from_request(request, db)
        r = db.query(ServiceRequest).get(request_id)
        if not r or not sess or sess.role != 'client' or sess.user_id != r.client_id:
            raise HTTPException(403, 'Pa akses')
        ext = (Path(file.filename or '').suffix or '.bin').lower()
        if ext not in {'.jpg','.jpeg','.png','.webp','.gif','.mp4','.mov'}:
            raise HTTPException(400, 'Format media i palejuar')
        name = f"req_{request_id}_{secrets.token_hex(6)}{ext}"
        dest = UPLOAD_DIR / name
        with dest.open('wb') as out:
            shutil.copyfileobj(file.file, out)
        m = RequestMedia(request_id=request_id, file_name=safe_filename(file.filename), file_path=name, media_type='video' if ext in {'.mp4','.mov'} else 'image')
        db.add(m); db.commit(); db.refresh(m)
        return {'ok': True, 'id': m.id, 'url': f'/uploads/{name}'}
    finally:
        db.close()

@app.post('/api/professionals/{professional_id}/media')
async def upload_professional_media(request: Request, professional_id: int, file: UploadFile = File(...)):
    db = SessionLocal()
    try:
        sess = get_session_from_request(request, db)
        if not sess or sess.role != 'professional' or sess.professional_id != professional_id:
            raise HTTPException(403, 'Pa akses')
        ext = (Path(file.filename or '').suffix or '.bin').lower()
        if ext not in {'.jpg','.jpeg','.png','.webp'}:
            raise HTTPException(400, 'Lejohen vetëm foto')
        name = f"pro_{professional_id}_{secrets.token_hex(6)}{ext}"
        dest = UPLOAD_DIR / name
        with dest.open('wb') as out:
            shutil.copyfileobj(file.file, out)
        m = ProfessionalMedia(professional_id=professional_id, file_name=safe_filename(file.filename), file_path=name)
        db.add(m); db.commit(); db.refresh(m)
        return {'ok': True, 'id': m.id, 'url': f'/uploads/{name}'}
    finally:
        db.close()

@app.get('/uploads/{filename}')
def uploaded_file(filename: str):
    path = UPLOAD_DIR / safe_filename(filename)
    if not path.exists():
        raise HTTPException(404)
    return FileResponse(path)

@app.get('/p/{professional_id}', response_class=HTMLResponse)
def public_professional(request: Request, professional_id: int):
    db = SessionLocal()
    try:
        p = db.query(Professional).get(professional_id)
        if not p:
            raise HTTPException(404, 'Profesionisti nuk u gjet')
        reviews = db.query(Review).filter(Review.professional_id==p.id).order_by(Review.id.desc()).limit(30).all()
        media = db.query(ProfessionalMedia).filter(ProfessionalMedia.professional_id==p.id).order_by(ProfessionalMedia.id.desc()).all()
        jobs = db.query(Offer).filter(Offer.professional_id==p.id, Offer.status=='ACCEPTED').count()
        return templates.TemplateResponse('professional_public.html', {'request':request,'p':p,'reviews':reviews,'media':media,'jobs':jobs})
    finally:
        db.close()

@app.get('/api/requests/{request_id}/matches')
def ranked_matches(request_id: int):
    db = SessionLocal()
    try:
        r = db.query(ServiceRequest).get(request_id)
        if not r:
            raise HTTPException(404, 'Kërkesa nuk u gjet')
        pros = db.query(Professional).join(professional_categories).filter(professional_categories.c.category_id==r.category_id).all()
        rows=[]
        for p in pros:
            rows.append({'professional_id':p.id,'name':p.name,'city':p.city,'zone':p.zone,'rating':p.rating,'verified':p.verified,'plan':p.plan,'active':p.active,'score':match_score(r,p)})
        rows.sort(key=lambda x:x['score'], reverse=True)
        return {'request_id': r.id, 'matches': rows}
    finally:
        db.close()

@app.get('/api/whatsapp/outbox')
def whatsapp_outbox():
    db = SessionLocal()
    try:
        rows = db.query(Notification).filter(Notification.channel=='whatsapp').order_by(Notification.id.desc()).limit(200).all()
        return {'mode':'queue','meta_configured':bool(os.getenv('WHATSAPP_TOKEN') and os.getenv('WHATSAPP_PHONE_NUMBER_ID')),'items':[{'id':n.id,'status':n.status,'payload':json.loads(n.payload or '{}')} for n in rows]}
    finally:
        db.close()


# ---------- V1.1: low-cost production operations ----------
class AdminSettingsUpdate(BaseModel):
    matching_batch_size: int = 20
    matching_max_professionals: int = 60
    matching_same_city_required: bool = True
    whatsapp_enabled: bool = False

@app.get('/api/admin/settings')
def admin_get_settings(_: bool = Depends(require_admin)):
    db=SessionLocal()
    try:
        return {k: setting(db,k,v) for k,v in DEFAULT_SETTINGS.items()}
    finally: db.close()

@app.post('/api/admin/settings')
def admin_update_settings(data: AdminSettingsUpdate, _: bool = Depends(require_admin)):
    if data.matching_batch_size < 1 or data.matching_batch_size > 200:
        raise HTTPException(400,'Batch size duhet 1–200')
    if data.matching_max_professionals < data.matching_batch_size or data.matching_max_professionals > 1000:
        raise HTTPException(400,'Max matching duhet >= batch dhe <= 1000')
    values={
        'matching_batch_size':str(data.matching_batch_size),
        'matching_max_professionals':str(data.matching_max_professionals),
        'matching_same_city_required':str(data.matching_same_city_required).lower(),
        'whatsapp_enabled':str(data.whatsapp_enabled).lower(),
    }
    db=SessionLocal()
    try:
        for k,v in values.items():
            row=db.query(AppSetting).filter(AppSetting.key==k).first()
            if row: row.value=v
            else: db.add(AppSetting(key=k,value=v))
        db.commit(); return {'ok':True,'settings':values}
    finally: db.close()

class ProAdminUpdate(BaseModel):
    verified: bool | None = None
    active: bool | None = None
    plan: str | None = None

@app.post('/api/admin/professionals/{professional_id}/update')
def admin_update_professional(professional_id:int,data:ProAdminUpdate, _: bool = Depends(require_admin)):
    db=SessionLocal()
    try:
        p=db.query(Professional).get(professional_id)
        if not p: raise HTTPException(404,'Profesionisti nuk u gjet')
        if data.verified is not None: p.verified=data.verified
        if data.active is not None: p.active=data.active
        if data.plan is not None:
            plan=data.plan.upper()
            if plan not in ('FREE','PRO','BUSINESS'): raise HTTPException(400,'Plan i pavlefshëm')
            p.plan=plan
        db.commit(); return {'ok':True,'professional_id':p.id,'verified':p.verified,'active':p.active,'plan':p.plan}
    finally: db.close()

def admin_stats_payload(db):
    reqs=db.query(ServiceRequest).all()
    offers=db.query(Offer).all()
    completed=sum(1 for r in reqs if r.status in ('COMPLETED','REVIEWED'))
    accepted=[o for o in offers if o.status=='ACCEPTED']
    declared=sum((o.price or o.price_from or 0) for o in accepted)
    by_source={}
    for r in reqs: by_source[r.source or 'direct']=by_source.get(r.source or 'direct',0)+1
    by_month={}
    for r in reqs:
        key=r.created_at.strftime('%Y-%m') if r.created_at else 'unknown'
        row=by_month.setdefault(key,{'requests':0,'offers':0,'completed':0,'declared_value':0})
        row['requests']+=1
        if r.status in ('COMPLETED','REVIEWED'): row['completed']+=1
    for o in offers:
        key=o.created_at.strftime('%Y-%m') if o.created_at else 'unknown'
        row=by_month.setdefault(key,{'requests':0,'offers':0,'completed':0,'declared_value':0})
        row['offers']+=1
        if o.status=='ACCEPTED': row['declared_value']+=o.price or o.price_from or 0
    return {
        'users':db.query(User).count(),'professionals':db.query(Professional).count(),
        'requests':len(reqs),'offers':len(offers),'completed_jobs':completed,
        'accepted_offers':len(accepted),'declared_value':round(declared,2),
        'conversion_rate':round((completed/len(reqs)*100),1) if reqs else 0,
        'by_source':by_source,'by_month':dict(sorted(by_month.items(),reverse=True)),
    }

@app.get('/api/admin/stats')
def admin_stats(_: bool = Depends(require_admin)):
    db=SessionLocal()
    try: return admin_stats_payload(db)
    finally: db.close()

@app.get('/api/admin/export/{dataset}.csv')
def admin_export_csv(dataset:str, _: bool = Depends(require_admin)):
    db=SessionLocal()
    try:
        out=io.StringIO(); w=csv.writer(out)
        if dataset=='requests':
            w.writerow(['id','date','client_id','type','city','zone','status','source','description'])
            for r in db.query(ServiceRequest).order_by(ServiceRequest.id).all():
                w.writerow([r.id,r.created_at.isoformat() if r.created_at else '',r.client_id,r.request_type,r.city,r.zone or '',r.status,r.source,r.description])
        elif dataset=='professionals':
            w.writerow(['id','name','phone','city','zone','verified','active','plan','rating','created_at'])
            for p in db.query(Professional).order_by(Professional.id).all():
                w.writerow([p.id,p.name,p.phone,p.city,p.zone or '',p.verified,p.active,p.plan,p.rating,p.created_at.isoformat() if p.created_at else ''])
        elif dataset=='offers':
            w.writerow(['id','request_id','professional_id','price','status','created_at'])
            for o in db.query(Offer).order_by(Offer.id).all():
                w.writerow([o.id,o.request_id,o.professional_id,o.price or o.price_from or '',o.status,o.created_at.isoformat() if o.created_at else ''])
        else: raise HTTPException(404,'Dataset i panjohur')
        data=out.getvalue().encode('utf-8-sig')
        return StreamingResponse(io.BytesIO(data),media_type='text/csv',headers={'Content-Disposition':f'attachment; filename=punembaruar_{dataset}.csv'})
    finally: db.close()

@app.get('/api/system/cost-mode')
def cost_mode():
    db=SessionLocal()
    try:
        return {
            'version':'1.1.0','database':'postgresql' if DB_URL.startswith('postgres') else 'sqlite-local',
            'matching_batch_size':setting_int(db,'matching_batch_size',20),
            'matching_max_professionals':setting_int(db,'matching_max_professionals',60),
            'whatsapp_live':bool(os.getenv('WHATSAPP_TOKEN') and os.getenv('WHATSAPP_PHONE_NUMBER_ID')),
            'r2_ready':bool(os.getenv('R2_ENDPOINT_URL') and os.getenv('R2_BUCKET')),
        }
    finally: db.close()



@app.get("/professional/{professional_id}/verification", response_class=HTMLResponse)
def provider_verification_page(request: Request, professional_id: int, db: Session = Depends(get_db)):
    p=db.get(Professional, professional_id)
    if not p: raise HTTPException(404, "Professional not found")
    return templates.TemplateResponse("provider_verification.html", {"request":request,"professional":p})

# --- Provider verification workflow v1.4 ---
from pydantic import BaseModel as _PMBaseModel

class VerificationSubmission(_PMBaseModel):
    responsible_person: str
    nipt: str | None = None
    business_address: str
    maps_url: str | None = None
    notes: str | None = None

class VerificationEvidenceIn(_PMBaseModel):
    evidence_type: str
    file_url: str
    label: str | None = None

class VerificationDecision(_PMBaseModel):
    status: str
    verification_level: str | None = None
    notes: str | None = None
    physical_visit: bool | None = None

@app.post("/api/professionals/{professional_id}/verification/submit")
def submit_provider_verification(professional_id: int, data: VerificationSubmission, db: Session = Depends(get_db)):
    p=db.get(Professional, professional_id)
    if not p: raise HTTPException(404, "Professional not found")
    if not data.responsible_person.strip():
        raise HTTPException(400, "Personi përgjegjës është i detyrueshëm")
    if not data.business_address.strip():
        raise HTTPException(400, "Adresa e biznesit është e detyrueshme")
    # NIPT is required for registered businesses in the launch onboarding flow.
    if not data.nipt or not data.nipt.strip():
        raise HTTPException(400, "NIPT është i detyrueshëm për regjistrimin e biznesit")
    photos=db.query(VerificationEvidence).filter(
        VerificationEvidence.professional_id==professional_id,
        VerificationEvidence.evidence_type=='PHOTO'
    ).count()
    if photos < 3:
        raise HTTPException(400, f"Duhet të ngarkohen minimumi 3 foto verifikimi. Aktualisht: {photos}")
    p.responsible_person=data.responsible_person
    p.nipt=data.nipt
    p.business_address=data.business_address
    p.maps_url=data.maps_url
    p.verification_notes=data.notes
    p.approval_status='UNDER_REVIEW'
    p.active=False
    db.commit()
    return {"ok":True,"approval_status":p.approval_status,"photos":photos}

@app.post("/api/professionals/{professional_id}/verification/evidence")
def add_verification_evidence(professional_id: int, data: VerificationEvidenceIn, db: Session = Depends(get_db)):
    p=db.get(Professional, professional_id)
    if not p: raise HTTPException(404, "Professional not found")
    et=data.evidence_type.upper()
    if et not in {'PHOTO','VIDEO','DOCUMENT','OTHER'}:
        raise HTTPException(400, "Lloj prove i pavlefshëm")
    if not data.file_url.strip():
        raise HTTPException(400, "Skedari/prova është e detyrueshme")
    ev=VerificationEvidence(professional_id=professional_id,evidence_type=et,
                            file_url=data.file_url,label=data.label)
    db.add(ev); db.commit()
    return {"ok":True,"id":ev.id}

@app.get("/api/admin/verifications")
def admin_verifications(db: Session = Depends(get_db), _=Depends(admin_guard)):
    ps=db.query(Professional).filter(Professional.approval_status.in_(
        ['APPLICATION','DOCUMENTS_SUBMITTED','UNDER_REVIEW','MORE_INFO_REQUIRED'])).all()
    return [{"id":p.id,"name":getattr(p,'business_name',None) or getattr(p,'name',None),
             "status":p.approval_status,"level":p.verification_level,"nipt":p.nipt,
             "address":p.business_address,"maps_url":p.maps_url,"physical_visit":p.physical_visit}
            for p in ps]

@app.post("/api/admin/professionals/{professional_id}/verification")
def admin_verification_decision(professional_id: int, data: VerificationDecision,
                                db: Session = Depends(get_db), _=Depends(admin_guard)):
    p=db.get(Professional, professional_id)
    if not p: raise HTTPException(404, "Professional not found")
    allowed={'APPROVED','MORE_INFO_REQUIRED','REJECTED','SUSPENDED','UNDER_REVIEW'}
    status=data.status.upper()
    if status not in allowed: raise HTTPException(400, "Invalid status")
    p.approval_status=status
    if data.verification_level: p.verification_level=data.verification_level.upper()
    if data.notes is not None: p.verification_notes=data.notes
    if data.physical_visit is not None: p.physical_visit=data.physical_visit
    p.active=(status=='APPROVED')
    p.verified=(status=='APPROVED')
    if p.physical_visit and status=='APPROVED':
        p.verification_level='VISITED_VERIFIED'
    elif status=='APPROVED' and p.verification_level in (None,'UNVERIFIED'):
        p.verification_level='BUSINESS_VERIFIED'
    db.commit()
    return {"ok":True,"status":p.approval_status,"active":p.active,
            "verification_level":p.verification_level}

@app.get("/api/professionals/{professional_id}/verification")
def provider_verification_status(professional_id: int, db: Session = Depends(get_db)):
    p=db.get(Professional, professional_id)
    if not p: raise HTTPException(404, "Professional not found")
    return {"approval_status":p.approval_status,"verification_level":p.verification_level,
            "physical_visit":p.physical_visit,"active":p.active,
            "notes":p.verification_notes}


# --- v1.5 moderation, job outcomes and WhatsApp/chat operations ---
class ReportIn(_PMBaseModel):
    reporter_phone: str | None = None
    target_type: str
    target_id: int
    reason: str
    details: str | None = None

class JobOutcomeIn(_PMBaseModel):
    offer_id: int | None = None
    outcome: str
    note: str | None = None

class ModerationIn(_PMBaseModel):
    active: bool

@app.post("/api/reports")
def create_report(data: ReportIn, db: Session = Depends(get_db)):
    allowed={'professional','request','offer','message'}
    if data.target_type.lower() not in allowed: raise HTTPException(400,"Invalid report target")
    if not data.reason.strip(): raise HTTPException(400,"Reason required")
    r=Report(reporter_phone=data.reporter_phone,target_type=data.target_type.lower(),
             target_id=data.target_id,reason=data.reason,details=data.details)
    db.add(r); db.commit(); db.refresh(r)
    return {"ok":True,"report_id":r.id}

@app.get("/api/admin/reports")
def admin_reports(db: Session = Depends(get_db), _=Depends(admin_guard)):
    rows=db.query(Report).order_by(Report.created_at.desc()).all()
    return [{"id":x.id,"target_type":x.target_type,"target_id":x.target_id,
             "reason":x.reason,"details":x.details,"status":x.status,
             "created_at":x.created_at.isoformat()} for x in rows]

@app.post("/api/requests/{request_id}/outcome")
def set_job_outcome(request_id:int,data:JobOutcomeIn,db:Session=Depends(get_db)):
    req=db.get(ServiceRequest,request_id)
    if not req: raise HTTPException(404,"Request not found")
    allowed={'COMPLETED','NO_SHOW','CANCELLED','DISPUTED'}
    out=data.outcome.upper()
    if out not in allowed: raise HTTPException(400,"Invalid outcome")
    row=JobOutcome(request_id=request_id,offer_id=data.offer_id,outcome=out,note=data.note)
    db.add(row)
    req.status = 'completed' if out=='COMPLETED' else out.lower()
    db.commit()
    return {"ok":True,"outcome":out}

@app.post("/api/admin/professionals/{professional_id}/active")
def admin_toggle_professional(professional_id:int,data:ModerationIn,db:Session=Depends(get_db),_=Depends(admin_guard)):
    p=db.get(Professional,professional_id)
    if not p: raise HTTPException(404,"Professional not found")
    p.active=data.active
    if not data.active and p.approval_status=='APPROVED': p.approval_status='SUSPENDED'
    db.commit(); return {"ok":True,"active":p.active}

@app.post("/api/admin/requests/{request_id}/active")
def admin_toggle_request(request_id:int,data:ModerationIn,db:Session=Depends(get_db),_=Depends(admin_guard)):
    r=db.get(ServiceRequest,request_id)
    if not r: raise HTTPException(404,"Request not found")
    r.status='open' if data.active else 'suspended'
    db.commit(); return {"ok":True,"status":r.status}

@app.post("/api/admin/offers/{offer_id}/active")
def admin_toggle_offer(offer_id:int,data:ModerationIn,db:Session=Depends(get_db),_=Depends(admin_guard)):
    o=db.get(Offer,offer_id)
    if not o: raise HTTPException(404,"Offer not found")
    o.status='sent' if data.active else 'suspended'
    db.commit(); return {"ok":True,"status":o.status}

@app.get("/api/system/whatsapp-status")
def whatsapp_status():
    configured=bool(os.getenv('WHATSAPP_TOKEN') and os.getenv('WHATSAPP_PHONE_NUMBER_ID'))
    return {"enabled":configured,"mode":"Meta WhatsApp Business Platform",
            "note":"Automatic provider notifications are queued by matching. Real sending requires Meta credentials."}


# --- v1.6 trial credits + Admin-controlled fake/spam review ---
class TrustDecisionIn(_PMBaseModel):
    status: str
    note: str | None = None

class TrialRefundIn(_PMBaseModel):
    reason: str = "Admin refund"
    note: str | None = None

def _trial_limit(db):
    row=db.query(AppSetting).filter(AppSetting.key=='free_trial_requests').first()
    try: return int(row.value) if row else 5
    except: return 5

def _trial_usage(db, professional_id):
    rows=db.query(TrialCreditLedger).filter(TrialCreditLedger.professional_id==professional_id).all()
    used=sum(1 for x in rows if x.action=='CONSUMED')-sum(1 for x in rows if x.action=='REFUNDED')
    used=max(0,used); limit=_trial_limit(db)
    return {"limit":limit,"used":used,"remaining":max(0,limit-used)}

@app.get("/api/professionals/{professional_id}/trial")
def get_trial(professional_id:int,db:Session=Depends(get_db)):
    if not db.get(Professional,professional_id): raise HTTPException(404,"Professional not found")
    return _trial_usage(db,professional_id)

@app.post("/api/admin/professionals/{professional_id}/trial/consume/{request_id}")
def consume_trial(professional_id:int,request_id:int,db:Session=Depends(get_db),_=Depends(admin_guard)):
    if not db.get(Professional,professional_id) or not db.get(ServiceRequest,request_id):
        raise HTTPException(404,"Not found")
    exists=db.query(TrialCreditLedger).filter(TrialCreditLedger.professional_id==professional_id,
        TrialCreditLedger.request_id==request_id,TrialCreditLedger.action=='CONSUMED').first()
    if not exists:
        db.add(TrialCreditLedger(professional_id=professional_id,request_id=request_id,
            action='CONSUMED',reason='Valid matched request delivered')); db.commit()
    return {"ok":True,**_trial_usage(db,professional_id)}

@app.post("/api/admin/professionals/{professional_id}/trial/refund/{request_id}")
def refund_trial(professional_id:int,request_id:int,data:TrialRefundIn,db:Session=Depends(get_db),_=Depends(admin_guard)):
    consumed=db.query(TrialCreditLedger).filter(TrialCreditLedger.professional_id==professional_id,
        TrialCreditLedger.request_id==request_id,TrialCreditLedger.action=='CONSUMED').first()
    if not consumed: raise HTTPException(400,"No consumed credit")
    refunded=db.query(TrialCreditLedger).filter(TrialCreditLedger.professional_id==professional_id,
        TrialCreditLedger.request_id==request_id,TrialCreditLedger.action=='REFUNDED').first()
    if not refunded:
        db.add(TrialCreditLedger(professional_id=professional_id,request_id=request_id,
            action='REFUNDED',reason=data.reason,admin_note=data.note)); db.commit()
    return {"ok":True,**_trial_usage(db,professional_id)}

@app.post("/api/admin/requests/{request_id}/trust")
def decide_trust(request_id:int,data:TrustDecisionIn,db:Session=Depends(get_db),_=Depends(admin_guard)):
    req=db.get(ServiceRequest,request_id)
    if not req: raise HTTPException(404,"Request not found")
    status=data.status.upper()
    if status not in {'VALID','FAKE','SPAM','DUPLICATE','PENDING'}: raise HTTPException(400,"Invalid status")
    review=db.query(RequestTrustReview).filter(RequestTrustReview.request_id==request_id).first()
    if not review:
        review=RequestTrustReview(request_id=request_id); db.add(review)
    review.status=status; review.admin_note=data.note; review.reviewed_at=datetime.utcnow()
    if status in {'FAKE','SPAM','DUPLICATE'}:
        req.status='suspended'
        for c in db.query(TrialCreditLedger).filter(TrialCreditLedger.request_id==request_id,
                                                   TrialCreditLedger.action=='CONSUMED').all():
            exists=db.query(TrialCreditLedger).filter(TrialCreditLedger.professional_id==c.professional_id,
                TrialCreditLedger.request_id==request_id,TrialCreditLedger.action=='REFUNDED').first()
            if not exists:
                db.add(TrialCreditLedger(professional_id=c.professional_id,request_id=request_id,
                    action='REFUNDED',reason=status,admin_note='Automatic refund after Admin decision'))
    elif status=='VALID' and req.status=='suspended':
        req.status='open'
    db.commit()
    return {"ok":True,"status":status}

@app.get("/api/admin/trial-ledger")
def trial_ledger(db:Session=Depends(get_db),_=Depends(admin_guard)):
    rows=db.query(TrialCreditLedger).order_by(TrialCreditLedger.created_at.desc()).all()
    return [{"professional_id":x.professional_id,"request_id":x.request_id,"action":x.action,
             "reason":x.reason,"admin_note":x.admin_note,"created_at":x.created_at.isoformat()} for x in rows]


# --- v1.7 Admin-managed automotive category catalog ---
class ManagedCategoryIn(_PMBaseModel):
    name: str
    slug: str
    category_type: str = "AUTOMOTIVE"
    priority: int = 100
    active: bool = True

DEFAULT_AUTOMOTIVE_CATEGORIES = [
    ("Servise mekanike","servise-mekanike",10),
    ("Pjesë këmbimi të reja","pjese-kembimi-reja",20),
    ("Pjesë këmbimi të përdorura","pjese-kembimi-perdorura",30),
    ("Elektroauto","elektroauto",40),
    ("Diagnostikë elektronike","diagnostike-elektronike",50),
    ("Gomisteri","gomisteri",60),
    ("Kondicioner auto","kondicioner-auto",70),
    ("Karroceri","karroceri",80),
    ("Bojë / lyerje auto","boje-lyerje-auto",90),
    ("Servis kambio","servis-kambio",100),
    ("Servis diesel / injektorë","servis-diesel-injektore",110),
    ("Marmita / shkarkimi","marmita-shkarkimi",120),
    ("Xhama auto","xhama-auto",130),
    ("Bateri","bateri",140),
    ("Disqe / goma","disqe-goma",150),
    ("Autoçelësa","autocelesa",160),
    ("Aksesore auto","aksesore-auto",170),
    ("Tapiceri auto","tapiceri-auto",180),
    ("Detailing / lavazh","detailing-lavazh",190),
    ("Karrotrec / asistencë","karrotrec-asistence",200),
]

def _seed_managed_categories(db):
    if db.query(ManagedCategory).count()==0:
        for name,slug,priority in DEFAULT_AUTOMOTIVE_CATEGORIES:
            db.add(ManagedCategory(name=name,slug=slug,category_type="AUTOMOTIVE",
                                   priority=priority,active=True))
        db.commit()

@app.get("/api/categories/manageable")
def list_managed_categories(active_only:bool=True,db:Session=Depends(get_db)):
    _seed_managed_categories(db)
    q=db.query(ManagedCategory)
    if active_only: q=q.filter(ManagedCategory.active==True)
    rows=q.order_by(ManagedCategory.priority.asc(),ManagedCategory.name.asc()).all()
    return [{"id":x.id,"name":x.name,"slug":x.slug,"category_type":x.category_type,
             "priority":x.priority,"active":x.active} for x in rows]

@app.get("/api/admin/categories")
def admin_categories(db:Session=Depends(get_db),_=Depends(admin_guard)):
    _seed_managed_categories(db)
    rows=db.query(ManagedCategory).order_by(ManagedCategory.priority.asc()).all()
    return [{"id":x.id,"name":x.name,"slug":x.slug,"category_type":x.category_type,
             "priority":x.priority,"active":x.active} for x in rows]

@app.post("/api/admin/categories")
def admin_add_category(data:ManagedCategoryIn,db:Session=Depends(get_db),_=Depends(admin_guard)):
    if db.query(ManagedCategory).filter(ManagedCategory.slug==data.slug).first():
        raise HTTPException(400,"Category slug already exists")
    row=ManagedCategory(name=data.name.strip(),slug=data.slug.strip().lower(),
        category_type=data.category_type.upper(),priority=data.priority,active=data.active)
    db.add(row); db.commit(); db.refresh(row)
    return {"ok":True,"id":row.id}

@app.put("/api/admin/categories/{category_id}")
def admin_update_category(category_id:int,data:ManagedCategoryIn,db:Session=Depends(get_db),_=Depends(admin_guard)):
    row=db.get(ManagedCategory,category_id)
    if not row: raise HTTPException(404,"Category not found")
    row.name=data.name.strip(); row.slug=data.slug.strip().lower()
    row.category_type=data.category_type.upper(); row.priority=data.priority; row.active=data.active
    db.commit()
    return {"ok":True}

@app.post("/api/admin/categories/{category_id}/toggle")
def admin_toggle_category(category_id:int,db:Session=Depends(get_db),_=Depends(admin_guard)):
    row=db.get(ManagedCategory,category_id)
    if not row: raise HTTPException(404,"Category not found")
    row.active=not row.active; db.commit()
    return {"ok":True,"active":row.active}

@app.delete("/api/admin/categories/{category_id}")
def admin_delete_category(category_id:int,db:Session=Depends(get_db),_=Depends(admin_guard)):
    row=db.get(ManagedCategory,category_id)
    if not row: raise HTTPException(404,"Category not found")
    # Soft delete protects historical requests/matching references.
    row.active=False; db.commit()
    return {"ok":True,"deleted":"soft"}


# --- v1.8 WhatsApp lifecycle + dual job confirmation ---
class NotificationIn(_PMBaseModel):
    user_type: str
    user_id: int
    event_type: str
    request_id: int | None = None
    job_id: int | None = None
    payload: str | None = None

class JobConfirmationIn(_PMBaseModel):
    party_type: str
    party_id: int
    answer: str
    note: str | None = None

def _queue_notification(db, user_type, user_id, event_type, request_id=None, job_id=None, payload=None):
    # WhatsApp remains a notification/return channel; actions happen on PunëMbaruar web.
    row=NotificationEvent(user_type=user_type.upper(),user_id=user_id,event_type=event_type.upper(),
        request_id=request_id,job_id=job_id,payload=payload,status='QUEUED')
    db.add(row); db.commit(); db.refresh(row)
    return row

@app.post("/api/notifications/queue")
def queue_notification(data:NotificationIn,db:Session=Depends(get_db),_=Depends(admin_guard)):
    allowed={'NEW_REQUEST','NEW_OFFER','OFFER_ACCEPTED','UNREAD_CHAT','JOB_CONFIRMATION','REVIEW'}
    if data.event_type.upper() not in allowed: raise HTTPException(400,"Unsupported event")
    row=_queue_notification(db,data.user_type,data.user_id,data.event_type,data.request_id,data.job_id,data.payload)
    return {"ok":True,"notification_id":row.id}

@app.get("/api/admin/notifications")
def admin_notifications(status:str|None=None,db:Session=Depends(get_db),_=Depends(admin_guard)):
    q=db.query(NotificationEvent)
    if status: q=q.filter(NotificationEvent.status==status.upper())
    rows=q.order_by(NotificationEvent.created_at.desc()).limit(500).all()
    return [{"id":x.id,"user_type":x.user_type,"user_id":x.user_id,"event_type":x.event_type,
             "request_id":x.request_id,"job_id":x.job_id,"status":x.status,
             "grouped_count":x.grouped_count,"payload":x.payload,
             "created_at":x.created_at.isoformat()} for x in rows]

@app.post("/api/jobs/{job_id}/confirm")
def confirm_job(job_id:int,data:JobConfirmationIn,db:Session=Depends(get_db)):
    party=data.party_type.upper(); answer=data.answer.upper()
    if party not in {'CLIENT','PROFESSIONAL'}: raise HTTPException(400,"Invalid party")
    if answer not in {'YES','NO','STILL_IN_PROGRESS'}: raise HTTPException(400,"Invalid answer")
    old=db.query(JobConfirmation).filter(JobConfirmation.job_id==job_id,
        JobConfirmation.party_type==party,JobConfirmation.party_id==data.party_id).first()
    if old:
        old.answer=answer; old.note=data.note; old.created_at=datetime.utcnow()
    else:
        db.add(JobConfirmation(job_id=job_id,party_type=party,party_id=data.party_id,
            answer=answer,note=data.note))
    db.commit()
    answers=db.query(JobConfirmation).filter(JobConfirmation.job_id==job_id).all()
    client=next((x.answer for x in answers if x.party_type=='CLIENT'),None)
    pro=next((x.answer for x in answers if x.party_type=='PROFESSIONAL'),None)
    if client=='YES' and pro=='YES': outcome='COMPLETED'
    elif client=='NO' and pro=='NO': outcome='NOT_COMPLETED'
    elif client=='STILL_IN_PROGRESS' or pro=='STILL_IN_PROGRESS': outcome='IN_PROGRESS'
    elif client and pro and client!=pro: outcome='DISPUTED'
    else: outcome='AWAITING_OTHER_PARTY'
    return {"ok":True,"job_id":job_id,"client_answer":client,"professional_answer":pro,"outcome":outcome,
            "verified_review_allowed": outcome=='COMPLETED'}

@app.get("/api/admin/jobs/{job_id}/confirmations")
def admin_job_confirmations(job_id:int,db:Session=Depends(get_db),_=Depends(admin_guard)):
    rows=db.query(JobConfirmation).filter(JobConfirmation.job_id==job_id).all()
    return [{"party_type":x.party_type,"party_id":x.party_id,"answer":x.answer,
             "note":x.note,"created_at":x.created_at.isoformat()} for x in rows]

@app.post("/api/admin/jobs/{job_id}/request-confirmation")
def request_job_confirmation(job_id:int,client_id:int,professional_id:int,db:Session=Depends(get_db),_=Depends(admin_guard)):
    c=_queue_notification(db,'CLIENT',client_id,'JOB_CONFIRMATION',job_id=job_id,
        payload='A u krye puna? Po / Jo / Ende jo')
    pr=_queue_notification(db,'PROFESSIONAL',professional_id,'JOB_CONFIRMATION',job_id=job_id,
        payload='A u krye puna? Po / Jo / Ende ne proces')
    return {"ok":True,"client_notification":c.id,"professional_notification":pr.id}

@app.post("/api/admin/notifications/group-client-offers")
def group_client_offer_notifications(client_id:int,request_id:int,db:Session=Depends(get_db),_=Depends(admin_guard)):
    # Groups queued NEW_OFFER alerts to avoid WhatsApp spam.
    rows=db.query(NotificationEvent).filter(NotificationEvent.user_type=='CLIENT',
        NotificationEvent.user_id==client_id,NotificationEvent.request_id==request_id,
        NotificationEvent.event_type=='NEW_OFFER',NotificationEvent.status=='QUEUED').all()
    if len(rows)<=1: return {"ok":True,"grouped":len(rows)}
    keep=rows[0]; keep.grouped_count=len(rows); keep.payload=f"Ke marre {len(rows)} oferta te reja."
    for x in rows[1:]: x.status='GROUPED'
    db.commit()
    return {"ok":True,"grouped":len(rows),"notification_id":keep.id}
