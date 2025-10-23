import streamlit as st
import os
import google.generativeai as genai

# --- Konfigurasi Halaman Streamlit ---
st.set_page_config(page_title="Generator Perawatan Berkala TKR", page_icon="⚙️", layout="wide")
st.title("⚙️ Generator Prosedur Perawatan Berkala")
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

# --- Fungsi untuk Membuat Prompt Perawatan ---
def buat_prompt_perawatan(jenis_kendaraan, kilometer):
    # Prompt spesifik untuk rekomendasi perawatan
    return f"""
    Anda adalah seorang instruktur TKR (Teknik Kendaraan Ringan) senior yang ahli dalam jadwal perawatan berkala berbagai jenis kendaraan umum di Indonesia. Anda bertugas memberikan panduan kepada siswa SMK TKR.

    Informasi Kendaraan:
    - Jenis Kendaraan: '{jenis_kendaraan}'
    - Kilometer Tempuh Saat Ini: {kilometer} km

    Tugas Anda:
    1. Berdasarkan jenis kendaraan dan kilometer tempuh, buatlah daftar rekomendasi item perawatan berkala yang UMUMNYA perlu dilakukan SEGERA atau pada interval servis BERIKUTNYA (misalnya, jika KM 18.000, fokus pada item servis 20.000 km).
    2. Berikan maksimal 7 item perawatan yang paling relevan untuk kondisi tersebut.
    3. Untuk setiap item perawatan, berikan penjelasan singkat (1-2 kalimat) mengapa perawatan tersebut penting dilakukan pada kilometer tersebut.
    4. Gunakan bahasa yang jelas, teknis secukupnya, dan mudah dipahami oleh siswa SMK TKR.
    5. Gunakan **general best practices** (praktik umum terbaik) karena Anda tidak memiliki data spesifik pabrikan. Sebutkan batasan ini.

    Format Jawaban (Gunakan Markdown):
    **Rekomendasi Perawatan Berkala untuk {jenis_kendaraan} ({kilometer} km):**

    Berikut adalah beberapa item perawatan umum yang disarankan berdasarkan kilometer tempuh Anda (berdasarkan praktik umum, bukan jadwal pabrikan spesifik):

    1.  **[Nama Item Perawatan 1]:** [Penjelasan singkat pentingnya item ini].
    2.  **[Nama Item Perawatan 2]:** [Penjelasan singkat pentingnya item ini].
    ... (dan seterusnya, maksimal 7)

    ---
    **Catatan Penting:**
    * Ini adalah rekomendasi **umum**. Jadwal perawatan **resmi dari pabrikan** kendaraan Anda adalah panduan yang paling akurat dan harus selalu diikuti.
    * Kondisi penggunaan kendaraan (sering macet, medan berat, dll.) dapat mempengaruhi jadwal perawatan. Konsultasikan dengan guru praktik atau mekanik terpercaya.
    """

# --- Interface Pengguna Streamlit ---
st.subheader("Masukkan Detail Kendaraan:")

# Input Kolom Berdampingan
col1, col2 = st.columns(2)
with col1:
    jenis_kendaraan_input = st.text_input("Jenis Kendaraan (misal: Motor Matic Honda Beat, Mobil MPV Toyota Avanza)")
with col2:
    # Pastikan input kilometer valid
    kilometer_input = st.number_input("Kilometer Tempuh Saat Ini (Angka)", min_value=0, step=1000, format="%d")

buat_rekomendasi_button = st.button("Buat Rekomendasi Perawatan", type="primary")

# --- Logika Saat Tombol Ditekan ---
if buat_rekomendasi_button:
	model_ready = initialize_model()
    # Validasi input
    if not jenis_kendaraan_input:
        st.warning("Mohon masukkan jenis kendaraan terlebih dahulu.")
    elif kilometer_input <= 0: # Kilometer harus lebih dari 0 untuk relevan
        st.warning("Mohon masukkan kilometer tempuh yang valid (lebih dari 0).")
    else:
        # Buat prompt jika input valid
        prompt_final_perawatan = buat_prompt_perawatan(jenis_kendaraan_input, kilometer_input)

        with st.spinner("🤖 KA sedang menyusun rekomendasi perawatan... Mohon tunggu..."):
            try:
                # Kirim ke Gemini
                response = model.generate_content(prompt_final_perawatan)
                jawaban_ai_perawatan = response.text

                # Tampilkan hasil
                st.divider() # Garis pemisah
                st.subheader("🔧 Rekomendasi Perawatan Berkala:")
                st.markdown(jawaban_ai_perawatan) # Gunakan markdown

            except Exception as e:
                # Tangani error
                st.error(f"Terjadi kesalahan saat menghubungi KA: {e}")
                st.info("Tips: Coba lagi beberapa saat. Pastikan API Key valid dan koneksi internet stabil.")

# --- Footer (Opsional) ---
st.divider()
st.markdown("Aplikasi TKR Generator Perawatan | Dibuat dengan Streamlit & Google Gemini")