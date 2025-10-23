import streamlit as st
import torch
from transformers import pipeline
import json
import re # Untuk parsing yang lebih fleksibel jika JSON gagal

# --- Konfigurasi Awal ---
st.set_page_config(page_title="Asisten Belajar", layout="wide")
st.title("🎓 Asisten Belajar SMK")
st.caption("Latihan soal sesuai materi pelajaranmu!")

# --- Inisialisasi Model LLM (Sekali saja per sesi) ---
# Gunakan st.cache_resource agar model tidak di-load ulang setiap interaksi
@st.cache_resource
def load_model():
    model_id = "meta-llama/Llama-3.2-3B-Instruct"
    try:
        pipe = pipeline(
            "text-generation",
            model=model_id,
            model_kwargs={"dtype": torch.bfloat16}, # Sesuaikan dtype jika perlu
            device_map="auto", # Otomatis menggunakan GPU jika tersedia
        )
        return pipe
    except Exception as e:
        st.error(f"Gagal memuat model LLM: {e}. Pastikan model '{model_id}' tersedia dan dependensi terinstal.")
        st.stop() # Hentikan eksekusi jika model gagal dimuat
        return None

pipe = load_model()

# --- Fungsi Pembantu ---
def parse_llm_output(output_string):
    """Mencoba parse output LLM sebagai JSON, lebih toleran dan dengan debug."""
    cleaned_string = None
    json_str = None
    try:
        # 1. Bersihkan whitespace awal/akhir secara agresif
        cleaned_string = output_string.strip()

        # 2. Hapus markdown code block jika ada
        if cleaned_string.startswith("```json"):
            cleaned_string = cleaned_string[7:]
        if cleaned_string.endswith("```"):
            cleaned_string = cleaned_string[:-3]
        cleaned_string = cleaned_string.strip()

        # 3. Coba cari '{' pertama dan '}' terakhir
        start_index = cleaned_string.find('{')
        end_index = cleaned_string.rfind('}')

        # --- DEBUGGING INDICES ---
        print(f">>> DEBUG: start_index = {start_index}")
        print(f">>> DEBUG: end_index = {end_index}")
        print(f">>> DEBUG: len(cleaned_string) = {len(cleaned_string)}")
        # --- END DEBUGGING ---

        data = None # Inisialisasi data

        # Coba ekstraksi pakai find/rfind dulu
        if start_index != -1 and end_index != -1 and end_index > start_index:
            json_str = cleaned_string[start_index : end_index + 1]
            print(">>> Mencoba parsing (via find/rfind):", repr(json_str))
            try:
                data = json.loads(json_str)
            except json.JSONDecodeError as e_find:
                print(f">>> Parsing (via find/rfind) GAGAL: {e_find}")
                data = None # Set data ke None jika parsing ini gagal

        # Jika find/rfind gagal ATAU parsingnya gagal, coba regex yang lebih longgar
        if data is None:
            print(">>> find/rfind gagal atau parsingnya gagal, mencoba regex...")
            # Regex mencari blok { } pertama yg paling besar
            json_match = re.search(r'(\{.*\})', cleaned_string, re.DOTALL)
            if json_match:
                json_str = json_match.group(1).strip() # Ambil grup 1 dan strip lagi
                print(">>> Mencoba parsing (via regex):", repr(json_str))
                try:
                    data = json.loads(json_str)
                except json.JSONDecodeError as e_re:
                    print(f">>> Parsing (via regex) GAGAL: {e_re}")
                    st.warning(f"Output LLM bukan JSON yang valid. Error: {e_re}")
                    return None # Langsung keluar jika regex pun gagal parse
            else:
                # Jika regex pun tidak menemukan blok JSON
                st.warning("Tidak menemukan blok JSON utama '{...}' dalam output LLM (via regex).")
                print(">>> PARSING GAGAL MENEMUKAN BLOK '{}' (via regex):", repr(cleaned_string))
                return None # Langsung keluar

        # --- Jika sampai sini, 'data' seharusnya berisi hasil parsing ---
        if data is not None:
             # 5. Validasi Struktur
            if isinstance(data, dict) and "essay_score" in data and "overall_feedback" in data:
                print(">>> PARSING BERHASIL (EVALUASI), Mengembalikan data:", data)
                return data
            elif isinstance(data, dict) and "mcqs" in data and "essay" in data:
                print(">>> PARSING BERHASIL (PERTANYAAN), Mengembalikan data:", data)
                return data
            else:
                st.warning("Struktur JSON dari LLM tidak sesuai harapan (bukan evaluasi/pertanyaan).")
                print(">>> PARSING GAGAL VALIDASI STRUKTUR:", data)
                return None
        else:
             # Seharusnya tidak sampai sini jika logika di atas benar, tapi sebagai fallback
             st.error("Terjadi kesalahan tak terduga saat parsing.")
             return None
    except Exception as e: # Tangkap error umum lainnya
        st.error(f"Error umum saat parsing output LLM: {e}")
        print(">>> PARSING GAGAL Exception:", repr(cleaned_string if cleaned_string is not None else output_string))
        return None

def generate_questions(topic):
    """Memanggil LLM untuk menghasilkan soal."""
    system_prompt_generate = """
    You are an AI assistant tasked with creating study questions for Indonesian Vocational High School (SMK) students across various majors like TKR, DPIB, and TJKT. Your goal is to generate relevant and challenging questions based on a given topic.
    """
    # DEBUGGING =======================================
    user_prompt_generate = f"""
    You are an AI assistant tasked with creating study questions for Indonesian Vocational High School (SMK) students based on the topic: '{topic}'.

    Your task is to:
    1. Generate exactly 4 unique multiple-choice questions (MCQ).
    2. Generate exactly 1 unique essay question that encourages critical thinking relevant to SMK.
    3. Provide a detailed rubric for the essay question with 3-4 criteria and 3 scoring levels per criterion.

    The following is an EXAMPLE of the required JSON output structure ONLY. Do NOT copy the content, only follow the structure. The actual questions and rubric MUST be based on the topic '{topic}'.

    {{
      "mcqs": [
        {{
          "question": "Apa fungsi utama karburator pada mesin bensin?",
          "options": {{ "A": "Mencampur udara dan bahan bakar", "B": "Mendinginkan mesin", "C": "Membuang gas sisa", "D": "Mengatur waktu pengapian" }},
          "correct_answer_letter": "A"
        }},
        {{
          "question": "Komponen sistem rem ABS yang mencegah roda terkunci saat pengereman mendadak?",
          "options": {{ "A": "Kaliper", "B": "Master Silinder", "C": "Sensor Roda & Modulator", "D": "Kampas Rem" }},
          "correct_answer_letter": "C"
        }}
      ],
      "essay": {{
        "question": "Jelaskan prinsip kerja sistem rem ABS dan mengapa sistem ini penting untuk keselamatan berkendara di kondisi jalan licin.",
        "rubric": {{
            "Pemahaman Prinsip Kerja": {{
                "description": "Menilai pemahaman siswa tentang cara kerja ABS.",
                "levels": {{
                    "Baik Sekali (3 pts)": "Penjelasan detail, akurat, menyebutkan komponen utama.",
                    "Baik (2 pts)": "Penjelasan cukup baik, ada sedikit kekurangan.",
                    "Perlu Perbaikan (1 pt)": "Penjelasan kurang atau salah."
                }}
            }},
            "Penjelasan Keselamatan": {{
                "description": "Menilai pemahaman siswa tentang pentingnya ABS untuk keselamatan.",
                "levels": {{
                    "Baik Sekali (3 pts)": "Penjelasan relevan, jelas, mengaitkan dengan kondisi licin.",
                    "Baik (2 pts)": "Penjelasan relevan, kurang detail.",
                    "Perlu Perbaikan (1 pt)": "Penjelasan kurang relevan atau salah."
                }}
             }}
         }}
      }}
    }}

    Now, generate the 4 MCQs and 1 Essay question with its rubric based on the topic '{topic}'.
    Adhere STRICTLY to the JSON structure shown in the example.
    Output ONLY the single valid JSON object. Your response MUST start with '{{' and end with '}}'.
    Do NOT include any text outside the JSON object.
    """
    # EOF DEBUGGING =======================================
    messages = [
        {"role": "system", "content": system_prompt_generate},
        {"role": "user", "content": user_prompt_generate},
    ]

    terminators = [
        pipe.tokenizer.eos_token_id,
        pipe.tokenizer.convert_tokens_to_ids("<|eot_id|>")
    ]

    try:
        with st.spinner("Sedang mempersiapkan soal..."):
            outputs = pipe(
                messages,
                max_new_tokens=1024, # Tingkatkan jika soal/rubrik kompleks
                eos_token_id=terminators,
                do_sample=True,
                temperature=0.6, # Sedikit kreativitas untuk soal
                top_p=0.9,
                pad_token_id=pipe.tokenizer.eos_token_id # Menghindari warning
            )
        # Ekstrak teks yang dihasilkan oleh asisten saja
        generated_text_response = outputs[0]['generated_text'][-1]['content']
        # Debugging
        print("--- LLM Raw Output (Generate Questions) ---")
        print(generated_text_response)
        print("--- End LLM Raw Output ---")
        # END Debugging
        return parse_llm_output(generated_text_response)
    except Exception as e:
        st.error(f"Terjadi kesalahan saat menghubungi LLM: {e}")
        return None

def evaluate_answers(questions_data, user_answers):
    """Memanggil LLM untuk mengevaluasi jawaban essay dan menghitung skor total."""
    system_prompt_evaluate = """
    You are an AI teaching assistant evaluating an Indonesian SMK student's answers. Evaluate the essay answer based strictly on the provided rubric. Assess its depth, critical thinking, analytical quality, and relevance. Also, check the MCQ answers. Provide a score for the essay (based on the rubric total points), calculate the number of correct MCQs, and generate overall constructive feedback ini Bahasa Indonesia.
    """

    mcq_results = []
    correct_mcq_count = 0
    total_mcq = len(questions_data.get("mcqs", []))

    # Evaluasi MCQ
    for i, q in enumerate(questions_data.get("mcqs", [])):
        user_ans = user_answers.get(f"mcq_{i}")
        correct_ans = q.get("correct_answer_letter")
        is_correct = user_ans == correct_ans
        if is_correct:
            correct_mcq_count += 1
        mcq_results.append({
            "question": q.get("question"),
            "user_answer": user_ans,
            "correct_answer": correct_ans,
            "is_correct": is_correct
        })

    essay_question_text = questions_data.get("essay", {}).get("question", "N/A")
    essay_rubric_text = json.dumps(questions_data.get("essay", {}).get("rubric", {}), indent=2) # Kirim rubric sebagai JSON string
    essay_user_answer = user_answers.get("essay_answer", "")

    # Hitung total poin maksimal dari rubrik
    max_essay_score = 0
    if isinstance(questions_data.get("essay", {}).get("rubric"), dict):
      for criterion in questions_data["essay"]["rubric"].values():
          if "levels" in criterion and isinstance(criterion["levels"], dict):
             # Cari skor tertinggi (asumsi format 'Excellent (X pts)')
             scores = [int(re.search(r'\((\d+)\s*pts\)', level).group(1)) for level in criterion["levels"] if re.search(r'\((\d+)\s*pts\)', level)]
             if scores:
                 max_essay_score += max(scores)


    user_prompt_evaluate = f"""
    Please evaluate the student's answers.

    MCQ Results Summary: {correct_mcq_count} out of {total_mcq} correct.

    Essay Question: {essay_question_text}
    Rubric:
    {essay_rubric_text}

    Student's Essay Answer:
    {essay_user_answer}

    Evaluation Task:
    1. Evaluate the essay answer STRICTLY based on the provided rubric. Assess depth, critical thinking, analysis, and relevance. Be critical and specific.
    2. Assign a score for the essay based on the rubric criteria (maximum possible score is {max_essay_score} points).
    3. Provide concise, constructive, and encouraging overall feedback for the student, considering both MCQ and essay performance. Explain the essay score based on the rubric.

    Output ONLY a single valid JSON object with the following structure:
    {{
      "essay_score": <integer score based on rubric>,
      "max_essay_score": {max_essay_score},
      "correct_mcq_count": {correct_mcq_count},
      "total_mcq": {total_mcq},
      "overall_feedback": "..."
    }}
    Do not include any text outside the JSON object.
    Ensure the JSON is complete and correctly formatted.
    + IMPORTANT: Do NOT include any introductory text, concluding text, explanations, apologies, or markdown formatting like ```json before or after the JSON object itself. Your entire response must start with '{' and end with '}'.
    """

    messages = [
        {"role": "system", "content": system_prompt_evaluate},
        {"role": "user", "content": user_prompt_evaluate},
    ]

    terminators = [
        pipe.tokenizer.eos_token_id,
        pipe.tokenizer.convert_tokens_to_ids("<|eot_id|>")
    ]

    try:
        with st.spinner("Sedang mengevaluasi jawaban..."):
            outputs = pipe(
                messages,
                max_new_tokens=512, # Feedback bisa jadi cukup panjang
                eos_token_id=terminators,
                do_sample=True,
                temperature=0.5, # Lebih faktual untuk evaluasi
                top_p=0.9,
                 pad_token_id=pipe.tokenizer.eos_token_id
            )
        generated_text_response = outputs[0]['generated_text'][-1]['content']
        # Debugging
        print("--- LLM Raw Output (Evaluate Answers) SEBELUM PARSING ---")
        print(repr(generated_text_response)) # Gunakan repr() untuk melihat karakter tersembunyi
        print("--- End LLM Raw Output Evaluate ---")
        # END Debugging
        evaluation_result = parse_llm_output(generated_text_response)

        # Tambahkan detail MCQ ke hasil evaluasi untuk ditampilkan
        if evaluation_result:
            evaluation_result["mcq_details"] = mcq_results
        return evaluation_result

    except Exception as e:
        st.error(f"Terjadi kesalahan saat mengevaluasi jawaban: {e}")
        # Kembalikan hasil MCQ saja jika evaluasi LLM gagal
        return {
          "essay_score": 0,
          "max_essay_score": max_essay_score,
          "correct_mcq_count": correct_mcq_count,
          "total_mcq": total_mcq,
          "overall_feedback": "Gagal mengevaluasi jawaban essay.",
          "mcq_details": mcq_results
        }


# --- State Management ---
# Gunakan Session State untuk menyimpan data antar interaksi
if 'topic' not in st.session_state:
    st.session_state.topic = ""
if 'questions_data' not in st.session_state:
    st.session_state.questions_data = None
if 'evaluation_result' not in st.session_state:
    st.session_state.evaluation_result = None
if 'show_results' not in st.session_state:
    st.session_state.show_results = False

# --- Tampilan Utama ---

# Input Topik
topic_input = st.text_input("Masukkan Mata Pelajaran atau Materi:", value=st.session_state.topic, key="topic_input_key")
col1, col2 = st.columns([1, 4])
with col1:
    generate_clicked = st.button("🚀 Buat Soal Latihan")
with col2:
    reset_clicked = st.button("🔄 Mulai Lagi / Topik Baru")

if reset_clicked:
    # Reset semua state
    st.session_state.topic = ""
    st.session_state.questions_data = None
    st.session_state.evaluation_result = None
    st.session_state.show_results = False
    st.rerun() # Muat ulang halaman

if generate_clicked and topic_input:
    st.session_state.topic = topic_input
    st.session_state.questions_data = generate_questions(st.session_state.topic)
    st.session_state.evaluation_result = None # Reset hasil evaluasi lama
    st.session_state.show_results = False
    # Rerun untuk menampilkan soal setelah state questions_data diupdate
    st.rerun()

# Tampilkan Soal jika sudah digenerate
if st.session_state.questions_data and not st.session_state.show_results:
    st.markdown("---")
    st.subheader(f"📝 Soal Latihan untuk: {st.session_state.topic}")

    user_answers = {}
    with st.form(key='answer_form'):
        # Tampilkan Soal Pilihan Ganda
        st.markdown("---")
        st.markdown("### Pilihan Ganda")
        mcqs = st.session_state.questions_data.get("mcqs", [])
        if not mcqs:
             st.warning("Tidak ada soal pilihan ganda yang berhasil dibuat.")

        for i, q in enumerate(mcqs):
            question_text = q.get("question", f"Soal {i+1} tidak tersedia")
            options_dict = q.get("options", {})
            # Pastikan urutan A, B, C, D konsisten
            options_list = [f"{letter}: {options_dict.get(letter, 'N/A')}" for letter in ['A', 'B', 'C', 'D']]
            # Ambil hanya huruf A, B, C, D untuk pilihan radio
            option_keys = list(options_dict.keys())

            user_answers[f"mcq_{i}"] = st.radio(
                f"{i+1}. {question_text}",
                options=option_keys, # Gunakan hanya A, B, C, D
                format_func=lambda key: f"{key}: {options_dict.get(key, 'N/A')}", # Tampilkan A: Teks Jawaban
                key=f"mcq_radio_{i}",
                horizontal=False # Tampilkan vertikal agar lebih rapi
            )
            st.markdown("---") # Pemisah antar soal MCQ


        # Tampilkan Soal Essay dan Rubriknya
        st.markdown("---")
        st.markdown("### Essay")
        essay_data = st.session_state.questions_data.get("essay", {})
        essay_question = essay_data.get("question")
        essay_rubric = essay_data.get("rubric")

        if essay_question:
            st.write(f"**Soal Essay:** {essay_question}")

            if essay_rubric and isinstance(essay_rubric, dict):
                st.markdown("**Rubrik Penilaian Essay:**")

                #REVISI 1: Menangani berbagai struktur rubrik ======================
                for crit_name, crit_details in essay_rubric.items():
                    # Periksa apakah crit_details adalah dictionary (struktur yg diharapkan)
                    if isinstance(crit_details, dict):
                        # Tampilkan description jika ada, jika tidak, tampilkan crit_name
                        st.markdown(f"- **{crit_details.get('description', crit_name)}**")
                        levels = crit_details.get("levels", {})
                        # Pastikan levels juga dictionary sebelum di-loop
                        if isinstance(levels, dict):
                            for level_name, level_desc in levels.items():
                                st.markdown(f"  - _{level_name}_: {level_desc}")
                        else:
                            st.markdown(f"  - _Detail level untuk '{crit_name}' tidak ditemukan atau format salah._")
                    # Fallback jika crit_details hanya string (struktur lebih sederhana dari LLM)
                    elif isinstance(crit_details, str):
                         st.markdown(f"- **{crit_name}**: {crit_details}") # Tampilkan nama kriteria dan deskripsi stringnya
                    # Tangani tipe data lain yang tidak diharapkan
                    else:
                        st.markdown(f"- **{crit_name}**: _Format detail kriteria tidak dikenali (tipe: {type(crit_details)})_")
                #END REVISI 1==============================
            else:
                 st.warning("Rubrik essay tidak tersedia atau formatnya salah.")


            user_answers["essay_answer"] = st.text_area("Jawaban Essay Anda:", height=200, key="essay_input")
        else:
             st.warning("Tidak ada soal essay yang berhasil dibuat.")

        # Tombol Submit
        submitted = st.form_submit_button("✅ Kumpulkan Jawaban")

    if submitted:
        st.session_state.evaluation_result = evaluate_answers(st.session_state.questions_data, user_answers)
        st.session_state.show_results = True
        # Rerun untuk menampilkan hasil setelah state evaluation_result diupdate
        st.rerun()        

# Tampilkan Hasil Evaluasi jika sudah disubmit
if st.session_state.show_results and st.session_state.evaluation_result:
    print(">>> KONDISI TAMPILKAN HASIL TERPENUHI")
    st.markdown("---")
    st.subheader("🎉 Hasil Latihan")

    eval_res = st.session_state.evaluation_result
    mcq_correct = eval_res.get("correct_mcq_count", 0)
    mcq_total = eval_res.get("total_mcq", 0)
    essay_score = eval_res.get("essay_score", 0)
    essay_max_score = eval_res.get("max_essay_score", 0) # Ambil max score

    # Hitung skor total sederhana (misal: 1 poin per MCQ benar + skor essay)
    # Anda bisa membuat skema penilaian yang lebih kompleks
    total_score = mcq_correct + essay_score
    max_total_score = mcq_total + essay_max_score

    st.metric("Skor Pilihan Ganda", f"{mcq_correct} / {mcq_total}")
    if essay_max_score > 0:
      st.metric("Skor Essay", f"{essay_score} / {essay_max_score}")
      st.metric("Total Skor", f"{total_score} / {max_total_score}")
    else:
       st.metric("Total Skor", f"{mcq_correct} / {mcq_total}" ) # Hanya skor MCQ jika essay gagal


    st.markdown("---")
    st.markdown("### Umpan Balik Keseluruhan:")
    st.info(eval_res.get("overall_feedback", "Tidak ada umpan balik."))

    # Tampilkan detail jawaban MCQ (opsional)
    with st.expander("Lihat Detail Jawaban Pilihan Ganda"):
        mcq_details = eval_res.get("mcq_details", [])
        for i, detail in enumerate(mcq_details):
             st.write(f"**Soal {i+1}:** {detail.get('question')}")
             st.write(f"Jawaban Anda: {detail.get('user_answer')}")
             st.write(f"Jawaban Benar: {detail.get('correct_answer')}")
             if detail.get('is_correct'):
                 st.success("✔️ Benar")
             else:
                 st.error("❌ Salah")
             st.markdown("---")
else:
    print(">>> KONDISI TAMPILKAN HASIL TIDAK TERPENUHI")

# --- Footer (Opsional) ---
st.markdown("---")
st.markdown("Dibuat dengan Streamlit & Llama 3")