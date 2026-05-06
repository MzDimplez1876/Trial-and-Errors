import streamlit as st
import pandas as pd
import re
from docx import Document
import PyPDF2

st.title("📊 Backup & Antivirus Compliance Dashboard")

# -------- FILE READERS -------- #

def read_pdf(file):
    text = ""
    reader = PyPDF2.PdfReader(file)
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

def read_docx(file):
    doc = Document(file)
    return "\n".join([p.text for p in doc.paragraphs])

def read_excel(file):
    df = pd.read_excel(file)
    return df.astype(str).to_string()

# -------- EXTRACTION LOGIC -------- #

def extract_data(text):
    text_lower = text.lower()

    data = {
        "Customer": "Unknown",
        "Computers": "Unknown",
        "Servers": "Unknown",
        "Backup Software": "Unknown",
        "Backup Status": "Unknown",
        "Antivirus Version": "Unknown",
        "Antivirus Status": "Unknown",
        "Compliance": "Non-Compliant"
    }

    # Customer
    match = re.search(r"(customer|client)\s*[:\-]\s*(.+)", text, re.IGNORECASE)
    if match:
        data["Customer"] = match.group(2).strip()

    # Computers
    comp = re.search(r"(\d+)\s*(computers|pcs|workstations)", text_lower)
    if comp:
        data["Computers"] = comp.group(1)

    # Servers
    serv = re.search(r"(\d+)\s*(servers)", text_lower)
    if serv:
        data["Servers"] = serv.group(1)

    # Backup software
    if "veeam" in text_lower:
        data["Backup Software"] = "Veeam"
    elif "acronis" in text_lower:
        data["Backup Software"] = "Acronis"

    # Backup status
    if "backup successful" in text_lower:
        data["Backup Status"] = "Successful"
    elif "backup failed" in text_lower:
        data["Backup Status"] = "Failed"

    # Antivirus version
    av = re.search(r"(version|ver)\s*[:\-]?\s*([\d\.]+)", text_lower)
    if av:
        data["Antivirus Version"] = av.group(2)

    # Antivirus status
    if "threat detected" in text_lower:
        data["Antivirus Status"] = "Threat Detected"
    elif "quarantined" in text_lower:
        data["Antivirus Status"] = "Quarantined"
    elif "clean" in text_lower or "no threats" in text_lower:
        data["Antivirus Status"] = "Clean"

    # Compliance
    if data["Backup Status"] == "Successful" and data["Antivirus Status"] == "Clean":
        data["Compliance"] = "Compliant"

    return data

# -------- FILE UPLOAD -------- #

uploaded_files = st.file_uploader(
    "Upload Reports (PDF, Excel, Word)", 
    accept_multiple_files=True
)

if uploaded_files:
    results = []

    for file in uploaded_files:
        try:
            if file.name.endswith(".pdf"):
                text = read_pdf(file)
            elif file.name.endswith(".docx"):
                text = read_docx(file)
            elif file.name.endswith(".xlsx"):
                text = read_excel(file)
            else:
                continue

            data = extract_data(text)
            data["File"] = file.name
            results.append(data)

        except Exception as e:
            results.append({
                "File": file.name,
                "Error": str(e)
            })

    df = pd.DataFrame(results)

    st.subheader("📋 Consolidated Report")
    st.dataframe(df)

    # Download
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Download Report",
        csv,
        "compliance_report.csv",
        "text/csv"
    )