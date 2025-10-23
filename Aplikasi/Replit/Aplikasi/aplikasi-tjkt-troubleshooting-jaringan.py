import streamlit as st
import os
import google.generativeai as genai

# --- Konfigurasi Halaman Streamlit ---
st.set_page_config(page_title="Troubleshooting Jaringan TJKT", page_icon="🔧", layout="wide")
st.title("🔧 Generator Langkah Troubleshooting Dasar Jaringan")
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

# --- Fungsi untuk Membuat Prompt Troubleshooting ---
def buat_prompt_troubleshooting(masalah):
    # Prompt spesifik untuk langkah troubleshooting
    return f"""
    Anda adalah seorang Network Engineer Senior yang sangat berpengalaman dalam troubleshooting jaringan dan sabar membimbing teknisi junior (siswa SMK TJKT). Anda berpikir secara sistematis dan logis.

    Seorang siswa melaporkan masalah jaringan berikut: '{masalah}'

    Tugas Anda:
    Buatlah daftar langkah-langkah troubleshooting dasar yang **sistematis dan berurutan** (mulai dari lapisan fisik jika memungkinkan) untuk membantu siswa mendiagnosis masalah tersebut. Fokus pada langkah-langkah **awal** yang bisa dilakukan dengan alat standar (seperti command prompt/terminal) atau pemeriksaan visual.

    Instruksi Spesifik:
    1.  Berikan **maksimal 6 langkah** troubleshooting yang paling relevan dan logis untuk masalah '{masalah}'.
    2.  Setiap langkah harus berupa **tindakan spesifik** yang bisa dilakukan siswa (misal: "Periksa lampu indikator pada modem/router", "Lakukan ping ke alamat IP 8.8.8.8").
    3.  Berikan **penjelasan singkat (1 kalimat)** untuk setiap langkah, menjelaskan **tujuan** dari langkah tersebut.
    4.  Urutkan langkah-langkah dari yang paling dasar/fisik menuju yang lebih logikal/software.
    5.  Gunakan bahasa yang jelas dan instruktif.

    Format Jawaban (Gunakan Markdown):

    ### Langkah Troubleshooting Dasar untuk: {masalah}

    Berikut adalah langkah-langkah awal yang bisa dicoba secara berurutan:

    1.  **Langkah 1: [Nama Tindakan]**
        * _Tujuan:_ [Penjelasan singkat tujuan langkah ini, 1 kalimat].
    2.  **Langkah 2: [Nama Tindakan]**
        * _Tujuan:_ [Penjelasan singkat tujuan langkah ini, 1 kalimat].
    3.  **Langkah 3: [Nama Tindakan]**
        * _Tujuan:_ [Penjelasan singkat tujuan langkah ini, 1 kalimat].
    ... (dan seterusnya, maksimal 6)

    ---
    **Penting:**
    * Lakukan langkah-langkah ini secara **berurutan**. Jika masalah teratasi di satu langkah, Anda mungkin tidak perlu melanjutkan ke langkah berikutnya.
    * Ini adalah panduan **dasar**. Masalah jaringan bisa kompleks. Jika langkah-langkah ini tidak berhasil, catat hasil dari setiap langkah dan konsultasikan dengan guru atau teknisi yang lebih berpengalaman.
    """

# --- Interface Pengguna Streamlit ---
st.subheader("Deskripsikan Masalah Jaringan yang Dihadapi:")
masalah_input = st.text_area("Contoh: Laptop tidak bisa konek ke WiFi sekolah, Internet lambat saat browsing, Tidak bisa ping ke google.com", height=100)

troubleshoot_button = st.button("Mulai Troubleshooting", type="primary")

# --- Logika Saat Tombol Ditekan ---
if troubleshoot_button:
    # ---- Panggil Inisialisasi Model DI SINI ----
    model_ready = initialize_model()

    if model_ready: # Hanya lanjut jika model berhasil diinisialisasi
        # Validasi input
        if not masalah_input:
            st.warning("Mohon deskripsikan masalah jaringan terlebih dahulu.")
        else:
            # Buat prompt jika input valid
            prompt_final_troubleshoot = buat_prompt_troubleshooting(masalah_input)

            with st.spinner(f"🛠️ AI sedang menyusun langkah troubleshooting..."):
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
                    st.subheader(f"📋 Langkah Troubleshooting untuk '{masalah_input}':")
                    st.markdown(jawaban_ai_troubleshoot)

                except Exception as e:
                    # Tangani error
                    st.error(f"Terjadi kesalahan saat menghubungi AI: {e}")
                    st.info("Tips: Coba lagi beberapa saat...")
    else:
        # Pesan jika model gagal inisialisasi (sudah ditampilkan di dalam fungsi initialize_model)
        pass # Tidak perlu pesan tambahan

# --- Footer ---
st.divider()
st.markdown("Aplikasi TJKT Troubleshooting Jaringan | Dibuat dengan Streamlit & Google Gemini")