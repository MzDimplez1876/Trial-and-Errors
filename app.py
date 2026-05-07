import streamlit as st
import pandas as pd
import re
from docx import Document
import PyPDF2

st.set_page_config(page_title="Compliance Dashboard", layout="wide")
st.title("📊 Backup & Antivirus Compliance Dashboard")

# -------- FUNCTIONS -------- #

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
        "Compliance": "🔴 Non-Compliant"
    }

    if "backup successful" in text_lower:
        data["Backup Status"] = "Successful"

    if "clean" in text_lower or "no threats" in text_lower:
        data["Antivirus Status"] = "Clean"

    if data["Backup Status"] == "Successful" and data["Antivirus Status"] == "Clean":
        data["Compliance"] = "🟢 Compliant"

    return data

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

# -------- MANUAL ENTRY -------- #

st.subheader("✍️ Manual Entry (Accurate Data)")

with st.form("manual_form"):
    customer = st.text_input("Customer Name")
    computers = st.number_input("Number of Computers", 0)
    servers = st.number_input("Number of Servers", 0)
    backup = st.selectbox("Backup Status", ["Successful", "Failed"])
    av = st.selectbox("Antivirus Status", ["Clean", "Threat Detected", "Quarantined"])

    submitted = st.form_submit_button("Add Record")

    manual_data = []

    if submitted:
        compliance = "🔴 Non-Compliant"
        if backup == "Successful" and av == "Clean":
            compliance = "🟢 Compliant"
        elif backup == "Successful":
            compliance = "🟡 Partial"

        manual_data.append({
            "Customer": customer,
            "Computers": computers,
            "Servers": servers,
            "Backup Status": backup,
            "Antivirus Status": av,
            "Compliance": compliance
        })

# -------- FILE UPLOAD -------- #

st.subheader("📂 Upload Reports")

uploaded_files = st.file_uploader("Upload Files", accept_multiple_files=True)

results = []

if uploaded_files:
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
            data["Customer"] = file.name
            results.append(data)

        except:
            continue

# Combine
df = pd.DataFrame(results + manual_data if 'manual_data' in locals() else results)

# -------- DASHBOARD -------- #

if not df.empty:

    st.subheader("📈 Dashboard")

    col1, col2, col3 = st.columns(3)

    col1.metric("Total", len(df))
    col2.metric("Compliant", len(df[df["Compliance"] == "🟢 Compliant"]))
    col3.metric("Non-Compliant", len(df[df["Compliance"] == "🔴 Non-Compliant"]))

    st.bar_chart(df["Compliance"].value_counts())

    # Filter
    st.subheader("🔍 Filter")
    customer_filter = st.selectbox("Select Customer", ["All"] + list(df["Customer"].unique()))

    if customer_filter != "All":
        df = df[df["Customer"] == customer_filter]

    st.dataframe(df)

    # Download
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download Report", csv, "report.csv")

else:
    st.info("Upload files or add manual records to begin.")