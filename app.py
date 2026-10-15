import streamlit as st
import pandas as pd
import requests
import json
import tempfrom  # opraveno z tempfile nebo ponecháno níže jako tempfile
import tempfile
from fpdf import FPDF

# --- KONFIGURACE STRÁNKY ---
st.set_page_config(page_title="SiteArmor Lite", page_icon="🛡️", layout="wide")

# --- SLOVNÍK PRO PŘEPÍNAČ JAZYKŮ (CZ / DE / EN) ---
LANGS = {
    "Čeština": {
        "lang_code": "CZ",
        "title": "🛡️ SiteArmor Lite – Správa inventáře",
        "subtitle": "Správa materiálu na stavbě",
        "tab_edit": "Upravit inventář",
        "tab_add": "Přidat materiál",
        "tab_cloud": "Cloud (Google Sheets)",
        "search": "Hledat v materiálu...",
        "confirm_changes": "Potvrdit změny v tabulce",
        "save_cloud": "Uložit vše do cloudu",
        "overview": "Celkový přehled stavu (sečteno podle materiálu)",
        "print_pdf": "Generovat PDF report",
        "download_pdf": "Stáhnout hotové PDF",
        "no_export": "Žádná data k exportu.",
        "empty_table": "Tabulka je prázdná.",
        "status_ok": "V pořádku",
        "status_miss": "Chybí",
        "col_mat": "Materiál",
        "col_loc": "Umístění",
        "col_tot": "Celkem (ks)",
        "col_req": "Požadováno (ks)",
        "col_miss_pcs": "Chybí (ks)",
        "col_stat": "Stav",
        "pdf_title": "Bestandsübersicht & Fehlteile",
        "pdf_cols": [("Material", 50), ("Lagerort", 40), ("Gesamt (Stk.)", 25), ("Soll (Stk.)", 25), ("Fehlmenge (Stk.)", 25), ("Status", 25)]
    },
    "Deutsch": {
        "lang_code": "DE",
        "title": "🛡️ SiteArmor Lite – Bestandsverwaltung",
        "subtitle": "Baustellenmaterial-Management",
        "tab_edit": "Bestand bearbeiten",
        "tab_add": "Material hinzufügen",
        "tab_cloud": "Cloud (Google Sheets)",
        "search": "Material suchen...",
        "confirm_changes": "Änderungen in der Tabelle bestätigen",
        "save_cloud": "Alles in der Cloud speichern",
        "overview": "Gesamtübersicht & Fehlteile (summiert nach Material)",
        "print_pdf": "PDF-Bericht erstellen",
        "download_pdf": "PDF herunterladen",
        "no_export": "Keine Daten zum Exportieren.",
        "empty_table": "Tabelle ist leer.",
        "status_ok": "Komplett",
        "status_miss": "Fehlt",
        "col_mat": "Material",
        "col_loc": "Lagerort",
        "col_tot": "Gesamt (Stk.)",
        "col_req": "Soll (Stk.)",
        "col_miss_pcs": "Fehlmenge (Stk.)",
        "col_stat": "Status",
        "pdf_title": "Bestandsübersicht & Fehlteile",
        "pdf_cols": [("Material", 50), ("Lagerort", 40), ("Gesamt (Stk.)", 25), ("Soll (Stk.)", 25), ("Fehlmenge (Stk.)", 25), ("Status", 25)]
    },
    "English": {
        "lang_code": "EN",
        "title": "🛡️ SiteArmor Lite – Inventory Management",
        "subtitle": "Construction Site Material Management",
        "tab_edit": "Edit Inventory",
        "tab_add": "Add Material",
        "tab_cloud": "Cloud (Google Sheets)",
        "search": "Search material...",
        "confirm_changes": "Confirm table changes",
        "save_cloud": "Save all to Cloud",
        "overview": "Status Overview (Aggregated by Material)",
        "print_pdf": "Generate PDF Report",
        "download_pdf": "Download PDF Report",
        "no_export": "No data to export.",
        "empty_table": "Table is empty.",
        "status_ok": "Complete",
        "status_miss": "Missing",
        "col_mat": "Material",
        "col_loc": "Location",
        "col_tot": "Total (Pcs)",
        "col_req": "Required (Pcs)",
        "col_miss_pcs": "Missing (Pcs)",
        "col_stat": "Status",
        "pdf_title": "Status Overview & Shortages",
        "pdf_cols": [("Material", 50), ("Location", 40), ("Total (Pcs)", 25), ("Required (Pcs)", 25), ("Missing (Pcs)", 25), ("Status", 25)]
    }
}

# Boční panel pro výběr jazyka
with st.sidebar:
    selected_lang = st.selectbox("🌐 Jazyk / Sprache / Language", list(LANGS.keys()))
t = LANGS[selected_lang]

st.title(t["title"])
st.subheader(t["subtitle"])

# --- 1. NASTAVENÍ GOOGLE SHEETS API ---
# (Zde doplňte svou URL adresu z Google Apps Script, řádek 14)
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbz.../exec" 

# --- 2. INICIALIZACE STAVU DAT ---
if "df" not in st.session_state:
    # Výchozí struktura dat, pokud ještě není načteno
    st.session_state.df = pd.DataFrame(columns=["Materiál", "Umístění", "Ks v balení", "Počet balení", "Požadováno ks"])

# Načtení dat z Google Sheets při startu, pokud je prázdno
@st.cache_data(ttl=60)
def load_data_from_cloud(url):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data:
                return pd.DataFrame(data)
    except Exception:
        pass
    return None

# --- 3. SPRÁVA POLOŽEK (TABULKA A VYHLEDÁVÁNÍ) ---
search_query = st.text_input("🔍", placeholder=t["search"], label_visibility="collapsed")

# Filtrování dat podle vyhledávání
df_view = st.session_state.df.copy()
if search_query:
    mask = df_view.astype(str).apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)
    df_view = df_view[mask]

st.markdown("### " + t["tab_edit"])
edited_df = st.data_editor(df_view, num_rows="dynamic", use_container_width=True, key="inventory_editor")

if st.button(t["confirm_changes"]):
    # Aktualizace hlavního dataframe podle úprav v editoru
    for idx, row in edited_df.iterrows():
        st.session_state.df.loc[idx] = row
    st.success("Změny uloženy v paměti!")

# --- 4. UKLÁDÁNÍ DO CLOUDU ---
if st.button(t["save_cloud"]):
    try:
        data_to_send = st.session_state.df.to_dict(orient="records")
        response = requests.post(WEB_APP_URL, json=data_to_send, timeout=10)
        if response.status_code == 200:
            st.success("Úspěšně uloženo do Google Sheets!")
        else:
            st.error("Chyba při ukládání do cloudu.")
    except Exception as e:
        st.error(f"Chyba připojení: {e}")

st.divider()

# --- 5. VÝPOČTY (Agregace podle materiálu) ---
st.subheader(t["overview"])
df_raw = st.session_state.df.copy()
df_raw = df_raw[df_raw["Materiál"].astype(str).str.strip() != ""]

if not df_raw.empty:
    for c in ["Ks v balení", "Počet balení", "Požadováno ks"]:
        df_raw[c] = pd.to_numeric(df_raw[c], errors="coerce").fillna(0)

    df_raw["Row_Total"] = df_raw["Ks v balení"] * df_raw["Počet balení"]
    df_raw["Mat_Key"] = df_raw["Materiál"].astype(str).str.strip().str.upper()

    df_grouped = df_raw.groupby("Mat_Key", as_index=False, sort=False).agg(
        Mat_Name=("Materiál", lambda x: str(x.iloc[0]).strip()),
        Location=("Umístění", lambda x: ", ".join(dict.fromkeys([str(v).strip() for v in x if str(v).strip() != ""]))),
        Total_Pcs=("Row_Total", "sum"),
        Required_Pcs=("Požadováno ks", "max"),
        Pkg_Size=("Ks v balení", "max")
    )
    
    df_grouped["Shortage_Pcs"] = (df_grouped["Required_Pcs"] - df_grouped["Total_Pcs"]).clip(lower=0)
    df_grouped["Status"] = df_grouped["Shortage_Pcs"].apply(lambda x: t["status_ok"] if x == 0 else t["status_miss"])

    df_display = pd.DataFrame({
        t["col_mat"]: df_grouped["Mat_Name"],
        t["col_loc"]: df_grouped["Location"],
        t["col_tot"]: df_grouped["Total_Pcs"],
        t["col_req"]: df_grouped["Required_Pcs"],
        t["col_miss_pcs"]: df_grouped["Shortage_Pcs"],
        t["col_stat"]: df_grouped["Status"]
    })

    st.dataframe(df_display, use_container_width=True, hide_index=True)
else:
    df_grouped = pd.DataFrame()
    st.info(t["empty_table"])

# --- 6. PDF EXPORT ---
def clean_pdf_text(text):
    replacements = {
        'á':'a', 'č':'c', 'ď':'d', 'é':'e', 'ě':'e', 'í':'i', 'ň':'n', 'ó':'o', 'ř':'r', 'š':'s', 'ť':'t', 'ú':'u', 'ů':'u', 'ý':'y', 'ž':'z',
        'Á':'A', 'Č':'C', 'Ď':'D', 'É':'E', 'Ě':'E', 'Í':'I', 'Ň':'N', 'Ó':'O', 'Ř':'R', 'Š':'S', 'Ť':'T', 'Ú':'U', 'Ů':'U', 'Ý':'Y', 'Ž':'Z'
    }
    text = str(text)
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text.encode('latin-1', 'replace').decode('latin-1')

if not df_grouped.empty:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, t["pdf_title"], ln=True, align="C")
    pdf.ln(5)
    
    pdf.set_font("Arial", "B", 9)
    cols_pdf = t["pdf_cols"]
    for name, w in cols_pdf:
        pdf.cell(w, 8, name, border=1, align="C")
    pdf.ln()
    
    pdf.set_font("Arial", "", 9)
    for _, row in df_grouped.iterrows():
        stat_txt = "OK" if row["Shortage_Pcs"] == 0 else ("Fehlt" if t["lang_code"] == "DE" else ("Missing" if t["lang_code"] == "EN" else "Chybi"))
        pdf.cell(cols_pdf[0][1], 8, clean_pdf_text(row["Mat_Name"]), border=1)
        pdf.cell(cols_pdf[1][1], 8, clean_pdf_text(row["Location"]), border=1)
        pdf.cell(cols_pdf[2][1], 8, str(int(row["Total_Pcs"])), border=1, align="C")
        pdf.cell(cols_pdf[3][1], 8, str(int(row["Required_Pcs"])), border=1, align="C")
        pdf.cell(cols_pdf[4][1], 8, str(int(row["Shortage_Pcs"])), border=1, align="C")
        pdf.cell(cols_pdf[5][1], 8, stat_txt, border=1, align="C")
        pdf.ln()
        
    pdf_output = pdf.output()
    if isinstance(pdf_output, str):
        pdf_output = pdf_output.encode('latin1')
    elif isinstance(pdf_output, bytearray):
        pdf_output = bytes(pdf_output)
        
    pdf_filename = f"Bestandsliste_{t['lang_code']}.pdf"
    
    st.download_button(
        label=t["download_pdf"],
        data=pdf_output,
        file_name=pdf_filename,
        mime="application/pdf"
    )
else:
    st.info(t["no_export"])
