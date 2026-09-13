"""
FastAPI Backend -- AI Sports Performance Analytics
=====================================================
Endpoint utama: POST /predict
Terima data profil user + data sensor (real/simulasi), return
fatigue score, HR zone, risk level, dan rekomendasi personalized.

Jalankan:
    uvicorn app.main:app --reload --port 8000

Docs otomatis (buat testing manual di browser):
    http://localhost:8000/docs
"""

import os
import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import PredictRequest, PredictResponse, Insight, ProgressResponse
from app.utils import (
    calculate_hr_max,
    estimate_hr_rest,
    calculate_hr_zone,
    calculate_bmi,
    get_risk_level,
    get_recommendation,
    build_headline,
    build_hr_status,
    build_body_status,
    build_goal_insight,
    get_warning,
    analyze_progressive_overload,
)
from app.database import init_db, save_session, get_recent_sessions

# ============================================================
# SETUP APP
# ============================================================
app = FastAPI(
    title="AI Sports Performance Analytics API",
    description="API untuk prediksi fatigue score & rekomendasi latihan personalized",
    version="1.0.0",
)

# CORS -- biar webapp frontend (beda origin/port) bisa akses API ini.
# Untuk production, ganti allow_origins ke domain webapp kamu yang sebenarnya.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# LOAD MODEL (sekali saat server start, bukan tiap request)
# ============================================================
MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "model", "fatigue_model.pkl")
model = None


@app.on_event("startup")
def load_model():
    global model
    if not os.path.exists(MODEL_PATH):
        raise RuntimeError(f"Model tidak ditemukan di {MODEL_PATH}")
    model = joblib.load(MODEL_PATH)
    print(f"✅ Model berhasil dimuat dari {MODEL_PATH}")

    # Supabase opsional saat startup -- kalau .env belum diisi, server tetap
    # nyala (endpoint /predict masih bisa dites), tapi /progress & auto-save
    # sesi bakal error sampai .env dikonfigurasi dengan benar.
    try:
        init_db()
    except Exception as e:
        print(f"⚠️  Supabase belum siap: {e}")
        print("   -> Cek .env kamu (lihat .env.example). Endpoint /predict tetap jalan,")
        print("      tapi histori sesi tidak akan tersimpan sampai ini diperbaiki.")


# ============================================================
# ENDPOINTS
# ============================================================
@app.get("/")
def root():
    return {"status": "ok", "message": "AI Sports Performance Analytics API is running"}


@app.get("/health")
def health_check():
    return {"status": "healthy", "model_loaded": model is not None}


@app.post("/predict", response_model=PredictResponse)
def predict_fatigue(req: PredictRequest):
    if model is None:
        raise HTTPException(status_code=503, detail="Model belum siap, coba lagi sebentar")

    # ---- 1. Hitung variabel turunan (personalized baseline) ----
    hr_max = calculate_hr_max(req.age)
    hr_rest = req.hr_rest if req.hr_rest is not None else estimate_hr_rest(req.training_history)
    hr_pct_of_max = req.hr_current / hr_max
    hr_zone = calculate_hr_zone(hr_pct_of_max)
    bmi = calculate_bmi(req.weight_kg, req.height_cm)

    # ---- 2. Susun input sesuai format yang dipakai saat training model ----
    model_input = pd.DataFrame([{
        "age": req.age,
        "height_cm": req.height_cm,
        "weight_kg": req.weight_kg,
        "bmi": bmi,
        "hr_rest": hr_rest,
        "hr_max": hr_max,
        "hr_current": req.hr_current,
        "hr_pct_of_max": hr_pct_of_max,
        "breathing_rate": req.breathing_rate,
        "duration_in_high_zone_min": req.duration_in_high_zone_min,
        "speed_decline_pct": req.speed_decline_pct,
        "sleep_hours_last_night": req.sleep_hours_last_night,
        "rpe_self_report": req.rpe_self_report,
        "gender": req.gender,
        "training_history": req.training_history,
    }])

    # ---- 3. Prediksi pakai model ML ----
    fatigue_score = float(model.predict(model_input)[0])
    fatigue_score = max(0, min(100, fatigue_score))  # safety clamp

    # ---- 4. Turunan hasil: risk level & insight personal ----
    risk_level = get_risk_level(fatigue_score)

    insight = Insight(
        headline=build_headline(fatigue_score, risk_level),
        hr_status=build_hr_status(req.hr_current, hr_max, hr_pct_of_max, hr_zone),
        body_status=build_body_status(bmi, req.height_cm, req.weight_kg),
        goal_insight=build_goal_insight(fatigue_score, hr_zone, req.goal),
        recommendation=get_recommendation(fatigue_score, hr_zone, bmi, req.training_history),
        warning=get_warning(req.injury_history, hr_zone, req.speed_decline_pct),
    )

    # ---- 5. Simpan sesi ini ke histori (buat Progressive Overload Tracker) ----
    # Dibungkus try/except -- kalau Supabase gagal (misal koneksi internet
    # putus), prediksi utama tetap jalan dan user tetap dapat hasilnya.
    try:
        save_session(
            user_id=req.user_id,
            fatigue_score=fatigue_score,
            hr_zone=hr_zone,
            hr_pct_of_max=hr_pct_of_max,
            duration_in_high_zone_min=req.duration_in_high_zone_min,
            goal=req.goal,
        )
    except Exception as e:
        print(f"⚠️  Gagal simpan sesi ke Supabase: {e}")

    return PredictResponse(
        fatigue_score=round(fatigue_score, 1),
        risk_level=risk_level,
        hr_zone=hr_zone,
        hr_max=round(hr_max, 1),
        hr_pct_of_max=round(hr_pct_of_max, 3),
        bmi=bmi,
        insight=insight,
    )


@app.get("/progress/{user_id}", response_model=ProgressResponse)
def get_progress(user_id: str):
    """Progressive Overload Tracker -- analisis tren dari histori sesi
    user, kasih rekomendasi naik/turun/pertahankan beban latihan."""
    try:
        sessions = get_recent_sessions(user_id, limit=10)
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Gagal ambil histori dari Supabase: {e}. Cek konfigurasi .env kamu.",
        )
    result = analyze_progressive_overload(sessions)
    return ProgressResponse(**result)
