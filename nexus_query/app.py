import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory

import requests
import streamlit as st
from scripts.utils import logger

st.set_page_config("Nexus Query", page_icon="📝")

# Values
if "messages" not in st.session_state:
    st.session_state["messages"] = []

if "uploaded" not in st.session_state:
    st.session_state["uploaded"] = False

API_BASE_URL = "http://127.0.0.1:8000"
url_create_documents = f"{API_BASE_URL}/api/v1/create_documents_add_vector_store"
url_main = f"{API_BASE_URL}/api/v1/chat"
# health_check = requests.get(f"{API_BASE_URL}/health")


# Chat function
def chat_stream(prompt):
    """Streaming API response from agent"""
    response = requests.get(
        url_main,
        json={
            "query": prompt,
        },
        stream=True,
    )
    for line in response.iter_lines():
        if not line.strip():
            continue
        chunk = json.loads(line)
        # msg_type = chunk.get("type", "")
        content = chunk.get("content", "")
        yield content


# Sidebar interface
with st.sidebar:
    with st.container(border=True, gap="medium"):
        st.markdown("**Welcome to Nexus Query!**")
        st.markdown(
            "You can upload your file and have a conversation over your documents"
        )
    with st.container(border=True, gap="medium"):
        with st.spinner("", show_time=True, width=30):
            uploaded_pdf = st.file_uploader(
                "Upload your file",
                type="pdf",
            )
            if uploaded_pdf and not st.session_state["uploaded"]:
                try:
                    with TemporaryDirectory(dir="nexus_query/data") as tmp_dir:
                        pdf_path = Path(tmp_dir, uploaded_pdf.name)
                        with open(pdf_path, "wb") as pdf:
                            pdf.write(uploaded_pdf.getvalue())
                        requests.post(
                            url_create_documents, params={"pdf_path": str(pdf_path)}
                        )
                    logger.debug("Documents added to vector store.")
                    st.session_state["uploaded"] = True
                except Exception as e:
                    logger.warning(f"Upload failed: {e}")
    if os.path.isdir("nexus_query/data/" + os.environ["DB_NAME"]):
        documents = [
            f
            for f in os.listdir("nexus_query/data/" + os.environ["DB_NAME"])
            if os.path.isdir(
                os.path.join("nexus_query/data/" + os.environ["DB_NAME"], f)
            )
        ]
        if documents:
            document_info = st.success(
                f"{os.environ['DB_NAME']} database has documents"
            )
        else:
            document_info = st.warning(
                f"{os.environ['DB_NAME']} database has no document"
            )


# Chat interface
if "messages" not in st.session_state:
    st.session_state["messages"] = []

for message in st.session_state["messages"]:
    with st.chat_message(message["role"]):
        st.write(message["content"])

if prompt := st.chat_input("Type here"):
    st.session_state["messages"].append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        response = st.write_stream(chat_stream(prompt))
        st.session_state["messages"].append({"role": "assistant", "content": response})
