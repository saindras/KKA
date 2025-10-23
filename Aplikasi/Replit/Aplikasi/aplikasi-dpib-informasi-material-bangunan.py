import streamlit as st
import os
import google.generativeai as genai

# --- Konfigurasi Halaman Streamlit ---
st.set_page_config(page_title="Info Material Bangunan DPIB", page_icon="🧱", layout="wide")
st.title("🧱 Asisten Informasi Material Bangunan")
st.caption("Didukung oleh KA Generatif (Gemini)")

# --- Konfigurasi API Key & Model Gemini ---
api_key_configured = False
model = None

# --- Fungsi untuk Inisialisasi Model (Dipanggil saat dibutuhkan) ---
def initialize_model():
    global model, api_key_configured
    if model is None and not api_key_configured: # Hanya inisialisasi sekali
        api_key_configured= True # Tandai sudah dicek
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
         # Jika api_key_configuredTrue tapi model masih None, berarti gagal sebelumnya
         st.error("Konfigurasi API Key gagal sebelumnya. Periksa Secrets dan refresh halaman.")
         return False
# Konfigurasi library genai jika API Key ditemukan
if api_key_configured:
    try:
        # Nama model yang akan digunakan
        model = genai.GenerativeModel('models/gemini-2.0-flash-lite')
        st.info("Model Generative KA ('models/gemini-2.0-flash-lite') siap digunakan.")
    except Exception as e:
        st.error(f"Error saat mengkonfigurasi atau memuat model KA: {e}")
        st.stop()

# --- Fungsi untuk Membuat Prompt Material ---
def buat_prompt_material(nama_material):
    # Prompt spesifik untuk informasi material
    return f"""
    Anda adalah seorang ahli material bangunan dan arsitektur yang bertugas menjelaskan konsep kepada siswa SMK jurusan DPIB (Desain Pemodelan dan Informasi Bangunan). Gunakan bahasa yang jelas, informatif, dan mudah dipahami oleh pemula.

    Siswa ingin mengetahui informasi tentang material bangunan berikut: '{nama_material}'

    Tugas Anda:
    Berikan deskripsi ringkas namun komprehensif tentang material tersebut, mencakup poin-poin berikut:

    1.  **Deskripsi Umum:** Jelaskan secara singkat apa material itu.
    2.  **Karakteristik Utama:** Sebutkan 3-4 sifat atau ciri khas utama dari material ini (misal: kekuatan, bobot, ketahanan air, isolasi termal, dll.).
    3.  **Kelebihan:** Sebutkan 2-3 keuntungan utama menggunakan material ini dalam konstruksi.
    4.  **Kekurangan:** Sebutkan 2-3 keterbatasan atau kerugian utama dari material ini.
    5.  **Penggunaan Umum:** Berikan 2-3 contoh aplikasi atau bagian bangunan di mana material ini sering digunakan.

    Format Jawaban (Gunakan Markdown):

    ### Informasi Material: {nama_material}

    **1. Deskripsi Umum:**
    [Penjelasan singkat material]

    **2. Karakteristik Utama:**
    * [Karakteristik 1]: [Penjelasan singkat]
    * [Karakteristik 2]: [Penjelasan singkat]
    * [Karakteristik 3]: [Penjelasan singkat]
    * [Karakteristik 4 (jika relevan)]: [Penjelasan singkat]

    **3. Kelebihan:**
    * [Kelebihan 1]
    * [Kelebihan 2]
    * [Kelebihan 3 (jika relevan)]

    **4. Kekurangan:**
    * [Kekurangan 1]
    * [Kekurangan 2]
    * [Kekurangan 3 (jika relevan)]

    **5. Penggunaan Umum:**
    * [Contoh penggunaan 1]
    * [Contoh penggunaan 2]
    * [Contoh penggunaan 3 (jika relevan)]

    ---
    **Catatan Penting:**
    * Informasi ini bersifat **umum**. Sifat dan spesifikasi material dapat bervariasi tergantung pada produsen, kualitas, dan standar yang berlaku.
    * Selalu rujuk **data teknis (datasheet)** dari produsen dan konsultasikan dengan guru atau profesional untuk pemilihan material pada proyek spesifik.
    """

# --- Interface Pengguna Streamlit ---
st.subheader("Masukkan Nama Material Bangunan:")
material_input = st.text_input("Contoh: Bata Ringan AAC, Baja WF, Kayu Meranti, Kaca Tempered")

cari_info_button = st.button("Cari Informasi Material", type="primary")

# --- Logika Saat Tombol Ditekan ---
if cari_info_button:
	model_ready = initialize_model()
    # Validasi input
    if not material_input:
        st.warning("Mohon masukkan nama material terlebih dahulu.")
    else:
        # Buat prompt jika input valid
        prompt_final_material = buat_prompt_material(material_input)

        with st.spinner(f"🤖 KA sedang mencari informasi tentang {material_input}... Mohon tunggu..."):
            try:
                # Kirim ke Gemini
                response = model.generate_content(prompt_final_material)
                # Cek apakah ada potensi diblokir karena safety
                if response.parts:
                    jawaban_ai_material = response.text
                else:
                    # Coba akses safety ratings jika ada, atau berikan pesan umum
                    try:
                        safety_feedback = response.prompt_feedback
                        jawaban_ai_material = f"**Permintaan diblokir karena alasan keamanan.**\n\nDetail:\n{safety_feedback}"
                    except Exception:
                         jawaban_ai_material = "**Permintaan diblokir karena alasan keamanan.** Tidak ada detail tambahan tersedia."
                         st.warning("Respons KA mungkin diblokir karena kebijakan keamanan.")

                # Tampilkan hasil
                st.divider() # Garis pemisah
                st.subheader(f"📄 Informasi Mengenai {material_input}:")
                st.markdown(jawaban_ai_material) # Gunakan markdown

            except Exception as e:
                # Tangani error
                st.error(f"Terjadi kesalahan saat menghubungi KA: {e}")
                st.info("Tips: Coba lagi beberapa saat. Pastikan API Key valid dan nama material cukup umum dikenal.")

# --- Footer (Opsional) ---
st.divider()
st.markdown("Aplikasi DPIB Info Material | Dibuat dengan Streamlit & Google Gemini")