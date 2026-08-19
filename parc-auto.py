import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, datetime
from io import BytesIO

# ============================================================
# CONFIGURARE APLICATIE
# ============================================================

st.set_page_config(
    page_title="Administrare Parc Auto",
    page_icon="🚗",
    layout="wide"
)

DB_FILE = "parc_auto.db"


# ============================================================
# FUNCTII BAZA DE DATE
# ============================================================

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def column_exists(conn, table_name, column_name):
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row["name"] for row in cursor.fetchall()]
    return column_name in columns


def add_column_if_missing(conn, table_name, column_name, column_definition):
    if not column_exists(conn, table_name, column_name):
        conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}")
        conn.commit()


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Tabel soferi / utilizatori
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS soferi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nume TEXT NOT NULL,
            prenume TEXT,
            telefon TEXT,
            email TEXT,
            serie_permis TEXT,
            categorie_permis TEXT,
            data_expirare_permis TEXT,
            departament TEXT,
            activ INTEGER DEFAULT 1,
            observatii TEXT
        )
    """)

    # Tabel vehicule
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vehicule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nr_inmatriculare TEXT UNIQUE NOT NULL,
            marca TEXT,
            model TEXT,
            an_fabricatie INTEGER,
            vin TEXT,
            serie_motor TEXT,
            capacitate_cilindrica INTEGER,
            putere_kw REAL,
            putere_cp REAL,
            combustibil TEXT,
            norma_poluare TEXT,
            cutie_viteze TEXT,
            tractiune TEXT,
            culoare TEXT,
            masa_maxima INTEGER,
            dimensiune_anvelope_vara TEXT,
            dimensiune_anvelope_iarna TEXT,
            km_actuali INTEGER,
            data_achizitie TEXT,
            valoare_achizitie REAL,
            expirare_rca TEXT,
            expirare_itp TEXT,
            expirare_casco TEXT,
            expirare_rovinieta TEXT,
            expirare_revizie TEXT,
            sofer_id INTEGER,
            status TEXT DEFAULT 'Activ',
            observatii TEXT,
            FOREIGN KEY(sofer_id) REFERENCES soferi(id)
        )
    """)

    # Tabel cheltuieli
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cheltuieli (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicul_id INTEGER NOT NULL,
            data_cheltuiala TEXT,
            tip_cheltuiala TEXT,
            furnizor TEXT,
            document TEXT,
            km_bord INTEGER,
            cantitate_litri REAL,
            pret_litru REAL,
            suma REAL,
            observatii TEXT,
            FOREIGN KEY(vehicul_id) REFERENCES vehicule(id)
        )
    """)

    # Tabel foi de parcurs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS foi_parcurs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicul_id INTEGER NOT NULL,
            sofer_id INTEGER,
            data_foaie TEXT,
            localitate_plecare TEXT,
            localitate_sosire TEXT,
            scop_deplasare TEXT,
            km_plecare INTEGER,
            km_sosire INTEGER,
            km_parcursi INTEGER,
            ora_plecare TEXT,
            ora_sosire TEXT,
            combustibil_initial REAL,
            combustibil_final REAL,
            alimentare_litri REAL,
            observatii TEXT,
            FOREIGN KEY(vehicul_id) REFERENCES vehicule(id),
            FOREIGN KEY(sofer_id) REFERENCES soferi(id)
        )
    """)

    conn.commit()

    # Migrare pentru baze vechi, daca au tabele create anterior
    vehicule_columns = {
        "an_fabricatie": "INTEGER",
        "vin": "TEXT",
        "serie_motor": "TEXT",
        "capacitate_cilindrica": "INTEGER",
        "putere_kw": "REAL",
        "putere_cp": "REAL",
        "combustibil": "TEXT",
        "norma_poluare": "TEXT",
        "cutie_viteze": "TEXT",
        "tractiune": "TEXT",
        "culoare": "TEXT",
        "masa_maxima": "INTEGER",
        "dimensiune_anvelope_vara": "TEXT",
        "dimensiune_anvelope_iarna": "TEXT",
        "km_actuali": "INTEGER",
        "data_achizitie": "TEXT",
        "valoare_achizitie": "REAL",
        "expirare_casco": "TEXT",
        "expirare_rovinieta": "TEXT",
        "expirare_revizie": "TEXT",
        "sofer_id": "INTEGER",
        "status": "TEXT DEFAULT 'Activ'",
        "observatii": "TEXT"
    }

    for col, definition in vehicule_columns.items():
        add_column_if_missing(conn, "vehicule", col, definition)

    conn.close()


def fetch_df(query, params=()):
    conn = get_connection()
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


def execute_query(query, params=()):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    conn.commit()
    conn.close()


def fetch_all(query, params=()):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows


def fetch_one(query, params=()):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    row = cursor.fetchone()
    conn.close()
    return row


def safe_days_until(date_text):
    if not date_text:
        return None
    try:
        target = datetime.strptime(date_text, "%Y-%m-%d").date()
        return (target - date.today()).days
    except Exception:
        return None


def calculate_status_from_days(days):
    if days is None:
        return "N/A"
    if days < 0:
        return "Expirat"
    if days <= 30:
        return "Expira in 30 zile"
    if days <= 60:
        return "Expira in 60 zile"
    return "OK"


def to_csv_download(df):
    return df.to_csv(index=False).encode("utf-8-sig")


init_db()


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("🚗 Parc Auto")
st.sidebar.caption("Administrare vehicule, soferi, costuri si foi de parcurs")

meniu = st.sidebar.radio(
    "Meniu",
    [
        "📊 Dashboard",
        "🚗 Vehicule",
        "👤 Soferi / Utilizatori",
        "🧾 Foi de parcurs",
        "💰 Cheltuieli",
        "📤 Export date"
    ]
)


# ============================================================
# DASHBOARD
# ============================================================

if meniu == "📊 Dashboard":
    st.title("📊 Dashboard parc auto")

    vehicule_df = fetch_df("""
        SELECT 
            v.id,
            v.nr_inmatriculare,
            v.marca,
            v.model,
            v.km_actuali,
            v.expirare_rca,
            v.expirare_itp,
            v.expirare_casco,
            v.expirare_rovinieta,
            v.expirare_revizie,
            v.status,
    
