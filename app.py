import os
import streamlit as st
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from google import genai

# -----------------------------------------------------------------------------
# 1. Konfigurasi Halaman & Tema Streamlit
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Asisten Cagar Budaya Masjid Syuhada",
    page_icon="🕌",
    layout="wide"
)

st.title("🕌 Asisten RAG Cagar Budaya Masjid Syuhada Yogyakarta")
st.caption("Aplikasi Publikasi Metadata Arsitektur & Inventarisasi Kerusakan berbasis Dublin Core (DCMI) & Google Gemini AI")

# -----------------------------------------------------------------------------
# 2. Pengaturan API Key & Klien Google GenAI Resmi
# -----------------------------------------------------------------------------
api_key = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")

if not api_key:
    st.error("🔑 API Key belum ditemukan! Silahkan atur GEMINI_API_KEY pada file .streamlit/secrets.toml atau Streamlit Cloud Secrets.")
    st.stop()

# Inisialisasi klien resmi Google GenAI
client = genai.Client(api_key=api_key)

# -----------------------------------------------------------------------------
# 3. Pemuatan Data & Mesin Pencari TF-IDF (Lokal, Cepat, & Stabil)
# -----------------------------------------------------------------------------
@st.cache_resource(show_spinner="Memuat dan Mengindeks Dataset Metadata...")
def load_and_prepare_search_engine(excel_path: str):
    if not os.path.exists(excel_path):
        st.error(f"File data tidak ditemukan pada path: {excel_path}")
        st.stop()
        
    xls = pd.ExcelFile(excel_path)
    documents = []

    # Read Tab Elemen Arsitektur
    if "Metadata Elemen Arsitektur" in xls.sheet_names:
        df_elem = pd.read_excel(xls, "Metadata Elemen Arsitektur")
        for _, row in df_elem.iterrows():
            content = str(row.get("RAG_Summary_Context", ""))
            metadata = {
                "identifier": str(row.get("Identifier (dc:identifier)", "")),
                "title": str(row.get("Title (dc:title)", "")),
                "type": str(row.get("Type (dc:type)", "")),
                "coverage": str(row.get("Spatial_Coverage (dc:coverage)", "")),
                "significance": str(row.get("Significance_Level (dc:rights)", "")),
                "source": "Dokumen 2 (Gambar Teknis & Identifikasi)"
            }
            documents.append({"page_content": content, "metadata": metadata})

    # Read Tab Kerusakan Elemen
    if "Metadata Kerusakan Elemen" in xls.sheet_names:
        df_damg = pd.read_excel(xls, "Metadata Kerusakan Elemen")
        for _, row in df_damg.iterrows():
            content = str(row.get("RAG_Summary_Context", ""))
            metadata = {
                "identifier": str(row.get("Identifier (dc:identifier)", "")),
                "title": str(row.get("Jenis Kerusakan (dc:title)", "")),
                "type": str(row.get("Kategori Elemen (dc:type)", "")),
                "coverage": str(row.get("Spatial_Coverage (dc:coverage)", "")),
                "urgency": str(row.get("Status / Urgensi Penanganan", "")),
                "source": str(row.get("Source_Document (dc:source)", "Dokumen 4"))
            }
            documents.append({"page_content": content, "metadata": metadata})

    # Buat TF-IDF Vectorizer Matrix untuk Pencarian Lokal
    corpus = [doc["page_content"] for doc in documents]
    vectorizer = TfidfVectorizer().fit(corpus)
    doc_vectors = vectorizer.transform(corpus)
    
    return documents, vectorizer, doc_vectors

excel_file_path = "data/Metadata_DublinCore_RAG_Masjid_Syuhada.xlsx"
documents, vectorizer, doc_vectors = load_and_prepare_search_engine(excel_file_path)

def search_documents(query, top_k=4):
    query_vector = vectorizer.transform([query])
    similarities = cosine_similarity(query_vector, doc_vectors).flatten()
    top_indices = similarities.argsort()[::-1][:top_k]
    
    results = []
    for idx in top_indices:
        if similarities[idx] > 0.0:
            results.append(documents[idx])
    return results

# -----------------------------------------------------------------------------
# 4. Antarmuka Chatbot Streamlit
# -----------------------------------------------------------------------------
st.sidebar.markdown("### 📋 Pusat Data Cagar Budaya")
st.sidebar.info(
    "**Dataset Terintegrasi:**\n"
    "- Dokumen 2: Gambar Teknis & Elemen Arsitektur\n"
    "- Dokumen 4: Inventarisasi Kerusakan\n"
    "- Standar Metadata: Dublin Core (DCMI)\n"
    "- Mesin Pencari: TF-IDF Semantic Index"
)

# Inisialisasi Riwayat Percakapan
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "Halo! Saya Asisten AI Masjid Syuhada. Silakan tanyakan hal-hal mengenai elemen arsitektur, material, status cagar budaya, maupun data kerusakan teknis masjid."}
    ]

# Tampilkan Pesan Percakapan
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# Input Pengguna
if user_input := st.chat_input("Tanyakan sesuatu (misal: Bagaimana spesifikasi pelengkung di foyer? atau Apa kerusakan pada kubah utama?)"):
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.chat_message("user").write(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Mencari dalam Metadata Cagar Budaya..."):
            # Retrieval Step
            retrieved_docs = search_documents(user_input, top_k=4)
            context_text = "\n\n".join([doc["page_content"] for doc in retrieved_docs]) if retrieved_docs else "Tidak ada dokumen yang cocok."
            
            # Prompt Construction
            prompt_text = f"""Anda adalah asisten ahli Cagar Budaya dan Arsitektur resmi untuk Masjid Peringatan Syuhada Yogyakarta.
Tugas Anda adalah menjawab pertanyaan publik, peneliti, atau pemangku kepentingan berdasarkan konteks metadata berikut:

{context_text}

Pertanyaan Pengguna: {user_input}

Petunjuk Jawaban:
1. Jawab pertanyaan dengan ramah, jelas, lugas, dan akurat berdasarkan data konteks yang diberikan.
2. Sertakan rincian penting seperti Kode Elemen/Kerusakan (dc:identifier), Lokasi Ruang (dc:coverage), Material, dan Tingkat Signifikansi Cagar Budaya / Urgensi Perbaikan jika relevan.
3. Jika jawaban tidak ada pada konteks metadata di atas, sampaikan dengan santun bahwa informasi spesifik tersebut belum tercatat dalam database inventarisasi saat ini."""

            # LLM Generation Step menggunakan model gemini-2.5-flash
            try:
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt_text
                )
                answer = response.text
            except Exception as e:
                answer = f"Terjadi kesalahan saat memproses permintaan ke Gemini API: {str(e)}"

            st.write(answer)
            
            # Tampilkan Referensi Sumber Metadata (RAG Transparency)
            with st.expander("🔍 Lihat Referensi Metadata DCMI yang Dipakai AI"):
                for idx, doc in enumerate(retrieved_docs, 1):
                    meta = doc["metadata"]
                    st.markdown(f"**[{idx}] {meta.get('identifier', 'Doc')} - {meta.get('title', '')}**")
                    st.markdown(f"- **Lokasi:** {meta.get('coverage', '-')}")
                    st.markdown(f"- **Sumber:** {meta.get('source', '-')}")
                    st.caption(f"Context: {doc['page_content']}")
                    st.divider()

    st.session_state.messages.append({"role": "assistant", "content": answer})
