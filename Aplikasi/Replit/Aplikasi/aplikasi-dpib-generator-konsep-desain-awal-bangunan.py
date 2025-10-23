import streamlit as st
import os
import google.generativeai as genai

# --- Konfigurasi Halaman Streamlit ---
st.set_page_config(page_title="Generator Konsep Desain DPIB", page_icon="🏛️", layout="wide")
st.title("🏛️ Generator Konsep Desain Awal Bangunan")
st.caption("Didukung oleh KA Generatif (Gemini)")

# --- Konfigurasi API Key & Model Gemini ---
api_key_configured = False
model = None

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

# Konfigurasi library genai jika API Key ditemukan
if api_key_configured:
    try:
        # Menggunakan nama model 'gemini-pro-latest'
        model = genai.GenerativeModel('models/gemini-pro-latest')
        st.info("Model Generative KA ('gemini-pro-latest') siap digunakan.")
    except Exception as e:
        st.error(f"Error saat mengkonfigurasi atau memuat model KA: {e}")
        st.stop()

# --- Fungsi untuk Membuat Prompt Konsep Desain ---
def buat_prompt_konsep(gaya, fungsi, lantai):
    # Prompt spesifik untuk konsep desain awal
    return f"""
    Anda adalah seorang asisten arsitek kreatif yang membantu siswa SMK DPIB memvisualisasikan ide desain awal dalam bentuk narasi singkat. Anda bertugas sebagai teman brainstorming.

    Parameter Desain yang diberikan Siswa:
    - Gaya Arsitektur: '{gaya}'
    - Fungsi Bangunan: '{fungsi}'
    - Jumlah Lantai: {lantai}

    Tugas Anda:
    Buatlah sebuah **deskripsi naratif singkat (sekitar 2-3 paragraf)** mengenai konsep desain awal yang sesuai dengan parameter tersebut. Deskripsi harus membangkitkan imajinasi dan mencakup ide-ide awal tentang:

    1.  **Keseluruhan Tampilan & Nuansa:** Bagaimana kesan pertama bangunan tersebut?
    2.  **Tata Ruang (Ide Umum):** Bagaimana kemungkinan penataan ruang utama secara garis besar? Apakah terbuka, tertutup, fungsional?
    3.  **Bentuk Atap (Saran):** Sebutkan satu atau dua ide bentuk atap yang cocok dengan gaya tersebut (misal: atap datar, pelana, limasan, miring sebelah).
    4.  **Material Dominan (Saran):** Sebutkan satu atau dua material utama yang mungkin menonjol sesuai gaya dan fungsi (misal: beton ekspos, kayu, kaca, bata).
    5.  Gunakan bahasa yang deskriptif dan inspiratif, namun tetap relevan dengan parameter yang diberikan.

    Format Jawaban (Gunakan Markdown):

    ### Konsep Desain Awal

    **Gaya:** {gaya} | **Fungsi:** {fungsi} | **Lantai:** {lantai}

    [Paragraf 1: Deskripsi tampilan umum dan nuansa bangunan sesuai gaya]

    [Paragraf 2: Ide tentang tata ruang utama dan saran bentuk atap yang sesuai]

    [Paragraf 3: Saran material dominan yang mendukung konsep dan gaya]

    ---
    **Ingat:** Ini hanyalah **konsep awal** untuk inspirasi. Desain detail memerlukan analisis tapak, kebutuhan pengguna yang lebih spesifik, perhitungan struktur, dan pertimbangan lainnya.
    """

# --- Interface Pengguna Streamlit ---
st.subheader("Masukkan Parameter Desain:")

# Input Kolom Berdampingan
col1, col2, col3 = st.columns(3)
with col1:
    gaya_input = st.text_input("Gaya Arsitektur", placeholder="Minimalis, Tropis Modern, Industrial")
with col2:
    fungsi_input = st.text_input("Fungsi Bangunan", placeholder="Rumah Tinggal, Ruko 2 Lantai, Cafe")
with col3:
    lantai_input = st.number_input("Jumlah Lantai", min_value=1, step=1, format="%d", value=1) # Default 1 lantai

buat_konsep_button = st.button("Buat Konsep Desain Awal", type="primary")

# --- Logika Saat Tombol Ditekan ---
if buat_konsep_button:
    model_ready = initialize_model()
    # Validasi input
    if not gaya_input:
        st.warning("Mohon masukkan Gaya Arsitektur.")
    elif not fungsi_input:
        st.warning("Mohon masukkan Fungsi Bangunan.")
    elif lantai_input < 1:
        st.warning("Jumlah lantai minimal 1.")
    else:
        # Buat prompt jika input valid
        prompt_final_konsep = buat_prompt_konsep(gaya_input, fungsi_input, lantai_input)

        with st.spinner("✨ KA sedang merancang konsep... Menunggu inspirasi..."):
            try:
                # Kirim ke Gemini
                response = model.generate_content(prompt_final_konsep)

                # Cek safety
                if response.parts:
                    jawaban_ai_konsep = response.text
                else:
                    try:
                        safety_feedback = response.prompt_feedback
                        jawaban_ai_konsep = f"**Permintaan diblokir karena alasan keamanan.**\n\nDetail:\n{safety_feedback}"
                    except Exception:
                         jawaban_ai_konsep = "**Permintaan diblokir karena alasan keamanan.** Tidak ada detail tambahan tersedia."
                         st.warning("Respons AI mungkin diblokir karena kebijakan keamanan.")

                # Tampilkan hasil
                st.divider() # Garis pemisah
                st.subheader("💡 Konsep Desain Awal:")
                st.markdown(jawaban_ai_konsep) # Gunakan markdown

            except Exception as e:
                # Tangani error
                st.error(f"Terjadi kesalahan saat menghubungi KA: {e}")
                st.info("Tips: Coba lagi beberapa saat. Pastikan API Key valid dan parameter desain cukup jelas.")

# --- Footer ---
st.divider()
st.markdown("Aplikasi DPIB Konsep Desain | Dibuat dengan Streamlit & Google Gemini")