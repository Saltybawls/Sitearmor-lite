import streamlit as st
import pandas as pd
from fpdf import FPDF
import tempfile
import requests
import math
import os

# Zákaz jakýchkoliv automatických překladačů třetích stran v prohlížeči
st.set_page_config(
    page_title="SiteArmor Lite | Schumann Tanks", 
    page_icon="🛡️", 
    layout="wide",
    initial_sidebar_state="collapsed"
)
st.markdown('<meta name="google" content="notranslate">', unsafe_allow_html=True)

# ==========================================
# ⚠️ SEM VLOŽ SVOU FUNKČNÍ GOOGLE SCRIPT URL:
# ==========================================
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbzbhQUzV7HfoWMqhd5JtvVV__LGoMBpds8lAP76zXYmnYhE4NUgoehXPVQhvLqyhzIpaQ/exec"

COLS = ["Materiál", "Umístění", "Ks v balení", "Počet balení", "Požadováno ks"]

# --- TŘÍJAZYKOVÝ SLOVNÍK (CZ / DE / EN) ---
LANGS = {
    "Deutsch 🇩🇪": {
        "lang_code": "DE",
        "title": "🛡️ SiteArmor Lite",
        "subtitle": "Lager- und Montageverwaltung",
        "quick_add": "📦 Schneller Wareneingang",
        "select_mat": "Material & Packungsgröße auswählen",
        "add_pkg": "Packungen hinzufügen (Stk.)",
        "add_btn": "➕ Bestand erhöhen",
        "add_success": "{add_qty} Packung(en) zu {sel_mat} hinzugefügt! Bitte unten in der Cloud speichern.",
        "table_header": "📋 Bestandsaufnahme & Bearbeitung (Einzelpackungen)",
        "search": "🔍 Material suchen (Name oder Teilbegriff eingeben...)",
        "confirm_table": "✅ Tabellenänderungen übernehmen",
        "table_saved": "Änderungen vorgemerkt! Du kannst weiterbearbeiten oder direkt in der Cloud speichern.",
        "save_cloud": "☁️ Alles in der Cloud speichern",
        "sending": "Daten werden in die Cloud übertragen...",
        "save_success": "✅ Erfolgreich in der Datenbank gespeichert!",
        "save_error": "Fehler beim Senden.",
        "conn_error": "Verbindungsfehler: {e}",
        "overview": "📊 Gesamtübersicht & Fehlteile (summiert nach Material)",
        "empty_table": "Die Tabelle ist leer. Bitte oben im Inventar Positionen hinzufügen.",
        "print_pdf": "🖨 PDF-Bericht erstellen",
        "no_export": "Keine Daten zum Exportieren vorhanden.",
        "download_pdf": "📥 PDF-Bericht herunterladen",
        "pdf_title": "Bestandsliste (Gesamtsumme) - Schumann Tanks",
        "status_ok": "🟢 Vollständig",
        "status_miss": "🔴 Fehlt",
        "pkg_unit": "Stk./Pack.",
        "col_mat": "Material",
        "col_loc": "Lagerort",
        "col_pck_size": "Stk. / Packung",
        "col_pck_cnt": "Packungen (Ist)",
        "col_req": "Soll (Stk.)",
        "col_tot": "Gesamt (Stk.)",
        "col_miss_pcs": "Fehlmenge (Stk.)",
        "col_miss_pck": "Fehlende Pack.",
        "col_stat": "Status",
        "pdf_cols": [("Material", 55), ("Lagerort", 35), ("Gesamt Stk", 25), ("Soll Stk", 25), ("Fehlt Stk", 25), ("Status", 25)]
    },
    "Čeština 🇨🇿": {
        "lang_code": "CZ",
        "title": "🛡️ SiteArmor Lite",
        "subtitle": "Systém řízení skladu a montáže",
        "quick_add": "📦 Rychlý příjem materiálu",
        "select_mat": "Vyber materiál (a typ balení)",
        "add_pkg": "Přidat balení (ks)",
        "add_btn": "➕ Přičíst na sklad",
        "add_success": "Přidáno {add_qty} balení k {sel_mat}! Nezapomeň dole uložit do cloudu.",
        "table_header": "📋 Inventář a Úpravy (jednotlivá balení)",
        "search": "🔍 Hledat v materiálu (napiš název nebo část...)",
        "confirm_table": "✅ Potvrdit změny v tabulce",
        "table_saved": "Změny zapsány do paměti! Můžeš pokračovat v úpravách, nebo to rovnou uložit do cloudu.",
        "save_cloud": "☁️ Uložit vše do cloudu",
        "sending": "Odesílám data do cloudu...",
        "save_success": "✅ Úspěšně uloženo do Google Tabulky!",
        "save_error": "Chyba při odesílání.",
        "conn_error": "Chyba připojení: {e}",
        "overview": "📊 Celkový přehled stavu (sečteno podle materiálu)",
        "empty_table": "Tabulka je prázdná. Přidej položky výše v Inventáři.",
        "print_pdf": "🖨 Generovat PDF report",
        "no_export": "Není co exportovat.",
        "download_pdf": "📥 Stáhnout hotové PDF",
        "pdf_title": "Inventarni soupis (Soucet) - Schumann Tanks",
        "status_ok": "🟢 Splněno",
        "status_miss": "🔴 Chybí",
        "pkg_unit": "ks/bal.",
        "col_mat": "Materiál",
        "col_loc": "Umístění",
        "col_pck_size": "Ks v balení",
        "col_pck_cnt": "Počet balení",
        "col_req": "Požadováno ks",
        "col_tot": "Celkem ks",
        "col_miss_pcs": "Chybí ks",
        "col_miss_pck": "Chybí balení (odhad)",
        "col_stat": "Stav",
        "pdf_cols": [("Material", 55), ("Umisteni", 35), ("Celkem ks", 25), ("Pozadovano", 25), ("Chybi ks", 25), ("Stav", 25)]
    },
    "English 🇬🇧": {
        "lang_code": "EN",
        "title": "🛡️ SiteArmor Lite",
        "subtitle": "Inventory and Assembly Management",
        "quick_add": "📦 Quick Material Intake",
        "select_mat": "Select material & package type",
        "add_pkg": "Add packages (pcs)",
        "add_btn": "➕ Add to Stock",
        "add_success": "Added {add_qty} package(s) to {sel_mat}! Remember to save to cloud below.",
        "table_header": "📋 Inventory & Editing (Individual Packages)",
        "search": "🔍 Search material (type name or part...)",
        "confirm_table": "✅ Confirm table changes",
        "table_saved": "Changes saved to memory! You can continue editing or save to cloud.",
        "save_cloud": "☁️ Save all to Cloud",
        "sending": "Sending data to cloud...",
        "save_success": "✅ Successfully saved to Google Sheet!",
        "save_error": "Error sending data.",
        "conn_error": "Connection error: {e}",
        "overview": "📊 Status Overview (Aggregated by Material)",
        "empty_table": "Table is empty. Add items above in Inventory.",
        "print_pdf": "🖨 Generate PDF Report",
        "no_export": "Nothing to export.",
        "download_pdf": "📥 Download PDF",
        "pdf_title": "Inventory Summary (Total) - Schumann Tanks",
        "status_ok": "🟢 Complete",
        "status_miss": "🔴 Missing",
        "pkg_unit": "pcs/pkg",
        "col_mat": "Material",
        "col_loc": "Location",
        "col_pck_size": "Pcs / Package",
        "col_pck_cnt": "Packages (Actual)",
        "col_req": "Required (Pcs)",
        "col_tot": "Total (Pcs)",
        "col_miss_pcs": "Shortage (Pcs)",
        "col_miss_pck": "Missing Pkg.",
        "col_stat": "Status",
        "pdf_cols": [("Material", 55), ("Location", 35), ("Total Pcs", 25), ("Required Pcs", 25), ("Missing Pcs", 25), ("Status", 25)]
    }
}

# --- HLAVIČKA A PŘEPÍNAČ JAZYKŮ PŘÍMO NA STRÁNCE ---
col_head, col_lang = st.columns([2.5, 1.5])

with col_lang:
    selected_lang = st.selectbox(
        "🌐 Language / Sprache / Jazyk",
        ["Deutsch 🇩🇪", "Čeština 🇨🇿", "English 🇬🇧"],
        index=0  # Němčina jako výchozí
    )

t = LANGS[selected_lang]

with col_head:
    st.title(t["title"])

# Zobrazení loga (pokud existuje logo.png, použije se, jinak moderní SVG)
logo_loaded = False
for ext in ["logo.png", "logo.svg", "logo.jpg", "logo.webp"]:
    if os.path.exists(ext):
        st.image(ext, width=220)
        logo_loaded = True
        break

if not logo_loaded:
    st.markdown(f"""
    <div style="display: flex; align-items: center; margin-top: -10px; margin-bottom: 20px; flex-wrap: wrap; gap: 12px;">
        <svg width="235" height="42" viewBox="0 0 235 42" xmlns="http://www.w3.org/2000/svg" style="border-radius: 4px; box-shadow: 0 2px 6px rgba(0,0,0,0.18);">
            <rect width="235" height="42" fill="#003865"/>
            <rect width="5" height="42" fill="#E67E22"/>
            <g transform="translate(14, 6)" stroke="#ffffff" stroke-width="1.5" fill="none">
                <path d="M2,8 L15,2 L28,8" stroke="#E67E22" stroke-width="2" fill="rgba(230,126,34,0.2)"/>
                <rect x="2" y="8" width="26" height="20" rx="1" fill="#004d8c"/>
                <line x1="2" y1="14" x2="28" y2="14" stroke-opacity="0.6"/>
                <line x1="2" y1="21" x2="28" y2="21" stroke-opacity="0.6"/>
                <line x1="10" y1="8" x2="10" y2="28" stroke-opacity="0.4"/>
                <line x1="20" y1="8" x2="20" y2="28" stroke-opacity="0.4"/>
            </g>
            <text x="52" y="20" font-family="Arial, Helvetica, sans-serif" font-size="15" font-weight="900" fill="#ffffff" letter-spacing="1.5">SCHUMANN</text>
            <text x="52" y="33" font-family="Arial, Helvetica, sans-serif" font-size="9" font-weight="bold" fill="#E67E22" letter-spacing="3.5">TANKS</text>
        </svg>
        <span style="color: #666; font-size: 14px; font-weight: 500;">| &nbsp;{t["subtitle"]}</span>
    </div>
    """, unsafe_allow_html=True)

# 1. ČISTÉ NAČTENÍ DAT
def load_data():
    empty_df = pd.DataFrame(columns=COLS)
    try:
        r = requests.get(WEB_APP_URL, timeout=20)
        if r.status_code == 200:
            data = r.json()
            if data and len(data) > 0:
                df = pd.DataFrame(data)
                for col in COLS:
                    if col not in df.columns:
                        df[col] = "" if col in ["Materiál", "Umístění"] else 0
                return df[COLS]
    except:
        pass
    return empty_df

if "df" not in st.session_state:
    st.session_state.df = load_data()

# 2. RYCHLÝ PŘÍJEM
valid_rows = st.session_state.df[st.session_state.df["Materiál"].astype(str).str.strip() != ""]
if not valid_rows.empty:
    st.subheader(t["quick_add"])
    with st.form("add_form"):
        c1, c2, c3 = st.columns([2, 1, 1])
        
        options_map = {}
        for idx, row in valid_rows.iterrows():
            mat_name = str(row["Materiál"]).strip()
            pkg_sz = pd.to_numeric(row["Ks v balení"], errors="coerce") or 0
            loc_name = str(row["Umístění"]).strip()
            label = f"{mat_name} ({int(pkg_sz)} {t['pkg_unit']}" + (f" – {loc_name})" if loc_name else ")")
            if label in options_map:
                label = f"{label} [#{idx+1}]"
            options_map[label] = idx
            
        sel_label = c1.selectbox(t["select_mat"], list(options_map.keys()))
        add_qty = c2.number_input(t["add_pkg"], min_value=1, step=1)
        
        if c3.form_submit_button(t["add_btn"]):
            target_idx = options_map[sel_label]
            curr = pd.to_numeric(st.session_state.df.loc[target_idx, "Počet balení"], errors="coerce") or 0
            st.session_state.df.loc[target_idx, "Počet balení"] = curr + add_qty
            st.success(t["add_success"].format(add_qty=add_qty, sel_mat=sel_label))
            st.rerun()

st.divider()

# 3. HLAVNÍ TABULKA & VYHLEDÁVÁNÍ
st.subheader(t["table_header"])

search_query = st.text_input(t["search"], "")

df_to_show = st.session_state.df.copy()
if search_query:
    df_to_show = df_to_show[df_to_show["Materiál"].astype(str).str.contains(search_query, case=False, na=False)]

with st.form("table_form"):
    edited_df = st.data_editor(
        df_to_show,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        column_config={
            "Materiál": st.column_config.TextColumn(t["col_mat"], required=True),
            "Umístění": st.column_config.TextColumn(t["col_loc"]),
            "Ks v balení": st.column_config.NumberColumn(t["col_pck_size"], min_value=0, step=1),
            "Počet balení": st.column_config.NumberColumn(t["col_pck_cnt"], min_value=0, step=1),
            "Požadováno ks": st.column_config.NumberColumn(t["col_req"], min_value=0, step=1),
        }
    )
    submit_table = st.form_submit_button(t["confirm_table"])

if submit_table:
    if search_query:
        st.session_state.df.update(edited_df)
        new_rows = edited_df.index.difference(st.session_state.df.index)
        if not new_rows.empty:
            st.session_state.df = pd.concat([st.session_state.df, edited_df.loc[new_rows]], ignore_index=True)
    else:
        st.session_state.df = edited_df.reset_index(drop=True)
    
    st.success(t["table_saved"])
    st.rerun()

# 4. ULOŽENÍ DO CLOUDU
if st.button(t["save_cloud"], type="primary"):
    with st.spinner(t["sending"]):
        try:
            records = st.session_state.df.to_dict(orient="records")
            r = requests.post(WEB_APP_URL, json=records, timeout=20)
            if r.status_code == 200:
                st.success(t["save_success"])
            else:
                st.error(t["save_error"])
        except Exception as e:
            st.error(t["conn_error"].format(e=e))

st.divider()

# 5. VÝPOČTY (Bezpečné sčítání bez chyb v diakritice)
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

    # Vytvoření tabulky přímo s lokalizovanými názvy (žádné přejmenovávání, které by mohlo selhat)
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

# 6. PDF EXPORT
def clean_pdf_text(text):
    replacements = {
        'á':'a', 'č':'c', 'ď':'d', 'é':'e', 'ě':'e', 'í':'i', 'ň':'n', 'ó':'o', 'ř':'r', 'š':'s', 'ť':'t', 'ú':'u', 'ů':'u', 'ý':'y', 'ž':'z',
        'Á':'A', 'Č':'C', 'Ď':'D', 'É':'E', 'Ě':'E', 'Í':'I', 'Ň':'N', 'Ó':'O', 'Ř':'R', 'Š':'S', 'Ť':'T', 'Ú':'U', 'Ů':'U', 'Ý':'Y', 'Ž':'Z'
    }
    text = str(text)
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text.encode('latin-1', 'replace').decode('latin-1')

if st.button(t["print_pdf"]):
    if df_grouped.empty:
        st.warning(t["no_export"])
    else:
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
            
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        pdf.output(tmp.name)
        pdf_filename = f"Bestandsliste_{t['lang_code']}.pdf"
        with open(tmp.name, "rb") as f:
            st.download_button(t["download_pdf"], f, pdf_filename, "application/pdf")

# 6. PDF EXPORT
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
        
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(tmp.name)
    pdf_filename = f"Bestandsliste_{t['lang_code']}.pdf"
    with open(tmp.name, "rb") as f:
        st.download_button(t["download_pdf"], f, pdf_filename, "application/pdf")
else:
  st.info(t["no_export"])
