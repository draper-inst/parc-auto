import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, datetime

st.set_page_config(page_title="Administrare Parc Auto", page_icon="🚗", layout="wide")
DB_FILE = "parc_auto.db"

# =========================
# BAZA DE DATE
# =========================

def conn_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def execute(sql, params=()):
    conn = conn_db()
    cur = conn.cursor()
    cur.execute(sql, params)
    conn.commit()
    conn.close()


def fetchall(sql, params=()):
    conn = conn_db()
    cur = conn.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()
    return rows


def fetchone(sql, params=()):
    conn = conn_db()
    cur = conn.cursor()
    cur.execute(sql, params)
    row = cur.fetchone()
    conn.close()
    return row


def df_query(sql, params=()):
    conn = conn_db()
    df = pd.read_sql_query(sql, conn, params=params)
    conn.close()
    return df


def column_exists(table, column):
    conn = conn_db()
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table})")
    cols = [r[1] for r in cur.fetchall()]
    conn.close()
    return column in cols


def add_column(table, column, definition):
    if not column_exists(table, column):
        execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def init_db():
    conn = conn_db()
    cur = conn.cursor()

    cur.execute('''
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
    ''')

    cur.execute('''
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
    ''')

    cur.execute('''
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
    ''')

    cur.execute('''
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
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS documente (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicul_id INTEGER NOT NULL,
            tip_document TEXT,
            serie_document TEXT,
            data_emitere TEXT,
            data_expirare TEXT,
            emitent TEXT,
            observatii TEXT,
            FOREIGN KEY(vehicul_id) REFERENCES vehicule(id)
        )
    ''')

    conn.commit()
    conn.close()

    veh_cols = {
        "an_fabricatie": "INTEGER", "vin": "TEXT", "serie_motor": "TEXT",
        "capacitate_cilindrica": "INTEGER", "putere_kw": "REAL", "putere_cp": "REAL",
        "combustibil": "TEXT", "norma_poluare": "TEXT", "cutie_viteze": "TEXT",
        "tractiune": "TEXT", "culoare": "TEXT", "masa_maxima": "INTEGER",
        "dimensiune_anvelope_vara": "TEXT", "dimensiune_anvelope_iarna": "TEXT",
        "km_actuali": "INTEGER", "data_achizitie": "TEXT", "valoare_achizitie": "REAL",
        "expirare_casco": "TEXT", "expirare_rovinieta": "TEXT", "expirare_revizie": "TEXT",
        "sofer_id": "INTEGER", "status": "TEXT DEFAULT 'Activ'", "observatii": "TEXT"
    }
    for col, definition in veh_cols.items():
        add_column("vehicule", col, definition)


def csv_bytes(df):
    return df.to_csv(index=False).encode("utf-8-sig")


def zile_pana_la(data_text):
    if not data_text:
        return None
    try:
        return (datetime.strptime(str(data_text), "%Y-%m-%d").date() - date.today()).days
    except Exception:
        return None


def status_expirare(days):
    if days is None:
        return "N/A"
    if days < 0:
        return "Expirat"
    if days <= 30:
        return "Expira in 30 zile"
    if days <= 60:
        return "Expira in 60 zile"
    return "OK"


def parse_date_or_today(value):
    try:
        if value:
            return datetime.strptime(value, "%Y-%m-%d").date()
    except Exception:
        pass
    return date.today()


init_db()

st.sidebar.title("🚗 Parc Auto")
st.sidebar.caption("Versiune extinsa")
page = st.sidebar.radio(
    "Meniu",
    ["📊 Dashboard", "🚗 Vehicule", "👤 Soferi", "🧾 Foi de parcurs", "💰 Cheltuieli", "📄 Documente", "📤 Export"]
)

if page == "📊 Dashboard":
    st.title("📊 Dashboard parc auto")
    nr_vehicule = fetchone("SELECT COUNT(*) c FROM vehicule")["c"]
    nr_soferi = fetchone("SELECT COUNT(*) c FROM soferi WHERE activ = 1")["c"]
    nr_foi = fetchone("SELECT COUNT(*) c FROM foi_parcurs")["c"]
    total_costuri = fetchone("SELECT COALESCE(SUM(suma),0) total FROM cheltuieli")["total"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Vehicule", nr_vehicule)
    c2.metric("Soferi activi", nr_soferi)
    c3.metric("Foi parcurs", nr_foi)
    c4.metric("Costuri totale", f"{total_costuri:,.2f} RON")
    st.divider()
    st.subheader("⚠️ Alerte documente")
    vehicule = fetchall('''
        SELECT nr_inmatriculare, marca, model, expirare_rca, expirare_itp,
               expirare_casco, expirare_rovinieta, expirare_revizie
        FROM vehicule ORDER BY nr_inmatriculare
    ''')
    alerts = []
    for v in vehicule:
        docs = {"RCA": v["expirare_rca"], "ITP": v["expirare_itp"], "CASCO": v["expirare_casco"], "Rovinieta": v["expirare_rovinieta"], "Revizie": v["expirare_revizie"]}
        for tip, data_exp in docs.items():
            days = zile_pana_la(data_exp)
            stat = status_expirare(days)
            if stat in ["Expirat", "Expira in 30 zile", "Expira in 60 zile"]:
                alerts.append({"Vehicul": v["nr_inmatriculare"], "Marca": v["marca"], "Model": v["model"], "Document": tip, "Data expirare": data_exp, "Zile ramase": days, "Status": stat})
    if alerts:
        df_alerts = pd.DataFrame(alerts)
        st.dataframe(df_alerts, use_container_width=True)
        st.download_button("Descarca alerte CSV", csv_bytes(df_alerts), "alerte.csv", "text/csv")
    else:
        st.success("Nu exista documente expirate sau apropiate de expirare in urmatoarele 60 zile.")
    st.divider()
    st.subheader("Costuri pe vehicul")
    df_costuri = df_query('''
        SELECT v.nr_inmatriculare Vehicul, v.marca Marca, v.model Model,
               COALESCE(SUM(c.suma), 0) AS Cost_total_RON
        FROM vehicule v LEFT JOIN cheltuieli c ON v.id = c.vehicul_id
        GROUP BY v.id ORDER BY Cost_total_RON DESC
    ''')
    st.dataframe(df_costuri, use_container_width=True)

elif page == "🚗 Vehicule":
    st.title("🚗 Vehicule")
    tab1, tab2, tab3 = st.tabs(["Adauga", "Lista", "Editeaza"])
    soferi_rows = fetchall("SELECT id, nume, prenume FROM soferi WHERE activ = 1 ORDER BY nume, prenume")
    sofer_opts = {"Fara sofer": None}
    for s in soferi_rows:
        sofer_opts[f"{s['nume']} {s['prenume'] or ''}".strip()] = s["id"]

    with tab1:
        with st.form("add_vehicle"):
            c1, c2, c3 = st.columns(3)
            with c1:
                nr = st.text_input("Numar inmatriculare *").upper().strip()
                marca = st.text_input("Marca")
                model = st.text_input("Model")
                an_fabricatie = st.number_input("An fabricatie", min_value=1950, max_value=2100, value=2024)
                vin = st.text_input("Serie sasiu / VIN").upper().strip()
                serie_motor = st.text_input("Serie motor")
            with c2:
                capacitate = st.number_input("Capacitate cilindrica cmc", min_value=0, step=100)
                putere_kw = st.number_input("Putere kW", min_value=0.0, step=1.0)
                putere_cp = st.number_input("Putere CP", min_value=0.0, step=1.0)
                combustibil = st.selectbox("Combustibil", ["", "Benzina", "Diesel", "Hibrid", "Plug-in Hybrid", "Electric", "GPL", "CNG"])
                norma = st.selectbox("Norma poluare", ["", "Euro 3", "Euro 4", "Euro 5", "Euro 6", "Electric"])
                cutie = st.selectbox("Cutie viteze", ["", "Manuala", "Automata"])
            with c3:
                tractiune = st.selectbox("Tractiune", ["", "Fata", "Spate", "4x4 / AWD"])
                culoare = st.text_input("Culoare")
                masa = st.number_input("Masa maxima autorizata kg", min_value=0, step=100)
                anvelope_vara = st.text_input("Dimensiune anvelope vara", placeholder="Ex: 205/55 R16")
                anvelope_iarna = st.text_input("Dimensiune anvelope iarna", placeholder="Ex: 205/55 R16")
                km_actuali = st.number_input("Km actuali", min_value=0, step=1000)
            st.divider()
            c4, c5, c6 = st.columns(3)
            with c4:
                data_achizitie = st.date_input("Data achizitie", value=date.today())
                valoare = st.number_input("Valoare achizitie RON", min_value=0.0, step=1000.0)
                sofer_label = st.selectbox("Sofer alocat", list(sofer_opts.keys()))
            with c5:
                expirare_rca = st.date_input("Expirare RCA", value=date.today())
                expirare_itp = st.date_input("Expirare ITP", value=date.today())
                expirare_casco = st.date_input("Expirare CASCO", value=date.today())
            with c6:
                expirare_rovinieta = st.date_input("Expirare rovinieta", value=date.today())
                expirare_revizie = st.date_input("Scadenta revizie", value=date.today())
                status = st.selectbox("Status", ["Activ", "In service", "Vandut", "Casat", "Inactiv"])
            observatii = st.text_area("Observatii")
            if st.form_submit_button("Salveaza vehicul"):
                if not nr:
                    st.error("Numarul de inmatriculare este obligatoriu.")
                else:
                    try:
                        execute('''
                            INSERT INTO vehicule (nr_inmatriculare, marca, model, an_fabricatie, vin, serie_motor,
                            capacitate_cilindrica, putere_kw, putere_cp, combustibil, norma_poluare, cutie_viteze,
                            tractiune, culoare, masa_maxima, dimensiune_anvelope_vara, dimensiune_anvelope_iarna,
                            km_actuali, data_achizitie, valoare_achizitie, expirare_rca, expirare_itp, expirare_casco,
                            expirare_rovinieta, expirare_revizie, sofer_id, status, observatii)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (nr, marca, model, an_fabricatie, vin, serie_motor, capacitate, putere_kw, putere_cp,
                              combustibil, norma, cutie, tractiune, culoare, masa, anvelope_vara, anvelope_iarna,
                              km_actuali, str(data_achizitie), valoare, str(expirare_rca), str(expirare_itp),
                              str(expirare_casco), str(expirare_rovinieta), str(expirare_revizie), sofer_opts[sofer_label], status, observatii))
                        st.success("Vehicul salvat.")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Acest numar de inmatriculare exista deja.")
    with tab2:
        df = df_query('''
            SELECT v.id, v.nr_inmatriculare AS 'Nr inmatriculare', v.marca AS Marca, v.model AS Model,
            v.an_fabricatie AS An, v.vin AS VIN, v.capacitate_cilindrica AS Cilindree, v.putere_kw AS 'Putere kW',
            v.putere_cp AS 'Putere CP', v.combustibil AS Combustibil, v.dimensiune_anvelope_vara AS 'Anvelope vara',
            v.dimensiune_anvelope_iarna AS 'Anvelope iarna', v.km_actuali AS 'Km actuali', v.expirare_rca AS RCA,
            v.expirare_itp AS ITP, v.expirare_casco AS CASCO, v.expirare_rovinieta AS Rovinieta,
            v.expirare_revizie AS Revizie, COALESCE(s.nume || ' ' || IFNULL(s.prenume, ''), '') AS Sofer, v.status AS Status
            FROM vehicule v LEFT JOIN soferi s ON v.sofer_id = s.id ORDER BY v.nr_inmatriculare
        ''')
        st.dataframe(df, use_container_width=True)
        if not df.empty:
            st.download_button("Descarca vehicule CSV", csv_bytes(df), "vehicule.csv", "text/csv")
    with tab3:
        vehicule = fetchall("SELECT id, nr_inmatriculare FROM vehicule ORDER BY nr_inmatriculare")
        if not vehicule:
            st.info("Nu exista vehicule de editat.")
        else:
            opt = {v["nr_inmatriculare"]: v["id"] for v in vehicule}
            selected = st.selectbox("Alege vehicul", list(opt.keys()))
            veh_id = opt[selected]
            row = fetchone("SELECT * FROM vehicule WHERE id = ?", (veh_id,))
            with st.form("edit_vehicle"):
                c1, c2, c3 = st.columns(3)
                with c1:
                    marca_edit = st.text_input("Marca", value=row["marca"] or "")
                    model_edit = st.text_input("Model", value=row["model"] or "")
                    vin_edit = st.text_input("VIN", value=row["vin"] or "")
                    km_edit = st.number_input("Km actuali", min_value=0, value=int(row["km_actuali"] or 0), step=1000)
                with c2:
                    rca_edit = st.date_input("Expirare RCA", value=parse_date_or_today(row["expirare_rca"]))
                    itp_edit = st.date_input("Expirare ITP", value=parse_date_or_today(row["expirare_itp"]))
                    casco_edit = st.date_input("Expirare CASCO", value=parse_date_or_today(row["expirare_casco"]))
                    rov_edit = st.date_input("Expirare rovinieta", value=parse_date_or_today(row["expirare_rovinieta"]))
                with c3:
                    rev_edit = st.date_input("Scadenta revizie", value=parse_date_or_today(row["expirare_revizie"]))
                    status_list = ["Activ", "In service", "Vandut", "Casat", "Inactiv"]
                    status_value = row["status"] if row["status"] in status_list else "Activ"
                    status_edit = st.selectbox("Status", status_list, index=status_list.index(status_value))
                    sofer_keys = list(sofer_opts.keys())
                    default_sofer = "Fara sofer"
                    for k, v in sofer_opts.items():
                        if v == row["sofer_id"]:
                            default_sofer = k
                    sofer_edit = st.selectbox("Sofer alocat", sofer_keys, index=sofer_keys.index(default_sofer))
                obs_edit = st.text_area("Observatii", value=row["observatii"] or "")
                c_save, c_delete = st.columns(2)
                if c_save.form_submit_button("Salveaza modificarile"):
                    execute('''
                        UPDATE vehicule SET marca=?, model=?, vin=?, km_actuali=?, expirare_rca=?, expirare_itp=?,
                        expirare_casco=?, expirare_rovinieta=?, expirare_revizie=?, status=?, sofer_id=?, observatii=? WHERE id=?
                    ''', (marca_edit, model_edit, vin_edit, km_edit, str(rca_edit), str(itp_edit), str(casco_edit),
                          str(rov_edit), str(rev_edit), status_edit, sofer_opts[sofer_edit], obs_edit, veh_id))
                    st.success("Vehicul actualizat.")
                    st.rerun()
                if c_delete.form_submit_button("Sterge vehicul"):
                    execute("DELETE FROM vehicule WHERE id=?", (veh_id,))
                    st.warning("Vehicul sters.")
                    st.rerun()

elif page == "👤 Soferi":
    st.title("👤 Soferi / utilizatori")
    tab1, tab2 = st.tabs(["Adauga", "Lista"])
    with tab1:
        with st.form("add_driver"):
            c1, c2, c3 = st.columns(3)
            with c1:
                nume = st.text_input("Nume *")
                prenume = st.text_input("Prenume")
                telefon = st.text_input("Telefon")
            with c2:
                email = st.text_input("Email")
                serie_permis = st.text_input("Serie permis")
                categorie = st.text_input("Categorie permis", placeholder="B, C, CE")
            with c3:
                expirare = st.date_input("Expirare permis", value=date.today())
                departament = st.text_input("Departament")
                activ = st.checkbox("Activ", value=True)
            observatii = st.text_area("Observatii")
            if st.form_submit_button("Salveaza sofer"):
                if not nume:
                    st.error("Numele este obligatoriu.")
                else:
                    execute('''
                        INSERT INTO soferi (nume, prenume, telefon, email, serie_permis, categorie_permis,
                        data_expirare_permis, departament, activ, observatii) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (nume, prenume, telefon, email, serie_permis, categorie, str(expirare), departament, 1 if activ else 0, observatii))
                    st.success("Sofer salvat.")
                    st.rerun()
    with tab2:
        df = df_query('''
            SELECT id, nume AS Nume, prenume AS Prenume, telefon AS Telefon, email AS Email, serie_permis AS 'Serie permis',
            categorie_permis AS Categorie, data_expirare_permis AS 'Expirare permis', departament AS Departament,
            CASE WHEN activ=1 THEN 'Activ' ELSE 'Inactiv' END AS Status, observatii AS Observatii FROM soferi ORDER BY nume, prenume
        ''')
        st.dataframe(df, use_container_width=True)
        if not df.empty:
            st.download_button("Descarca soferi CSV", csv_bytes(df), "soferi.csv", "text/csv")

elif page == "🧾 Foi de parcurs":
    st.title("🧾 Foi de parcurs")
    tab1, tab2 = st.tabs(["Genereaza foaie", "Istoric"])
    vehicule = fetchall("SELECT id, nr_inmatriculare, marca, model, km_actuali FROM vehicule ORDER BY nr_inmatriculare")
    soferi = fetchall("SELECT id, nume, prenume FROM soferi WHERE activ=1 ORDER BY nume, prenume")
    with tab1:
        if not vehicule:
            st.warning("Adauga intai un vehicul.")
        else:
            veh_opts = {f"{v['nr_inmatriculare']} - {v['marca'] or ''} {v['model'] or ''}".strip(): v for v in vehicule}
            sofer_trip_opts = {"Fara sofer": None}
            for s in soferi:
                sofer_trip_opts[f"{s['nume']} {s['prenume'] or ''}".strip()] = s["id"]
            with st.form("add_trip"):
                c1, c2 = st.columns(2)
                with c1:
                    veh_label = st.selectbox("Vehicul", list(veh_opts.keys()))
                    veh = veh_opts[veh_label]
                    data_foaie = st.date_input("Data", value=date.today())
                    km_start_default = int(veh["km_actuali"] or 0)
                    km_plecare = st.number_input("Km plecare", min_value=0, value=km_start_default, step=1)
                    km_sosire = st.number_input("Km sosire", min_value=0, value=km_start_default, step=1)
                    ora_plecare = st.text_input("Ora plecare", placeholder="08:00")
                    ora_sosire = st.text_input("Ora sosire", placeholder="17:00")
                with c2:
                    sofer_label = st.selectbox("Sofer", list(sofer_trip_opts.keys()))
                    plecare = st.text_input("Localitate plecare")
                    sosire = st.text_input("Localitate sosire")
                    scop = st.text_input("Scop deplasare")
                    combustibil_initial = st.number_input("Combustibil initial litri", min_value=0.0, step=1.0)
                    combustibil_final = st.number_input("Combustibil final litri", min_value=0.0, step=1.0)
                    alimentare = st.number_input("Alimentare litri", min_value=0.0, step=1.0)
                observatii = st.text_area("Observatii")
                if st.form_submit_button("Salveaza foaie"):
                    if km_sosire < km_plecare:
                        st.error("Km sosire nu poate fi mai mic decat Km plecare.")
                    else:
                        km_parcursi = km_sosire - km_plecare
                        execute('''
                            INSERT INTO foi_parcurs (vehicul_id, sofer_id, data_foaie, localitate_plecare, localitate_sosire,
                            scop_deplasare, km_plecare, km_sosire, km_parcursi, ora_plecare, ora_sosire, combustibil_initial,
                            combustibil_final, alimentare_litri, observatii) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (veh["id"], sofer_trip_opts[sofer_label], str(data_foaie), plecare, sosire, scop, km_plecare,
                              km_sosire, km_parcursi, ora_plecare, ora_sosire, combustibil_initial, combustibil_final, alimentare, observatii))
                        execute("UPDATE vehicule SET km_actuali=? WHERE id=?", (km_sosire, veh["id"]))
                        st.success(f"Foaie salvata. Km parcursi: {km_parcursi}")
                        st.rerun()
    with tab2:
        df = df_query('''
            SELECT fp.id, fp.data_foaie AS Data, v.nr_inmatriculare AS Vehicul,
            COALESCE(s.nume || ' ' || IFNULL(s.prenume,''), '') AS Sofer, fp.localitate_plecare AS Plecare,
            fp.localitate_sosire AS Sosire, fp.scop_deplasare AS Scop, fp.km_plecare AS 'Km plecare', fp.km_sosire AS 'Km sosire',
            fp.km_parcursi AS 'Km parcursi', fp.ora_plecare AS 'Ora plecare', fp.ora_sosire AS 'Ora sosire',
            fp.alimentare_litri AS 'Alimentare litri', fp.observatii AS Observatii
            FROM foi_parcurs fp JOIN vehicule v ON fp.vehicul_id = v.id LEFT JOIN soferi s ON fp.sofer_id = s.id
            ORDER BY fp.data_foaie DESC, fp.id DESC
        ''')
        st.dataframe(df, use_container_width=True)
        if not df.empty:
            st.download_button("Descarca foi parcurs CSV", csv_bytes(df), "foi_parcurs.csv", "text/csv")

elif page == "💰 Cheltuieli":
    st.title("💰 Cheltuieli si alimentari")
    tab1, tab2 = st.tabs(["Adauga", "Istoric"])
    vehicule = fetchall("SELECT id, nr_inmatriculare, marca, model FROM vehicule ORDER BY nr_inmatriculare")
    with tab1:
        if not vehicule:
            st.warning("Adauga intai un vehicul.")
        else:
            opts = {f"{v['nr_inmatriculare']} - {v['marca'] or ''} {v['model'] or ''}".strip(): v["id"] for v in vehicule}
            with st.form("add_cost"):
                c1, c2, c3 = st.columns(3)
                with c1:
                    veh_label = st.selectbox("Vehicul", list(opts.keys()))
                    data_ch = st.date_input("Data", value=date.today())
                    tip = st.selectbox("Tip", ["Combustibil", "Revizie", "Reparatie", "Anvelope", "RCA", "CASCO", "Rovinieta", "ITP", "Spalatorie", "Taxe", "Altele"])
                with c2:
                    furnizor = st.text_input("Furnizor")
                    document = st.text_input("Document/factura/bon")
                    km_bord = st.number_input("Km bord", min_value=0, step=100)
                with c3:
                    cantitate = st.number_input("Cantitate litri", min_value=0.0, step=1.0)
                    pret_litru = st.number_input("Pret litru", min_value=0.0, step=0.1)
                    suma = st.number_input("Suma RON", min_value=0.0, step=10.0)
                observatii = st.text_area("Observatii")
                if st.form_submit_button("Salveaza cheltuiala"):
                    if tip == "Combustibil" and cantitate > 0 and pret_litru > 0 and suma == 0:
                        suma = cantitate * pret_litru
                    execute('''
                        INSERT INTO cheltuieli (vehicul_id, data_cheltuiala, tip_cheltuiala, furnizor, document,
                        km_bord, cantitate_litri, pret_litru, suma, observatii) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (opts[veh_label], str(data_ch), tip, furnizor, document, km_bord, cantitate, pret_litru, suma, observatii))
                    st.success("Cheltuiala salvata.")
                    st.rerun()
    with tab2:
        df = df_query('''
            SELECT c.id, c.data_cheltuiala AS Data, v.nr_inmatriculare AS Vehicul, c.tip_cheltuiala AS Tip,
            c.furnizor AS Furnizor, c.document AS Document, c.km_bord AS 'Km bord', c.cantitate_litri AS Litri,
            c.pret_litru AS 'Pret litru', c.suma AS 'Suma RON', c.observatii AS Observatii
            FROM cheltuieli c JOIN vehicule v ON c.vehicul_id = v.id ORDER BY c.data_cheltuiala DESC, c.id DESC
        ''')
        st.dataframe(df, use_container_width=True)
        if not df.empty:
            st.metric("Total cheltuieli", f"{df['Suma RON'].sum():,.2f} RON")
            st.download_button("Descarca cheltuieli CSV", csv_bytes(df), "cheltuieli.csv", "text/csv")

elif page == "📄 Documente":
    st.title("📄 Documente vehicule")
    tab1, tab2 = st.tabs(["Adauga document", "Lista documente"])
    vehicule = fetchall("SELECT id, nr_inmatriculare, marca, model FROM vehicule ORDER BY nr_inmatriculare")
    with tab1:
        if not vehicule:
            st.warning("Adauga intai un vehicul.")
        else:
            opts = {f"{v['nr_inmatriculare']} - {v['marca'] or ''} {v['model'] or ''}".strip(): v["id"] for v in vehicule}
            with st.form("add_doc"):
                c1, c2 = st.columns(2)
                with c1:
                    veh_label = st.selectbox("Vehicul", list(opts.keys()))
                    tip_doc = st.selectbox("Tip document", ["RCA", "ITP", "CASCO", "Rovinieta", "CIV", "Talon", "Contract", "Revizie", "Alt document"])
                    serie_doc = st.text_input("Serie / numar document")
                    emitent = st.text_input("Emitent")
                with c2:
                    data_emitere = st.date_input("Data emitere", value=date.today())
                    data_expirare = st.date_input("Data expirare", value=date.today())
                    observatii = st.text_area("Observatii")
                if st.form_submit_button("Salveaza document"):
                    execute('''
                        INSERT INTO documente (vehicul_id, tip_document, serie_document, data_emitere,
                        data_expirare, emitent, observatii) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (opts[veh_label], tip_doc, serie_doc, str(data_emitere), str(data_expirare), emitent, observatii))
                    st.success("Document salvat.")
                    st.rerun()
    with tab2:
        df = df_query('''
            SELECT d.id, v.nr_inmatriculare AS Vehicul, d.tip_document AS Tip, d.serie_document AS Serie,
            d.data_emitere AS 'Data emitere', d.data_expirare AS 'Data expirare', d.emitent AS Emitent, d.observatii AS Observatii
            FROM documente d JOIN vehicule v ON d.vehicul_id = v.id ORDER BY d.data_expirare ASC
        ''')
        st.dataframe(df, use_container_width=True)
        if not df.empty:
            st.download_button("Descarca documente CSV", csv_bytes(df), "documente.csv", "text/csv")

elif page == "📤 Export":
    st.title("📤 Export date")
    tables = {
        "vehicule.csv": "SELECT * FROM vehicule",
        "soferi.csv": "SELECT * FROM soferi",
        "foi_parcurs.csv": "SELECT * FROM foi_parcurs",
        "cheltuieli.csv": "SELECT * FROM cheltuieli",
        "documente.csv": "SELECT * FROM documente"
    }
    for filename, query in tables.items():
        st.subheader(filename)
        df = df_query(query)
        st.dataframe(df, use_container_width=True)
        st.download_button(f"Descarca {filename}", csv_bytes(df), filename, "text/csv")
