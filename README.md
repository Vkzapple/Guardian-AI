# AI Sports Performance Analytics -- Backend API

## Struktur Folder
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI app + endpoint /predict
│   ├── schemas.py        # Validasi input/output (Pydantic)
│   └── utils.py          # Formula HR zone, BMI, risk level, rekomendasi
├── model/
│   └── fatigue_model.pkl # Model Random Forest hasil training di Kaggle
├── requirements.txt
└── README.md
```

## Setup di VSCode

1. Buka folder `backend/` di VSCode
2. Bikin virtual environment:
   ```bash
   python -m venv venv
   ```
3. Aktifkan virtual environment:
   - Windows: `venv\Scripts\activate`
   - Mac/Linux: `source venv/bin/activate`
4. Install dependencies (versi sudah di-pin biar sama persis dengan environment training di Kaggle, supaya model .pkl bisa di-load tanpa error):
   ```bash
   pip install -r requirements.txt
   ```
5. Jalankan server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
6. Buka browser ke `http://localhost:8000/docs` -- ini dokumentasi interaktif otomatis dari FastAPI (Swagger UI), bisa langsung dicoba klik "Try it out" tanpa perlu Postman.

## Contoh Request ke /predict

```json
POST http://localhost:8000/predict
Content-Type: application/json

{
  "age": 22,
  "gender": "male",
  "height_cm": 172,
  "weight_kg": 68,
  "training_history": "rutin",
  "hr_current": 165,
  "breathing_rate": 32,
  "duration_in_high_zone_min": 12,
  "speed_decline_pct": 15,
  "sleep_hours_last_night": 6.5,
  "rpe_self_report": 7
}
```

Field yang WAJIB diisi: `age`, `gender`, `height_cm`, `weight_kg`, `training_history`, `hr_current`, `breathing_rate`.
Field lain punya default value kalau tidak diisi (lihat `app/schemas.py`).

## Contoh Response

```json
{
  "fatigue_score": 64.5,
  "risk_level": "Waspada",
  "hr_zone": 4,
  "hr_max": 192.6,
  "hr_pct_of_max": 0.857,
  "recommendation": "Kondisi mulai menunjukkan tanda kelelahan (Waspada)..."
}
```

## Integrasi ke Frontend/Webapp

Dari JavaScript (React/vanilla), panggil endpoint ini pakai `fetch`:

```javascript
const response = await fetch("http://localhost:8000/predict", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    age: 22,
    gender: "male",
    height_cm: 172,
    weight_kg: 68,
    training_history: "rutin",
    hr_current: simulatedHR,       // dari sensor simulasi real-time
    breathing_rate: simulatedBreathing,
    duration_in_high_zone_min: durationHighZone,
    speed_decline_pct: speedDecline,
    sleep_hours_last_night: 6.5,
    rpe_self_report: 7
  })
});
const result = await response.json();
console.log(result.fatigue_score, result.risk_level, result.recommendation);
```

## Troubleshooting

**Error saat load model / InconsistentVersionWarning**
Pastikan `scikit-learn==1.6.1` persis ter-install (cek dengan `pip show scikit-learn`). Model dilatih di Kaggle dengan versi ini.

**CORS error di browser saat webapp manggil API**
Backend sudah di-set `allow_origins=["*"]` untuk development. Untuk production, ganti ke domain webapp yang sebenarnya di `app/main.py`.

**Model tidak ketemu**
Pastikan file `fatigue_model.pkl` ada persis di folder `model/`, bukan di dalam `app/`.
