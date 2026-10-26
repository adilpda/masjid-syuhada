import os
import streamlit as st
import pandas as pd
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI

# -----------------------------------------------------------------------------
# 1. Konfigurasi Halaman & Tema Streamlit
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Asisten Cagar Budaya Masjid Syuhada",
    page_icon="🕌",
    layout="wide"
)

st.title("🕌 Asisten RAG Cagar Budaya Masjid Syuhada Yogyakarta")
st.caption("Aplikasi Publikasi Metadata Arsitektur & Inventarisasi Kerusakan berbasis Dublin Core (DCMI) & Google Gemini RAG")

# -----------------------------------------------------------------------------
# 2. Pengaturan API Key & Model Google Gemini
# -----------------------------------------------------------------------------
api_key = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")

if not api_key:
    st.error("🔑 API Key belum ditemukan! Silahkan atur GEMINI_API_KEY pada file .streamlit/secrets.toml atau Streamlit Cloud Secrets.")
    st.stop()

# Initialize Embeddings & LLM
embeddings = GoogleGenerativeAIEmbeddings(
    model="models/embedding-001",
    google_api_key=api_key
)

llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    google_api_key=api_key,
    temperature=0.2
)

# -----------------------------------------------------------------------------
# 3. Fungsi Pemuatan & Vektorisasi Data Excel (Caching)
# -----------------------------------------------------------------------------
@st.cache_resource(show_spinner="Menyiapkan Vector Database dari Dataset Metadata...")
def load_and_build_vectorstore(excel_path: str):
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
            documents.append(Document(page_content=content, metadata=metadata))

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
            documents.append(Document(page_content=content, metadata=metadata))

    # Build FAISS Vector Database
    vectorstore = FAISS.from_documents(documents, embeddings)
    return vectorstore

# Path Excel Dataset
excel_file_path = "data/Metadata_DublinCore_RAG_Masjid_Syuhada.xlsx"
vectorstore = load_and_build_vectorstore(excel_file_path)
retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

# -----------------------------------------------------------------------------
# 4. Antarmuka Chatbot Streamlit
# -----------------------------------------------------------------------------
st.sidebar.markdown("### 📋 Pusat Data Cagar Budaya")
st.sidebar.info(
    "**Dataset Terintegrasi:**\n"
    "- Dokumen 2: Gambar Teknis & Elemen Arsitektur\n"
    "- Dokumen 4: Inventarisasi Kerusakan\n"
    "- Standar Metadata: Dublin Core (DCMI)"
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
            retrieved_docs = retriever.invoke(user_input)
            context_text = "\n\n".join([doc.page_content for doc in retrieved_docs])
            
            # Prompt Construction
            prompt_text = f"""Anda adalah asisten ahli Cagar Budaya dan Arsitektur resmi untuk Masjid Peringatan Syuhada Yogyakarta.
Tugas Anda adalah menjawab pertanyaan publik, peneliti, atau pemangku kepentingan berdasarkan konteks metadata berikut:

{context_text}

Pertanyaan Pengguna: {user_input}

Petunjuk Jawaban:
1. Jawab pertanyaan dengan ramah, jelas, lugas, dan akurat berdasarkan data konteks yang diberikan.
2. Sertakan rincian penting seperti Kode Elemen/Kerusakan (dc:identifier), Lokasi Ruang (dc:coverage), Material, dan Tingkat Signifikansi Cagar Budaya / Urgensi Perbaikan jika relevan.
3. Jika jawaban tidak ada pada konteks metadata di atas, sampaikan dengan santun bahwa informasi spesifik tersebut belum tercatat dalam database inventarisasi saat ini."""

            # LLM Generation Step
            response = llm.invoke(prompt_text)
            answer = response.content
            
            st.write(answer)
            
            # Tampilkan Referensi Sumber Metadata (RAG Transparency)
            with st.expander("🔍 Lihat Referensi Metadata DCMI yang Dipakai AI"):
                for idx, doc in enumerate(retrieved_docs, 1):
                    meta = doc.metadata
                    st.markdown(f"**[{idx}] {meta.get('identifier', 'Doc')} - {meta.get('title', '')}**")
                    st.markdown(f"- **Lokasi:** {meta.get('coverage', '-')}")
                    st.markdown(f"- **Sumber:** {meta.get('source', '-')}")
                    st.caption(f"Context: {doc.page_content}")
                    st.divider()

    st.session_state.messages.append({"role": "assistant", "content": answer})
