import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date

# Configurare pagină web
st.set_page_config(page_title="Administrare Parc Auto", layout="wide", page_icon="🚗")

# Conectare și inițializare bază de date
DB_FILE = "parc_auto.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Tabel Vehicule
    c.execute('''CREATE TABLE IF NOT EXISTS vehicule (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nr_inmatriculare TEXT UNIQUE,
                    marca TEXT,
                    model TEXT,
                    expirare_rca TEXT,
                    expirare_itp TEXT)''')
    # Tabel Cheltuieli
    c.execute('''CREATE TABLE IF NOT EXISTS cheltuieli (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vehicul_id INTEGER,
                    tip_cheltuială TEXT,
                    suma REAL,
                    data_cheltuiala TEXT,
                    FOREIGN KEY(vehicul_id) REFERENCES vehicule(id))''')
    conn.commit()
    conn.close()

init_db()

# Funcții pentru manipularea datelor
def query_db(query, params=(), commit=False):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(query, params)
    if commit:
        conn.commit()
        res = None
    else:
        res = c.fetchall()
    conn.close()
    return res

# Meniu Lateral pentru Navigare
st.sidebar.title("📌 Navigare")
meniu = st.sidebar.radio("Mergi la:", ["📊 Dashboard & Alerte", "🚗 Adaugă / Vezi Vehicule", "💰 Înregistrează Cheltuieli"])

# --- PAGINA 1: DASHBOARD & ALERTE ---
if meniu == "📊 Dashboard & Alerte":
    st.title("📊 Panou de Control & Alerte Acte")
    
    vehicule = query_db("SELECT id, nr_inmatriculare, marca, model, expirare_rca, expirare_itp FROM vehicule")
    
    if not vehicule:
        st.info("Nu există vehicule înregistrate în baza de date. Mergi la secțiunea 'Adaugă / Vezi Vehicule'.")
    else:
        st.subheader("⚠️ Alerte Expirare Acte (Următoarele 30 de zile)")
        today = date.today()
        au_fost_alerte = False
        
        for v in vehicule:
            v_id, nr, marca, model, rca, itp = v
            dt_rca = datetime.strptime(rca, "%Y-%m-%d").date()
            dt_itp = datetime.strptime(itp, "%Y-%m-%d").date()
            
            zile_rca = (dt_rca - today).days
            zile_itp = (dt_itp - today).days
            
            if zile_rca <= 30:
                st.error(f"🚨 RCA expira în {zile_rca} zile pentru {nr} ({marca} {model}) - Dată expirare: {rca}")
                au_fost_alerte = True
            if zile_itp <= 30:
                st.warning(f"⚠️ ITP expira în {zile_itp} zile pentru {nr} ({marca} {model}) - Dată expirare: {itp}")
                au_fost_alerte = True
                
        if not au_fost_alerte:
            st.success("✅ Toate actele mașinilor sunt în regulă pentru următoarele 30 de zile!")
            
        # Sumar financiar simplu
        st.write("---")
        st.subheader("📈 Sumar Total Cheltuieli")
        total_cheltuieli = query_db("SELECT SUM(suma) FROM cheltuieli")[0][0]
        total_cheltuieli = total_cheltuieli if total_cheltuieli else 0.0
        st.metric(label="Total Investit în Flotă (RON)", value=f"{total_cheltuieli:,.2f} RON")

# --- PAGINA 2: ADAUGĂ / VEZI VEHICULE ---
elif meniu == "🚗 Adaugă / Vezi Vehicule":
    st.title("🚗 Management Vehicule")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Adaugă Vehicul Nou")
        with st.form("form_vehicul", clear_on_submit=True):
            nr_inmat = st.text_input("Număr Înmatriculare (ex: B123ABC)").upper().strip()
            marca = st.text_input("Marcă")
            model = st.text_input("Model")
            exp_rca = st.date_input("Dată Expirare RCA")
            exp_itp = st.date_input("Dată Expirare ITP")
            
            submitted = st.form_submit_button("Salvează Vehicul")
            if submitted:
                if nr_inmat and marca and model:
                    try:
                        query_db("INSERT INTO vehicule (nr_inmatriculare, marca, model, expirare_rca, expirare_itp) VALUES (?, ?, ?, ?, ?)",
                                 (nr_inmat, marca, model, str(exp_rca), str(exp_itp)), commit=True)
                        st.success(f"Vehiculul {nr_inmat} a fost salvat cu succes!")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Acest număr de înmatriculare există deja în baza de date!")
                else:
                    st.error("Te rog completează toate câmpurile obligatorii.")
                    
    with col2:
        st.subheader("Listă Vehicule Existente")
        vehicule_date = query_db("SELECT nr_inmatriculare, marca, model, expirare_rca, expirare_itp FROM vehicule")
        if vehicule_date:
            df = pd.DataFrame(vehicule_date, columns=["Nr. Înmatriculare", "Marcă", "Model", "Expirare RCA", "Expirare ITP"])
            st.dataframe(df, use_container_width=True)
        else:
            st.text("Nu există vehicule înregistrate.")

# --- PAGINA 3: ÎNREGISTREAZĂ CHELTUIELI ---
elif meniu == "💰 Înregistrează Cheltuieli":
    st.title("💰 Management Financiar Flotă")
    
    vehicule = query_db("SELECT id, nr_inmatriculare FROM vehicule")
    
    if not vehicule:
        st.warning("Trebuie să adaugi cel puțin un vehicul înainte de a introduce cheltuieli.")
    else:
        opțiuni_vehicule = {v[1]: v[0] for v in vehicule}
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Adaugă o Cheltuială Nouă")
            with st.form("form_cheltuiala", clear_on_submit=True):
                vehicul_selectat = st.selectbox("Alege Vehiculul", list(opțiuni_vehicule.keys()))
                tip_cheltuiala = st.selectbox("Tip Cheltuială", ["Combustibil", "Reparație / Service", "Asigurare", "Rovinietă", "Spălătorie / Altele"])
                suma = st.number_input("Sumă (RON)", min_value=0.1, step=50.0)
                data_ch = st.date_input("Dată Efectuare")
                
                submitted_ch = st.form_submit_button("Înregistrează Cheltuiala")
                if submitted_ch:
                    v_id = opțiuni_vehicule[vehicul_selectat]
                    query_db("INSERT INTO cheltuieli (vehicul_id, tip_cheltuială, suma, data_cheltuiala) VALUES (?, ?, ?, ?)",
                             (v_id, tip_cheltuiala, suma, str(data_ch)), commit=True)
                    st.success("Cheltuiala a fost înregistrată!")
                    st.rerun()
                    
        with col2:
            st.subheader("Istoric Ultimele Cheltuieli")
            istoric = query_db('''SELECT v.nr_inmatriculare, c.tip_cheltuială, c.suma, c.data_cheltuiala 
                                   FROM cheltuieli c 
                                   JOIN vehicule v ON c.vehicul_id = v.id 
                                   ORDER BY c.data_cheltuiala DESC''')
            if istoric:
                df_ist = pd.DataFrame(istoric, columns=["Vehicul", "Tip", "Sumă (RON)", "Dată"])
                st.dataframe(df_ist, use_container_width=True)
            else:
                st.text("Nu există cheltuieli înregistrate în istoric.")
 
