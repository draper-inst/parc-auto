import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, datetime

DB_FILE = "parc_auto.db"

st.set_page_config(
    page_title="Administrare Parc Auto",
    page_icon="🚗",
    layout="wide"
)

# ============================================================
# BAZA DE DATE
# ============================================================

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def table_exists(conn, table_name):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,)
    )
    return cursor.fetchone() is not None


def column_exists(conn, table_name, column_name):
    if not table_exists(conn, table_name):
        return False
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

    cheltuieli_columns = {
        "data_cheltuiala": "TEXT",
        "tip_cheltuiala": "TEXT",
        "furnizor": "TEXT",
        "document": "TEXT",
        "km_bord": "INTEGER",
        "cantitate_litri": "REAL",
        "pret_litru": "REAL",
        "suma": "REAL",
        "observatii": "TEXT"
    }

    for col, definition in cheltuieli_columns.items():
        add_column_if_missing(conn, "cheltuieli", col, definition)

    # Compatibilitate cu prima versiune, unde coloana era scrisa cu diacritica.
    if column_exists(conn, "cheltuieli", "tip_cheltuială") and column_exists(conn, "cheltuieli", "tip_cheltuiala"):
        conn.execute("""
            UPDATE cheltuieli
            SET tip_cheltuiala = COALESCE(tip_cheltuiala, tip_cheltuială)
        """)
        conn.commit()

    conn.close()


def fetch_df(query, params=()):
    conn = get_connection()
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


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


def execute_query(query, params=()):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    conn.commit()
    conn.close()


def to_csv_download(df):
    return df.to_csv(index=False).encode("utf-8-sig")


def safe_date_to_value(text_value):
    if not text_value:
        return date.today()
    try:
        return datetime.strptime(text_value, "%Y-%m-%d").date()
    except Exception:
        return date.today()


def safe_days_until(text_value):
    if not text_value:
        return None
    try:
        target_date = datetime.strptime(text_value, "%Y-%m-%d").date()
        return (target_date - date.today()).days
    except Exception:
        return None


def status_for_days(days):
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

# ============================================================
# MENIU
# ============================================================

st.sidebar.title("Parc auto")
st.sidebar.caption("Vehicule, soferi, cheltuieli si foi de parcurs")

meniu = st.sidebar.radio(
    "Meniu",
    [
        "Dashboard",
        "Vehicule",
        "Soferi / Utilizatori",
        "Foi de parcurs",
        "Cheltuieli",
        "Export date"
    ]
)

# ============================================================
# DASHBOARD
# ============================================================

if meniu == "Dashboard":
    st.title("Dashboard parc auto")

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
            COALESCE(s.nume || ' ' || IFNULL(s.prenume, ''), '') AS sofer
        FROM vehicule v
        LEFT JOIN soferi s ON v.sofer_id = s.id
        ORDER BY v.nr_inmatriculare
    """)

    total_cost_row = fetch_one("SELECT COALESCE(SUM(suma), 0) AS total FROM cheltuieli")
    total_costuri = total_cost_row["total"] if total_cost_row else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Vehicule", len(vehicule_df))
    col2.metric("Cheltuieli totale", f"{total_costuri:,.2f} RON")
    col3.metric("Soferi activi", fetch_one("SELECT COUNT(*) AS c FROM soferi WHERE activ = 1")["c"])
    col4.metric("Foi de parcurs", fetch_one("SELECT COUNT(*) AS c FROM foi_parcurs")["c"])

    st.divider()
    st.subheader("Alerte expirari")

    if vehicule_df.empty:
        st.info("Nu exista vehicule introduse.")
    else:
        alerts = []
        for _, row in vehicule_df.iterrows():
            documente = {
                "RCA": row["expirare_rca"],
                "ITP": row["expirare_itp"],
                "CASCO": row["expirare_casco"],
                "Rovinieta": row["expirare_rovinieta"],
                "Revizie": row["expirare_revizie"]
            }
            for nume_doc, data_doc in documente.items():
                zile = safe_days_until(data_doc)
                status = status_for_days(zile)
                if status in ["Expirat", "Expira in 30 zile", "Expira in 60 zile"]:
                    alerts.append({
                        "Vehicul": row["nr_inmatriculare"],
                        "Marca": row["marca"],
                        "Model": row["model"],
                        "Document": nume_doc,
                        "Data expirare": data_doc,
                        "Zile ramase": zile,
                        "Status": status,
                        "Sofer": row["sofer"]
                    })

        if alerts:
            alerts_df = pd.DataFrame(alerts)
            st.dataframe(alerts_df, use_container_width=True)
            st.download_button(
                "Descarca alerte CSV",
                data=to_csv_download(alerts_df),
                file_name="alerte_expirari.csv",
                mime="text/csv"
            )
        else:
            st.success("Nu exista documente expirate sau care expira in urmatoarele 60 de zile.")

    st.divider()
    st.subheader("Costuri pe vehicul")

    costuri_df = fetch_df("""
        SELECT
            v.nr_inmatriculare AS vehicul,
            v.marca,
            v.model,
            COALESCE(SUM(c.suma), 0) AS cost_total
        FROM vehicule v
        LEFT JOIN cheltuieli c ON v.id = c.vehicul_id
        GROUP BY v.id
        ORDER BY cost_total DESC
    """)
    st.dataframe(costuri_df, use_container_width=True)

# ============================================================
# VEHICULE
# ============================================================

elif meniu == "Vehicule":
    st.title("Management vehicule")

    tab_add, tab_list, tab_edit = st.tabs(["Adauga vehicul", "Lista vehicule", "Editeaza / sterge"])

    soferi_rows = fetch_all("SELECT id, nume, prenume FROM soferi WHERE activ = 1 ORDER BY nume, prenume")
    sofer_options = {"Fara sofer alocat": None}
    for s in soferi_rows:
        label = f"{s['nume']} {s['prenume'] or ''}".strip()
        sofer_options[label] = s["id"]

    with tab_add:
        st.subheader("Adauga vehicul")

        with st.form("form_adauga_vehicul"):
            col1, col2, col3 = st.columns(3)

            with col1:
                nr = st.text_input("Numar inmatriculare *").upper().strip()
               *marca = st.text_input("Marca")
   *            model = st.text_input(*Model")
                an_fabrica*ie = st.number_input("An fabricati*", min_value=1950, max_value=2100,*value=2024)
                vin = *t.text_input("Serie sasiu / VIN").*pper().strip()
                ser*e_motor = st.text_input("Serie mot*r")

            with col2:
      *         capacitate = st.number_in*ut("Capacitate cilindrica cmc", mi*_value=0, step=100)
              * putere_kw = st.number_input("Pute*e kW", min_value=0.0, step=1.0)
  *             putere_cp = st.number*input("Putere CP", min_value=0.0, *tep=1.0)
                combustib*l = st.selectbox("Combustibil", ["", "Benzina", "Diesel", "Hibrid", "Plug-in Hybrid", "Electric", "GPL", "CNG"])
                norma = st*selectbox("Norma poluare", ["", "Euro 3", "Euro 4", "Euro 5", "Euro 6", "Electric"])
                cut*e = st.selectbox("Cutie viteze", ["", "Manuala", "Automata"])

      *     with col3:
                tr*ctiune = st.selectbox("Tractiune",*["", "Fata", "Spate", "4x4 / AWD"]*
                culoare = st.text*input("Culoare")
                m*sa = st.number_input("Masa maxima *utorizata kg", min_value=0, step=1*0)
                anvelope_vara =*st.text_input("Dimensiune anvelope*vara", placeholder="Ex: 205/55 R16*)
                anvelope_iarna =*st.text_input("Dimensiune anvelope*iarna", placeholder="Ex: 205/55 R1*")
                km_actuali = st*number_input("Km actuali", min_val*e=0, step=1000)

            st.di*ider()
            col4, col5, col* = st.columns(3)

            with*col4:
                data_achizit*e = st.date_input("Data achizitie"* value=date.today())
             *  valoare = st.number_input("Valoa*e achizitie RON", min_value=0.0, s*ep=1000.0)
                sofer_s*lectat = st.selectbox("Sofer aloca*", list(sofer_options.keys()))

  *         with col5:
              * expirare_rca = st.date_input("Exp*rare RCA", value=date.today())
   *            expirare_itp = st.date*input("Expirare ITP", value=date.t*day())
                expirare_ca*co = st.date_input("Expirare CASCO*, value=date.today())

           *with col6:
                expirar*_rovinieta = st.date_input("Expira*e rovinieta", value=date.today())
*               expirare_revizie = *t.date_input("Scadenta revizie", v*lue=date.today())
                *tatus = st.selectbox("Status", ["Activ", "In service", "Vandut", "Casat", "Inactiv"])

            obser*atii = st.text_area("Observatii")
*           submitted = st.form_sub*it_button("Salveaza vehicul")

   *        if submitted:
            *   if not nr:
                    *t.error("Numarul de inmatriculare *ste obligatoriu.")
               *else:
                    try:
   *                    execute_query(*""
                            INS*RT INTO vehicule (
               *                nr_inmatriculare, *arca, model, an_fabricatie, vin, s*rie_motor,
                       *        capacitate_cilindrica, put*re_kw, putere_cp, combustibil, nor*a_poluare,
                       *        cutie_viteze, tractiune, c*loare, masa_maxima,
              *                 dimensiune_anvelo*e_vara, dimensiune_anvelope_iarna,*km_actuali,
                      *         data_achizitie, valoare_a*hizitie, expirare_rca, expirare_it*,
                                *xpirare_casco, expirare_rovinieta,*expirare_revizie,
                *               sofer_id, status, o*servatii
                         *  )
                            VA*UES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?,*?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?* ?, ?, ?, ?, ?, ?)
               *        """, (
                   *        nr, marca, model, an_fabri*atie, vin, serie_motor,
          *                 capacitate, puter*_kw, putere_cp, combustibil, norma*
                            cutie* tractiune, culoare, masa,
       *                    anvelope_vara,*anvelope_iarna, km_actuali,
      *                     str(data_achi*itie), valoare, str(expirare_rca),*str(expirare_itp),
               *            str(expirare_casco), s*r(expirare_rovinieta), str(expirar*_revizie),
                       *    sofer_options[sofer_selectat],*status, observatii
               *        ))
                       *st.success(f"Vehiculul {nr} a fost*salvat.")
                        *t.rerun()
                    exce*t sqlite3.IntegrityError:
        *               st.error("Acest num*r de inmatriculare exista deja.")
*    with tab_list:
        st.subh*ader("Lista vehicule")
        df * fetch_df("""
            SELECT
 *              v.nr_inmatriculare A* 'Nr inmatriculare',
             *  v.marca AS Marca,
              * v.model AS Model,
               *v.an_fabricatie AS An,
           *    v.vin AS VIN,
                *.capacitate_cilindrica AS Cilindre*,
                v.putere_kw AS '*utere kW',
                v.puter*_cp AS 'Putere CP',
              * v.combustibil AS Combustibil,
   *            v.dimensiune_anvelope_*ara AS 'Anvelope vara',
          *     v.dimensiune_anvelope_iarna A* 'Anvelope iarna',
               *v.km_actuali AS 'Km actuali',
    *           v.expirare_rca AS RCA,
*               v.expirare_itp AS I*P,
                v.expirare_casc* AS CASCO,
                v.expir*re_rovinieta AS Rovinieta,
       *        v.expirare_revizie AS Revi*ie,
                COALESCE(s.num* || ' ' || IFNULL(s.prenume, ''), *') AS Sofer,
                v.sta*us AS Status
            FROM vehi*ule v
            LEFT JOIN soferi*s ON v.sofer_id = s.id
           *ORDER BY v.nr_inmatriculare
      * """)
        st.dataframe(df, use*container_width=True)
        if n*t df.empty:
            st.downloa*_button("Descarca vehicule CSV", d*ta=to_csv_download(df), file_name=*vehicule.csv", mime="text/csv")

 *  with tab_edit:
        st.subhea*er("Editeaza rapid vehicul")
     *  vehicule_rows = fetch_all("SELEC* id, nr_inmatriculare FROM vehicul* ORDER BY nr_inmatriculare")
     *  if not vehicule_rows:
          * st.info("Nu exista vehicule de ed*tat.")
        else:
            v*h_options = {v["nr_inmatriculare"]* v["id"] for v in vehicule_rows}
 *          selected_nr = st.selectb*x("Selecteaza vehicul", list(veh_o*tions.keys()))
            veh_id * veh_options[selected_nr]
        *   row = fetch_one("SELECT * FROM *ehicule WHERE id = ?", (veh_id,))
*            with st.form("form_edi*_vehicul"):
                col1, *ol2, col3 = st.columns(3)

       *        with col1:
               *    marca_edit = st.text_input("Ma*ca", value=row["marca"] or "")
   *                model_edit = st.te*t_input("Model", value=row["model"] or "")
                    vin_ed*t = st.text_input("VIN", value=row*"vin"] or "")
                    *m_edit = st.number_input("Km actua*i", min_value=0, value=int(row["km_actuali"] or 0), step=1000)

     *          with col2:
             *      rca_edit = st.date_input("Ex*irare RCA", value=safe_date_to_val*e(row["expirare_rca"]))
          *         itp_edit = st.date_input(*Expirare ITP", value=safe_date_to_*alue(row["expirare_itp"]))
       *            casco_edit = st.date_i*put("Expirare CASCO", value=safe_d*te_to_value(row["expirare_casco"])*
                    rov_edit = st*date_input("Expirare rovinieta", v*lue=safe_date_to_value(row["expirare_rovinieta"]))

                w*th col3:
                    rev_e*it = st.date_input("Scadenta reviz*e", value=safe_date_to_value(row["expirare_revizie"]))
              *     status_list = ["Activ", "In service", "Vandut", "Casat", "Inactiv"]
                    status_valu* = row["status"] if row["status"] *n status_list else "Activ"
       *            status_edit = st.selec*box("Status", status_list, index=s*atus_list.index(status_value))

  *                 sofer_keys = list*sofer_options.keys())
            *       selected_sofer_key = "Fara *ofer alocat"
                    f*r key, val in sofer_options.items(*:
                        if val =* row["sofer_id"]:
                *           selected_sofer_key = ke*
                    sofer_edit = *t.selectbox("Sofer alocat", sofer_*eys, index=sofer_keys.index(select*d_sofer_key))

                obs*edit = st.text_area("Observatii", *alue=row["observatii"] or "")

   *            col_save, col_delete =*st.columns(2)
                save*= col_save.form_submit_button("Sal*eaza modificarile")
              * delete = col_delete.form_submit_b*tton("Sterge vehiculul")

        *       if save:
                  * execute_query("""
               *        UPDATE vehicule
          *             SET marca = ?, model * ?, vin = ?, km_actuali = ?,
     *                      expirare_rca*= ?, expirare_itp = ?, expirare_ca*co = ?,
                          * expirare_rovinieta = ?, expirare_*evizie = ?,
                      *     status = ?, sofer_id = ?, obs*rvatii = ?
                       *WHERE id = ?
                    "*", (
                        marca*edit, model_edit, vin_edit, km_edi*,
                        str(rca_*dit), str(itp_edit), str(casco_edi*),
                        str(rov*edit), str(rev_edit),
            *           status_edit, sofer_opti*ns[sofer_edit], obs_edit, veh_id
 *                  ))
             *      st.success("Vehicul actualiz*t.")
                    st.rerun(*

                if delete:
     *              execute_query("DELET* FROM vehicule WHERE id = ?", (veh*id,))
                    st.warni*g("Vehicul sters.")
              *     st.rerun()

# ===============*==================================*=========
# SOFERI
# =============*==================================*===========

elif meniu == "Soferi*/ Utilizatori":
    st.title("Sofe*i / Utilizatori")
    tab_add, tab*list = st.tabs(["Adauga sofer", "Lista soferi"])

    with tab_add:
 *      with st.form("form_sofer"):
*           col1, col2, col3 = st.c*lumns(3)
            with col1:
  *             nume = st.text_input(*Nume *")
                prenume =*st.text_input("Prenume")
         *      telefon = st.text_input("Tel*fon")
            with col2:
     *          email = st.text_input("E*ail")
                serie_permis*= st.text_input("Serie permis")
  *             categorie = st.text_i*put("Categorie permis", placeholde*="Ex: B, C, CE")
            with *ol3:
                expirare_perm*s = st.date_input("Data expirare p*rmis", value=date.today())
       *        departament = st.text_inpu*("Departament")
                ac*iv = st.checkbox("Activ", value=Tr*e)
            observatii = st.tex*_area("Observatii")
            su*mitted = st.form_submit_button("Sa*veaza sofer")

            if subm*tted:
                if not nume:*                    st.error("*umele este obligator*u.")
*               else:
             *      execute_query("""
*                       INSERT INTO*soferi*(
                            nume* prenume* telefon,*email, serie_permis*
                            categ*rie_permis, data*expirare_permis* departament,
                    *       activ, observ*tii
                        )
    *                   VALUES (?, ?, ?* ?, ?, ?,*?, ?, ?,*?)
                    ""*, (
                        nume* pren*me, telefon* email* serie_per*is,
*                       categorie* str(exp*rare*permis*, departament,
                   *    1*if activ else 0* observ*tii
                   *))
                    st.success*"Sofer*salvat.")
*                   st.rer*n()

   *with tab_list*
       *df = fetch*df("""
*           SELECT
*               id,
               *nume AS*Nume*
                pren*me AS*Prenume,
                telefon*AS Telefon*
                email*AS Email*
                serie_permis*AS 'Serie permis*,
                categorie*permis*AS Categorie,
               *data_expir*re_permis AS*'Expir*re permis',
                depart*ment AS*Departament,
*               CASE*WHEN activ = 1*THEN '*ctiv' ELSE*'In*ctiv' END*AS Status*
               *observatii*AS Observatii*            FROM so*eri
*           ORDER BY nume* pren*me
       *""")
        st*dataframe(df* use*container_width=True)
       *if not*df.empty*
            st.download_button*"Des*arca so*eri CSV", data=*o_csv_download*df), file_name="*ofer*.csv",*mime="text/c*v")

#*==================================*=========================
# FOI DE*PARCUR*
# ===============================*============================

elif*meniu ==*"Foi*de parcurs":
*   st.title("Foi*de parcurs")
   *tab_add* tab_list*= st*tabs(["Genereaza foaie", "Istoric foi"])

    vehicule_rows = fetch_a*l("SELECT id, nr_in*atric*lare, marca, model* km_actuali FROM*vehicule*ORDER BY nr_inmat*iculare")
*   soferi*rows =*fetch_all("*ELECT id* nume, pren*me FROM sofer* WHERE activ*= 1 ORDER*BY nume* prenume")

*   with*tab_add:
        if*not vehicule*rows:
            st*warning("*rebuie sa ad*ugi*cel put*n un veh*cul.")
*       else*
            veh_options =*{f*{v*'nr_inmatriculare']} - {*['marca'] or*''}*{v*'model'] or ''}".strip*): v*for v in*vehicule*rows}
*           sofer*options =*{"F*ra so*er": None*
            for s*in so*eri_rows:
               *sofer*options[f"{s['nume']} {s['prenume'] or ''}".strip()] = s["id"]

     *      with st.form("form_foaie"):
*               col1, col2 = st.col*mns(2)
                with col1:
*                   veh_label = st.*electbox("*ehicul", list(*eh_options*keys()))
*                   veh = veh_optio*s[veh_label]
                    d*fault_km =*int(veh*"km_actuali"] or 0*
                    data*foaie =*st.date_input*"Data foii*, value*date.today())
*                   km_plecare =*st.number*input("Km*plecare", min*value=0* value=default*km, step*1)
*                   km*sos*re = st*number_input("Km*sosire*, min*value=0* value*default*km, step*1)
*                   ora_ple*are =*st.text*input("Ora*plecare", placeholder*"Ex* *8:30")
*                   ora_sos*re =*st.text*input("Ora*sosire*, placeholder*"Ex* *7:15")

*               with col*:
                    so*er_label*= st*selectbox("*ofer*, list(*ofer_options.keys*)))
                   *localitate*plecare*= st*text_input*"Local*tate ple*are")
                   *localitate_sos*re =*st.text_input("Localitate*sosire*)
                   *scop =*st.text*input("Sc*p deplasare")
                   *combustibil_initial =*st.number_input*"Combustibil initial lit*i",*min_value=0.*,*step=1.*)
*                   combust*bil_final = st.number*input("Combust*bil final*litri*, min_value*0.0* step=1*0*
                    alimentare_l*tri = st*number_input("Al*mentare litri",*min_value=0*0* step*1*0*

                observ*tii = st.text*area("Observatii*)
               *submitted = st*form_submit_button("Salve*za fo*ie de parcurs*)

                if*submitted:
                    if*km_sosire*< km_plecare*
                       *st.error("Km*sosire*nu poate*fi mai*mic decat*Km plecare*")
                    else*
                        km_par*urs* =*km_s*sire - km_ple*are
                       *execute_query("""
                *           INSERT INTO*foi_par*urs (
*                               veh*cul_id, sofer_id* data*fo*ie, local*tate_plecare,
                    *           localitate*sos*re, scop_de*lasare,*km_plecare*
                                k*_sosire* km*parcurs*, ora_plecare* ora*sosire,
*                               com*ustibil_initial* combustibil*final, alimentare*litri,
*                               obs*rvatii
                           *)
                            VALU*S (?, ?, ?,*?, ?,*?, ?, ?, ?,*?, ?,*?, ?, ?, ?*
                       *""",*(
                            veh["id"], sofer*options[sofer_label], str(data*foaie*,
                            loca*itate_ple*are,*localitate_sos*re,*scop,
*                           km*ple*are,*km_s*sire* km*parc*rsi,
                           *ora_*lecare,*ora_s*sire,
*                           combust*bil_initial,*combustibil*final, alimentare*lit*i,
*                           observ*tii
*                       ))
*                       execute*query("*PDATE vehicule SET*km_actual* =*? WHERE*id =*?", (*m_s*sire* veh*"id"]))
                       *st.success(f"*oa*e salv*ta.*Km parcursi* {*m_par*ursi*")
                       *st.r*run()

   *with tab*list:
*       df*= fetch*df("""
*           SELECT*               *fp.id*
                fp.data*fo*ie AS*Data,
                v*nr_in*atric*lare AS Vehicul*
               *v.m*rca AS*Marca,
*               v*model AS*Model,
*               COALESCE(s.n*me || ' '*|| IF*ULL(s.prenume,*''), '') AS*Sofer*
               *fp.local*tate_plecare AS Ple*are,
*               fp.localitate*sos*re AS Sosire*
                fp.sc*p_deplasare AS Sc*p,
                fp*km_ple*are AS*'Km plecare*,
               *fp.k*_sosire*AS '*m sosire',
*               fp*km_parc*rsi*AS 'Km*parcursi',
               *fp.*ra_*lecare*AS '*ra plecare',
*               fp*ora_sos*re AS*'Ora sosire*,
               *fp.alimentare*lit*i AS '*limentare litri*,
               *fp.ob*ervatii*AS Observ*tii
            FROM*foi_par*urs fp
*           JOIN*vehicule*v ON fp.*ehicul_id*= v*id
*           LEFT JOIN so*eri*s ON fp*sofer_id*= s*id
            ORDER*BY fp*data_*oaie*DESC, fp*id DESC
*       """)
       *st.data*rame(df* use_container_width*True)
*       if*not df.empty:
*           st*download_button*"Descar*a foi*de parc*rs CSV*, data=*o_csv_download(df),*file_name*"fo*_par*urs*csv",*mime="text/c*v")

* =================================*==========================
* CHE*TUI*LI
* =================================*==========================

*lif men*u == "*heltu*eli":
*   st*title("*helt*ieli*)
    tab_add* tab_list*= st.tabs(["Adauga cheltuiala", "Istoric cheltuieli"])

    vehicule_*ows = fetch_all("SELECT id, nr_inm*triculare, marca, model FROM vehic*le ORDER BY nr_in*atric*lare")

*   with*tab_add:
       *if not*vehicule_rows:
*           st*warning("*rebu*e sa*adau*i cel*putin*un veh*cul.")
*       else*
           *veh_options = {f*{v*'nr_inmatriculare']} -*{v*'marca'] or*''}*{v*'model'] or ''*".strip():*v["id"] for*v in*vehicule*rows}

            with st.form*"*orm_cheltu*ala"):
*              *col1,*col2,*col3 =*st.columns*3)
*               with col1*
                   *veh_label = st*select*ox("*ehicul", list*veh*options*keys()))
                   *data_che*tuiala = st*date_input*"Data*, value=date.today())
*                   tip*= st*selectbox*"Tip*chelt**ala", ["Combustibil", "Revizie", "Reparatie", "Anvelope", "RCA", "CASCO", "Rovinieta", "ITP", "Spalatorie", "Taxe", "Altele"])
            *   with col2:
                    *urnizor = st.text_input("Furnizor*)
                    document =*st.text*input("*ocument /*factura / bon")
*                   km*bord = st*number_input*"Km*bord", min*value=0,*step=100)
*               with col3*
                    cantitate*= st*number_input*"Cant*tate litri",*min_value=*.*,*step=1.**
                   *pret_l*tru = st*number_input*"Pret*litru*, min*value=0*0* step=0*1*
                   *suma =*st.number_input*"S*ma tot*la R*N",*min_value*0.*, step=*0.*)

*               if*tip ==*"Comb*stibil"*and cant*tate >*0*and pret_lit*u > * and suma ==*0*
                   *suma =*cantitate** pret_l*tru*                   *st.info(f"S*ma calculata*estimativ* {*uma*.2*} R*N")

                observ*tii =*st.text*area("*bservatii")
*               submitted*= st.form_submit*button*"Sal*eaza*che*tuiala*)

               *if submitted:
*                   execute*query("""
*                       INSERT*INTO che*tuieli*(
                           *vehicul*id,*data_che*tuiala* tip*chelt*iala*
                            furni*or, document* km*bord* cantitate*l*tri,
*                           pret*litru, suma* observ*tii
*                       )
*                       VALUES (?,*?,*?, ?, ?,*?, ?,*?, ?, ?*
                    """,*(
                       *veh_options*veh_label], str*data*cheltu*ala*, tip,
                       *furniz*r* document* km*bord, cant*tate*
*                       pret_l*tru* suma,*observatii*                   *))
                   *st*success*"Chelt*iala*salvata.")
*                   st*rerun()

*  *with*tab_list:
*       df*= fetch_df*"""
           *SELECT
                c*id*
               *c.data*che*tu*ala AS*Data*
                v*nr*in*atriculare*AS Veh*cul,
               *v.m*rca AS Marca*
               *v.model*AS Model,
               *c.tip_che*tu*ala*AS Tip*
               *c.furn*zor*AS Furn*zor*
*               c.document AS*Document*
               *c.km*bord AS*'*m bord',
               *c.c*nt*tate_l*tri*AS 'Cant*tate litri',
*               c*pret*lit*u AS '*ret lit*u',
*              *c.s*ma AS*'*uma*RON*,
*               c*observ*tii AS Observ*tii
*           FROM*chelt*ieli c
           *JOIN veh*cule v*ON c.*ehicul*id = v*id
*           ORDER*BY c*data*chelt*iala*DESC* c*id DESC**       """)
       *st.dataframe*df,*use*container_width*True)
*       if not*df.empty*
           *total =*df["Suma RON"].*um()
*          *st.metric*"Total chelt**eli af*sate*, f*{total*,.2*}*R*N")
*           st*download*button("*escar*a chelt*ieli*CSV",*data=*o_csv*download(df),*file_name*"che*t*ieli*csv", mime*"text*csv*)

#*==================================*=========================
# EXPORT*#*==================================*=========================

elif me*iu*== "*xport date*:
*   st*title("*xport date")
*   st*write("*escar*a*t*belele principale*in*format*CSV.")

   *export*ri*= {
       *"*eh*cule.csv":*fetch*df*"SELECT **FROM*veh*cule"),
       *"*o*eri.csv*:*fetch_df("SELECT***FROM so*eri*),
       *"foi*parc*rs.csv*: fetch_df*"SELECT** FROM foi*parc*rs"),
       *"*heltu*eli.csv*: fetch*df("*ELECT **FROM che*tu*eli")
   *}

   *for*file_name* df*in exporturi*items():
*      *st.sub*eader(file*name)
        st.data*rame(df**use_container*width=True*
       *st.download_button*
           *f*Des*arca*{*ile_name*",
           *data=to*csv_download*df),
           *file_name*file*name,
*           mime*"text/c*v"
*       )
*`*
    
