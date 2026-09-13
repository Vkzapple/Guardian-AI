"""
Database layer -- Supabase (Postgres) untuk nyimpen histori sesi latihan.

Kenapa pindah dari SQLite ke Supabase:
- Bisa diakses dari mana aja (nggak keiket ke 1 laptop/server)
- Ada dashboard visual buat liat data tanpa command line
- Lebih siap kalau nanti webapp di-deploy (SQLite file-based kurang cocok
  untuk multi-instance deployment)

Setup:
1. Buat project di supabase.com
2. Jalankan supabase_schema.sql di SQL Editor project kamu
3. Isi .env dengan SUPABASE_URL dan SUPABASE_SERVICE_KEY
   (ambil dari Project Settings -> API)
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

_client: Client | None = None


def get_client() -> Client:
    global _client
    if _client is None:
        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            raise RuntimeError(
                "SUPABASE_URL / SUPABASE_SERVICE_KEY belum di-set. "
                "Cek file .env kamu (lihat .env.example)."
            )
        _client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    return _client


def init_db():
    """Cek koneksi ke Supabase jalan atau nggak saat server startup.
    (Tabel sendiri dibuat manual lewat supabase_schema.sql, bukan di sini.)"""
    client = get_client()
    # Ping sederhana: coba select 1 baris, kalau tabel belum ada ini bakal error
    # dengan pesan yang jelas ketimbang error nyasar pas request pertama masuk.
    try:
        client.table("sessions").select("id").limit(1).execute()
        print("✅ Koneksi Supabase berhasil, tabel 'sessions' ditemukan.")
    except Exception as e:
        print(f"⚠️  Gagal konek/tabel belum ada: {e}")
        print("   -> Pastikan sudah menjalankan supabase_schema.sql di SQL Editor Supabase.")


def save_session(user_id: str, fatigue_score: float, hr_zone: int,
                  hr_pct_of_max: float, duration_in_high_zone_min: float, goal: str):
    client = get_client()
    client.table("sessions").insert({
        "user_id": user_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "fatigue_score": fatigue_score,
        "hr_zone": hr_zone,
        "hr_pct_of_max": hr_pct_of_max,
        "duration_in_high_zone_min": duration_in_high_zone_min,
        "goal": goal,
    }).execute()


def get_recent_sessions(user_id: str, limit: int = 10) -> list[dict]:
    client = get_client()
    response = (
        client.table("sessions")
        .select("*")
        .eq("user_id", user_id)
        .order("timestamp", desc=True)
        .limit(limit)
        .execute()
    )
    rows = response.data or []
    # Balik urutannya jadi kronologis (lama -> baru) biar konsisten sama
    # logic analyze_progressive_overload() yang sudah ada.
    return list(reversed(rows))
