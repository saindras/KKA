import streamlit as st
import os
import google.generativeai as genai

# --- Konfigurasi Halaman Streamlit ---
st.set_page_config(page_title="Asisten Diagnostik TKR", page_icon="🛠️", layout="wide")
st.title("🛠️ Asisten Diagnostik Awal Kendaraan")
st.caption("Didukung oleh KA Generatif (Gemini)")

# --- Konfigurasi API Key & Model Gemini ---
api_key_configured = False
model = None

# --- Fungsi untuk Inisialisasi Model (Dipanggil saat dibutuhkan) ---
def initialize_model():
    global model, api_key_configured
    if model is None and not api_key_configured: # Hanya inisialisasi sekali
        api_key_configured = True # Tandai sudah dicek
        try:
            # Menggunakan GOOGLE_API_KEY
            api_key = os.environ['GOOGLE_API_KEY']
            genai.configure(api_key=api_key)
            # Menggunakan model LLM Gemini
            model = genai.GenerativeModel('models/gemini-2.0-flash-lite')
            st.success("API Key & Model KA berhasil dikonfigurasi.")
            return True # Berhasil
        except KeyError:
            st.error("Error: GOOGLE_API_KEY tidak ditemukan di Replit Secrets.")
            st.info("Pastikan Anda sudah menambahkan GOOGLE_API_KEY ke bagian Secrets di Replit.")
            return False # Gagal
        except Exception as e:
            st.error(f"Error saat mengkonfigurasi atau memuat model KA: {e}")
            return False # Gagal
    elif model is not None:
         return True # Sudah terinisialisasi sebelumnya
    else:
         # Jika api_key_configured True tapi model masih None, berarti gagal sebelumnya
         st.error("Konfigurasi API Key gagal sebelumnya. Periksa Secrets dan refresh halaman.")
         return False

# --- Fungsi untuk Membuat Prompt ---
def buat_prompt(gejala):
    # Prompt yang sama detailnya seperti sebelumnya
    return f"""
    Anda adalah seorang mekanik senior TKR (Teknik Kendaraan Ringan) yang sangat berpengalaman dan sabar dalam menjelaskan kepada siswa SMK.

    Seorang siswa melaporkan gejala kerusakan kendaraan berikut: '{gejala}'
    Tugas Anda:
    1. Analisis gejala tersebut.
    2. Berikan daftar kemungkinan penyebab umum kerusakan tersebut (maksimal 5 penyebab). Urutkan dari yang paling mungkin terjadi.
    3. Untuk setiap kemungkinan penyebab, berikan 1-2 langkah diagnostik awal yang SANGAT SEDERHANA dan AMAN yang bisa diperiksa oleh siswa TKR dengan pengawasan guru (misalnya cek visual, cek level cairan, mendengarkan suara). Hindari langkah yang memerlukan alat khusus atau pembongkaran kompleks di tahap awal ini.
    4. Gunakan bahasa yang teknis namun mudah dipahami oleh siswa SMK TKR. Berikan penjelasan singkat mengapa gejala itu bisa terkait dengan penyebab tersebut.

    Format Jawaban (Gunakan Markdown):
    **Kemungkinan Penyebab:**
    1. **[Nama Penyebab 1]:** [Penjelasan singkat kaitan gejala dengan penyebab].
       * _Langkah Diagnostik Awal:_ [Langkah 1]
       * _Langkah Diagnostik Awal:_ [Langkah 2 (jika ada)]
    2. **[Nama Penyebab 2]:** [Penjelasan singkat kaitan gejala dengan penyebab].
       * _Langkah Diagnostik Awal:_ [Langkah 1]
       * _Langkah Diagnostik Awal:_ [Langkah 2 (jika ada)]
    ... (dan seterusnya, maksimal 5)

    ---
    **Penting:** Ingatkan siswa bahwa ini hanyalah **diagnostik awal**. Pemeriksaan dan perbaikan lebih lanjut harus dilakukan oleh mekanik profesional atau di bawah pengawasan ketat guru praktik di bengkel sekolah.
    """

# --- Interface Pengguna Streamlit ---
st.subheader("Deskripsikan Gejala Kerusakan:")
gejala_input = st.text_area("Contoh: Mesin mobil tidak mau menyala saat distarter, hanya bunyi 'klik'.", height=100)
diagnosa_button = st.button("Mulai Diagnostik Awal", type="primary")

# --- Logika Saat Tombol Ditekan ---
if diagnosa_button:
    model_ready = initialize_model()
    if model_ready: # Hanya lanjut jika model berhasil diinisialisasi
        #validasi input
        if not gejala_input:
            st.warning("Mohon masukkan deskripsi gejala terlebih dahulu.")
        else:
            prompt_final = buat_prompt(gejala_input)
            with st.spinner("🤖 KA sedang menganalisis gejala... Mohon tunggu sebentar..."):
                try:
                    response = model.generate_content(prompt_final)
                    jawaban_ai = response.text
                    st.divider() # Garis pemisah
                    st.subheader("🔬 Hasil Analisis KA:")
                    st.markdown(jawaban_ai) # Gunakan markdown untuk format yang lebih baik
                except Exception as e:
                    st.error(f"Terjadi kesalahan saat menghubungi KA: {e}")
                    st.info("Tips: Coba lagi beberapa saat. Pastikan API Key valid dan tidak melebihi batas penggunaan.")
    else: # Pesan jika model gagal inisialisasi (sudah ditampilkan di dalam fungsi initialize_model)
        pass

# --- Footer ---
st.divider()
st.markdown("Aplikasi TKR Diagnostik Kendaraan | Dibuat dengan Streamlit & Google Gemini")