import os
import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import PredictRequest, PredictResponse
from app.utils import (
    calculate_hr_max,
    estimate_hr_rest,
    calculate_hr_zone,
    calculate_bmi,
    get_risk_level,
    get_recommendation,
    estimate_pace_zones,
    calculate_acwr_injury_risk,
    calculate_fallback_injury_risk,
    build_next_session_recommendation,
)

app = FastAPI(
    title="AI Sports Performance Analytics API",
    description="Stateless AI microservice: fatigue prediction, injury risk (ACWR), pace-HR recommendation.",
    version="3.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "model", "fatigue_model.pkl")
model = None


@app.on_event("startup")
def load_model():
    global model
    if not os.path.exists(MODEL_PATH):
        raise RuntimeError(f"Model tidak ditemukan di {MODEL_PATH}")
    model = joblib.load(MODEL_PATH)
    print(f"Model berhasil dimuat dari {MODEL_PATH}")


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

    hr_max = calculate_hr_max(req.age)
    hr_rest = req.hr_rest if req.hr_rest is not None else estimate_hr_rest(req.training_history)
    hr_pct_of_max = req.hr_current / hr_max
    hr_zone = calculate_hr_zone(hr_pct_of_max)
    bmi = calculate_bmi(req.weight_kg, req.height_cm)

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
    fatigue_score = float(model.predict(model_input)[0])
    fatigue_score = max(0, min(100, fatigue_score))

    risk_level = get_risk_level(fatigue_score)
    recommendation = get_recommendation(fatigue_score, hr_zone, bmi, req.training_history)

    if len(req.recent_fatigue_scores) >= 5:
        injury_risk_percent, injury_risk_method = calculate_acwr_injury_risk(req.recent_fatigue_scores)
    else:
        injury_risk_percent, injury_risk_method = calculate_fallback_injury_risk(
            fatigue_score, hr_zone, req.injury_history, req.speed_decline_pct,
        )

    next_session_recommendation = build_next_session_recommendation(
        injury_risk_percent=injury_risk_percent,
        hr_rest=hr_rest, hr_max=hr_max,
        current_hr_zone=hr_zone, sport=req.sport,
    )

    pace_zones = estimate_pace_zones(hr_rest, hr_max) if req.sport == "lari" else {}

    return PredictResponse(
        fatigue_score=round(fatigue_score, 1),
        risk_level=risk_level,
        hr_zone=hr_zone,
        hr_max=round(hr_max, 1),
        hr_pct_of_max=round(hr_pct_of_max, 3),
        recommendation=recommendation,
        injury_risk_percent=injury_risk_percent,
        injury_risk_method=injury_risk_method,
        next_session_recommendation=next_session_recommendation,
        pace_zones=pace_zones,
    )
