import tkinter as tk
from tkinter import scrolledtext
import threading
import torch
from transformers import pipeline

# Inisialisasi pipeline dengan model LLM
model_id = "meta-llama/Llama-3.2-3B-Instruct"
pipe = pipeline(
    "text-generation",
    model=model_id,
    dtype=torch.bfloat16,
    device_map="auto",
)

# Pesan sistem tetap untuk mengarahkan chatbot
system_message = "You are a pirate chatbot who always responds in pirate speak!"

def extract_assistant_text(generated_data):
    """
    Fungsi ini memeriksa apakah generated_data berupa list pesan.
    Jika ya, cari pesan dengan 'role': 'assistant' dan kembalikan kontennya.
    Jika tidak ditemukan, kembalikan string kosong atau data apa adanya.
    """
    if isinstance(generated_data, list):
        # Asumsikan setiap elemen di generated_data adalah dictionary dengan kunci 'role' dan 'content'
        for item in generated_data:
            if item.get("role") == "assistant":
                # Mengganti baris baru (newline) dengan spasi
                return item["content"].replace("\n", " ")
        # Jika tidak ditemukan 'assistant', kembalikan string kosong
        return ""
    else:
        # Jika bukan list, kembalikan apa adanya (atau bisa disesuaikan dengan kebutuhan)
        return str(generated_data)

def generate_text():
    # Nonaktifkan tombol generate agar tidak terjadi panggilan berulang
    generate_button.config(state=tk.DISABLED)
    
    # Ambil prompt dari kotak teks
    prompt = prompt_entry.get("1.0", tk.END).strip()
    
    # Buat pesan dengan kombinasi pesan sistem dan pesan pengguna
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": prompt},
    ]
    
    try:
        outputs = pipe(messages, max_new_tokens=256)
        # Berdasarkan struktur output, ambil data yang ada di "generated_text"
        raw_output = outputs[0]["generated_text"]
        # Ekstrak hanya teks milik 'assistant'
        generated = extract_assistant_text(raw_output)
    except Exception as e:
        generated = f"Error: {e}"
    
    # Tampilkan hasil pada area output
    output_text.delete("1.0", tk.END)
    output_text.insert(tk.END, generated)
    
    # Aktifkan kembali tombol generate
    generate_button.config(state=tk.NORMAL)

def on_generate():
    # Jalankan fungsi generate_text pada thread terpisah agar GUI tidak freeze
    thread = threading.Thread(target=generate_text)
    thread.start()

# Setup antarmuka menggunakan tkinter
root = tk.Tk()
root.title("Pirate Chatbot Generator")

# Label untuk prompt input
prompt_label = tk.Label(root, text="Enter your prompt:")
prompt_label.pack(pady=(10, 0))

# Kotak teks untuk memasukkan prompt
prompt_entry = tk.Text(root, height=5, width=60)
prompt_entry.pack(padx=10, pady=(0, 10))

# Tombol untuk memicu generasi teks
generate_button = tk.Button(root, text="Generate", command=on_generate)
generate_button.pack(pady=5)

# Label untuk hasil output
output_label = tk.Label(root, text="Generated Text:")
output_label.pack(pady=(10, 0))

# Area teks yang dapat discroll untuk menampilkan output
output_text = scrolledtext.ScrolledText(root, height=10, width=60)
output_text.pack(padx=10, pady=(0, 10))

# Mulai loop utama GUI
root.mainloop()
