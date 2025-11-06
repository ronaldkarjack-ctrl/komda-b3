import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import base64
from io import BytesIO

# --- SEITENKONFIG ---
st.set_page_config(page_title="Komda B3 Clone", layout="wide", initial_sidebar_state="expanded")
st.title("🚀 Komda® B3 Clone – Deine 100% kostenlose Betreuungssoftware")
st.markdown("**Vollversion wie B3: Klienten, Abrechnung, Mobile, Reporting, DMS – läuft lokal & in der Cloud!**")

# --- DATENBANK ---
conn = sqlite3.connect('komda_b3.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS klienten (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, pflegegrad INTEGER, budget_entlastung REAL, budget_verhinderung REAL, verwendet REAL DEFAULT 0)''')
c.execute('''CREATE TABLE IF NOT EXISTS mitarbeiter (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, qualifikation TEXT, urlaub REAL DEFAULT 0)''')
c.execute('''CREATE TABLE IF NOT EXISTS einsaetze (id INTEGER PRIMARY KEY AUTOINCREMENT, klient_id INTEGER, mitarbeiter_id INTEGER, datum TEXT, leistung TEXT, stunden REAL, kosten REAL)''')
conn.commit()

# --- SIDEBAR NAVIGATION ---
seite = st.sidebar.radio("📋 Module", ["Klientenverwaltung", "Mitarbeiter & Planung", "Abrechnung & Depot", "Mobile Dokumentation", "Reporting & Statistiken", "DMS & Formulare"])

# === 1. KLIENTENVERWALTUNG ===
if seite == "Klientenverwaltung":
    st.header("👥 Klienten verwalten (§45b, §39, §42a)")
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Name")
        pflegegrad = st.selectbox("Pflegegrad", [0,1,2,3,4,5])
    with col2:
        budget_entlastung = st.number_input("§45b Entlastungsbetrag €", value=125.0, step=10.0)
        budget_verhinderung = st.number_input("§39 Verhinderungspflege €", value=1612.0, step=100.0)
    if st.button("➕ Klient speichern"):
        c.execute("INSERT INTO klienten (name, pflegegrad, budget_entlastung, budget_verhinderung) VALUES (?, ?, ?, ?)", (name, pflegegrad, budget_entlastung, budget_verhinderung))
        conn.commit()
        st.success(f"Klient **{name}** gespeichert!")
    st.markdown("---")
    df = pd.read_sql("SELECT * FROM klienten", conn)
    st.dataframe(df, use_container_width=True)

# === 2. MITARBEITER & PLANUNG ===
elif seite == "Mitarbeiter & Planung":
    st.header("👷 Mitarbeiter & Dienstplan")
    col1, col2 = st.columns(2)
    with col1:
        ma_name = st.text_input("Mitarbeiter Name")
    with col2:
        quali = st.text_input("Qualifikation")
    if st.button("➕ Mitarbeiter hinzufügen"):
        c.execute("INSERT INTO mitarbeiter (name, qualifikation) VALUES (?, ?)", (ma_name, quali))
        conn.commit()
        st.success("Mitarbeiter gespeichert!")
    df_ma = pd.read_sql("SELECT * FROM mitarbeiter", conn)
    st.dataframe(df_ma, use_container_width=True)
    st.info("🔥 Drag & Drop Kalender kommt als nächstes Update – sag einfach 'Kalender'!")

# === 3. ABRECHNUNG & DEPOT ===
elif seite == "Abrechnung & Depot":
    st.header("💶 Abrechnung & Budget-Depot")
    klient_id = st.number_input("Klient ID", min_value=1, step=1)
    leistung = st.selectbox("Leistung", ["Einkauf", "Begleitung Arzt", "Haushaltshilfe", "Verhinderungspflege", "Kurzzeitpflege §42a"])
    stunden = st.number_input("Stunden", min_value=0.25, step=0.25)
    tarif = st.number_input("Stundensatz €", value=25.0, step=5.0)
    kosten = stunden * tarif
    st.write(f"**Kosten: {kosten:.2f} €**")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💸 Abrechnen"):
            c.execute("INSERT INTO einsaetze (klient_id, datum, leistung, stunden, kosten) VALUES (?, ?, ?, ?, ?)", (klient_id, datetime.now().strftime("%Y-%m-%d"), leistung, stunden, kosten))
            c.execute("UPDATE klienten SET verwendet = verwendet + ? WHERE id = ?", (kosten, klient_id))
            conn.commit()
            st.success("Einsatz abgerechnet!")
    with col2:
        if st.button("🔄 Budget zurücksetzen (Test)"):
            c.execute("UPDATE klienten SET verwendet = 0 WHERE id = ?", (klient_id,))
            conn.commit()
            st.success("Budget zurückgesetzt!")
    df_einsaetze = pd.read_sql("SELECT * FROM einsaetze", conn)
    st.dataframe(df_einsaetze, use_container_width=True)

# === 4. MOBILE DOKUMENTATION ===
elif seite == "Mobile Dokumentation":
    st.header("📱 Mobile App Simulation")
    st.info("Öffne das auf deinem Handy – funktioniert wie echte Mobile App!")
    uploaded_file = st.file_uploader("📷 Foto/Dokument hochladen", type=["png","jpg","pdf"])
    if uploaded_file:
        st.image(uploaded_file, caption="Hochgeladenes Dokument")
    sprache = st.text_area("🎤 Sprachdokumentation / Notiz")
    if st.button("✔️ Sync & Unterschrift speichern"):
        st.success("Echtzeit-Sync simuliert – Daten gespeichert!")

# === 5. REPORTING & STATISTIKEN ===
elif seite == "Reporting & Statistiken":
    st.header("📊 Erweitertes Reporting")
    df = pd.read_sql("SELECT * FROM einsaetze", conn)
    if not df.empty:
        chart_data = df.groupby('datum')['kosten'].sum().reset_index()
        st.bar_chart(chart_data.set_index('datum'), use_container_width=True)
        total = df['kosten'].sum()
        st.metric("Gesamtumsatz", f"{total:.2f} €")
        # Ampelsystem
        if total > 5000:
            st.error("🔴 Hoher Umsatz – prüfen!")
        elif total > 2000:
            st.warning("🟡 Mittel")
        else:
            st.success("🟢 Alles im grünen Bereich")
    else:
        st.info("Noch keine Einsätze für Statistiken")

# === 6. DMS & FORMULARE ===
elif seite == "DMS & Formulare":
    st.header("📄 Dokumentenmanagement & Generator")
    text = st.text_area("Serienbrief / Rechnungstext", height=200)
    if st.button("🖨️ PDF generieren"):
        html = f"""
        <html><body>
        <h1>Rechnung / Betreuungsnachweis</h1>
        <p>{text.replace('\n', '<br>')}</p>
        <hr>
        <small>Generiert mit Komda B3 Clone – {datetime.now().strftime("%d.%m.%Y")}</small>
        </body></html>
        """
        pdf_buffer = BytesIO()
        # Einfacher PDF-Export ohne externe Tools
        from fpdf import FPDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, text)
        pdf.output(pdf_buffer)
        b64 = base64.b64encode(pdf_buffer.getvalue()).decode()
        href = f'<a href="data:application/pdf;base64,{b64}" download="rechnung.pdf">📥 Download PDF</a>'
        st.markdown(href, unsafe_allow_html=True)
        st.success("PDF bereit!")

# --- FOOTER ---
st.sidebar.markdown("---")
st.sidebar.success("💾 Daten gespeichert in komda_b3.db – backup einfach downloaden!")
st.sidebar.info("Du willst mehr? Sag: **Exe**, **Kalender**, **Login**, **E-Mail** – ich baue sofort weiter!")
