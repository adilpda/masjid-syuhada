# 🕌 Chatbot RAG Cagar Budaya Masjid Syuhada Yogyakarta

Aplikasi RAG (Retrieval-Augmented Generation) berbasis Streamlit, LangChain, FAISS, dan Google Gemini untuk publikasi data metadata arsitektur dan inventarisasi kerusakan Masjid Peringatan Syuhada Yogyakarta.

## 📁 Struktur Repositori

```text
masjid-syuhada-rag/
├── .streamlit/
│   └── secrets.toml
├── data/
│   └── Metadata_DublinCore_RAG_Masjid_Syuhada.xlsx
├── app.py
├── requirements.txt
└── README.md
```

## 🚀 Panduan Jalankan di Lokal

1. **Install dependensi**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Atur API Key**:
   Buka `.streamlit/secrets.toml` dan ganti `GEMINI_API_KEY` dengan API Key dari [Google AI Studio](https://aistudio.google.com/).

3. **Jalankan Streamlit**:
   ```bash
   streamlit run app.py
   ```

## 🌐 Panduan Deploy ke Streamlit Cloud

1. Upload seluruh isi project ini ke repositori GitHub.
2. Masuk ke [share.streamlit.io](https://share.streamlit.io/).
3. Buka **Settings > Secrets** pada aplikasi Streamlit Cloud Anda, lalu tambahkan:
   ```toml
   GEMINI_API_KEY = "API_KEY_GEMINI_ANDA"
   ```
4. Deploy aplikasi!
