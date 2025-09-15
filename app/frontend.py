import streamlit as st
import requests
import time
import os

# --- Configuration ---
# Set the base URL for your backend API.
# For local development, this would be "http://127.0.0.1:8000".
# For a deployed app, this would be your Cloud Run URL.
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
POLLING_INTERVAL = 3  # seconds

# --- Streamlit UI ---
st.set_page_config(page_title="Legal Document Analyzer", layout="wide")

st.title("Legal Document Analyzer")
st.write("Upload a legal document (PDF or DOCX) to get a summary, pros, cons, and potential loopholes.")

# --- Session State Initialization ---
# Using session_state to store information across reruns
if 'doc_id' not in st.session_state:
    st.session_state.doc_id = None
if 'status' not in st.session_state:
    st.session_state.status = "new"
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None
if 'error' not in st.session_state:
    st.session_state.error = None

# --- File Uploader ---
uploaded_file = st.file_uploader("Choose a document...", type=["pdf", "docx"])

if uploaded_file is not None:
    # Reset state if a new file is uploaded
    st.session_state.doc_id = None
    st.session_state.status = "new"
    st.session_state.analysis_result = None
    st.session_state.error = None

    st.info(f"File selected: `{uploaded_file.name}`")

# --- Analysis Trigger ---
if st.button("Analyze Document", disabled=(uploaded_file is None)):
    with st.spinner("Uploading and starting analysis..."):
        try:
            files = {'file': (uploaded_file.name, uploaded_file, uploaded_file.type)}
            response = requests.post(f"{API_BASE_URL}/upload", files=files, timeout=30)
            response.raise_for_status()  # Raise an exception for bad status codes
            
            upload_data = response.json()
            st.session_state.doc_id = upload_data.get("doc_id")
            st.session_state.status = upload_data.get("status", "processing")
            st.session_state.error = None
            st.success(f"Upload successful! Document ID: `{st.session_state.doc_id}`. Now processing...")

        except requests.exceptions.RequestException as e:
            st.session_state.error = f"Failed to connect to the backend: {e}"
            st.error(st.session_state.error)
        except Exception as e:
            st.session_state.error = f"An unexpected error occurred during upload: {e}"
            st.error(st.session_state.error)

# --- Polling and Status Display ---
if st.session_state.doc_id and st.session_state.status == "processing":
    progress_bar = st.progress(0)
    status_text = st.empty()

    while st.session_state.status == "processing":
        try:
            status_text.text("Checking document status...")
            response = requests.get(f"{API_BASE_URL}/documents/{st.session_state.doc_id}", timeout=10)
            response.raise_for_status()
            
            status_data = response.json()
            current_status = status_data.get("status")

            if current_status == "processed":
                st.session_state.status = "processed"
                st.session_state.analysis_result = status_data.get("analysis")
                status_text.success("Analysis complete!")
                progress_bar.progress(100)
                break  # Exit the loop
            elif current_status == "error":
                st.session_state.error = status_data.get("detail", "An unknown processing error occurred.")
                st.session_state.status = "error"
                status_text.error(st.session_state.error)
                break
            else:
                # Update progress for visual feedback
                progress_bar.progress(50) # Simulate progress
                status_text.info("Document is still processing. Please wait...")
                time.sleep(POLLING_INTERVAL)

        except requests.exceptions.RequestException as e:
            st.session_state.error = f"Failed to get status from the backend: {e}"
            st.session_state.status = "error"
            status_text.error(st.session_state.error)
            break
        except Exception as e:
            st.session_state.error = f"An unexpected error occurred while polling: {e}"
            st.session_state.status = "error"
            status_text.error(st.session_state.error)
            break

# --- Display Results ---
if st.session_state.status == "processed" and st.session_state.analysis_result:
    st.header("Analysis Results")
    result = st.session_state.analysis_result

    st.subheader("Summary")
    st.text_area("", result.get("summary", "Not available."), height=150)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Pros")
        st.text_area("", "\n".join(f"- {pro}" for pro in result.get("pros", [])), height=200)

    with col2:
        st.subheader("Cons")
        st.text_area("", "\n".join(f"- {con}" for con in result.get("cons", [])), height=200)

    st.subheader("Loopholes & Ambiguities")
    st.text_area("", "\n".join(f"- {loophole}" for loophole in result.get("loopholes", [])), height=200)

# --- Display Final Error State ---
elif st.session_state.status == "error":
    st.error(f"Processing failed: {st.session_state.error}")
