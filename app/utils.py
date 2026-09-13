"""
Helper functions -- semua rumus sports science (Tanaka, Karvonen, BMI)
dan logic turunan (risk level, rekomendasi) ada di sini, terpisah dari
main.py biar rapi.
"""


def calculate_hr_max(age: int) -> float:
    """Formula Tanaka -- sudah divalidasi vs dataset Gym Members Exercise
    (selisih rata-rata cuma ~1 bpm dari data real)."""
    return 208 - 0.7 * age


def estimate_hr_rest(training_history: str) -> float:
    """Estimasi default HR rest kalau user tidak input manual,
    berdasarkan kalibrasi dataset real (hr_rest_mean ~62)."""
    defaults = {"pemula": 69, "rutin": 62, "terlatih": 52}
    return defaults.get(training_history, 62)


def calculate_hr_zone(hr_pct_of_max: float) -> int:
    """Bagi ke 5 zona standar sports science berdasarkan % HR max."""
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
    """Kategori risiko dari fatigue_score 0-100."""
    if fatigue_score < 40:
        return "Aman"
    elif fatigue_score < 65:
        return "Waspada"
    elif fatigue_score < 85:
        return "Berisiko"
    else:
        return "Kritis"


def get_bmi_category(bmi: float) -> str:
    if bmi < 18.5:
        return "Underweight"
    elif bmi < 25:
        return "Normal"
    elif bmi < 30:
        return "Overweight"
    else:
        return "Obese"


# ============================================================
# INSIGHT GENERATOR -- setiap fungsi return kalimat siap-baca,
# bukan angka mentah. Webapp tinggal nampilin string-nya langsung.
# ============================================================

def build_headline(fatigue_score: float, risk_level: str) -> str:
    """1 kalimat ringkasan utama, ditampilkan paling besar di dashboard."""
    templates = {
        "Aman": f"Kondisi kamu bagus (skor {fatigue_score:.0f}/100) -- tubuh masih punya banyak ruang untuk latihan.",
        "Waspada": f"Mulai ada tanda kelelahan (skor {fatigue_score:.0f}/100) -- perhatikan sinyal tubuh 10-15 menit ke depan.",
        "Berisiko": f"Tubuh kamu sedang bekerja keras (skor {fatigue_score:.0f}/100) -- saatnya turunkan intensitas.",
        "Kritis": f"Kelelahan tinggi terdeteksi (skor {fatigue_score:.0f}/100) -- disarankan berhenti dan istirahat.",
    }
    return templates.get(risk_level, f"Skor fatigue kamu: {fatigue_score:.0f}/100")


def build_hr_status(hr_current: float, hr_max: float, hr_pct_of_max: float, hr_zone: int) -> str:
    """Terjemahin angka HR jadi kalimat yang punya makna personal."""
    pct = round(hr_pct_of_max * 100)
    zone_desc = {
        1: "zona recovery (sangat ringan)",
        2: "zona pembakaran lemak (ringan-sedang)",
        3: "zona tempo (sedang)",
        4: "zona threshold (berat)",
        5: "zona maksimal (sangat berat)",
    }
    return (
        f"Detak jantung kamu sekarang {hr_current:.0f} bpm, atau {pct}% dari HR Max "
        f"personal kamu ({hr_max:.0f} bpm) -- ini masuk {zone_desc.get(hr_zone, 'zona tidak diketahui')} (Zona {hr_zone})."
    )


def build_body_status(bmi: float, height_cm: float, weight_kg: float) -> str:
    category = get_bmi_category(bmi)
    category_id = {
        "Underweight": "kurang dari ideal (underweight)",
        "Normal": "ideal (normal)",
        "Overweight": "di atas ideal (overweight)",
        "Obese": "jauh di atas ideal (obese)",
    }
    return (
        f"Dengan tinggi {height_cm:.0f} cm dan berat {weight_kg:.0f} kg, BMI kamu {bmi:.1f} -- "
        f"tergolong {category_id.get(category, category)}. Ini yang dipakai sistem untuk "
        f"menyesuaikan jenis latihan yang direkomendasikan."
    )


def build_goal_insight(fatigue_score: float, hr_zone: int, goal: str) -> str:
    """Insight yang beda maknanya tergantung tujuan user -- fatigue score
    yang sama bisa berarti beda tergantung goal."""
    if goal == "turun_bb":
        if hr_zone <= 2:
            return (
                "Kamu ada di zona pembakaran lemak -- pertahankan durasi di zona ini "
                "selama mungkin, ini lebih efektif untuk turun berat badan dibanding buru-buru ke zona tinggi."
            )
        elif hr_zone >= 4:
            return (
                "Intensitas kamu sudah di atas zona pembakaran lemak optimal. Untuk goal turun BB, "
                "pertimbangkan turunkan sedikit ke Zona 2-3 agar bisa bertahan lebih lama."
            )
        return "Intensitas kamu sudah pas untuk goal turun berat badan, tetap konsisten."
    elif goal == "naik_otot":
        if fatigue_score >= 65:
            return (
                "Fatigue tinggi setelah latihan beban itu wajar -- ini indikasi otot mendapat stimulus "
                "yang cukup. Fokus sekarang: recovery dan asupan protein, bukan menahan diri."
            )
        return "Kondisi kamu masih cukup segar. Kalau targetnya naik otot, pastikan intensitas latihan beban cukup menantang."
    else:  # sehat
        return "Fokus kamu untuk kesehatan umum sudah on-track -- konsistensi di Zona 2-3 lebih penting daripada intensitas maksimal."


def get_warning(injury_history: str, hr_zone: int, speed_decline_pct: float) -> str | None:
    """Warning tambahan berdasarkan riwayat cedera -- threshold lebih sensitif
    kalau user pernah cedera di area tertentu."""
    injury_labels = {
        "lutut": "lutut", "pergelangan_kaki": "pergelangan kaki",
        "punggung": "punggung", "lainnya": "area yang pernah cedera",
    }
    if injury_history in injury_labels and (hr_zone >= 4 or speed_decline_pct >= 20):
        area = injury_labels[injury_history]
        return (
            f"Kamu punya riwayat cedera di {area}. Intensitas saat ini cukup tinggi -- "
            f"perhatikan teknik gerakan dan pertimbangkan hentikan lebih awal kalau terasa nyeri di {area}."
        )
    return None


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


# ============================================================
# PROGRESSIVE OVERLOAD ANALYSIS -- butuh histori beberapa sesi terakhir
# ============================================================

def analyze_progressive_overload(sessions: list[dict]) -> dict:
    """Analisis tren fatigue_score dari histori sesi, kasih rekomendasi
    naik/turun/pertahankan beban latihan.

    sessions: list of dict, urutan kronologis (lama -> baru), tiap dict
    punya key: fatigue_score, hr_zone, duration_in_high_zone_min, timestamp
    """
    if len(sessions) < 2:
        return {
            "status": "belum_cukup_data",
            "headline": "Butuh minimal 2 sesi latihan untuk mulai menganalisis tren progres kamu.",
            "trend": None,
            "overload_recommendation": None,
        }

    # Ambil sampai 5 sesi terakhir buat analisis tren
    recent = sessions[-5:]
    scores = [s["fatigue_score"] for s in recent]

    # Tren sederhana: bandingkan rata-rata separuh awal vs separuh akhir
    mid = len(scores) // 2
    if mid == 0:
        first_half_avg = scores[0]
        second_half_avg = scores[-1]
    else:
        first_half_avg = sum(scores[:mid]) / mid
        second_half_avg = sum(scores[mid:]) / (len(scores) - mid)

    delta = second_half_avg - first_half_avg

    if delta <= -5:
        trend = "menurun"
        headline = (
            f"Fatigue score kamu cenderung menurun dari sesi-sesi sebelumnya "
            f"({first_half_avg:.0f} -> {second_half_avg:.0f}) -- tanda kondisi kardiovaskular membaik."
        )
        overload_recommendation = (
            "Sistem merekomendasikan naikkan beban latihan sekitar 10-15% "
            "(durasi atau intensitas) di sesi berikutnya untuk progressive overload yang optimal."
        )
        action = "naikkan_beban"
    elif delta >= 5:
        trend = "meningkat"
        headline = (
            f"Fatigue score kamu cenderung naik dari sesi-sesi sebelumnya "
            f"({first_half_avg:.0f} -> {second_half_avg:.0f}) -- tubuh butuh waktu pemulihan lebih."
        )
        overload_recommendation = (
            "Sistem merekomendasikan pertahankan atau sedikit turunkan beban latihan, "
            "dan pastikan waktu istirahat antar sesi cukup sebelum menambah beban lagi."
        )
        action = "turunkan_atau_pertahankan"
    else:
        trend = "stabil"
        headline = (
            f"Fatigue score kamu relatif stabil di kisaran {second_half_avg:.0f} beberapa sesi terakhir."
        )
        overload_recommendation = (
            "Kondisi kamu konsisten. Sistem merekomendasikan naikkan beban sedikit (5-10%) "
            "untuk mulai mendorong adaptasi baru, selama tidak ada tanda kelelahan berlebih."
        )
        action = "naikkan_bertahap"

    return {
        "status": "ok",
        "headline": headline,
        "trend": trend,
        "action": action,
        "overload_recommendation": overload_recommendation,
        "sessions_analyzed": len(recent),
        "avg_fatigue_recent": round(second_half_avg, 1),
    }
