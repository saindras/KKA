import streamlit as st
import google.generativeai as genai
import os
import time

# --- Konfigurasi Awal
try:
    api_key = os.environ['GOOGLE_API_KEY']
    genai.configure(api_key=api_key)
except KeyError:
    st.error("Error: GOOGLE_API_KEY tidak ditemukan di Replit Secrets.")
    st.info("Pastikan Anda sudah menambahkan GOOGLE_API_KEY ke bagian Secrets di Replit.")
    st.stop()

# --- Definisi Persona ---
NAMA_BOT = "Chatbot Skanbara"
PERSONA = f"""
Anda adalah {NAMA_BOT}, sebuah robot asisten informasi virtual yang ramah dan membantu.
Tugas utama Anda adalah menjawab pertanyaan seputar SMK Negeri Bali Mandara (Skanbara) di Singaraja.
Anda juga memiliki pengetahuan mengenai Kota Singaraja, Kabupaten Buleleng, dan Pulau Bali secara umum.
Jawablah pertanyaan dengan sopan, jelas, dan informatif dalam Bahasa Indonesia.
Jika Anda tidak tahu jawabannya, katakan terus terang bahwa Anda tidak memiliki informasi tersebut, jangan mengarang.
Selalu identifikasi diri Anda sebagai {NAMA_BOT} jika ditanya siapa Anda.
"""
# ---------------------

# Inisialisasi model
model_name = 'models/gemini-2.0-flash-lite'
# model_name = 'models/gemini-2.5-pro'
try:
    # Menggunakan system_instruction untuk persona
    model = genai.GenerativeModel(
        model_name,
        system_instruction=PERSONA # Menambahkan persona di sini
        )
    # Membuat sesi chat untuk menjaga konteks (lebih baik untuk chatbot)
    chat = model.start_chat(history=[])

except Exception as e:
    st.error(f"Terjadi kesalahan saat inisialisasi model: {e}")
    st.info("Pastikan nama model sudah benar dan mendukung system_instruction.")
    st.stop()
# --------------------------------------------------

# --- Pengaturan Interface (Streamlit) ---
st.title(f"🤖 {NAMA_BOT}")
st.caption("Asisten Informasi Virtual SMK Negeri Bali Mandara")

# Inisialisasi riwayat chat jika belum ada
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Pesan sapaan awal sesuai persona
    st.session_state.messages.append({"role": "assistant", "content": f"Halo! Saya {NAMA_BOT}. Saya adalah robot asisten informasi di SMK Negeri Bali Mandara. Ada yang bisa saya bantu? 😊"})

# Tampilkan riwayat chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Input dari pengguna
prompt_pengguna = st.chat_input("Tanyakan sesuatu pada Chatbot Skanbara...")

if prompt_pengguna:
    # Tambahkan pesan pengguna ke riwayat chat dan tampilkan
    st.session_state.messages.append({"role": "user", "content": prompt_pengguna})
    with st.chat_message("user"):
        st.markdown(prompt_pengguna)

    # Kirim prompt ke Gemini dan tampilkan respons
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("Mohon menunggu...⚙️")
        try:
            # Mengirim prompt ke model Gemini menggunakan sesi chat       
            response = chat.send_message(prompt_pengguna) # Menggunakan sesi chat

            # Menampilkan respons            
            full_response = ""
            if hasattr(response, 'text'):
                 full_response = response.text
            elif hasattr(response, 'parts') and response.parts:
                 full_response = "".join(part.text for part in response.parts)
            else:
                 # Cek kandidat jika struktur berbeda
                 if response.candidates and response.candidates[0].content.parts:
                      full_response = "".join(part.text for part in response.candidates[0].content.parts)

            if full_response:
                message_placeholder.markdown(full_response)
                # Tambahkan respons KA ke riwayat chat
                st.session_state.messages.append({"role": "assistant", "content": full_response})
            else:
                fallback_msg = "Maaf, saya tidak dapat memproses permintaan Anda saat ini."
                message_placeholder.markdown(fallback_msg)
                st.session_state.messages.append({"role": "assistant", "content": fallback_msg})


        except Exception as e:
            st.error(f"Terjadi kesalahan saat mengirim prompt: {e}")
            error_msg = f"Maaf, terjadi kendala: {e}"
            message_placeholder.markdown(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})