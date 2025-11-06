import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime
import pdfkit  # Für PDF-Export (pip install pdfkit, wkhtmltopdf separat installieren)

# Datenbank initialisieren
conn = sqlite3.connect('komda_b3.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS klienten (id INTEGER PRIMARY KEY, name TEXT, pflegegrad INTEGER, budget_entlastung REAL, budget_verhinderung REAL, verwendet REAL)''')
c.execute('''CREATE TABLE IF NOT EXISTS mitarbeiter (id INTEGER PRIMARY KEY, name TEXT, qualifikation TEXT, urlaub REAL)''')
c.execute('''CREATE TABLE IF NOT EXISTS einsaetze (id INTEGER PRIMARY KEY, klient_id INTEGER, mitarbeiter_id INTEGER, datum TEXT, leistung TEXT, stunden REAL, kosten REAL)''')
conn.commit()

st.title("Komda® B3 Clone – Deine freie Betreuungssoftware")
st.sidebar.title("Navigation")
seite = st.sidebar.radio("Module", ["Klientenverwaltung", "Mitarbeiter & Planung", "Abrechnung & Depot", "Mobile Einsatz & Dokumentation", "Reporting & Statistiken", "DMS & Formulare"])

if seite == "Klientenverwaltung":
    st.header("Klienten verwalten (§45b, §39 usw.)")
    name = st.text_input("Name")
    pflegegrad = st.selectbox("Pflegegrad", [1,2,3,4,5])
    budget_entlastung = st.number_input("Entlastungsbetrag §45b", value=125.00)
    budget_verhinderung = st.number_input("Verhinderungspflege §39", value=1612.00)
    if st.button("Klient hinzufügen"):
        c.execute("INSERT INTO klienten (name, pflegegrad, budget_entlastung, budget_verhinderung, verwendet) VALUES (?, ?, ?, ?, 0)", (name, pflegegrad, budget_entlastung, budget_verhinderung))
        conn.commit()
        st.success("Klient hinzugefügt!")
    df_klienten = pd.read_sql("SELECT * FROM klienten", conn)
    st.dataframe(df_klienten)

elif seite == "Mitarbeiter & Planung":
    st.header("Personalmanagement & Dienstplan")
    ma_name = st.text_input("Mitarbeiter Name")
    quali = st.text_input("Qualifikation")
    if st.button("MA hinzufügen"):
        c.execute("INSERT INTO mitarbeiter (name, qualifikation, urlaub) VALUES (?, ?, 0)", (ma_name, quali))
        conn.commit()
    df_ma = pd.read_sql("SELECT * FROM mitarbeiter", conn)
    st.dataframe(df_ma)
    st.subheader("Einfacher Dienstplan")
    datum = st.date_input("Datum")
    # Hier könnte Kalender-Integration hin (z.B. mit streamlit-calendar)

elif seite == "Abrechnung & Depot":
    st.header("Abrechnung & Budget-Depot")
    klient_id = st.number_input("Klient ID", min_value=1)
    leistung = st.selectbox("Leistung", ["Einkauf", "Begleitung Arzt", "Haushaltshilfe"])
    stunden = st.number_input("Stunden")
    kosten = stunden * 25.00  # Beispieltarif
    if st.button("Einsatz abrechnen"):
        c.execute("INSERT INTO einsaetze (klient_id, datum, leistung, stunden, kosten) VALUES (?, ?, ?, ?, ?)", (klient_id, datetime.now(), leistung, stunden, kosten))
        c.execute("UPDATE klienten SET verwendet = verwendet + ? WHERE id = ?", (kosten, klient_id))
        conn.commit()
        st.success(f"Abrechnung: {kosten} €")
    df_einsaetze = pd.read_sql("SELECT * FROM einsaetze", conn)
    st.dataframe(df_einsaetze)

elif seite == "Mobile Einsatz & Dokumentation":
    st.header("Mobile App Simulation")
    st.info("Öffne das auf Handy – Foto-Upload & Sprachnotiz simulieren")
    uploaded_file = st.file_uploader("Foto/Doku hochladen")
    if uploaded_file:
        st.image(uploaded_file)
    sprache = st.text_area("Sprachdokumentation")
    if st.button("Sync & Unterschrift"):
        st.success("Echtzeit-Sync simuliert!")

elif seite == "Reporting & Statistiken":
    st.header("Erweitertes Reporting")
    df = pd.read_sql("SELECT * FROM einsaetze", conn)
    fig = px.bar(df, x='datum', y='kosten', title="Umsatz pro Tag")
    st.plotly_chart(fig)
    ampelfarbe = "grün" if df['kosten'].sum() < 5000 else "rot"
    st.metric("Ampel Zahlungen", ampelfarbe)

elif seite == "DMS & Formulare":
    st.header("Dokumentenmanagement & Generator")
    text = st.text_area("Serienbrief")
    if st.button("PDF generieren"):
        html = f"<h1>Rechnung</h1><p>{text}</p>"
        pdfkit.from_string(html, 'rechnung.pdf')
        st.download_button("Download PDF", 'rechnung.pdf')

st.sidebar.info("Das ist ein voller B3-Prototyp! Erweitere mich mit mehr Code. Für Produktion: Hosting auf Streamlit Cloud oder Heroku.")
