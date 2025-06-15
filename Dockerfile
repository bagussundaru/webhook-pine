# Gunakan base image Python resmi yang ringan
FROM python:3.9-slim

# Atur direktori kerja di dalam kontainer
WORKDIR /app

# Salin file requirements dan instal dependensi
# Ini memanfaatkan caching Docker agar tidak menginstal ulang setiap kali kode berubah
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Salin sisa kode aplikasi ke direktori kerja
COPY . .

# Beritahu Docker port mana yang akan diekspos oleh aplikasi
EXPOSE 8080

# Perintah untuk menjalankan aplikasi menggunakan Gunicorn saat kontainer dimulai
# -w 4: Menjalankan 4 worker process (angka yang baik untuk memulai)
# --bind 0.0.0.0:8080: Mengikat ke semua alamat IP pada port 8080
# app:app : Memberitahu Gunicorn untuk mencari objek bernama 'app' di dalam file 'app.py'
CMD ["gunicorn", "-w", "4", "--bind", "0.0.0.0:8080", "app:app"]
