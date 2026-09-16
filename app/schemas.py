
from pydantic import BaseModel, Field
from typing import Literal


class PredictRequest(BaseModel):
    age: int = Field(..., ge=10, le=80, description="Umur (tahun)")
    gender: Literal["male", "female"]
    height_cm: float = Field(..., ge=100, le=230, description="Tinggi badan (cm)")
    weight_kg: float = Field(..., ge=25, le=200, description="Berat badan (kg)")
    training_history: Literal["pemula", "rutin", "terlatih"]

    hr_current: float = Field(..., ge=30, le=250, description="Detak jantung saat ini (bpm)")
    breathing_rate: float = Field(..., ge=5, le=70, description="Napas per menit")
    duration_in_high_zone_min: float = Field(0, ge=0, le=180)
    speed_decline_pct: float = Field(0, ge=0, le=100)

    sleep_hours_last_night: float = Field(7, ge=0, le=14)
    rpe_self_report: float = Field(5, ge=1, le=10)

    hr_rest: float | None = Field(
        None, ge=30, le=120, description="HR istirahat/baseline personal (opsional, ada default estimasi)"
    )

    sport: str = Field("lari", description="Cabang olahraga -- dipakai untuk pace recommendation")
    injury_history: Literal["tidak_ada", "lutut", "pergelangan_kaki", "punggung", "lainnya"] = Field(
        "tidak_ada", description="Riwayat cedera user"
    )
    recent_fatigue_scores: list[float] = Field(
        default_factory=list,
        description="Histori fatigue_score kronologis (lama->baru) dari beberapa sesi "
                     "terakhir user, diambil Node dari Supabase. Minimal 5 data untuk "
                     "ACWR injury risk yang lebih akurat; kalau <5 dipakai fallback heuristik.",
    )


class PredictResponse(BaseModel):
    fatigue_score: float
    risk_level: str
    hr_zone: int
    hr_max: float
    hr_pct_of_max: float
    recommendation: str

    # ---- Field baru ----
    injury_risk_percent: float
    injury_risk_method: str  # "acwr" atau "heuristic_awal"
    next_session_recommendation: dict
    pace_zones: dict  # semua 5 zona, buat ditampilin sebagai referensi lengkap di UI
