# Nutriport — MBG Monitor

Nutriport adalah aplikasi berbasis **Streamlit** untuk membantu monitoring menu **Makan Bergizi Gratis (MBG)** di sekolah. Aplikasi ini menggunakan model **YOLO (`best.pt`)** untuk mendeteksi komponen makanan dari foto nampan, menghitung kelengkapan menu, menampilkan estimasi porsi visual, membuat rekomendasi AI berbasis LLM, dan menyiapkan laporan harian untuk dikirim.

---

## 1. Isi Folder Project

Pastikan struktur folder project seperti ini:

```text
nutriport_interface/
├── app.py
├── best.pt
└── .streamlit/
    └── secrets.toml
```

Keterangan:

| File / Folder | Fungsi |
|---|---|
| `app.py` | File utama aplikasi Streamlit |
| `best.pt` | Model YOLO hasil training untuk deteksi komponen makanan MBG |
| `.streamlit/secrets.toml` | Tempat menyimpan API key Groq untuk fitur rekomendasi AI |

Catatan: Di Windows Explorer, file `app.py` mungkin terlihat hanya sebagai `app` karena ekstensi file disembunyikan.

---

## 2. Fitur Utama

Aplikasi ini memiliki fitur:

1. **Login berdasarkan kode sekolah**
2. **Profil sekolah** berisi nama sekolah, NPSN, jumlah siswa, alamat, dan dapur SPPG
3. **Tab Laporan** untuk workflow harian:
   - Upload foto menu MBG
   - Analisis kelengkapan menu dengan YOLO
   - Deteksi multi-item, misalnya 2 lauk dalam 1 nampan
   - Estimasi porsi visual berdasarkan luas bounding box makanan
   - Rekomendasi AI berbasis Groq LLM
   - Tombol **Kirim Laporan Hari Ini**
4. **Tab Histori** untuk melihat:
   - Kepatuhan laporan
   - Rata-rata kelengkapan menu
   - Grafik tren laporan
   - Riwayat laporan harian

---

## 3. Komponen yang Dideteksi Model

Model `best.pt` mendeteksi 5 kelas:

```text
0 = buah
1 = lauk
2 = makanan_pokok
3 = sayur
4 = susu
```

Penting: Jangan mengganti urutan class ini. `app.py` mengecek class model agar sesuai dengan urutan di atas.

---

## 4. Cara Menjalankan Aplikasi

### A. Buka terminal di folder project

Masuk ke folder project. Contoh di Windows PowerShell:

```powershell
cd "D:\Ko Wancio\nutriport_interface"
```

### B. Buat virtual environment opsional tetapi disarankan

```powershell
python -m venv venv
```

Aktifkan virtual environment:

```powershell
venv\Scripts\activate
```

Kalau memakai Mac/Linux:

```bash
source venv/bin/activate
```

### C. Install dependency

Jalankan:

```bash
pip install streamlit pandas numpy plotly pillow ultralytics groq opencv-python
```

Jika sudah ada file `requirements.txt`, bisa pakai:

```bash
pip install -r requirements.txt
```

### D. Pastikan file model ada

Pastikan `best.pt` ada di folder yang sama dengan `app.py`:

```text
nutriport_interface/
├── app.py
└── best.pt
```

### E. Jalankan aplikasi

```bash
streamlit run app.py
```

Setelah berhasil, Streamlit biasanya membuka browser otomatis. Jika tidak, buka URL yang muncul di terminal, biasanya:

```text
http://localhost:8501
```

---

## 5. Setup Groq API untuk Rekomendasi AI

Fitur rekomendasi AI memakai Groq. Jika API key belum diisi, aplikasi tetap bisa berjalan, tetapi rekomendasi akan menggunakan fallback berbasis rule.

### A. Buat folder `.streamlit`

Di folder project, buat folder:

```text
.streamlit
```

### B. Buat file `secrets.toml`

Di dalam folder `.streamlit`, buat file:

```text
secrets.toml
```

Isi file:

```toml
GROQ_API_KEY = "ISI_API_KEY_GROQ_DI_SINI"
GROQ_MODEL = "llama-3.3-70b-versatile"
```

Model alternatif yang bisa dicoba:

```toml
GROQ_MODEL = "openai/gpt-oss-120b"
```

atau model yang lebih ringan:

```toml
GROQ_MODEL = "llama-3.1-8b-instant"
```

Jangan upload API key ke repository publik.

---

## 6. Alur Penggunaan Aplikasi

1. Jalankan aplikasi dengan `streamlit run app.py`
2. Masukkan kode sekolah
3. Masuk ke dashboard sekolah
4. Buka tab **Laporan**
5. Upload foto nampan MBG
6. Klik **Analisis Kelengkapan Menu**
7. Review hasil deteksi:
   - Komponen terdeteksi
   - Jumlah item
   - Confidence
   - Estimasi porsi visual
   - Status layak atau kurang
8. Klik **Buat Rekomendasi AI**
9. Setelah rekomendasi muncul, klik **Kirim Laporan Hari Ini**
10. Cek tab **Histori** untuk melihat monitoring dan riwayat laporan

---

## 7. Contoh Kode Sekolah untuk Login

Beberapa kode sekolah yang tersedia di aplikasi:

```text
367401
384201
291005
512803
403917
618204
724508
835612
946301
157489
```

Contoh:

```text
384201
```

---

## 8. Catatan Penting Tentang Estimasi Porsi

Estimasi porsi di aplikasi ini adalah **estimasi visual**, bukan pengukuran berat atau kandungan gizi aktual.

Saat ini sistem menghitung porsi berdasarkan:

```text
luas bounding box makanan / luas area foto
```

Artinya hasilnya digunakan sebagai indikator awal untuk monitoring visual, bukan sebagai pengganti analisis gizi, gramasi, kalori, atau standar medis.

---

## 9. Cara Mengganti Model YOLO

Jika ada model baru hasil training:

1. Download model baru dari Colab/Kaggle
2. Rename file menjadi:

```text
best.pt
```

3. Ganti file `best.pt` lama di folder project
4. Stop aplikasi Streamlit dengan `CTRL + C`
5. Jalankan ulang:

```bash
streamlit run app.py
```

Jika aplikasi masih memakai model lama, restart Streamlit dan refresh browser dengan `CTRL + F5`.

---

## 10. Troubleshooting

### Error: `ModuleNotFoundError: No module named 'streamlit'`

Install Streamlit:

```bash
pip install streamlit
```

### Error: `ModuleNotFoundError: No module named 'ultralytics'`

Install Ultralytics:

```bash
pip install ultralytics
```

### Error: `File model tidak ditemukan: best.pt`

Pastikan `best.pt` berada di folder yang sama dengan `app.py`.

### Error class model tidak sesuai

Pastikan model YOLO memiliki class berikut dengan urutan yang sama:

```text
buah, lauk, makanan_pokok, sayur, susu
```

### Rekomendasi AI tidak muncul

Cek hal berikut:

1. Package Groq sudah terinstall:

```bash
pip install groq
```

2. File `.streamlit/secrets.toml` sudah ada
3. API key benar
4. Model Groq valid, misalnya:

```toml
GROQ_MODEL = "llama-3.3-70b-versatile"
```

### Aplikasi tidak update setelah mengganti file

Stop Streamlit dulu:

```bash
CTRL + C
```

Lalu jalankan ulang:

```bash
streamlit run app.py
```

---

## 11. Dependency yang Dibutuhkan

Minimal dependency:

```text
streamlit
pandas
numpy
plotly
pillow
ultralytics
groq
opencv-python
```

---

## 12. Status Project Saat Ini

Yang sudah berjalan:

- Deteksi 5 komponen MBG
- Deteksi multi-item per komponen
- Estimasi porsi visual
- UI tab Laporan dan Histori
- Rekomendasi AI dengan Groq
- Fallback rekomendasi jika API key belum tersedia
- Tombol Kirim Laporan Hari Ini

Pengembangan berikutnya yang bisa dilakukan:

- Simpan laporan ke database atau Google Sheets
- Export laporan PDF
- Dashboard admin/SPPG
- Manual correction jika AI salah mendeteksi
- Deteksi bounding box nampan/tray agar estimasi porsi lebih akurat

---

## 13. Ringkasan Singkat untuk Teman Tim

Untuk menjalankan aplikasi:

```bash
pip install streamlit pandas numpy plotly pillow ultralytics groq opencv-python
streamlit run app.py
```

Pastikan file berikut ada:

```text
app.py
best.pt
.streamlit/secrets.toml
```

Gunakan salah satu kode sekolah, misalnya:

```text
384201
```

Lalu upload foto menu MBG di tab **Laporan**.
