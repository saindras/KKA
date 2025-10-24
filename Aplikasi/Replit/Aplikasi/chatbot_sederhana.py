import google.generativeai as genai
import os

# Ambil API Key dari Replit Secrets
try:
    api_key = os.environ['GOOGLE_API_KEY']
    genai.configure(api_key=api_key)
except KeyError:
    print("Error: GOOGLE_API_KEY tidak ditemukan di Replit Secrets.")
    print("Pastikan Anda sudah menambahkan GOOGLE_API_KEY ke bagian Secrets.")
    exit() # Keluar jika API Key tidak ada

# Inisialisasi model
# Gunakan nama model yang available
model_name = 'models/gemini-2.0-flash-lite'
print(f"Menginisialisasi model: {model_name}...")
try:
    model = genai.GenerativeModel(model_name)
except Exception as e:
    print(f"\nTerjadi kesalahan saat inisialisasi model: {e}")
    print("Pastikan nama model sudah benar sesuai output list_models().")
    exit()

# Definisikan prompt
prompt_teks = "Jelaskan secara singkat apa itu Internet of Things (IoT) untuk siswa SMK TJKT."

print("Sedang mengirim prompt ke Gemini...")

# Kirim prompt ke model
try:
    response = model.generate_content(prompt_teks)
    # Cetak respons dari KA
    print("\nJawaban dari Gemini:")
    # Periksa apakah ada teks dalam respons
    if response.parts:
         print(response.text)
    else:
         print("Gemini tidak memberikan respons teks.")
except Exception as e:
    print(f"\nTerjadi kesalahan saat mengirim prompt: {e}")
    print("Pastikan API Key sudah benar, koneksi internet stabil, dan model yang dipilih mendukung generate_content.")