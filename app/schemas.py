"""
Schema input/output API -- dipakai FastAPI buat validasi otomatis.
Kalau user (webapp) kirim data yang formatnya salah, FastAPI otomatis
nolak dengan pesan error yang jelas, tanpa kita perlu cek manual.
"""

from pydantic import BaseModel, Field
from typing import Literal


class PredictRequest(BaseModel):
    # ---- Identitas user (buat nyimpen histori sesi -- Progressive Overload Tracker) ----
    user_id: str = Field(..., min_length=1, description="ID unik user, dipakai untuk tracking histori")

    # ---- Data profil user (diisi sekali di awal / tersimpan di akun) ----
    age: int = Field(..., ge=10, le=80, description="Umur (tahun)")
    gender: Literal["male", "female"]
    height_cm: float = Field(..., ge=100, le=230, description="Tinggi badan (cm)")
    weight_kg: float = Field(..., ge=25, le=200, description="Berat badan (kg)")
    training_history: Literal["pemula", "rutin", "terlatih"]

    # ---- Personalisasi tambahan (briefing mentor) ----
    goal: Literal["sehat", "turun_bb", "naik_otot"] = Field(
        "sehat", description="Tujuan latihan user -- mempengaruhi cara insight diinterpretasikan"
    )
    injury_history: Literal["tidak_ada", "lutut", "pergelangan_kaki", "punggung", "lainnya"] = Field(
        "tidak_ada", description="Riwayat cedera -- mempengaruhi sensitivitas warning"
    )

    # ---- Data sensor real-time (dari strap, atau simulasi di webapp) ----
    hr_current: float = Field(..., ge=30, le=250, description="Detak jantung saat ini (bpm)")
    breathing_rate: float = Field(..., ge=5, le=70, description="Napas per menit")
    duration_in_high_zone_min: float = Field(
        0, ge=0, le=180, description="Menit yang sudah dihabiskan di HR zone tinggi (4-5) sesi ini"
    )
    speed_decline_pct: float = Field(
        0, ge=0, le=100, description="Persen penurunan kecepatan dari baseline personal"
    )

    # ---- Self-report (opsional tapi meningkatkan akurasi) ----
    sleep_hours_last_night: float = Field(7, ge=0, le=14, description="Jam tidur semalam")
    rpe_self_report: float = Field(
        5, ge=1, le=10, description="Rate of Perceived Exertion, skala 1-10 (self-report)"
    )

    # ---- HR istirahat, kalau ada datanya (opsional, ada default estimasi) ----
    hr_rest: float | None = Field(
        None, ge=30, le=120, description="HR istirahat (opsional, kalau kosong akan diestimasi)"
    )


class Insight(BaseModel):
    """Semua field di sini adalah kalimat siap-baca -- webapp tinggal
    nampilin string-nya langsung, tanpa perlu interpretasi tambahan
    di frontend."""
    headline: str          # 1 kalimat ringkasan utama, buat ditampilin gede di dashboard
    hr_status: str          # penjelasan HR relatif ke HR max personal
    body_status: str        # penjelasan BMI relatif ke tinggi/berat badan
    goal_insight: str       # insight yang disesuaikan sama goal user
    recommendation: str     # rekomendasi aksi konkret
    warning: str | None = None  # cuma keisi kalau ada kondisi yang perlu diwaspadai (termasuk dari injury_history)


class PredictResponse(BaseModel):
    # Angka mentah -- tetap disediakan buat kebutuhan chart/grafik di frontend,
    # TAPI bukan yang utama ditampilin ke user tanpa konteks.
    fatigue_score: float
    risk_level: str
    hr_zone: int
    hr_max: float
    hr_pct_of_max: float
    bmi: float

    # Insight -- ini yang jadi konten utama ditampilkan ke user
    insight: Insight


class ProgressResponse(BaseModel):
    """Response untuk GET /progress/{user_id} -- hasil analisis
    Progressive Overload Tracker."""
    status: str  # "ok" atau "belum_cukup_data"
    headline: str
    trend: str | None = None  # "menurun" / "meningkat" / "stabil"
    overload_recommendation: str | None = None
    sessions_analyzed: int = 0
    avg_fatigue_recent: float | None = None
