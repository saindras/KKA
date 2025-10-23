import streamlit as st
import os
import google.generativeai as genai

# --- Konfigurasi Halaman Streamlit ---
st.set_page_config(page_title="Penjelas Istilah Jaringan TJKT", page_icon="🌐", layout="wide")
st.title("🌐 Penjelas Istilah Jaringan & Telekomunikasi")
st.caption("Didukung oleh KA Generatif (Gemini)")

# --- Konfigurasi API Key & Model Gemini ---
api_key_checked = False
model = None

# --- Fungsi untuk Inisialisasi Model (Dipanggil saat dibutuhkan) ---
def initialize_model():
    global model, api_key_checked
    if model is None and not api_key_checked: # Hanya inisialisasi sekali
        api_key_checked = True # Tandai sudah dicek
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
         # Jika api_key_checked True tapi model masih None, berarti gagal sebelumnya
         st.error("Konfigurasi API Key gagal sebelumnya. Periksa Secrets dan refresh halaman.")
         return False

# --- Fungsi untuk Membuat Prompt Penjelasan Istilah ---
def buat_prompt_istilah(istilah):
    # Prompt spesifik untuk menjelaskan istilah jaringan
    return f"""
    Anda adalah seorang tutor ahli jaringan komputer dan telekomunikasi (TJKT) yang sangat pandai menyederhanakan konsep kompleks untuk siswa SMK. Gunakan bahasa yang mudah dipahami, hindari jargon berlebihan kecuali jika dijelaskan, dan fokus pada pemahaman konseptual.

    Seorang siswa SMK TJKT bertanya tentang istilah/konsep berikut: '{istilah}'

    Tugas Anda:
    Jelaskan istilah/konsep '{istilah}' tersebut dengan cara berikut:

    1.  **Definisi Singkat:** Berikan definisi dasar (1-2 kalimat) tentang apa itu '{istilah}'.
    2.  **Analogi Sederhana:** Buatlah sebuah analogi yang mudah dipahami (misalnya, membandingkan dengan pengiriman surat, lalu lintas jalan raya, nomor telepon) untuk menjelaskan cara kerja atau fungsi utama dari '{istilah}'. Analogi ini **wajib** ada dan harus relevan.
    3.  **Penjelasan Cara Kerja (Jika Relevan):** Jika memungkinkan dan relevan (terutama untuk protokol atau proses), jelaskan secara singkat langkah-langkah utama cara kerjanya (gunakan poin-poin atau urutan sederhana). Jika tidak relevan (misalnya untuk perangkat keras), lewati bagian ini atau jelaskan fungsi utamanya.
    4.  **Pentingnya/Kegunaan:** Jelaskan mengapa '{istilah}' ini penting dalam dunia jaringan atau telekomunikasi (1-2 kalimat).

    Format Jawaban (Gunakan Markdown):

    ### Penjelasan: {istilah}

    **1. Definisi Singkat:**
    [Definisi dasar 1-2 kalimat]

    **2. Analogi Sederhana:**
    Bayangkan seperti ini: [Analogi sederhana yang relevan dan mudah dipahami]

    **3. Cara Kerja / Fungsi Utama:**
    (Jika Relevan)
    * [Langkah/Fungsi 1]
    * [Langkah/Fungsi 2]
    * [dst.]
    (Jika Tidak Relevan)
    [Jelaskan fungsi utama secara singkat]

    **4. Mengapa Ini Penting?**
    [Penjelasan singkat kegunaan/pentingnya 1-2 kalimat]

    ---
    **Ingat:** Penjelasan ini adalah penyederhanaan untuk pemahaman awal. Untuk detail teknis yang mendalam, selalu rujuk buku teks, dokumentasi resmi (RFC jika ada), atau tanyakan pada guru Anda.
    """

# --- Interface Pengguna Streamlit ---
st.subheader("Masukkan Istilah Jaringan atau Telekomunikasi:")
istilah_input = st.text_input("Contoh: TCP/IP, Router, DNS, Subnetting, OSI Layer, Firewall, Kabel UTP Cat 6")

troubleshoot_button = st.button("Mulai Troubleshooting", type="primary")

# --- Logika Saat Tombol Ditekan ---
if troubleshoot_button:
    # ---- Panggil Inisialisasi Model DI SINI ----
    model_ready = initialize_model()

    if model_ready: # Hanya lanjut jika model berhasil diinisialisasi
        # Validasi input
        if not istilah_input:
            st.warning("Mohon deskripsikan masalah jaringan terlebih dahulu.")
        else:
            # Buat prompt jika input valid
            prompt_final_troubleshoot = buat_prompt_istilah(istilah_input)

            with st.spinner(f"🛠️ KA sedang menyusun langkah troubleshooting..."):
                try:
                    # Kirim ke Gemini (model sudah pasti ada jika model_ready True)
                    response = model.generate_content(prompt_final_troubleshoot)

                    # Cek safety
                    if response.parts:
                        jawaban_ai_troubleshoot = response.text
                    else:
                        # ... (penanganan safety tetap sama) ...
                        jawaban_ai_troubleshoot = "**Permintaan diblokir karena alasan keamanan.**"
                        st.warning("Respons AI mungkin diblokir...")

                    # Tampilkan hasil
                    st.divider()
                    st.subheader(f"📋 Langkah Troubleshooting untuk '{istilah_input}':")
                    st.markdown(jawaban_ai_troubleshoot)

                except Exception as e:
                    # Tangani error
                    st.error(f"Terjadi kesalahan saat menghubungi KA: {e}")
                    st.info("Tips: Coba lagi beberapa saat...")
    else:
        # Pesan jika model gagal inisialisasi (sudah ditampilkan di dalam fungsi initialize_model)
        pass # Tidak perlu pesan tambahan

# --- Footer ---
st.divider()
st.markdown("Aplikasi TJKT Penjelas Istilah | Dibuat dengan Streamlit & Google Gemini")