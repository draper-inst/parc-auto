import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, datetime

DB_FILE = "parc_auto.db"

st.set_page_config(page_title="Administrare Parc Auto", page_icon="Auto", layout="wide")


def db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def table_exists(conn, table):
    row = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone()
    return row is not None


def col_exists(conn, table, col):
    if not table_exists(conn, table):
        return False
    cols = [r["name"] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
    return col in cols


def add_col(conn, table, col, definition):
    if not col_exists(conn, table, col):
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {definition}")
        conn.commit()


def init_db():
    conn = db()
    cur = conn.cursor()

    cur.execute("""
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

    cur.execute("""
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
            observatii TEXT
        )
    """)

    cur.execute("""
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
            observatii TEXT
        )
    """)

    cur.execute("""
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
            observatii TEXT
        )
    """)
    conn.commit()

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
        add_col(conn, "vehicule", col, definition)

    cost_cols = {
        "data_cheltuiala": "TEXT", "tip_cheltuiala": "TEXT", "furnizor": "TEXT",
        "document": "TEXT", "km_bord": "INTEGER", "cantitate_litri": "REAL",
        "pret_litru": "REAL", "suma": "REAL", "observatii": "TEXT"
    }
    for col, definition in cost_cols.items():
        add_col(conn, "cheltuieli", col, definition)

    if col_exists(conn, "cheltuieli", "tip_cheltuială") and col_exists(conn, "cheltuieli", "tip_cheltuiala"):
        conn.execute("UPDATE cheltuieli SET tip_cheltuiala = COALESCE(tip_cheltuiala, tip_cheltuială)")
        conn.commit()

    conn.close()


def qdf(sql, params=()):
    conn = db()
    df = pd.read_sql_query(sql, conn, params=params)
    conn.close()
    return df


def qall(sql, params=()):
    conn = db()
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return rows


def qone(sql, params=()):
    conn = db()
    row = conn.execute(sql, params).fetchone()
    conn.close()
    return row


def exec_sql(sql, params=()):
    conn = db()
    conn.execute(sql, params)
    conn.commit()
    conn.close()


def csv_bytes(df):
    return df.to_csv(index=False).encode("utf-8-sig")


def parse_date(value):
    if not value:
        return date.today()
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except Exception:
        return date.today()


def days_until(value):
    if not value:
        return None
    try:
        return (datetime.strptime(value, "%Y-%m-%d").date() - date.today()).days
    except Exception:
        return None


def alert_status(days):
    if days is None:
        return "Fara data"
    if days < 0:
        return "Expirat"
    if days <= 30:
        return "Expira in 30 zile"
    if days <= 60:
        return "Expira in 60 zile"
    return "OK"


init_db()

st.sidebar.title("Parc auto")
page = st.sidebar.radio("Meniu", ["Dashboard", "Vehicule", "Soferi", "Foi de parcurs", "Cheltuieli", "Export"])

if page == "Dashboard":
    st.title("Dashboard parc auto")
    vehicule = qdf("""
        SELECT v.*, COALESCE(s.nume || ' ' || IFNULL(s.prenume, ''), '') AS sofer
        FROM vehicule v
        LEFT JOIN soferi s ON v.sofer_id = s.id
        ORDER BY v.nr_inmatriculare
    """)
    total = qone("SELECT COALESCE(SUM(suma), 0) AS total FROM cheltuieli")["total"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Vehicule", len(vehicule))
    c2.metric("Cheltuieli totale", f"{total:,.2f} RON")
    c3.metric("Soferi activi", qone("SELECT COUNT(*) AS c FROM soferi WHERE activ = 1")["c"])
    c4.metric("Foi parcurs", qone("SELECT COUNT(*) AS c FROM foi_parcurs")["c"])

    st.subheader("Alerte expirari")
    alerts = []
    for _, r in vehicule.iterrows():
        docs = {
            "RCA": r.get("expirare_rca"), "ITP": r.get("expirare_itp"),
            "CASCO": r.get("expirare_casco"), "Rovinieta": r.get("expirare_rovinieta"),
            "Revizie": r.get("expirare_revizie")
        }
        for doc, exp in docs.items():
            zile = days_until(exp)
            status = alert_status(zile)
            if status in ["Expirat", "Expira in 30 zile", "Expira in 60 zile"]:
                alerts.append({
                    "Vehicul": r["nr_inmatriculare"], "Document": doc, "Expirare": exp,
                    "Zile ramase": zile, "Status": status, "Sofer": r.get("sofer", "")
                })
    if alerts:
        adf = pd.DataFrame(alerts)
        st.dataframe(adf, use_container_width=True)
        st.download_button("Descarca alerte CSV", csv_bytes(adf), "alerte_expirari.csv", "text/csv")
    else:
        st.success("Nu exista alerte in urmatoarele 60 de zile.")

    st.subheader("Costuri pe vehicul")
    costuri = qdf("""
        SELECT v.nr_inmatriculare AS Vehicul, v.marca AS Marca, v.model AS Model,
               COALESCE(SUM(c.suma), 0) AS Cost_total
        FROM vehicule v
        LEFT JOIN cheltuieli c ON v.id = c.vehicul_id
        GROUP BY v.id
        ORDER BY Cost_total DESC
    """)
    st.dataframe(costuri, use_container_width=True)

elif page == "Vehicule":
    st.title("Vehicule")
    tab1, tab2, tab3 = st.tabs(["Adauga", "Lista", "Editeaza"])
    soferi = qall("SELECT id, nume, prenume FROM soferi WHERE activ = 1 ORDER BY nume, prenume")
    sofer_options = {"Fara sofer": None}
    for s in soferi:
        sofer_options[f"{s['nume']} {s['prenume'] or ''}".strip()] = s["id"]

    with tab1:
        with st.form("vehicul_nou"):
            c1, c2, c3 = st.columns(3)
            with c1:
                nr = st.text_input("Numar inmatriculare *").upper().strip()
                marca = st.text_input("Marca")
                model = st.text_input("Model")
                an = st.number_input("An fabricatie", 1950, 2100, 2024)
                vin = st.text_input("Serie sasiu / VIN").upper().strip()
                serie_motor = st.text_input("Serie motor")
            with c2:
                cilindree = st.number_input("Capacitate cilindrica cmc", min_value=0, step=100)
                kw = st.number_input("Putere kW", min_value=0.0, step=1.0)
                cp = st.number_input("Putere CP", min_value=0.0, step=1.0)
                combustibil = st.selectbox("Combustibil", ["", "Benzina", "Diesel", "Hibrid", "Plug-in Hybrid", "Electric", "GPL", "CNG"])
                norma = st.selectbox("Norma poluare", ["", "Euro 3", "Euro 4", "Euro 5", "Euro 6", "Electric"])
                cutie = st.selectbox("Cutie viteze", ["", "Manuala", "Automata"])
            with c3:
                tractiune = st.selectbox("Tractiune", ["", "Fata", "Spate", "4x4 / AWD"])
                culoare = st.text_input("Culoare")
                masa = st.number_input("Masa maxima autorizata kg", min_value=0, step=100)
                anvelope_v = st.text_input("Anvelope vara", placeholder="205/55 R16")
                anvelope_i = st.text_input("Anvelope iarna", placeholder="205/55 R16")
                km = st.number_input("Km actuali", min_value=0, step=1000)

            c4, c5, c6 = st.columns(3)
            with c4:
                data_ach = st.date_input("Data achizitie", date.today())
                valoare = st.number_input("Valoare achizitie RON", min_value=0.0, step=1000.0)
                sofer = st.selectbox("Sofer alocat", list(sofer_options.keys()))
            with c5:
                rca = st.date_input("Expirare RCA", date.today())
                itp = st.date_input("Expirare ITP", date.today())
                casco = st.date_input("Expirare CASCO", date.today())
            with c6:
                rov = st.date_input("Expirare rovinieta", date.today())
                rev = st.date_input("Scadenta revizie", date.today())
                status = st.selectbox("Status", ["Activ", "In service", "Vandut", "Casat", "Inactiv"])
            obs = st.text_area("Observatii")
            if st.form_submit_button("Salveaza vehicul"):
                if not nr:
                    st.error("Numarul de inmatriculare este obligatoriu.")
                else:
                    try:
                        exec_sql("""
                            INSERT INTO vehicule (
                                nr_inmatriculare, marca, model, an_fabricatie, vin, serie_motor,
                                capacitate_cilindrica, putere_kw, putere_cp, combustibil, norma_poluare,
                                cutie_viteze, tractiune, culoare, masa_maxima,
                                dimensiune_anvelope_vara, dimensiune_anvelope_iarna, km_actuali,
                                data_achizitie, valoare_achizitie, expirare_rca, expirare_itp,
                                expirare_casco, expirare_rovinieta, expirare_revizie, sofer_id,
                                status, observatii
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (nr, marca, model, an, vin, serie_motor, cilindree, kw, cp, combustibil, norma,
                              cutie, tractiune, culoare, masa, anvelope_v, anvelope_i, km, str(data_ach), valoare,
                              str(rca), str(itp), str(casco), str(rov), str(rev), sofer_options[sofer], status, obs))
                        st.success("Vehicul salvat.")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Acest vehicul exista deja.")

    with tab2:
        df = qdf("""
            SELECT v.nr_inmatriculare AS Nr, v.marca AS Marca, v.model AS Model, v.an_fabricatie AS An,
                   v.vin AS VIN, v.capacitate_cilindrica AS CMC, v.putere_kw AS kW, v.putere_cp AS CP,
                   v.combustibil AS Combustibil, v.dimensiune_anvelope_vara AS Anvelope_vara,
                   v.dimensiune_anvelope_iarna AS Anvelope_iarna, v.km_actuali AS Km,
                   v.expirare_rca AS RCA, v.expirare_itp AS ITP, v.expirare_casco AS CASCO,
                   v.expirare_rovinieta AS Rovinieta, v.expirare_revizie AS Revizie,
                   COALESCE(s.nume || ' ' || IFNULL(s.prenume, ''), '') AS Sofer, v.status AS Status
            FROM vehicule v LEFT JOIN soferi s ON v.sofer_id = s.id
            ORDER BY v.nr_inmatriculare
        """)
        st.dataframe(df, use_container_width=True)
        if not df.empty:
            st.download_button("Descarca vehicule CSV", csv_bytes(df), "vehicule.csv", "text/csv")

    with tab3:
        veh = qall("SELECT id, nr_inmatriculare FROM vehicule ORDER BY nr_inmatriculare")
        if not veh:
            st.info("Nu exista vehicule.")
        else:
            opts = {v["nr_inmatriculare"]: v["id"] for v in veh}
            nr_sel = st.selectbox("Alege vehicul", list(opts.keys()))
            r = qone("SELECT * FROM vehicule WHERE id=?", (opts[nr_sel],))
            with st.form("edit_vehicul"):
                c1, c2 = st.columns(2)
                with c1:
                    marca = st.text_input("Marca", r["marca"] or "")
                    model = st.text_input("Model", r["model"] or "")
                    vin = st.text_input("VIN", r["vin"] or "")
                    km = st.number_input("Km", min_value=0, value=int(r["km_actuali"] or 0), step=1000)
                with c2:
                    rca = st.date_input("RCA", parse_date(r["expirare_rca"]))
                    itp = st.date_input("ITP", parse_date(r["expirare_itp"]))
                    casco = st.date_input("CASCO", parse_date(r["expirare_casco"]))
                    rov = st.date_input("Rovinieta", parse_date(r["expirare_rovinieta"]))
                    rev = st.date_input("Revizie", parse_date(r["expirare_revizie"]))
                status = st.selectbox("Status", ["Activ", "In service", "Vandut", "Casat", "Inactiv"])
                obs = st.text_area("Observatii", r["observatii"] or "")
                save, delete = st.columns(2)
                if save.form_submit_button("Salveaza"):
                    exec_sql("""
                        UPDATE vehicule SET marca=?, model=?, vin=?, km_actuali=?, expirare_rca=?, expirare_itp=?,
                        expirare_casco=?, expirare_rovinieta=?, expirare_revizie=?, status=?, observatii=? WHERE id=?
                    """, (marca, model, vin, km, str(rca), str(itp), str(casco), str(rov), str(rev), status, obs, opts[nr_sel]))
                    st.success("Actualizat.")
                    st.rerun()
                if delete.form_submit_button("Sterge"):
                    exec_sql("DELETE FROM vehicule WHERE id=?", (opts[nr_sel],))
                    st.warning("Sters.")
                    st.rerun()

elif page == "Soferi":
    st.title("Soferi / Utilizatori")
    tab1, tab2 = st.tabs(["Adauga", "Lista"])
    with tab1:
        with st.form("sofer_nou"):
            c1, c2, c3 = st.columns(3)
            with c1:
                nume = st.text_input("Nume *")
                prenume = st.text_input("Prenume")
                telefon = st.text_input("Telefon")
            with c2:
                email = st.text_input("Email")
                permis = st.text_input("Serie permis")
                categorie = st.text_input("Categorie permis")
            with c3:
                exp = st.date_input("Expirare permis", date.today())
                dep = st.text_input("Departament")
                activ = st.checkbox("Activ", True)
            obs = st.text_area("Observatii")
            if st.form_submit_button("Salveaza sofer"):
                if not nume:
                    st.error("Numele este obligatoriu.")
                else:
                    exec_sql("""
                        INSERT INTO soferi (nume, prenume, telefon, email, serie_permis, categorie_permis,
                        data_expirare_permis, departament, activ, observatii) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (nume, prenume, telefon, email, permis, categorie, str(exp), dep, 1 if activ else 0, obs))
                    st.success("Sofer salvat.")
                    st.rerun()
    with tab2:
        df = qdf("SELECT * FROM soferi ORDER BY nume, prenume")
        st.dataframe(df, use_container_width=True)
        if not df.empty:
            st.download_button("Descarca soferi CSV", csv_bytes(df), "soferi.csv", "text/csv")

elif page == "Foi de parcurs":
    st.title("Foi de parcurs")
    tab1, tab2 = st.tabs(["Adauga", "Istoric"])
    veh = qall("SELECT id, nr_inmatriculare, marca, model, km_actuali FROM vehicule ORDER BY nr_inmatriculare")
    sof = qall("SELECT id, nume, prenume FROM soferi WHERE activ=1 ORDER BY nume, prenume")
    with tab1:
        if not veh:
            st.warning("Adauga mai intai un vehicul.")
        else:
            veh_opts = {f"{v['nr_inmatriculare']} - {v['marca'] or ''} {v['model'] or ''}".strip(): v for v in veh}
            sof_opts = {"Fara sofer": None}
            for s in sof:
                sof_opts[f"{s['nume']} {s['prenume'] or ''}".strip()] = s["id"]
            with st.form("foaie_noua"):
                c1, c2 = st.columns(2)
                with c1:
                    veh_label = st.selectbox("Vehicul", list(veh_opts.keys()))
                    selected = veh_opts[veh_label]
                    dataf = st.date_input("Data", date.today())
                    km_start = st.number_input("Km plecare", min_value=0, value=int(selected["km_actuali"] or 0))
                    km_stop = st.number_input("Km sosire", min_value=0, value=int(selected["km_actuali"] or 0))
                    ora_start = st.text_input("Ora plecare")
                    ora_stop = st.text_input("Ora sosire")
                with c2:
                    sofer = st.selectbox("Sofer", list(sof_opts.keys()))
                    plecare = st.text_input("Localitate plecare")
                    sosire = st.text_input("Localitate sosire")
                    scop = st.text_input("Scop deplasare")
                    comb_start = st.number_input("Combustibil initial litri", min_value=0.0)
                    comb_stop = st.number_input("Combustibil final litri", min_value=0.0)
                    alimentare = st.number_input("Alimentare litri", min_value=0.0)
                obs = st.text_area("Observatii")
                if st.form_submit_button("Salveaza foaie"):
                    if km_stop < km_start:
                        st.error("Km sosire nu poate fi mai mic decat Km plecare.")
                    else:
                        km_total = km_stop - km_start
                        exec_sql("""
                            INSERT INTO foi_parcurs (vehicul_id, sofer_id, data_foaie, localitate_plecare,
                            localitate_sosire, scop_deplasare, km_plecare, km_sosire, km_parcursi,
                            ora_plecare, ora_sosire, combustibil_initial, combustibil_final, alimentare_litri, observatii)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (selected["id"], sof_opts[sofer], str(dataf), plecare, sosire, scop, km_start,
                              km_stop, km_total, ora_start, ora_stop, comb_start, comb_stop, alimentare, obs))
                        exec_sql("UPDATE vehicule SET km_actuali=? WHERE id=?", (km_stop, selected["id"]))
                        st.success("Foaie salvata.")
                        st.rerun()
    with tab2:
        df = qdf("""
            SELECT fp.data_foaie AS Data, v.nr_inmatriculare AS Vehicul,
                   COALESCE(s.nume || ' ' || IFNULL(s.prenume, ''), '') AS Sofer,
                   fp.localitate_plecare AS Plecare, fp.localitate_sosire AS Sosire,
                   fp.scop_deplasare AS Scop, fp.km_plecare AS Km_plecare,
                   fp.km_sosire AS Km_sosire, fp.km_parcursi AS Km_parcursi,
                   fp.ora_plecare AS Ora_plecare, fp.ora_sosire AS Ora_sosire,
                   fp.alimentare_litri AS Alimentare_litri, fp.observatii AS Observatii
            FROM foi_parcurs fp
            JOIN vehicule v ON fp.vehicul_id = v.id
            LEFT JOIN soferi s ON fp.sofer_id = s.id
            ORDER BY fp.data_foaie DESC, fp.id DESC
        """)
        st.dataframe(df, use_container_width=True)
        if not df.empty:
            st.download_button("Descarca foi CSV", csv_bytes(df), "foi_parcurs.csv", "text/csv")

elif page == "Cheltuieli":
    st.title("Cheltuieli")
    tab1, tab2 = st.tabs(["Adauga", "Istoric"])
    veh = qall("SELECT id, nr_inmatriculare, marca, model FROM vehicule ORDER BY nr_inmatriculare")
    with tab1:
        if not veh:
            st.warning("Adauga mai intai un vehicul.")
        else:
            veh_opts = {f"{v['nr_inmatriculare']} - {v['marca'] or ''} {v['model'] or ''}".strip(): v["id"] for v in veh}
            with st.form("cost_nou"):
                c1, c2, c3 = st.columns(3)
                with c1:
                    vehicul = st.selectbox("Vehicul", list(veh_opts.keys()))
                    data_cost = st.date_input("Data", date.today())
                    tip = st.selectbox("Tip", ["Combustibil", "Revizie", "Reparatie", "Anvelope", "RCA", "CASCO", "Rovinieta", "ITP", "Spalatorie", "Taxe", "Altele"])
                with c2:
                    furnizor = st.text_input("Furnizor")
                    document = st.text_input("Document")
                    km = st.number_input("Km bord", min_value=0, step=100)
                with c3:
                    litri = st.number_input("Litri", min_value=0.0)
                    pret = st.number_input("Pret litru", min_value=0.0)
                    suma = st.number_input("Suma RON", min_value=0.0)
                if tip == "Combustibil" and litri > 0 and pret > 0 and suma == 0:
                    suma = litri * pret
                    st.info(f"Suma calculata: {suma:.2f} RON")
                obs = st.text_area("Observatii")
                if st.form_submit_button("Salveaza cheltuiala"):
                    exec_sql("""
                        INSERT INTO cheltuieli (vehicul_id, data_cheltuiala, tip_cheltuiala, furnizor,
                        document, km_bord, cantitate_litri, pret_litru, suma, observatii)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (veh_opts[vehicul], str(data_cost), tip, furnizor, document, km, litri, pret, suma, obs))
                    st.success("Cheltuiala salvata.")
                    st.rerun()
    with tab2:
        df = qdf("""
            SELECT c.data_cheltuiala AS Data, v.nr_inmatriculare AS Vehicul, c.tip_cheltuiala AS Tip,
                   c.furnizor AS Furnizor, c.document AS Document, c.km_bord AS Km,
                   c.cantitate_litri AS Litri, c.pret_litru AS Pret_litru, c.suma AS Suma_RON,
                   c.observatii AS Observatii
            FROM cheltuieli c
            JOIN vehicule v ON c.vehicul_id = v.id
            ORDER BY c.data_cheltuiala DESC, c.id DESC
        """)
        st.dataframe(df, use_container_width=True)
        if not df.empty:
            st.metric("Total", f"{df['Suma_RON'].sum():,.2f} RON")
            st.download_button("Descarca cheltuieli CSV", csv_bytes(df), "cheltuieli.csv", "text/csv")

elif page == "Export":
    st.title("Export date")
    tables = {
        "vehicule.csv": "SELECT * FROM vehicule",
        "soferi.csv": "SELECT * FROM soferi",
        "foi_parcurs.csv": "SELECT * FROM foi_parcurs",
        "cheltuieli.csv": "SELECT * FROM cheltuieli"
    }
    for name, sql in tables.items():
        df = qdf(sql)
        st.subheader(name)
        st.dataframe(df, use_container_width=True)
        st.download_button(f"Descarca {name}", csv_bytes(df), name, "text/csv")
