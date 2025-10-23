import streamlit as st
import torch
from transformers import pipeline, AutoTokenizer # Tambahkan AutoTokenizer
import time # Opsional: untuk efek mengetik

# -- Konfigurasi Halaman Streamlit --
st.set_page_config(page_title="Chatbot Skanbara", page_icon="🤖")
st.title("🤖 Chatbot Skanbara")
st.caption("Virtual Assistant untuk Informasi SMK Negeri Bali Mandara")

# -- Inisialisasi Model LLM dan Tokenizer (dengan caching Streamlit) --
@st.cache_resource
def load_llm_pipeline_and_tokenizer():
    try:
        model_id = "meta-llama/Llama-3.2-3B-Instruct" # Model LLM
        tokenizer = AutoTokenizer.from_pretrained(model_id) # Muat tokenizer

        pipe = pipeline(
            "text-generation",
            model=model_id,
            tokenizer=tokenizer, # Sertakan tokenizer
            dtype=torch.bfloat16, # Gunakan bfloat16 jika GPU mendukung
            device_map="auto", # Coba "cuda:0" jika 'auto' gagal, atau "cpu" jika tidak ada GPU
            # model_kwargs={"use_flash_attention_2": True} # Opsional: jika didukung & terinstall untuk percepatan
        )
        # Pastikan tokenizer memiliki pad_token_id jika belum ada (beberapa model Llama memerlukannya)
        if pipe.tokenizer.pad_token_id is None:
             pipe.tokenizer.pad_token_id = pipe.tokenizer.eos_token_id

        return pipe
    except Exception as e:
        st.error(f"Gagal memuat model LLM atau tokenizer: {e}")
        st.warning("Pastikan Anda memiliki GPU yang kompatibel (jika menggunakan GPU), library terinstal, dan mungkin perlu login ke Hugging Face (`huggingface-cli login`). Model Llama 3.1 8B membutuhkan resource yang cukup besar.")
        return None

pipe = load_llm_pipeline_and_tokenizer()

# -- Pesan Sistem untuk Chatbot Skanbara --
system_message = (
    "Anda adalah Chatbot Skanbara, asisten virtual AI yang ramah, sopan, dan sangat informatif. "
    "Tugas utama Anda adalah memberikan informasi yang akurat dan relevan tentang topik-topik berikut:\n"
    "1.  **SMK Negeri Bali Mandara (Skanbara):** Informasi umum, jurusan (TKR, DPIB, TJKT), kegiatan siswa, prestasi, pendaftaran, lokasi, kontak.\n"
    "2.  **Kota Singaraja:** Informasi umum, tempat wisata, sejarah singkat, budaya, kuliner khas.\n"
    "3.  **Kabupaten Buleleng:** Informasi umum, geografi, potensi daerah, tempat wisata unggulan (pantai, air terjun, dataran tinggi), budaya.\n"
    "4.  **Provinsi Bali:** Informasi umum, budaya Bali (upacara adat, tarian, seni), pariwisata secara umum, geografi, sejarah singkat.\n\n"
    "Gunakan bahasa Indonesia yang baik dan benar. Jawablah pertanyaan pengguna dengan jelas dan terstruktur. "
    "Jika pertanyaan di luar topik yang disebutkan, nyatakan dengan sopan bahwa Anda hanya dapat memberikan informasi terkait Skanbara, Singaraja, Buleleng, dan Bali. "
    "Jika Anda tidak yakin atau tidak tahu jawabannya, katakan terus terang daripada memberikan informasi yang salah."
)

# -- Fungsi Helper (Ekstrak teks asisten dari output pipeline) --
def extract_assistant_text(generated_data, num_input_messages):
    """
    Ekstrak teks respons dari asisten.
    Pipeline 'text-generation' dengan input messages akan mengembalikan seluruh history + respons baru.
    Kita hanya perlu mengambil bagian respons baru dari asisten.
    """
    try:
        if isinstance(generated_data, list) and generated_data:
            full_conversation = generated_data[0]["generated_text"]
            # Respons asisten adalah pesan setelah pesan input awal
            if len(full_conversation) > num_input_messages:
                 new_assistant_message = full_conversation[-1] # Ambil pesan terakhir
                 if new_assistant_message.get("role") == "assistant":
                     return new_assistant_message["content"].strip() # .replace("\n", " ") # Hapus strip() jika ingin mempertahankan paragraf
            # Jika tidak ada pesan baru atau role salah
            return "Maaf, saya tidak dapat menghasilkan respons saat ini."
        return "Maaf, format respons tidak dikenali."
    except (IndexError, KeyError, TypeError) as e:
        print(f"Error parsing LLM output: {e}\nOutput: {generated_data}") # Logging untuk debug
        return "Terjadi kesalahan saat memproses respons dari AI."

# -- Manajemen State Chat (Session State) --
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Pesan sambutan awal
    st.session_state.messages.append({"role": "assistant", "content": "Om Swastyastu! 🙏 Saya Chatbot Skanbara. Ada yang bisa saya bantu informasikan mengenai SMK Negeri Bali Mandara, Kota Singaraja, Kabupaten Buleleng, atau Provinsi Bali?"})

# -- Tampilkan Riwayat Chat --
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# -- Fungsi untuk Menghasilkan Respons --
def generate_response(user_prompt):
    if pipe is None:
        return "Maaf, model AI sedang tidak tersedia."

    # Siapkan history untuk model
    # Ambil beberapa pesan terakhir agar tidak melebihi batas token
    # MAX_HISTORY_TOKENS = 4096 # Contoh batas token (sesuaikan dengan model)
    # current_token_count = 0
    history_for_llm = []
    # Iterasi dari pesan terbaru ke terlama
    # for msg in reversed(st.session_state.messages):
    #     msg_tokens = len(pipe.tokenizer.encode(msg['content'])) # Hitung token (perkiraan)
    #     if current_token_count + msg_tokens < MAX_HISTORY_TOKENS:
    #         history_for_llm.insert(0, {"role": msg["role"], "content": msg["content"]}) # Tambah di awal
    #         current_token_count += msg_tokens
    #     else:
    #         break # Stop jika token sudah mendekati batas

    # Gabungkan pesan sistem, history (jika ada), dan prompt pengguna baru
    messages_for_llm = [
        {"role": "system", "content": system_message}
    ]
    # Tambahkan history jika diperlukan model Anda (contoh: ambil 5 pesan terakhir)
    messages_for_llm.extend(st.session_state.messages[-5:]) # Ambil 5 pesan terakhir sebagai history sederhana
    messages_for_llm.append({"role": "user", "content": user_prompt})

    num_input_msgs = len(messages_for_llm) # Simpan jumlah pesan input

    try:
        with st.spinner("Chatbot Skanbara sedang mencari informasi... 🤔"):
            # Panggil pipeline
            outputs = pipe(
                messages_for_llm,
                max_new_tokens=512, # Beri ruang lebih untuk jawaban informatif
                eos_token_id=pipe.tokenizer.eos_token_id, # Penting untuk Llama 3.1
                pad_token_id=pipe.tokenizer.pad_token_id, # Pastikan ini diset
                do_sample=True,
                temperature=0.6, # Sedikit lebih faktual
                top_p=0.9,
            )
        # Ekstrak teks dari output
        assistant_response = extract_assistant_text(outputs, num_input_msgs)
        return assistant_response
    except Exception as e:
        st.error(f"Error saat menghasilkan teks: {e}") # Tampilkan error di UI
        print(f"Error during pipeline call: {e}") # Log error di terminal
        return "Maaf, terjadi kendala teknis saat mencoba menjawab."

# -- Input Pengguna --
if prompt := st.chat_input("Tanyakan sesuatu tentang Skanbara, Singaraja, Buleleng, atau Bali!"):
    # 1. Tambahkan & tampilkan pesan pengguna
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Hasilkan & tampilkan respons chatbot
    response = generate_response(prompt)
    with st.chat_message("assistant"):
        # Efek mengetik sederhana (opsional)
        message_placeholder = st.empty()
        full_response = ""
        for chunk in response.split(): # Split sederhana per kata
            full_response += chunk + " "
            time.sleep(0.03) # Sedikit lebih cepat
            # Perbarui placeholder dengan teks saat ini + kursor
            message_placeholder.markdown(full_response + "▌")
        # Setelah selesai, perbarui placeholder dengan teks final tanpa kursor
        message_placeholder.markdown(full_response)
        # st.markdown(response) # Versi tanpa efek mengetik

    # 3. Tambahkan respons chatbot ke history state
    st.session_state.messages.append({"role": "assistant", "content": response}) # Simpan respons final

# -- Tambahan: Tombol untuk clear chat --
if st.button("🔄 Mulai Percakapan Baru"):
    st.session_state.messages = [{"role": "assistant", "content": "Percakapan telah dimulai ulang. Silakan bertanya lagi!"}]
    st.rerun() # Ganti experimental_rerun dengan rerun