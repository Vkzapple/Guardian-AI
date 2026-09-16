import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

_client: Client | None = None


def get_client() -> Client:
    global _client
    if _client is None:
        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            raise RuntimeError(
                "SUPABASE_URL / SUPABASE_SERVICE_KEY belum di-set. Cek file .env kamu."
            )
        _client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    return _client


def init_db():
    client = get_client()
    try:
        client.table("users").select("id").limit(1).execute()
        print("Koneksi Supabase berhasil, tabel 'users' ditemukan.")
    except Exception as e:
        print(f" Gagal konek/tabel belum ada: {e}")

def create_user(name: str, sport: str, age: int, gender: str, height_cm: float,
                    weight_kg: float, training_history: str,
                    resting_hr: float | None = None, max_hr: float | None = None) -> dict:
    client = get_client()
    payload = {
        "name": name, "sport": sport, "age": age, "gender": gender,
        "height_cm": height_cm, "weight_kg": weight_kg,
        "training_history": training_history,
    }
    if resting_hr is not None:
        payload["resting_hr"] = resting_hr
    if max_hr is not None:
        payload["max_hr"] = max_hr
    response = client.table("users").insert(payload).execute()
    return response.data[0]


def get_user(user_id: str) -> dict | None:
    client = get_client()
    response = client.table("users").select("*").eq("id", user_id).limit(1).execute()
    return response.data[0] if response.data else None


def list_users() -> list[dict]:
    client = get_client()
    response = client.table("users").select("*").order("created_at", desc=True).execute()
    return response.data or []


def save_reading(user_id: str, hr_current: float, hr_pct_of_max: float,
                  breathing_rate: float, sleep_hours_last_night: float,
                  rpe_self_report: float, speed_decline_pct: float,
                  duration_in_high_zone_min: float, bmi: float,
                  fatigue_score: float, risk_level: str, hr_zone: int,
                  recommendation: str, condition_status: str,
                  recovery_estimate_minutes: int, early_warning: bool,
                  warning_reasons: list[str]) -> dict:
    client = get_client()
    response = client.table("readings").insert({
        "user_id": user_id,
        "hr_current": hr_current,
        "hr_pct_of_max": hr_pct_of_max,
        "breathing_rate": breathing_rate,
        "sleep_hours_last_night": sleep_hours_last_night,
        "rpe_self_report": rpe_self_report,
        "speed_decline_pct": speed_decline_pct,
        "duration_in_high_zone_min": duration_in_high_zone_min,
        "bmi": bmi,
        "fatigue_score": fatigue_score,
        "risk_level": risk_level,
        "hr_zone": hr_zone,
        "recommendation": recommendation,
        "condition_status": condition_status,
        "recovery_estimate_minutes": recovery_estimate_minutes,
        "early_warning": early_warning,
        "warning_reasons": warning_reasons,
    }).execute()
    return response.data[0]


def get_recent_readings(user_id: str, limit: int = 10) -> list[dict]:
    client = get_client()
    response = (
        client.table("readings")
        .select("*")
        .eq("user_id", user_id)
        .order("recorded_at", desc=True)
        .limit(limit)
        .execute()
    )
    rows = response.data or []
    return list(reversed(rows))  # kronologis lama -> baru



def save_alert(user_id: str, user_name: str, status: str,
                reasons: list[str], fatigue_score: float) -> dict:
    client = get_client()
    response = client.table("alerts").insert({
        "user_id": user_id,
        "user_name": user_name,
        "status": status,
        "reasons": reasons,
        "fatigue_score": fatigue_score,
    }).execute()
    return response.data[0]

