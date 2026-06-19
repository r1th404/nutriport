import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import random
import io
import html
import json
import re
from PIL import Image
import os
import tempfile
from pathlib import Path

# ─── CONFIG ───────────────────────────────────────────────────────────────────
APP_DIR = Path(__file__).resolve().parent
MODEL_PATH = APP_DIR / "best.pt"
FOOD_CLASSES = ("buah", "lauk", "makanan_pokok", "sayur", "susu")
TRAY_CLASSES = ("tray", "nampan", "nampan_makanan")
DETECTION_CONFIDENCE = 0.25

# Ambang porsi awal berbasis persentase luas bounding box terhadap tray.
# Angka ini bersifat heuristic/MVP dan sebaiknya dikalibrasi lagi dengan ahli gizi
# atau standar porsi MBG yang dipakai instansi terkait.
MIN_PORTION_PCT = {
    "makanan_pokok": 10.0,
    "lauk": 5.0,
    "sayur": 4.0,
    "buah": 3.0,
    "susu": 2.0,
}

CATEGORIES_INFO = {
    "makanan_pokok": "Makanan Pokok",
    "lauk":          "Lauk / Protein",
    "sayur":         "Sayur",
    "buah":          "Buah",
    "susu":          "Susu",
}

# ─── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Nutriport — MBG Monitor",
    page_icon="🍱",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── SCHOOLS DATA ─────────────────────────────────────────────────────────────
SCHOOLS = {
    "367401": {
        "npsn": "20670035",
        "nama": "SMA Negeri 05 Nusantara",
        "jenjang": "SMA",
        "jumlah_murid": 890,
        "alamat": "Jl. Merdeka No. 45, Ciputat, Tangerang Selatan, Banten",
        "dapur_sppg": "SPPG Nusantara Barat — Jl. Logistik MBG No. 3",
        "kepala_sekolah": "Andi Pratama",
        "kontak": "081900001111",
    },
    "384201": {
        "npsn": "20701234",
        "nama": "SMP Negeri 12 Harapan Jaya",
        "jenjang": "SMP",
        "jumlah_murid": 640,
        "alamat": "Jl. Pahlawan No. 18, Bekasi Barat, Bekasi, Jawa Barat",
        "dapur_sppg": "SPPG Bekasi Mandiri — Jl. Industri No. 7",
        "kepala_sekolah": "Siti Rahayu",
        "kontak": "082100002222",
    },
    "291005": {
        "npsn": "20512345",
        "nama": "SD Negeri 03 Mekar Sari",
        "jenjang": "SD",
        "jumlah_murid": 415,
        "alamat": "Jl. Bunga Rampai No. 9, Depok, Jawa Barat",
        "dapur_sppg": "SPPG Depok Sejahtera — Jl. Gizi No. 2",
        "kepala_sekolah": "Budi Santoso",
        "kontak": "083200003333",
    },
    "512803": {
        "npsn": "20623456",
        "nama": "SMA Negeri 07 Tunas Bangsa",
        "jenjang": "SMA",
        "jumlah_murid": 1120,
        "alamat": "Jl. Kemerdekaan No. 33, Bogor Utara, Kota Bogor",
        "dapur_sppg": "SPPG Bogor Raya — Jl. Nutrisi No. 5",
        "kepala_sekolah": "Dewi Anggraini",
        "kontak": "084300004444",
    },
    "403917": {
        "npsn": "20734567",
        "nama": "SMP Islam Terpadu Al-Hikmah",
        "jenjang": "SMP",
        "jumlah_murid": 520,
        "alamat": "Jl. Al-Hidayah No. 12, Cilandak, Jakarta Selatan",
        "dapur_sppg": "SPPG Jakarta Selatan — Jl. Sehat No. 1",
        "kepala_sekolah": "Ahmad Fauzi",
        "kontak": "085400005555",
    },
    "618204": {
        "npsn": "20845678",
        "nama": "SD Negeri 11 Ceria",
        "jenjang": "SD",
        "jumlah_murid": 350,
        "alamat": "Jl. Melati No. 5, Serpong, Tangerang Selatan",
        "dapur_sppg": "SPPG Serpong Hijau — Jl. Pangan No. 8",
        "kepala_sekolah": "Lina Kusuma",
        "kontak": "086500006666",
    },
    "724508": {
        "npsn": "20956789",
        "nama": "SMA Muhammadiyah 4 Sejahtera",
        "jenjang": "SMA",
        "jumlah_murid": 780,
        "alamat": "Jl. KH. Ahmad Dahlan No. 22, Surabaya, Jawa Timur",
        "dapur_sppg": "SPPG Surabaya Barat — Jl. Gizi Raya No. 14",
        "kepala_sekolah": "Hendra Wijaya",
        "kontak": "087600007777",
    },
    "835612": {
        "npsn": "21067890",
        "nama": "SMP Negeri 8 Cemerlang",
        "jenjang": "SMP",
        "jumlah_murid": 590,
        "alamat": "Jl. Diponegoro No. 44, Yogyakarta",
        "dapur_sppg": "SPPG Yogyakarta Tengah — Jl. Padi No. 3",
        "kepala_sekolah": "Retno Wulandari",
        "kontak": "088700008888",
    },
    "946301": {
        "npsn": "21178901",
        "nama": "SD Islam Plus Bintang Timur",
        "jenjang": "SD",
        "jumlah_murid": 280,
        "alamat": "Jl. Surya Kencana No. 7, Bandung, Jawa Barat",
        "dapur_sppg": "SPPG Bandung Selatan — Jl. Nutrisi No. 9",
        "kepala_sekolah": "Fahmi Hidayat",
        "kontak": "089800009999",
    },
    "157489": {
        "npsn": "21289012",
        "nama": "SMA Negeri 2 Maju Bersama",
        "jenjang": "SMA",
        "jumlah_murid": 960,
        "alamat": "Jl. Sudirman No. 88, Semarang, Jawa Tengah",
        "dapur_sppg": "SPPG Semarang Utara — Jl. Logistik Gizi No. 6",
        "kepala_sekolah": "Sri Wahyuni",
        "kontak": "081200010000",
    },
}

# ─── HELPERS ──────────────────────────────────────────────────────────────────
def generate_history(kode_sekolah, days=14):
    random.seed(int(kode_sekolah) % 999)
    records = []
    for i in range(days):
        date = datetime.now() - timedelta(days=days - i)
        is_weekday = date.weekday() < 5
        submitted = is_weekday and random.choice([True, True, True, True, False])
        if submitted:
            components = {
                "makanan_pokok": random.choice(["Ada", "Ada", "Tidak Ada"]),
                "lauk_protein":  random.choice(["Ada", "Ada", "Tidak Ada"]),
                "sayur":         random.choice(["Ada", "Ada", "Tidak Ada"]),
                "buah":          random.choice(["Ada", "Ada", "Tidak Ada"]),
                "susu":          random.choice(["Ada", "Tidak Ada"]),
            }
            score = sum(s == "Ada" for s in components.values()) * 20
            category = "Baik" if score >= 80 else "Cukup" if score >= 60 else "Kurang"
        else:
            components = {key: "-" for key in ("makanan_pokok", "lauk_protein", "sayur", "buah", "susu")}
            score = None
            category = "-"
        records.append({
            "tanggal":       date.strftime("%Y-%m-%d"),
            "hari":          date.strftime("%A"),
            "wajib_lapor":   is_weekday,
            "status_laporan": "Sudah Lapor" if submitted else ("Belum Lapor" if is_weekday else "Libur"),
            "skor":          score,
            "kategori":      category,
            **components,
        })
    return pd.DataFrame(records)


def hitung_skor(detected):
    count = sum(cls in detected for cls in FOOD_CLASSES)
    return int((count / len(FOOD_CLASSES)) * 100)


def bbox_area(xyxy):
    """Menghitung luas bounding box format [x1, y1, x2, y2]."""
    x1, y1, x2, y2 = xyxy
    return max(0.0, x2 - x1) * max(0.0, y2 - y1)


def intersection_area(box_a, box_b):
    """Menghitung luas area perpotongan dua bounding box."""
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b
    x1 = max(ax1, bx1)
    y1 = max(ay1, by1)
    x2 = min(ax2, bx2)
    y2 = min(ay2, by2)
    return max(0.0, x2 - x1) * max(0.0, y2 - y1)


def get_portion_status(cls_name, area_pct):
    """Menentukan kelayakan porsi berbasis visual coverage terhadap tray."""
    min_pct = MIN_PORTION_PCT.get(cls_name, 0.0)
    return "Layak" if area_pct >= min_pct else "Kurang"


def load_model():
    if st.session_state.model is None:
        if MODEL_PATH.exists():
            try:
                from ultralytics import YOLO
                model = YOLO(str(MODEL_PATH))
                model_classes = tuple(str(model.names[i]).strip().lower() for i in sorted(model.names))
                missing_classes = [cls for cls in FOOD_CLASSES if cls not in model_classes]
                if missing_classes:
                    raise ValueError(
                        f"Class wajib model tidak lengkap. Hilang: {missing_classes}. "
                        f"Class model saat ini: {model_classes}."
                    )
                st.session_state.model = model
                return model
            except Exception as e:
                st.error(f"Model YOLO gagal dimuat: {e}")
                return None
        st.error(f"File model tidak ditemukan: {MODEL_PATH}")
    return st.session_state.model


def detect_food(image_pil):
    model = load_model()
    if model is None:
        return {}, None

    temp_path = None

    try:
        img_w, img_h = image_pil.size

        # Disamakan dengan cara prediksi di Colab:
        # Colab memanggil model.predict(source="path_gambar", imgsz=640, conf=0.25, iou=0.6).
        # Jadi di Streamlit, gambar upload disimpan sementara ke file path dulu.
        # Ini mengurangi perbedaan hasil antara inference lokal app dan inference di Colab.
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            temp_path = tmp.name
            image_pil.save(temp_path, format="JPEG", quality=95)

        results = model.predict(
            source=temp_path,
            imgsz=640,
            conf=DETECTION_CONFIDENCE,
            iou=0.6,
            verbose=False,
        )

        raw_food_items = []
        tray_candidates = []

        for result in results:
            for box in result.boxes:
                cls_id = int(box.cls[0])
                cls_name = str(result.names[cls_id]).strip().lower()
                conf = float(box.conf[0])
                xyxy = [float(v) for v in box.xyxy[0].detach().cpu().tolist()]

                # Opsional untuk versi berikutnya: jika model sudah dilatih dengan class tray/nampan,
                # app otomatis memakai bbox tray sebagai pembanding porsi.
                if cls_name in TRAY_CLASSES:
                    tray_candidates.append({
                        "conf": conf,
                        "bbox": xyxy,
                        "area": bbox_area(xyxy),
                    })
                    continue

                if cls_name not in FOOD_CLASSES:
                    continue

                raw_food_items.append({
                    "class": cls_name,
                    "conf": conf,
                    "bbox": xyxy,
                })

        # Jika belum ada class tray/nampan di model, tray diasumsikan sebagai seluruh foto.
        # Agar estimasi porsi lebih konsisten, ambil foto dengan nampan memenuhi frame.
        if tray_candidates:
            tray = max(tray_candidates, key=lambda item: item["area"])
            tray_bbox = tray["bbox"]
            tray_source = "model"
        else:
            tray_bbox = [0.0, 0.0, float(img_w), float(img_h)]
            tray_source = "full_image"

        tray_area = bbox_area(tray_bbox)

        grouped = {cls: [] for cls in FOOD_CLASSES}
        for item in raw_food_items:
            cls_name = item["class"]
            visible_area = intersection_area(item["bbox"], tray_bbox)
            area_pct = (visible_area / tray_area) * 100 if tray_area else 0

            grouped[cls_name].append({
                "conf": item["conf"],
                "bbox": item["bbox"],
                "area": visible_area,
                "area_pct": area_pct,
            })

        detected = {}
        for cls_name, items in grouped.items():
            if not items:
                continue

            items = sorted(items, key=lambda x: x["conf"], reverse=True)
            total_area = sum(item["area"] for item in items)
            total_area_pct = (total_area / tray_area) * 100 if tray_area else 0
            max_conf = items[0]["conf"]
            portion_status = get_portion_status(cls_name, total_area_pct)

            detected[cls_name] = {
                "items": items,
                "count": len(items),
                "conf": max_conf,  # kompatibel dengan kode lama
                "max_conf": max_conf,
                "total_area": total_area,
                "total_area_pct": total_area_pct,
                "min_area_pct": MIN_PORTION_PCT.get(cls_name, 0.0),
                "portion_status": portion_status,
                "tray_bbox": tray_bbox,
                "tray_area": tray_area,
                "tray_source": tray_source,
            }

        annotated = results[0].plot() if len(results) > 0 else None
        # Ultralytics plot() returns BGR, while Streamlit expects RGB.
        # This only fixes the displayed color and does not change detection results.
        if annotated is not None:
            annotated = annotated[..., ::-1]
        return detected, annotated

    except Exception as e:
        st.error(f"Deteksi gagal: {e}")
        return {}, None

    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


# ─── SESSION STATE ────────────────────────────────────────────────────────────
for key, default in [
    ("page", "login"),
    ("kode_sekolah", None),
    ("sekolah", None),
    ("detection_result", None),
    ("llm_recommendation", None),
    ("llm_context", None),
    ("report_sent", False),
    ("sent_reports", []),
    ("model", None),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ─── GLOBAL CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=DM+Mono:wght@400;500&display=swap');

:root {
    --blue-50:   #EFF6FF;
    --blue-100:  #DBEAFE;
    --blue-200:  #BFDBFE;
    --blue-400:  #60A5FA;
    --blue-500:  #3B82F6;
    --blue-600:  #2563EB;
    --blue-700:  #1D4ED8;
    --blue-900:  #1E3A5F;
    --sky-400:   #38BDF8;
    --sky-500:   #0EA5E9;
    --green-500: #22C55E;
    --green-50:  #F0FDF4;
    --green-800: #166534;
    --amber-400: #FBBF24;
    --amber-50:  #FFFBEB;
    --amber-800: #92400E;
    --red-400:   #F87171;
    --red-50:    #FEF2F2;
    --red-800:   #991B1B;
    --gray-50:   #F8FAFC;
    --gray-100:  #F1F5F9;
    --gray-200:  #E2E8F0;
    --gray-400:  #94A3B8;
    --gray-500:  #64748B;
    --gray-600:  #475569;
    --gray-700:  #334155;
    --gray-800:  #1E293B;
    --white:     #FFFFFF;
}

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
}

.stApp {
    background: #F0F5FF !important;
    min-height: 100vh;
}

/* hide streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.block-container {
    padding: 0 2.25rem 3rem 2.25rem !important;
    max-width: none !important;
    width: 100% !important;
}

/* ── TOPBAR ── */
.topbar {
    background: var(--white);
    border-bottom: 1px solid var(--blue-100);
    padding: 0 32px;
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: sticky;
    top: 0;
    z-index: 999;
    margin-bottom: 32px;
}
.topbar-brand {
    font-size: 1.25rem;
    font-weight: 800;
    color: var(--blue-700);
    letter-spacing: -0.5px;
}
.topbar-brand span { color: var(--sky-500); }
.topbar-date {
    font-size: 0.78rem;
    color: var(--gray-400);
    font-family: 'DM Mono', monospace;
    font-weight: 500;
}

/* ── LOGIN PAGE ── */
.login-page {
    min-height: calc(100vh - 100px);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 40px 16px;
}
.login-logo-area {
    text-align: center;
    margin-bottom: 32px;
}
.login-title {
    font-size: 3rem;
    font-weight: 800;
    color: var(--blue-700);
    letter-spacing: -2px;
    line-height: 1;
    margin-bottom: 8px;
}
.login-title span { color: var(--sky-500); }
.login-subtitle {
    font-size: 1rem;
    color: var(--gray-500);
    line-height: 1.6;
    max-width: 400px;
    margin: 0 auto;
}
.login-card {
    background: var(--white);
    border: 1px solid var(--blue-100);
    border-radius: 20px;
    padding: 36px 40px;
    box-shadow: 0 8px 48px rgba(37,99,235,0.08);
    width: 100%;
    max-width: 420px;
}
.login-card-label {
    font-size: 0.8rem;
    font-weight: 700;
    color: var(--gray-500);
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin-bottom: 8px;
}

/* ── SCHOOL PROFILE SECTION ── */
.school-header {
    background: linear-gradient(135deg, #1D4ED8 0%, #0EA5E9 100%);
    border-radius: 16px;
    padding: 28px 32px;
    color: white;
    margin-bottom: 32px;
}
.sh-tag {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(255,255,255,0.15);
    border-radius: 6px;
    padding: 4px 10px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.3px;
    margin-bottom: 12px;
}
.sh-name {
    font-size: 1.65rem;
    font-weight: 800;
    letter-spacing: -0.8px;
    line-height: 1.1;
    margin-bottom: 6px;
}
.sh-npsn {
    font-size: 0.78rem;
    opacity: 0.65;
    font-family: 'DM Mono', monospace;
    margin-bottom: 20px;
}
.sh-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px 24px;
    margin-top: 4px;
}
.sh-item-label {
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    opacity: 0.6;
    margin-bottom: 2px;
}
.sh-item-value {
    font-size: 0.88rem;
    font-weight: 500;
    opacity: 0.92;
    line-height: 1.4;
}

/* ── SECTION HEADINGS ── */
.section-wrap {
    background: var(--white);
    border: 1px solid var(--blue-100);
    border-radius: 16px;
    padding: 28px 32px;
    margin-bottom: 24px;
    box-shadow: 0 2px 16px rgba(37,99,235,0.04);
}
.section-heading {
    font-size: 1rem;
    font-weight: 700;
    color: var(--blue-900);
    letter-spacing: -0.2px;
    margin-bottom: 20px;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--blue-50);
}
.section-heading span {
    display: inline-block;
    width: 4px;
    height: 16px;
    background: var(--blue-500);
    border-radius: 2px;
    margin-right: 10px;
    vertical-align: middle;
    position: relative;
    top: -1px;
}

/* ── METRIC CARDS ── */
.metrics-row {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 14px;
    margin-bottom: 24px;
}
.metric-card {
    background: var(--white);
    border: 1px solid var(--blue-100);
    border-radius: 14px;
    padding: 20px 22px;
    box-shadow: 0 2px 12px rgba(37,99,235,0.04);
}
.metric-card-label {
    font-size: 0.72rem;
    color: var(--gray-400);
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 6px;
}
.metric-card-value {
    font-size: 1.75rem;
    font-weight: 800;
    color: var(--blue-900);
    letter-spacing: -1px;
    line-height: 1;
    margin-bottom: 4px;
}
.metric-card-sub {
    font-size: 0.75rem;
    color: var(--gray-400);
    font-weight: 500;
}

/* ── TABLE ── */
.stDataFrame {
    border-radius: 12px !important;
    overflow: hidden;
    border: 1px solid var(--blue-100) !important;
    background: #FFFFFF !important;
}
.stDataFrame [data-testid="stDataFrameResizable"] {
    background: #FFFFFF !important;
}
.stDataFrame canvas {
    background: #FFFFFF !important;
}

.history-table-wrap {
    width: 100%;
    overflow-x: auto;
    border: 1px solid #DBEAFE;
    border-radius: 12px;
    background: #FFFFFF;
}
.history-table {
    width: 100%;
    min-width: 1120px;
    border-collapse: collapse;
    background: #FFFFFF;
    color: #1E293B;
    font-size: 0.79rem;
}
.history-table th {
    background: #EFF6FF;
    color: #1E3A5F;
    font-weight: 800;
    text-align: left;
    white-space: nowrap;
    padding: 13px 14px;
    border-bottom: 1px solid #BFDBFE;
}
.history-table td {
    background: #FFFFFF;
    color: #334155;
    font-weight: 500;
    white-space: nowrap;
    padding: 12px 14px;
    border-bottom: 1px solid #E2E8F0;
}
.history-table tbody tr:nth-child(even) td { background: #F8FAFC; }
.history-table tbody tr:hover td { background: #EFF6FF; }
.history-table tbody tr:last-child td { border-bottom: none; }
.status-lapor { color:#166534; background:#DCFCE7; border-radius:6px; padding:3px 8px; font-weight:700; }
.status-belum { color:#991B1B; background:#FEE2E2; border-radius:6px; padding:3px 8px; font-weight:700; }
.status-libur { color:#475569; background:#E2E8F0; border-radius:6px; padding:3px 8px; font-weight:700; }

@media (max-width: 768px) {
    .block-container {
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    .sh-grid {
        grid-template-columns: 1fr;
    }
}

/* ── DETECTION ITEMS ── */
.det-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 16px;
    border-radius: 10px;
    margin-bottom: 8px;
    font-size: 0.88rem;
    font-weight: 500;
}
.det-found   { background: var(--green-50); color: var(--green-800); border: 1px solid #BBF7D0; }
.det-missing { background: var(--red-50);   color: var(--red-800);   border: 1px solid #FECACA; }
.det-badge {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.2px;
}

/* ── SCORE DISPLAY ── */
.score-block {
    background: var(--gray-50);
    border: 1px solid var(--blue-100);
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 20px;
}
.score-number {
    font-size: 3.5rem;
    font-weight: 800;
    letter-spacing: -2px;
    line-height: 1;
}
.score-good   { color: var(--green-500); }
.score-cukup  { color: var(--amber-400); }
.score-kurang { color: var(--red-400); }
.score-label {
    font-size: 0.78rem;
    font-weight: 700;
    color: var(--gray-400);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 4px;
}
.score-desc {
    font-size: 0.9rem;
    font-weight: 600;
    color: var(--gray-700);
}

/* ── REPORT BOX ── */
.report-block {
    background: #FFFFFF;
    border: 1px solid var(--blue-100);
    border-radius: 12px;
    padding: 28px 30px;
    font-size: 0.84rem;
    color: var(--gray-800);
    line-height: 1.5;
}
.report-title {
    color: #1E3A5F;
    font-size: 1rem;
    font-weight: 800;
    padding-bottom: 14px;
    margin-bottom: 18px;
    border-bottom: 1px solid #DBEAFE;
}
.report-section-title {
    color: #1D4ED8;
    font-size: 0.75rem;
    font-weight: 800;
    letter-spacing: 0.7px;
    margin: 20px 0 10px;
}
.report-grid {
    display: grid;
    grid-template-columns: minmax(130px, 170px) 1fr;
    gap: 7px 16px;
}
.report-label { color: #64748B; font-weight: 700; }
.report-value { color: #1E293B; font-weight: 600; }
.report-component {
    display: grid;
    grid-template-columns: minmax(160px, 220px) 1fr;
    gap: 14px;
    padding: 9px 0;
    border-bottom: 1px solid #F1F5F9;
}
.report-component:last-child { border-bottom: none; }
.report-component-name { color: #334155; font-weight: 700; }
.report-found { color: #166534; font-weight: 700; }
.report-warning { color: #92400E; font-weight: 700; }
.report-missing { color: #B91C1C; font-weight: 700; }
.report-summary {
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 14px 16px;
    margin-top: 18px;
}
.report-footer {
    color: #64748B;
    font-size: 0.76rem;
    margin-top: 22px;
    padding-top: 14px;
    border-top: 1px solid #DBEAFE;
}

/* ── CATEGORY PILL ── */
.pill-baik   { display:inline-block; background:#DCFCE7; color:#166534; border-radius:6px; padding:2px 10px; font-size:0.72rem; font-weight:700; }
.pill-cukup  { display:inline-block; background:#FEF9C3; color:#92400E; border-radius:6px; padding:2px 10px; font-size:0.72rem; font-weight:700; }
.pill-kurang { display:inline-block; background:#FEF2F2; color:#991B1B; border-radius:6px; padding:2px 10px; font-size:0.72rem; font-weight:700; }

/* ── DIVIDER ── */
.section-divider {
    height: 1px;
    background: var(--blue-100);
    margin: 32px 0;
    border: none;
}

/* ── INPUT ── */
.stTextInput > div > div > input {
    border: 2px solid var(--blue-200) !important;
    border-radius: 12px !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 1rem !important;
    padding: 12px 16px !important;
    background: white !important;
    color: var(--blue-900) !important;
    transition: border-color 0.2s !important;
    -webkit-text-fill-color: #1E3A5F !important;
    caret-color: #2563EB !important;
}
.stTextInput > div > div > input::placeholder {
    color: #64748B !important;
    -webkit-text-fill-color: #64748B !important;
    opacity: 1 !important;
    font-weight: 500 !important;
}
.stTextInput [data-testid="InputInstructions"] {
    color: #64748B !important;
    font-weight: 600 !important;
}
.stTextInput [data-baseweb="input"] {
    background: #FFFFFF !important;
}
.stTextInput > div > div > input:focus {
    border-color: var(--blue-500) !important;
    box-shadow: 0 0 0 3px rgba(59,130,246,0.12) !important;
    outline: none !important;
}

/* ── BUTTON ── */
.stButton > button {
    background: linear-gradient(135deg, #2563EB, #0EA5E9) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    padding: 12px 24px !important;
    transition: all 0.2s !important;
    box-shadow: 0 4px 14px rgba(37,99,235,0.22) !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(37,99,235,0.32) !important;
}
.stButton > button[kind="secondary"] {
    background: var(--white) !important;
    color: var(--blue-600) !important;
    border: 2px solid var(--blue-200) !important;
    box-shadow: none !important;
}

/* ── FILE UPLOADER ── */
.stFileUploader,
.stFileUploader > div,
.stFileUploader [data-testid="stFileUploaderDropzone"] {
    background: #FFFFFF !important;
    color: #1E3A5F !important;
}
.stFileUploader [data-testid="stFileUploaderDropzone"] {
    border: 1px dashed #93C5FD !important;
    border-radius: 12px !important;
    padding: 22px !important;
}
.stFileUploader label,
.stFileUploader p,
.stFileUploader span,
.stFileUploader small,
.stFileUploader div {
    color: #334155 !important;
    -webkit-text-fill-color: #334155 !important;
}
.stFileUploader button {
    background: #EFF6FF !important;
    color: #1D4ED8 !important;
    border: 1px solid #BFDBFE !important;
    font-weight: 700 !important;
}

/* ── SPINNER ── */
[data-testid="stSpinner"] {
    background: #EFF6FF !important;
    border: 1px solid #93C5FD !important;
    border-radius: 10px !important;
    padding: 12px 14px !important;
}
[data-testid="stSpinner"] p,
[data-testid="stSpinner"] div,
[data-testid="stSpinner"] span {
    color: #1D4ED8 !important;
    -webkit-text-fill-color: #1D4ED8 !important;
    font-weight: 800 !important;
}
[data-testid="stSpinner"] svg {
    fill: #2563EB !important;
    color: #2563EB !important;
}

/* ── ALERTS ── */
[data-testid="stAlert"], .stSuccess, .stError, .stWarning, .stInfo {
    border-radius: 12px !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    color: #1E293B !important;
}
[data-testid="stAlert"] p,
[data-testid="stAlert"] div,
[data-testid="stAlert"] span {
    color: #1E293B !important;
    font-weight: 600 !important;
}
[data-testid="stAlert"][data-baseweb="notification"] {
    background: #FFFFFF !important;
}
[data-testid="stException"] {
    background: #FFF1F2 !important;
    border: 2px solid #FF1F3D !important;
    border-radius: 12px !important;
}
[data-testid="stException"],
[data-testid="stException"] p,
[data-testid="stException"] div,
[data-testid="stException"] span,
[data-testid="stException"] code,
[data-testid="stException"] pre {
    color: #D90024 !important;
    -webkit-text-fill-color: #D90024 !important;
    font-weight: 700 !important;
}

/* page section scroll anchor label */
.page-anchor {
    font-size: 0.72rem;
    font-weight: 700;
    color: var(--gray-400);
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 12px;
}


/* ── PRODUCT UX REFINEMENT ── */
.dashboard-shell {
    max-width: 1480px;
    margin: 0 auto;
}
.school-header {
    box-shadow: 0 18px 48px rgba(37, 99, 235, 0.14) !important;
    border: 1px solid rgba(255,255,255,0.24) !important;
    margin-bottom: 18px !important;
}
[data-baseweb="tab-list"] {
    gap: 8px !important;
    border-bottom: 1px solid #CBDCFB !important;
    margin: 4px 0 22px 0 !important;
}
[data-baseweb="tab"] {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    color: #64748B !important;
    font-weight: 800 !important;
    font-size: 0.95rem !important;
    padding: 12px 22px !important;
    border-radius: 12px 12px 0 0 !important;
}
[data-baseweb="tab"][aria-selected="true"] {
    color: #1D4ED8 !important;
    background: #FFFFFF !important;
    border: 1px solid #DBEAFE !important;
    border-bottom: 1px solid #FFFFFF !important;
}
[data-baseweb="tab-highlight"] {
    background: #2563EB !important;
    height: 3px !important;
    border-radius: 999px !important;
}
.report-hero {
    background: linear-gradient(135deg, #FFFFFF 0%, #F8FBFF 100%);
    border: 1px solid #DBEAFE;
    border-radius: 20px;
    padding: 22px 24px;
    box-shadow: 0 10px 34px rgba(37,99,235,0.07);
    margin-bottom: 20px;
}
.report-hero-title {
    font-size: 1.16rem;
    font-weight: 900;
    color: #1E3A5F;
    letter-spacing: -0.4px;
    margin-bottom: 5px;
}
.report-hero-sub {
    font-size: 0.82rem;
    color: #64748B;
    line-height: 1.65;
}
.status-strip {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    margin-top: 18px;
}
.status-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 14px;
    padding: 15px 16px;
}
.status-label {
    font-size: 0.67rem;
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: 0.7px;
    color: #94A3B8;
    margin-bottom: 6px;
}
.status-value {
    font-size: 1.2rem;
    font-weight: 900;
    color: #1E3A5F;
    letter-spacing: -0.4px;
}
.status-sub {
    font-size: 0.72rem;
    font-weight: 650;
    color: #64748B;
    margin-top: 3px;
}
.work-card {
    background: #FFFFFF;
    border: 1px solid #DBEAFE;
    border-radius: 18px;
    padding: 22px 24px;
    box-shadow: 0 4px 20px rgba(37,99,235,0.055);
    margin-bottom: 18px;
}
.work-card-title {
    font-size: 0.96rem;
    font-weight: 900;
    color: #1E3A5F;
    margin-bottom: 4px;
}
.work-card-desc {
    font-size: 0.78rem;
    color: #64748B;
    line-height: 1.6;
    margin-bottom: 16px;
}
.component-grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 10px;
    margin: 14px 0 4px;
}
.component-card {
    border-radius: 14px;
    border: 1px solid #E2E8F0;
    background: #FFFFFF;
    padding: 14px 14px;
    min-height: 116px;
}
.component-card.good { background: #F0FDF4; border-color: #BBF7D0; }
.component-card.warn { background: #FFFBEB; border-color: #FDE68A; }
.component-card.bad { background: #FEF2F2; border-color: #FECACA; }
.component-name {
    font-size: 0.8rem;
    font-weight: 900;
    color: #1E293B;
    margin-bottom: 8px;
}
.component-status {
    display: inline-block;
    border-radius: 999px;
    padding: 4px 9px;
    font-size: 0.66rem;
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: 0.35px;
    margin-bottom: 10px;
}
.component-status.good { color: #166534; background: #DCFCE7; }
.component-status.warn { color: #92400E; background: #FEF3C7; }
.component-status.bad { color: #991B1B; background: #FEE2E2; }
.component-meta {
    font-size: 0.72rem;
    color: #64748B;
    line-height: 1.55;
    font-weight: 650;
}
.ai-card {
    background: linear-gradient(135deg, #F8FAFF 0%, #EEF6FF 100%);
    border: 1px solid #BFD7FF;
    border-radius: 18px;
    padding: 22px 24px;
    box-shadow: 0 8px 28px rgba(14,165,233,0.09);
    margin-bottom: 18px;
}
.ai-kicker {
    display: inline-flex;
    gap: 6px;
    align-items: center;
    color: #1D4ED8;
    background: #DBEAFE;
    border-radius: 999px;
    font-size: 0.68rem;
    font-weight: 900;
    padding: 5px 10px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 10px;
}
.ai-title {
    font-size: 1rem;
    font-weight: 900;
    color: #1E3A5F;
    margin-bottom: 8px;
}
.ai-text {
    font-size: 0.86rem;
    color: #334155;
    line-height: 1.75;
    font-weight: 560;
}
.ai-output {
    margin-top: 14px;
    background: #FFFFFF;
    border: 1px solid #DBEAFE;
    border-radius: 15px;
    padding: 18px 20px;
    color: #334155;
    line-height: 1.72;
    font-size: 0.88rem;
    box-shadow: 0 5px 18px rgba(37,99,235,0.05);
}
.ai-output p { margin: 0 0 10px 0; }
.ai-output ul { margin: 6px 0 12px 22px; padding: 0; }
.ai-output li { margin-bottom: 6px; }
.ai-output strong { color: #1D4ED8; font-weight: 900; }
.ai-output .ai-heading {
    color: #1E3A5F;
    font-weight: 900;
    font-size: 0.9rem;
    margin: 12px 0 6px 0;
}
.action-card {
    background: #0F172A;
    color: white;
    border-radius: 18px;
    padding: 20px 22px;
    margin-bottom: 18px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 18px;
}
.action-title {
    font-size: 0.98rem;
    font-weight: 900;
    color: #FFFFFF;
    margin-bottom: 4px;
}
.action-desc {
    font-size: 0.76rem;
    color: #CBD5E1;
    line-height: 1.6;
}
.soft-note {
    background: #F8FAFC;
    border: 1px dashed #CBD5E1;
    border-radius: 14px;
    padding: 16px 18px;
    color: #64748B;
    font-size: 0.82rem;
    line-height: 1.65;
}
@media (max-width: 980px) {
    .status-strip { grid-template-columns: repeat(2, 1fr); }
    .component-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 640px) {
    .status-strip { grid-template-columns: 1fr; }
    .component-grid { grid-template-columns: 1fr; }
    .action-card { flex-direction: column; align-items: stretch; }
}

</style>
""", unsafe_allow_html=True)


# ─── TOP BAR ─────────────────────────────────────────────────────────────────
def render_topbar(show_back=False):
    now = datetime.now()
    bulan_id = ["","Jan","Feb","Mar","Apr","Mei","Jun","Jul","Ags","Sep","Okt","Nov","Des"]
    date_str = f"{now.day} {bulan_id[now.month]} {now.year}, {now.strftime('%H:%M')}"

    if show_back:
        col_b, col_date = st.columns([1, 5])
        with col_b:
            if st.button("← Ganti Sekolah", key="back_btn"):
                st.session_state.page = "login"
                st.session_state.kode_sekolah = None
                st.session_state.sekolah = None
                st.session_state.detection_result = None
                st.session_state.llm_recommendation = None
                st.session_state.llm_context = None
                st.session_state.report_sent = False
                st.rerun()
        with col_date:
            st.markdown(f"""
            <div style="text-align:right;padding:14px 0 0 0;font-size:0.78rem;color:#64748B;
                font-family:'DM Mono',monospace;font-weight:600;">{date_str} WIB</div>
            """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="padding:14px 0 0 0;font-size:0.78rem;color:#64748B;
            font-family:'DM Mono',monospace;font-weight:600;">{date_str} WIB</div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:1px;background:#DBEAFE;margin:8px 0 28px 0;'></div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: LOGIN
# ══════════════════════════════════════════════════════════════════════════════
def page_login():
    render_topbar(show_back=False)

    _, col_c, _ = st.columns([1, 2.2, 1])
    with col_c:
        st.markdown("<div style='height:clamp(100px, 17vh, 190px);'></div>", unsafe_allow_html=True)
        # Logo & title
        st.markdown("""
        <div style="text-align:center; margin-bottom:28px;">
            <div style="font-size:0.75rem;font-weight:700;color:#94A3B8;letter-spacing:1.5px;
                text-transform:uppercase;margin-bottom:14px;">Program Makan Bergizi Gratis</div>
            <div style="font-size:3.2rem;font-weight:800;color:#1D4ED8;letter-spacing:-2px;line-height:1;">
                Nutri<span style="color:#0EA5E9;">port</span>
            </div>
            <div style="font-size:0.95rem;color:#64748B;margin-top:10px;line-height:1.65;max-width:340px;
                margin-left:auto;margin-right:auto;">
                Platform monitoring kualitas menu MBG berbasis AI untuk sekolah di seluruh Indonesia
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="text-align:center;font-size:0.8rem;font-weight:700;color:#475569;text-transform:uppercase;
            letter-spacing:0.8px;margin-bottom:8px;">Akses Dashboard Sekolah</div>
        <div style="text-align:center;font-size:0.8rem;color:#64748B;margin-bottom:14px;">
            Gunakan kode sekolah yang telah diberikan.
        </div>
        """, unsafe_allow_html=True)

        kode_input = st.text_input(
            "Kode Sekolah",
            placeholder="Masukkan kode sekolah",
            label_visibility="collapsed",
            max_chars=10,
        )

        if st.button("Masuk ke Dashboard", use_container_width=True, key="login_btn"):
            kode = kode_input.strip()
            if kode in SCHOOLS:
                st.session_state.kode_sekolah = kode
                st.session_state.sekolah = SCHOOLS[kode]
                st.session_state.page = "dashboard"
                st.rerun()
            else:
                st.error("Kode sekolah tidak ditemukan. Silakan periksa kembali.")



# ══════════════════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD (single-scroll, no tabs)
# ══════════════════════════════════════════════════════════════════════════════
# ─── DASHBOARD UI HELPERS ────────────────────────────────────────────────────
def score_category(skor):
    if skor >= 80:
        return "Baik"
    if skor >= 60:
        return "Cukup"
    return "Kurang"


def score_css_class(skor):
    if skor >= 80:
        return "score-good"
    if skor >= 60:
        return "score-cukup"
    return "score-kurang"


def get_menu_eligibility(detected, skor):
    missing = [key for key in FOOD_CLASSES if key not in detected]
    low_portion = [key for key in FOOD_CLASSES if key in detected and detected[key]["portion_status"] == "Kurang"]
    core_missing = any(key in missing for key in ("makanan_pokok", "lauk"))

    if skor == 100 and not low_portion:
        return "Layak", "Semua komponen utama terdeteksi dan estimasi porsi visual memenuhi ambang awal."
    if core_missing or skor < 60:
        return "Tidak Layak", "Komponen utama belum lengkap sehingga laporan perlu diverifikasi sebelum dikirim."
    return "Perlu Perbaikan", "Menu dapat dilaporkan dengan catatan karena ada komponen yang tidak terdeteksi atau estimasi porsi kurang."


def build_ai_recommendation(detected, skor):
    missing = [CATEGORIES_INFO[k] for k in FOOD_CLASSES if k not in detected]
    low_portion = [CATEGORIES_INFO[k] for k in FOOD_CLASSES if k in detected and detected[k]["portion_status"] == "Kurang"]
    status, status_note = get_menu_eligibility(detected, skor)

    if not detected:
        return "Upload dan analisis foto menu terlebih dahulu agar sistem dapat membuat rekomendasi otomatis."

    if not missing and not low_portion:
        return (
            "Menu hari ini sudah memenuhi lima komponen utama MBG. Makanan pokok, lauk/protein, sayur, buah, dan susu "
            "terdeteksi dengan estimasi porsi visual yang layak. Laporan dapat dikirim, namun operator tetap disarankan "
            "memastikan foto diambil dari atas dan seluruh komponen terlihat jelas agar monitoring tetap konsisten."
        )

    parts = []
    if missing:
        parts.append(f"Komponen yang belum terdeteksi: {', '.join(missing)}.")
    if low_portion:
        parts.append(f"Komponen dengan estimasi porsi visual kurang: {', '.join(low_portion)}.")

    followup = (
        "SPPG disarankan melakukan verifikasi menu sebelum laporan dikirim. Jika komponen sebenarnya tersedia tetapi tidak terlihat, "
        "unggah ulang foto dari sudut atas dengan pencahayaan yang lebih jelas. Jika hasil sudah sesuai kondisi aktual, laporan dapat "
        "dikirim dengan catatan evaluasi."
    )
    return f"Status menu: {status}. {status_note} " + " ".join(parts) + " " + followup




def get_secret_or_env(name, default=None):
    """Ambil secret dari Streamlit secrets, lalu fallback ke environment variable."""
    try:
        value = st.secrets.get(name, None)
        if value:
            return value
    except Exception:
        pass
    return os.getenv(name, default)


def build_llm_context(detected, skor, sekolah, kode):
    """Menyusun data ringkas hasil deteksi untuk dikirim ke LLM."""
    components = []

    for key, label in CATEGORIES_INFO.items():
        if key in detected:
            info = detected[key]
            components.append({
                "komponen": label,
                "status": "terdeteksi",
                "jumlah_item": int(info.get("count", 1)),
                "confidence_tertinggi_persen": round(float(info.get("max_conf", info.get("conf", 0))) * 100, 1),
                "estimasi_porsi_visual_persen": round(float(info.get("total_area_pct", 0)), 1),
                "ambang_minimum_porsi_persen": round(float(info.get("min_area_pct", 0)), 1),
                "status_porsi": info.get("portion_status", "Tidak diketahui"),
            })
        else:
            components.append({
                "komponen": label,
                "status": "tidak_terdeteksi",
                "jumlah_item": 0,
                "confidence_tertinggi_persen": 0,
                "estimasi_porsi_visual_persen": 0,
                "ambang_minimum_porsi_persen": round(float(MIN_PORTION_PCT.get(key, 0)), 1),
                "status_porsi": "Tidak Ada",
            })

    missing_components = [
        item["komponen"] for item in components
        if item["status"] == "tidak_terdeteksi"
    ]
    kurang_porsi = [
        item["komponen"] for item in components
        if item["status"] == "terdeteksi" and item["status_porsi"] == "Kurang"
    ]

    overall_status, overall_note = get_menu_eligibility(detected, skor)

    return {
        "nama_sekolah": sekolah["nama"],
        "kode_sekolah": kode,
        "jenjang": sekolah["jenjang"],
        "dapur_sppg": sekolah["dapur_sppg"],
        "tanggal_laporan": datetime.now().strftime("%Y-%m-%d %H:%M WIB"),
        "skor_kelengkapan": int(skor),
        "status_keseluruhan": overall_status,
        "catatan_status": overall_note,
        "komponen_tidak_terdeteksi": missing_components,
        "komponen_porsi_kurang": kurang_porsi,
        "komponen": components,
        "catatan_metode": (
            "Estimasi porsi bersifat visual berdasarkan luas bounding box makanan terhadap area foto/tray. "
            "Sistem tidak menghitung berat, kalori, volume, atau kandungan gizi aktual."
        ),
    }


def generate_rule_based_recommendation(context):
    """Fallback rekomendasi tanpa API agar demo tetap jalan."""
    missing = context.get("komponen_tidak_terdeteksi", [])
    kurang = context.get("komponen_porsi_kurang", [])
    skor = context.get("skor_kelengkapan", 0)
    status = context.get("status_keseluruhan", "Belum diketahui")

    if not missing and not kurang:
        return (
            f"**Ringkasan**\n\n"
            f"Menu hari ini memperoleh skor **{skor}/100** dan berstatus **{status}**. "
            "Seluruh komponen utama MBG terdeteksi dan estimasi porsi visual berada pada kategori layak.\n\n"
            "**Hal yang Perlu Diperhatikan**\n\n"
            "- Tidak ada komponen utama yang hilang dari hasil deteksi.\n"
            "- Estimasi porsi visual sudah memenuhi ambang awal sistem.\n"
            "- Pastikan foto laporan tetap diambil dari sudut atas agar monitoring konsisten.\n\n"
            "**Rekomendasi untuk SPPG/Sekolah**\n\n"
            "- Laporan dapat dikirim.\n"
            "- Pertahankan komposisi menu dan konsistensi penyajian.\n"
            "- Simpan dokumentasi foto sebagai bukti laporan harian.\n\n"
            "**Status Laporan**\n\n"
            "Siap dikirim"
        )

    attention = []
    if missing:
        attention.append(f"Komponen yang tidak terdeteksi: {', '.join(missing)}.")
    if kurang:
        attention.append(f"Komponen dengan estimasi porsi visual kurang: {', '.join(kurang)}.")

    status_laporan = "Perlu verifikasi" if status != "Tidak Layak" else "Perlu perbaikan sebelum dikirim"

    return (
        f"**Ringkasan**\n\n"
        f"Menu hari ini memperoleh skor **{skor}/100** dan berstatus **{status}**. "
        + " ".join(attention)
        + "\n\n**Hal yang Perlu Diperhatikan**\n\n"
        + (f"- {attention[0]}\n" if len(attention) > 0 else "")
        + (f"- {attention[1]}\n" if len(attention) > 1 else "")
        + "- Jika komponen sebenarnya tersedia tetapi tidak terlihat, operator perlu mengunggah ulang foto dengan posisi komponen lebih jelas.\n\n"
        "**Rekomendasi untuk SPPG/Sekolah**\n\n"
        "- Verifikasi kembali komponen yang tidak terdeteksi atau porsinya kurang.\n"
        "- Pastikan seluruh komponen menu terlihat dalam satu foto dari sudut atas.\n"
        "- Jika hasil deteksi sudah sesuai kondisi aktual, gunakan catatan ini sebagai bahan evaluasi SPPG.\n\n"
        "**Status Laporan**\n\n"
        f"{status_laporan}"
    )


def generate_llm_recommendation(context):
    """Generate rekomendasi dengan Groq. Jika API tidak tersedia, pakai fallback rule-based."""
    api_key = get_secret_or_env("GROQ_API_KEY")
    model_name = get_secret_or_env("GROQ_MODEL", "llama-3.3-70b-versatile")

    if not api_key:
        return generate_rule_based_recommendation(context)

    try:
        from groq import Groq

        client = Groq(api_key=api_key)

        system_prompt = """
Kamu adalah analis monitoring Program Makan Bergizi Gratis (MBG).
Tugasmu membuat rekomendasi singkat, jelas, dan profesional berdasarkan hasil deteksi AI.

Aturan penting:
- Jangan mengklaim kandungan gizi, kalori, berat gram, volume, atau standar medis.
- Jangan menyebut hasil ini sebagai pengukuran gizi akurat.
- Tekankan bahwa estimasi porsi bersifat visual.
- Gunakan bahasa Indonesia.
- Tone semi-formal, jelas, praktis, dan cocok untuk operator sekolah/SPPG.
- Fokus pada keputusan: apakah laporan siap dikirim, apa yang perlu diverifikasi, dan apa catatan untuk SPPG.
- Jangan terlalu panjang.
""".strip()

        user_prompt = f"""
Berikut hasil deteksi menu MBG dalam format JSON:

{json.dumps(context, ensure_ascii=False, indent=2)}

Buat rekomendasi dengan format berikut:

**Ringkasan**
1 paragraf singkat tentang kondisi menu hari ini.

**Hal yang Perlu Diperhatikan**
- Maksimal 3 poin.
- Sebut komponen hilang atau porsi kurang jika ada.

**Rekomendasi untuk SPPG/Sekolah**
- Maksimal 3 poin tindakan.

**Status Laporan**
Tulis salah satu:
- Siap dikirim
- Perlu verifikasi
- Perlu perbaikan sebelum dikirim
""".strip()

        chat_completion = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            max_completion_tokens=650,
            top_p=1,
            stream=False,
        )

        return chat_completion.choices[0].message.content.strip()

    except Exception as e:
        fallback = generate_rule_based_recommendation(context)
        return fallback + f"\n\n**Catatan Sistem**\n\nRekomendasi AI eksternal belum dapat dimuat, sehingga sistem memakai rekomendasi fallback. Detail error: {e}"


def markdown_to_simple_html(text):
    """Konversi markdown sederhana dari LLM ke HTML aman untuk ditaruh di card."""
    if not text:
        return ""

    lines = text.splitlines()
    html_parts = []
    in_list = False

    def inline_format(value):
        escaped = html.escape(value)
        return re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", escaped)

    for raw_line in lines:
        line = raw_line.strip()

        if not line:
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            continue

        # Heading markdown sederhana: **Ringkasan**
        if line.startswith("**") and line.endswith("**") and line.count("**") == 2:
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            heading = line.replace("**", "")
            html_parts.append(f'<div class="ai-heading">{html.escape(heading)}</div>')
            continue

        if line.startswith("- "):
            if not in_list:
                html_parts.append("<ul>")
                in_list = True
            html_parts.append(f"<li>{inline_format(line[2:])}</li>")
            continue

        if in_list:
            html_parts.append("</ul>")
            in_list = False
        html_parts.append(f"<p>{inline_format(line)}</p>")

    if in_list:
        html_parts.append("</ul>")

    return "".join(html_parts)

def render_school_profile(sekolah, kode):
    st.markdown('<div class="page-anchor">Profil Sekolah</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="school-header">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:12px;">
            <div style="flex:1;min-width:260px;">
                <div class="sh-tag">
                    <span style="width:7px;height:7px;border-radius:50%;background:rgba(255,255,255,0.86);display:inline-block;"></span>
                    {html.escape(sekolah['jenjang'])} · Aktif MBG
                </div>
                <div class="sh-name">{html.escape(sekolah['nama'])}</div>
                <div class="sh-npsn">NPSN {html.escape(sekolah['npsn'])} &nbsp;·&nbsp; Kode {html.escape(kode)}</div>
            </div>
            <div style="text-align:right;opacity:0.68;font-size:0.72rem;font-family:'DM Mono',monospace;font-weight:700;">
                Nutriport MBG Monitor
            </div>
        </div>
        <div class="sh-grid" style="margin-top:20px;">
            <div>
                <div class="sh-item-label">Jumlah Siswa</div>
                <div class="sh-item-value">{sekolah['jumlah_murid']:,} Siswa</div>
            </div>
            <div>
                <div class="sh-item-label">Kepala Sekolah</div>
                <div class="sh-item-value">{html.escape(sekolah['kepala_sekolah'])}</div>
            </div>
            <div>
                <div class="sh-item-label">Alamat</div>
                <div class="sh-item-value">{html.escape(sekolah['alamat'])}</div>
            </div>
            <div>
                <div class="sh-item-label">Dapur SPPG</div>
                <div class="sh-item-value">{html.escape(sekolah['dapur_sppg'])}</div>
            </div>
            <div>
                <div class="sh-item-label">Kontak</div>
                <div class="sh-item-value">{html.escape(sekolah['kontak'])}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_status_strip(res):
    if res:
        detected = res["detected"]
        skor = res["skor"]
        n_found = len(detected)
        missing = len(FOOD_CLASSES) - n_found
        status, _ = get_menu_eligibility(detected, skor)
        low_count = sum(1 for k in FOOD_CLASSES if k in detected and detected[k]["portion_status"] == "Kurang")
        score_text = f"{skor}/100"
        component_text = f"{n_found}/{len(FOOD_CLASSES)}"
        report_status = "Siap Dikirim" if status == "Layak" else "Perlu Review"
        issue_text = f"{missing} hilang · {low_count} porsi kurang" if (missing or low_count) else "Tidak ada catatan utama"
    else:
        score_text = "-"
        component_text = "-"
        status = "Belum Dianalisis"
        report_status = "Belum Dibuat"
        issue_text = "Upload foto untuk mulai laporan"

    st.markdown(f"""
    <div class="report-hero">
        <div style="display:flex;justify-content:space-between;gap:20px;align-items:flex-start;flex-wrap:wrap;">
            <div>
                <div class="report-hero-title">Laporan MBG Hari Ini</div>
                <div class="report-hero-sub">Upload foto nampan, review hasil deteksi, lalu kirim laporan harian ke dashboard monitoring.</div>
            </div>
            <div style="font-size:0.74rem;font-family:'DM Mono',monospace;color:#64748B;font-weight:700;">
                {datetime.now().strftime('%Y-%m-%d %H:%M')} WIB
            </div>
        </div>
        <div class="status-strip">
            <div class="status-card">
                <div class="status-label">Status Laporan</div>
                <div class="status-value">{report_status}</div>
                <div class="status-sub">{status}</div>
            </div>
            <div class="status-card">
                <div class="status-label">Skor AI</div>
                <div class="status-value">{score_text}</div>
                <div class="status-sub">kelengkapan komponen</div>
            </div>
            <div class="status-card">
                <div class="status-label">Komponen</div>
                <div class="status-value">{component_text}</div>
                <div class="status-sub">terdeteksi dari 5 komponen</div>
            </div>
            <div class="status-card">
                <div class="status-label">Catatan</div>
                <div class="status-value" style="font-size:0.96rem;line-height:1.25;">{issue_text}</div>
                <div class="status-sub">berbasis deteksi visual</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_component_cards(detected):
    """Render component cards without indented multiline HTML.
    Streamlit can interpret indented multiline HTML as a Markdown code block,
    so the HTML is built as compact strings.
    """
    cards = []
    for key, label in CATEGORIES_INFO.items():
        if key in detected:
            info = detected[key]
            portion_status = info["portion_status"]
            if portion_status == "Layak":
                cls = "good"
                status_text = "Layak"
            else:
                cls = "warn"
                status_text = "Porsi Kurang"

            meta = (
                f"{info['count']} item<br>"
                f"Confidence tertinggi {int(info['max_conf'] * 100)}%<br>"
                f"Estimasi porsi {info['total_area_pct']:.1f}%"
            )
        else:
            cls = "bad"
            status_text = "Tidak Ada"
            meta = "Tidak terdeteksi<br>Perlu verifikasi manual<br>-"

        cards.append(
            '<div class="component-card {cls}">'
            '<div class="component-name">{label}</div>'
            '<span class="component-status {cls}">{status}</span>'
            '<div class="component-meta">{meta}</div>'
            '</div>'.format(
                cls=cls,
                label=html.escape(label),
                status=html.escape(status_text),
                meta=meta,
            )
        )

    component_html = '<div class="component-grid">' + ''.join(cards) + '</div>'
    st.markdown(component_html, unsafe_allow_html=True)

def render_detection_list(detected):
    st.markdown("""
    <div style="font-size:0.78rem;font-weight:900;color:#475569;text-transform:uppercase;letter-spacing:0.5px;margin:14px 0 8px 0;">
        Detail Komponen Terdeteksi
    </div>
    """, unsafe_allow_html=True)

    for key, label in CATEGORIES_INFO.items():
        if key in detected:
            info = detected[key]
            count = info["count"]
            conf_pct = int(info["max_conf"] * 100)
            portion_pct = info["total_area_pct"]
            min_pct = info["min_area_pct"]
            portion_status = info["portion_status"]
            status_color = "#166534" if portion_status == "Layak" else "#92400E"
            st.markdown(f"""
            <div class="det-item det-found">
                <span style="font-weight:800;">✓ {html.escape(label)}</span>
                <span class="det-badge">
                    Ada {count} item · {conf_pct}% conf. tertinggi · {portion_pct:.1f}% area ·
                    <span style="color:{status_color};">{portion_status}</span>
                </span>
            </div>
            <div style="font-size:0.72rem;color:#64748B;margin:-4px 0 8px 16px;">
                Ambang porsi minimum awal: {min_pct:.1f}% area foto/tray
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="det-item det-missing">
                <span style="font-weight:800;">✗ {html.escape(label)}</span>
                <span class="det-badge">Tidak Terdeteksi</span>
            </div>
            """, unsafe_allow_html=True)


def build_report_text(sekolah, kode, detected, skor, recommendation):
    now = datetime.now()
    lines = [
        "LAPORAN HARIAN KUALITAS MENU MBG",
        "",
        "-" * 54,
        "",
        "IDENTITAS SEKOLAH",
        f"Nama Sekolah  : {sekolah['nama']}",
        f"Kode Sekolah  : {kode}",
        f"NPSN          : {sekolah['npsn']}",
        f"Jenjang       : {sekolah['jenjang']}",
        f"Jumlah Siswa  : {sekolah['jumlah_murid']} siswa",
        f"Alamat        : {sekolah['alamat']}",
        f"Dapur SPPG    : {sekolah['dapur_sppg']}",
        f"Tanggal       : {now.strftime('%Y-%m-%d')} | {now.strftime('%H:%M')} WIB",
        "",
        "HASIL DETEKSI KOMPONEN MENU",
    ]
    for key, label in CATEGORIES_INFO.items():
        if key in detected:
            info = detected[key]
            lines.append(
                f"+ {label:<20} : {info['count']} item | confidence tertinggi {int(info['max_conf']*100)}% | "
                f"estimasi porsi {info['total_area_pct']:.1f}% | minimum {info['min_area_pct']:.1f}% | {info['portion_status']}"
            )
        else:
            lines.append(f"- {label:<20} : Tidak Terdeteksi")
    status, _ = get_menu_eligibility(detected, skor)
    lines += [
        "",
        f"Komponen Lengkap : {len(detected)} dari {len(FOOD_CLASSES)} komponen",
        f"Skor Kelengkapan : {skor}/100 ({score_category(skor)})",
        f"Status Menu      : {status}",
        "",
        "REKOMENDASI AI",
        recommendation,
        "",
        "-" * 54,
        f"Dibuat oleh Nutriport pada {now.strftime('%Y-%m-%d %H:%M')} WIB",
    ]
    return "\n".join(lines)


def render_report_preview(sekolah, kode, detected, skor, recommendation):
    now = datetime.now()
    status, _ = get_menu_eligibility(detected, skor)
    component_rows = []
    for key, label in CATEGORIES_INFO.items():
        if key in detected:
            info = detected[key]
            result_class = "report-found" if info["portion_status"] == "Layak" else "report-warning"
            result_html = (
                f'<span class="{result_class}">'
                f'{info["count"]} item | confidence tertinggi {int(info["max_conf"]*100)}% | '
                f'estimasi porsi {info["total_area_pct"]:.1f}% | minimum {info["min_area_pct"]:.1f}% | {info["portion_status"]}'
                f'</span>'
            )
        else:
            result_html = '<span class="report-missing">Tidak Terdeteksi</span>'
        component_rows.append(
            f'<div class="report-component"><div class="report-component-name">{html.escape(label)}</div><div>{result_html}</div></div>'
        )

    st.markdown(f"""
    <div class="report-block">
        <div class="report-title">LAPORAN HARIAN KUALITAS MENU MBG</div>
        <div class="report-section-title">IDENTITAS SEKOLAH</div>
        <div class="report-grid">
            <div class="report-label">Nama Sekolah</div><div class="report-value">{html.escape(sekolah['nama'])}</div>
            <div class="report-label">Kode Sekolah</div><div class="report-value">{html.escape(kode)}</div>
            <div class="report-label">NPSN</div><div class="report-value">{html.escape(sekolah['npsn'])}</div>
            <div class="report-label">Jenjang</div><div class="report-value">{html.escape(sekolah['jenjang'])}</div>
            <div class="report-label">Dapur SPPG</div><div class="report-value">{html.escape(sekolah['dapur_sppg'])}</div>
            <div class="report-label">Tanggal</div><div class="report-value">{now.strftime('%Y-%m-%d')} | {now.strftime('%H:%M')} WIB</div>
        </div>
        <div class="report-section-title">HASIL DETEKSI KOMPONEN MENU</div>
        {''.join(component_rows)}
        <div class="report-summary">
            <div class="report-grid">
                <div class="report-label">Komponen Lengkap</div><div class="report-value">{len(detected)} dari {len(FOOD_CLASSES)} komponen</div>
                <div class="report-label">Skor Kelengkapan</div><div class="report-value">{skor}/100 ({score_category(skor)})</div>
                <div class="report-label">Status Menu</div><div class="report-value">{html.escape(status)}</div>
                <div class="report-label">Rekomendasi AI</div><div class="report-value">{html.escape(recommendation)}</div>
            </div>
        </div>
        <div class="report-footer">Laporan siap dikirim melalui sistem Nutriport.</div>
    </div>
    """, unsafe_allow_html=True)


def render_report_tab(sekolah, kode):
    if "report_sent" not in st.session_state:
        st.session_state.report_sent = False
    if "sent_reports" not in st.session_state:
        st.session_state.sent_reports = []

    render_status_strip(st.session_state.detection_result)

    st.markdown('<div class="page-anchor">Upload & Analisis Menu</div>', unsafe_allow_html=True)
    col_up, col_res = st.columns([0.92, 1.08], gap="large")

    with col_up:
        st.markdown("""
        <div class="work-card">
            <div class="work-card-title">1. Upload Foto Menu</div>
            <div class="work-card-desc">Gunakan foto nampan dari atas dengan seluruh komponen terlihat jelas.</div>
        """, unsafe_allow_html=True)

        uploaded = st.file_uploader(
            "Pilih foto nampan makanan",
            type=["jpg", "jpeg", "png"],
            key="food_upload",
            help="Format JPG / PNG. Maks 10MB.",
        )

        if uploaded:
            image = Image.open(uploaded).convert("RGB")
            st.image(image, caption="Foto asli yang diunggah", use_container_width=True)
            if st.button("🔍 Analisis Kelengkapan Menu", use_container_width=True, key="analyze_btn"):
                with st.spinner("Mendeteksi komponen makanan..."):
                    detected, annotated_img = detect_food(image)
                    skor = hitung_skor(detected)
                    st.session_state.detection_result = {
                        "detected": detected,
                        "skor": skor,
                        "annotated": annotated_img,
                        "tanggal": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    }
                    st.session_state.report_sent = False
                    st.session_state.llm_recommendation = None
                    st.session_state.llm_context = None
                st.rerun()
        else:
            st.markdown("""
            <div class="soft-note">Belum ada foto yang dipilih. Setelah foto diunggah, sistem akan menampilkan foto asli dan hasil deteksi AI berdampingan.</div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    with col_res:
        st.markdown("""
        <div class="work-card">
            <div class="work-card-title">2. Review Hasil Deteksi</div>
            <div class="work-card-desc">Cek skor, status kelayakan, dan komponen yang perlu diverifikasi sebelum laporan dikirim.</div>
        """, unsafe_allow_html=True)

        res = st.session_state.detection_result
        if res:
            detected = res["detected"]
            skor = res["skor"]
            sc_class = score_css_class(skor)
            sc_label = score_category(skor)
            status, status_note = get_menu_eligibility(detected, skor)
            st.markdown(f"""
            <div class="score-block">
                <div class="score-number {sc_class}">{skor}</div>
                <div>
                    <div class="score-label">Skor Kelengkapan</div>
                    <div class="score-desc">{len(detected)} dari {len(FOOD_CLASSES)} komponen terdeteksi</div>
                    <div style="margin-top:7px;display:flex;gap:7px;align-items:center;flex-wrap:wrap;">
                        <span class="pill-{'baik' if skor>=80 else 'cukup' if skor>=60 else 'kurang'}">{sc_label}</span>
                        <span class="pill-{'baik' if status=='Layak' else 'cukup' if status=='Perlu Perbaikan' else 'kurang'}">{status}</span>
                    </div>
                    <div style="font-size:0.76rem;color:#64748B;margin-top:8px;line-height:1.55;">{html.escape(status_note)}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if res["annotated"] is not None:
                st.image(res["annotated"], caption="Visualisasi Deteksi AI", use_container_width=True)

            render_detection_list(detected)
        else:
            st.markdown("""
            <div style="background:#F8FAFC;border:2px dashed #BFDBFE;border-radius:14px;padding:56px 24px;text-align:center;color:#94A3B8;">
                <div style="font-size:2.2rem;margin-bottom:8px;">🍱</div>
                <div style="font-size:0.9rem;font-weight:700;color:#64748B;">Hasil deteksi akan muncul di sini</div>
                <div style="font-size:0.78rem;margin-top:4px;">Upload foto dan klik analisis untuk memulai.</div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    res = st.session_state.detection_result
    st.markdown('<div class="page-anchor">Ringkasan Komponen</div>', unsafe_allow_html=True)
    st.markdown('<div class="work-card"><div class="work-card-title">3. Ringkasan Kelayakan Komponen</div><div class="work-card-desc">Ringkasan ini memudahkan operator melihat komponen mana yang sudah layak, kurang, atau tidak terdeteksi.</div>', unsafe_allow_html=True)
    if res:
        render_component_cards(res["detected"])
    else:
        st.markdown('<div class="soft-note">Ringkasan komponen akan aktif setelah foto selesai dianalisis.</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="page-anchor">Rekomendasi AI</div>', unsafe_allow_html=True)
    res = st.session_state.detection_result

    if res:
        context = build_llm_context(
            detected=res["detected"],
            skor=res["skor"],
            sekolah=sekolah,
            kode=kode,
        )
        st.session_state.llm_context = context

        st.markdown("""
        <div class="ai-card">
            <div class="ai-kicker">✨ Rekomendasi AI</div>
            <div class="ai-title">Catatan otomatis untuk operator dan SPPG</div>
            <div class="ai-text">Gunakan fitur ini setelah hasil deteksi selesai. Rekomendasi akan membaca skor, komponen yang hilang, confidence, dan estimasi porsi visual.</div>
        """, unsafe_allow_html=True)

        if st.button("✨ Buat Rekomendasi AI", use_container_width=True, key="generate_llm_btn"):
            with st.spinner("Membuat rekomendasi AI..."):
                st.session_state.llm_recommendation = generate_llm_recommendation(context)

        if st.session_state.llm_recommendation:
            rec_html = markdown_to_simple_html(st.session_state.llm_recommendation)
            st.markdown(f'<div class="ai-output">{rec_html}</div>', unsafe_allow_html=True)
        else:
            st.markdown(
                '<div class="ai-output"><p>Rekomendasi belum dibuat. Klik tombol <strong>Buat Rekomendasi AI</strong> untuk menghasilkan catatan otomatis sebelum laporan dikirim.</p></div>',
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="ai-card">
            <div class="ai-kicker">✨ Rekomendasi AI</div>
            <div class="ai-title">Catatan otomatis akan muncul setelah analisis</div>
            <div class="ai-output"><p>Upload dan analisis foto menu terlebih dahulu agar sistem dapat membuat rekomendasi berbasis hasil deteksi.</p></div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="page-anchor">Kirim Laporan</div>', unsafe_allow_html=True)
    res = st.session_state.detection_result
    recommendation = st.session_state.llm_recommendation

    if res:
        if recommendation:
            report_text = build_report_text(sekolah, kode, res["detected"], res["skor"], recommendation)
            render_report_preview(sekolah, kode, res["detected"], res["skor"], recommendation)
            st.markdown("""
            <div class="action-card">
                <div>
                    <div class="action-title">Laporan sudah siap dikirim</div>
                    <div class="action-desc">Pastikan foto, hasil deteksi, dan rekomendasi AI sudah sesuai. Setelah dikirim, laporan akan ditandai sebagai laporan hari ini.</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("📤 Kirim Laporan Hari Ini", use_container_width=True, key="send_report_btn"):
                st.session_state.report_sent = True
                st.session_state.sent_reports.append({
                    "kode": kode,
                    "tanggal": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "skor": res["skor"],
                    "status": get_menu_eligibility(res["detected"], res["skor"])[0],
                    "rekomendasi_ai": recommendation,
                    "report_text": report_text,
                })
                st.success("Laporan berhasil dikirim ke dashboard monitoring.")
            if st.session_state.report_sent:
                st.info("Status laporan hari ini: sudah terkirim.")
        else:
            st.markdown('<div class="soft-note">Hasil deteksi sudah tersedia, tetapi laporan belum bisa dikirim. Buat rekomendasi AI terlebih dahulu agar laporan memiliki catatan evaluasi.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="soft-note">Laporan belum bisa dikirim karena belum ada hasil deteksi. Upload dan analisis foto menu terlebih dahulu.</div>', unsafe_allow_html=True)


def render_history_tab(kode):
    df = generate_history(kode)
    st.markdown('<div class="page-anchor">Dashboard & Histori</div>', unsafe_allow_html=True)

    weekday_df = df[df["wajib_lapor"]].copy()
    submitted_df = weekday_df[weekday_df["status_laporan"] == "Sudah Lapor"].copy()
    submitted_count = (weekday_df["status_laporan"] == "Sudah Lapor").sum()
    expected_count = len(weekday_df)
    missing_reports = expected_count - submitted_count
    report_rate = (submitted_count / expected_count * 100) if expected_count else 0
    avg_skor = submitted_df["skor"].mean() if not submitted_df.empty else 0
    complete_count = (submitted_df["skor"] == 100).sum()

    avg_cat = score_category(avg_skor)
    cat_color = {"Baik": "#22C55E", "Cukup": "#FBBF24", "Kurang": "#F87171"}

    col1, col2, col3, col4 = st.columns(4, gap="medium")
    with col1:
        st.markdown(f"""
        <div class="metric-card"><div class="metric-card-label">Kepatuhan Laporan Weekday</div>
        <div class="metric-card-value" style="color:#2563EB;">{report_rate:.0f}%</div>
        <div class="metric-card-sub">{submitted_count} dari {expected_count} hari wajib lapor</div></div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card"><div class="metric-card-label">Belum Lapor</div>
        <div class="metric-card-value" style="color:{'#22C55E' if missing_reports == 0 else '#F87171'};">{missing_reports}</div>
        <div class="metric-card-sub">hari kerja terlewat</div></div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card"><div class="metric-card-label">Rata-rata Kelengkapan</div>
        <div class="metric-card-value" style="color:{cat_color[avg_cat]};">{avg_skor:.0f}<span style="font-size:1rem;color:#94A3B8;">/100</span></div>
        <div class="metric-card-sub">Status menu: {avg_cat}</div></div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="metric-card"><div class="metric-card-label">Menu Lengkap</div>
        <div class="metric-card-value" style="color:#22C55E;">{complete_count}</div>
        <div class="metric-card-sub">hari dengan 5 komponen lengkap</div></div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

    st.markdown("""
    <div style="background:white;border:1px solid #DBEAFE;border-radius:16px;padding:24px 28px 16px 28px;box-shadow:0 2px 12px rgba(37,99,235,0.04);margin-bottom:20px;">
        <div style="font-size:0.95rem;font-weight:800;color:#1E3A5F;margin-bottom:2px;">Tren Kepatuhan Laporan Weekday</div>
        <div style="font-size:0.78rem;color:#64748B;margin-bottom:16px;">Hijau berarti laporan masuk, merah berarti belum masuk. Sabtu dan Minggu tidak dihitung.</div>
    """, unsafe_allow_html=True)

    report_values = [1 if status == "Sudah Lapor" else 0 for status in weekday_df["status_laporan"]]
    report_colors = ["#22C55E" if value == 1 else "#F87171" for value in report_values]
    fig = go.Figure(go.Bar(
        x=weekday_df["tanggal"], y=report_values, marker_color=report_colors,
        text=weekday_df["status_laporan"], textposition="outside",
        textfont=dict(size=10, color="#475569")
    ))
    fig.update_layout(
        height=260, margin=dict(l=0, r=0, t=25, b=0), paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)", font=dict(family="Plus Jakarta Sans"),
        xaxis=dict(showgrid=False, tickfont=dict(size=10, color="#94A3B8")),
        yaxis=dict(range=[0, 1.25], showgrid=False, showticklabels=False), showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("""
    <div style="background:white;border:1px solid #DBEAFE;border-radius:16px;padding:24px 28px 16px 28px;box-shadow:0 2px 12px rgba(37,99,235,0.04);margin-bottom:20px;">
        <div style="font-size:0.95rem;font-weight:800;color:#1E3A5F;margin-bottom:2px;">Ketersediaan Komponen Menu</div>
        <div style="font-size:0.78rem;color:#64748B;margin-bottom:16px;">Persentase kemunculan setiap komponen dari laporan yang sudah masuk</div>
    """, unsafe_allow_html=True)

    comp_map = {"makanan_pokok": "Makanan Pokok", "lauk_protein": "Lauk/Protein", "sayur": "Sayur", "buah": "Buah", "susu": "Susu"}
    comp_pct = []
    for col_key in comp_map.keys():
        pct = (submitted_df[col_key] == "Ada").mean() * 100 if not submitted_df.empty and col_key in df.columns else 0
        comp_pct.append(pct)

    colors = ["#3B82F6", "#8B5CF6", "#22C55E", "#F59E0B", "#EC4899"]
    fig2 = go.Figure(go.Bar(
        x=list(comp_map.values()), y=comp_pct, marker_color=colors,
        text=[f"{v:.0f}%" for v in comp_pct], textposition="outside",
        textfont=dict(size=11, family="Plus Jakarta Sans", color="#475569")
    ))
    fig2.update_layout(
        height=240, margin=dict(l=0, r=0, t=20, b=0), paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)", font=dict(family="Plus Jakarta Sans"),
        yaxis=dict(range=[0, 118], showgrid=True, gridcolor="#F1F5F9", tickfont=dict(size=10, color="#94A3B8"), ticksuffix="%"),
        xaxis=dict(showgrid=False, tickfont=dict(size=11, color="#475569")), showlegend=False, bargap=0.38,
    )
    st.plotly_chart(fig2, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("""
    <div style="background:white;border:1px solid #DBEAFE;border-radius:16px;padding:24px 28px;box-shadow:0 2px 12px rgba(37,99,235,0.04);margin-bottom:32px;">
        <div style="font-size:0.95rem;font-weight:800;color:#1E3A5F;margin-bottom:4px;">Riwayat Laporan Harian</div>
        <div style="font-size:0.78rem;color:#64748B;margin-bottom:16px;">Data 14 hari terakhir. Status laporan memudahkan pemantauan hari kerja yang terlewat.</div>
    """, unsafe_allow_html=True)
    display_df = df[["tanggal", "status_laporan", "skor", "kategori", "makanan_pokok", "lauk_protein", "sayur", "buah", "susu"]].copy()
    display_df.columns = ["Tanggal", "Status Laporan", "Skor", "Kategori", "Makanan Pokok", "Lauk/Protein", "Sayur", "Buah", "Susu"]
    display_df["Skor"] = display_df["Skor"].apply(lambda value: "-" if pd.isna(value) else f"{int(value)}/100")
    history_html = display_df.to_html(index=False, classes="history-table", border=0)
    history_html = history_html.replace(">Sudah Lapor<", '><span class="status-lapor">Sudah Lapor</span><')
    history_html = history_html.replace(">Belum Lapor<", '><span class="status-belum">Belum Lapor</span><')
    history_html = history_html.replace(">Libur<", '><span class="status-libur">Libur</span><')
    st.markdown(f'<div class="history-table-wrap">{history_html}</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def page_dashboard():
    render_topbar(show_back=True)
    sekolah = st.session_state.sekolah
    kode = st.session_state.kode_sekolah

    st.markdown('<div class="dashboard-shell">', unsafe_allow_html=True)
    render_school_profile(sekolah, kode)

    tab_laporan, tab_histori = st.tabs(["Laporan", "Histori"])
    with tab_laporan:
        render_report_tab(sekolah, kode)
    with tab_histori:
        render_history_tab(kode)

    st.markdown('</div>', unsafe_allow_html=True)

# ─── ROUTER ───────────────────────────────────────────────────────────────────
if st.session_state.page == "login":
    page_login()
elif st.session_state.page == "dashboard":
    page_dashboard()
