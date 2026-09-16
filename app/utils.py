def calculate_hr_max(age: int) -> float:
    """Formula Tanaka -- sudah divalidasi vs dataset Gym Members Exercise
    (selisih rata-rata cuma ~1 bpm dari data real)."""
    return 208 - 0.7 * age


def estimate_hr_rest(training_history: str) -> float:
    """Estimasi default HR rest kalau tidak dikirim di request."""
    defaults = {"pemula": 69, "rutin": 62, "terlatih": 52}
    return defaults.get(training_history, 62)


def calculate_hr_zone(hr_pct_of_max: float) -> int:
    if hr_pct_of_max < 0.6:
        return 1
    elif hr_pct_of_max < 0.7:
        return 2
    elif hr_pct_of_max < 0.8:
        return 3
    elif hr_pct_of_max < 0.9:
        return 4
    else:
        return 5


def calculate_bmi(weight_kg: float, height_cm: float) -> float:
    height_m = height_cm / 100
    return round(weight_kg / (height_m ** 2), 2)


def get_risk_level(fatigue_score: float) -> str:
    """Kategori risiko dalam Bahasa Indonesia -- backend Node.js men-decode
    ini lewat keyword matching ('aman'/'waspada'/'bahaya'/dst) jadi status
    internal (optimal/caution/warning/critical), jadi kata kuncinya harus
    tetap konsisten."""
    if fatigue_score < 40:
        return "Aman"
    elif fatigue_score < 65:
        return "Waspada"
    elif fatigue_score < 85:
        return "Berisiko"
    else:
        return "Kritis"


def get_recommendation(fatigue_score: float, hr_zone: int, bmi: float, training_history: str) -> str:
    """Rekomendasi aksi konkret -- gabungan fatigue score, HR zone, BMI, training history."""

    if fatigue_score >= 85:
        return (
            "Segera hentikan sesi latihan. Kondisi menunjukkan kelelahan berat -- "
            "istirahat total dan pastikan hidrasi tercukupi. Pantau kondisi 30 menit ke depan."
        )
    if fatigue_score >= 65:
        return (
            "Turunkan intensitas latihan ke Zona 1-2. Pertimbangkan mengakhiri sesi "
            "lebih awal dari rencana untuk mencegah risiko cedera."
        )
    if fatigue_score >= 55:
        return (
            "Kondisi mulai menunjukkan tanda kelelahan (Waspada). Pertahankan intensitas saat ini, "
            "jangan naikkan beban latihan, dan perhatikan sinyal tubuh dalam 10-15 menit ke depan."
        )

    if bmi < 18.5:
        base = "Fokus jalan cepat dan jogging ringan di Zona 1-2, hindari intensitas tinggi."
    elif bmi < 25:
        base = "Kondisi fisik mendukung latihan di Zona 2-3 dengan durasi lebih panjang."
    elif bmi < 30:
        base = "Disarankan jalan cepat / jogging interval, fokus di Zona 1-2 dulu."
    else:
        base = "Disarankan jalan kaki dan latihan intensitas rendah (Zona 1), hindari beban tinggi pada sendi."

    history_note = {
        "pemula": " Mulai dengan sesi pendek 15-20 menit dan tingkatkan bertahap.",
        "rutin": " Durasi 30-45 menit sudah sesuai untuk level kamu saat ini.",
        "terlatih": " Kondisi mendukung untuk interval training di Zona 3-4 jika diperlukan.",
    }
    return base + history_note.get(training_history, "")


def estimate_vo2max(hr_max: float, hr_rest: float) -> float:
    """Formula Uth-Sorensen-Overgaard-Pedersen -- estimasi VO2max dari
    rasio HR Max terhadap HR Rest. Published, banyak dipakai di riset
    sports science sebagai estimasi cepat tanpa tes lab."""
    return 15.3 * (hr_max / hr_rest)


def estimate_pace_zones(hr_rest: float, hr_max: float) -> dict:
    """Hitung range pace (menit:detik per km) untuk tiap HR zone,
    personal per user (berdasarkan HR max & HR rest mereka sendiri).

    Alur: VO2max -> velocity di VO2max (vVO2max, pakai formula ACSM
    metabolic equation) -> velocity tiap zone sebagai % dari vVO2max
    -> dikonversi ke pace (menit/km).
    """
    vo2max = estimate_vo2max(hr_max, hr_rest)

    # ACSM running metabolic equation (VO2 dalam ml/kg/min, speed dalam m/min):
    # VO2 = 0.2 * speed + 3.5  ->  speed = (VO2 - 3.5) / 0.2
    v_vo2max_m_per_min = (vo2max - 3.5) / 0.2
    v_vo2max_kmh = v_vo2max_m_per_min * 60 / 1000
    # % dari vVO2max per HR zone (berdasarkan korelasi HR%-velocity%
    zone_velocity_pct = {
        1: (0.55, 0.65),  # Recovery
        2: (0.65, 0.78),  # Easy / aerobic
        3: (0.78, 0.88),  # Tempo
        4: (0.88, 0.95),  # Threshold
        5: (0.95, 1.02),  # Interval / VO2max
    }

    def kmh_to_pace_str(kmh: float) -> str:
        if kmh <= 0:
            return "-"
        pace_min_per_km = 60 / kmh
        minutes = int(pace_min_per_km)
        seconds = int(round((pace_min_per_km - minutes) * 60))
        if seconds == 60:
            minutes += 1
            seconds = 0
        return f"{minutes}:{seconds:02d}"

    zones = {}
    for zone, (pct_low, pct_high) in zone_velocity_pct.items():
        v_low = v_vo2max_kmh * pct_low
        v_high = v_vo2max_kmh * pct_high
        # Pace berbanding terbalik dengan velocity => velocity rendah = pace lambat (angka besar)
        zones[zone] = {
            "pace_range": f"{kmh_to_pace_str(v_high)}-{kmh_to_pace_str(v_low)} /km",
            "velocity_kmh_range": [round(v_low, 1), round(v_high, 1)],
        }
    return zones


def get_pace_recommendation(hr_rest: float, hr_max: float, target_hr_zone: int) -> dict:
    """Rekomendasi pace konkret untuk 1 target HR zone spesifik
    (dipakai buat next_session_recommendation)."""
    zones = estimate_pace_zones(hr_rest, hr_max)
    target = zones.get(target_hr_zone, zones[2])
    return {
        "target_hr_zone": target_hr_zone,
        "pace_range": target["pace_range"],
    }


def calculate_acwr_injury_risk(recent_fatigue_scores: list) -> tuple[float, str]:
    n = len(recent_fatigue_scores)
    acute_window = min(3, n)
    acute_load = sum(recent_fatigue_scores[-acute_window:]) / acute_window
    chronic_load = sum(recent_fatigue_scores) / n  # semua data yang ada sbg proxy chronic (s.d. 28)

    if chronic_load == 0:
        acwr = 1.0
    else:
        acwr = acute_load / chronic_load

    import math
    risk = 1 / (1 + math.exp(-6 * (acwr - 1.3)))
    risk_percent = round(risk * 100, 1)

    return risk_percent, "acwr"


def calculate_fallback_injury_risk(
    fatigue_score: float, hr_zone: int, injury_history: str, speed_decline_pct: float
) -> tuple[float, str]:
    """Fallback if histori <5 sesi -- estimasi dari sinyal sesi
    saat ini saja."""
    base = fatigue_score * 0.55  # fatigue tinggi => kontribusi terbesar
    zone_add = {1: 0, 2: 0, 3: 5, 4: 12, 5: 20}.get(hr_zone, 0)
    injury_add = 15 if (injury_history and injury_history != "tidak_ada") else 0
    decline_add = min(speed_decline_pct * 0.3, 15)

    risk_percent = min(base + zone_add + injury_add + decline_add, 97)
    return round(risk_percent, 1), "heuristic_awal"


def build_next_session_recommendation(
    injury_risk_percent: float, hr_rest: float, hr_max: float,
    current_hr_zone: int, sport: str = "lari",
) -> dict:
    """translate injury risk % jadi rekomendasi dalam bahasa buat user:target HR bpm + pace"""
    if injury_risk_percent >= 50:
        target_zone = max(1, current_hr_zone - 2)
        urgency = f"Risiko cedera terdeteksi {injury_risk_percent:.0f}%."
    elif injury_risk_percent >= 30:
        target_zone = max(1, current_hr_zone - 1)
        urgency = f"Risiko cedera mulai naik ({injury_risk_percent:.0f}%)."
    else:
        target_zone = current_hr_zone
        urgency = f"Risiko cedera masih rendah ({injury_risk_percent:.0f}%)."

    zone_upper_pct = {1: 0.6, 2: 0.7, 3: 0.8, 4: 0.9, 5: 1.0}
    target_hr_bpm = round(hr_rest + (hr_max - hr_rest) * zone_upper_pct.get(target_zone, 0.7))

    pace_info = get_pace_recommendation(hr_rest, hr_max, target_zone) if sport == "lari" else None

    if injury_risk_percent >= 50:
        text = (
            f"{urgency} Turunkan HR latihan berikutnya ke bawah {target_hr_bpm} bpm "
            f"(Zona {target_zone})"
        )
        if pace_info:
            text += f", setara pace {pace_info['pace_range']}."
        else:
            text += "."
        text += " Pertimbangkan istirahat 1 hari sebelum sesi berikutnya."
    else:
        text = f"{urgency} Target HR sesi berikutnya di bawah {target_hr_bpm} bpm (Zona {target_zone})"
        if pace_info:
            text += f", setara pace {pace_info['pace_range']}."
        else:
            text += "."

    result = {
        "target_hr_bpm": target_hr_bpm,
        "target_hr_zone": target_zone,
        "text": text,
    }
    if pace_info:
        result["target_pace_range"] = pace_info["pace_range"]
    return result
