import streamlit as st
import pandas as pd
from fpdf import FPDF
import tempfile
import requests
import math
import os

st.set_page_config(page_title="SiteArmor Lite | Schumann Tanks", page_icon="🛡️", layout="wide")

# ==========================================
# ⚠️ SEM VLOŽ SVOU FUNKČNÍ GOOGLE SCRIPT URL:
# ==========================================
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbzbhQUzV7HfoWMqhd5JtvVV__LGoMBpds8lAP76zXYmnYhE4NUgoehXPVQhvLqyhzIpaQ/exec"

COLS = ["Materiál", "Umístění", "Ks v balení", "Počet balení", "Požadováno ks"]

# --- KOMPLETNÍ SLOVNÍK (CZ / DE) ---
LANGS = {
    "Čeština 🇨🇿": {
        "lang_code": "CZ",
        "title": "🛡️ SiteArmor Lite",
        "subtitle": "Systém řízení skladu a montáže",
        "quick_add": "📦 Rychlý příjem materiálu",
        "select_mat": "Vyber materiál (a typ balení)",
        "add_pkg": "Přidat balení (ks)",
        "add_btn": "➕ Přičíst na sklad",
        "add_success": "Přidáno {add_qty} balení k {sel_mat} a automaticky uloženo do cloudu!",
        "table_header": "📋 Inventář a Úpravy (jednotlivá balení)",
        "search": "🔍 Hledat v materiálu (napiš název nebo část...)",
        "confirm_table": "✅ Potvrdit a uložit změny v tabulce",
        "table_saved": "Změny zapsány a automaticky zálohovány do Google Tabulky!",
        "save_cloud": "☁️ Vynutit ruční zálohu do cloudu",
        "sending": "Automaticky zálohuji data do Google Tabulky...",
        "save_success": "✅ Úspěšně zálohováno do Google Tabulky!",
        "save_error": "⚠️ Změny jsou v paměti, ale automatická záloha do cloudu selhala (kód {code}).",
        "conn_error": "⚠️ Chyba připojení při zálohování: {e}",
        "overview": "📊 Celkový přehled stavu (sečteno podle materiálu)",
        "empty_table": "Tabulka je prázdná. Přidej položky výše v Inventáři.",
        "print_pdf": "🖨 Generovat PDF report",
        "no_export": "Není co exportovat.",
        "download_pdf": "📥 Stáhnout hotové PDF",
        "pdf_title": "Inventarni soupis (Soucet) - Schumann Tanks",
        "status_ok": "🟢 Splněno",
        "status_miss": "🔴 Chybí",
        "pkg_unit": "ks/bal.",
        # Překlady sloupců v tabulkách
        "col_mat": "Materiál",
        "col_loc": "Umístění",
        "col_pck_size": "Ks v balení",
        "col_pck_cnt": "Počet balení",
        "col_req": "Požadováno ks",
        "col_tot": "Celkem ks",
        "col_miss_pcs": "Chybí ks",
        "col_miss_pck": "Chybí balení (odhad)",
        "col_stat": "Stav",
        # Sloupce do PDF (bez diakritiky)
        "pdf_cols": [("Material", 55), ("Umisteni", 35), ("Celkem ks", 25), ("Pozadovano", 25), ("Chybi ks", 25), ("Stav", 25)]
    },
    "Deutsch 🇩🇪": {
        "lang_code": "DE",
        "title": "🛡️ SiteArmor Lite",
        "subtitle": "Lager- und Montageverwaltung",
        "quick_add": "📦 Schneller Wareneingang",
        "select_mat": "Material & Packungsgröße auswählen",
        "add_pkg": "Packungen hinzufügen (Stk.)",
        "add_btn": "➕ Bestand erhöhen",
        "add_success": "{add_qty} Packung(en) zu {sel_mat} hinzugefügt & automatisch in der Cloud gespeichert!",
        "table_header": "📋 Bestandsaufnahme & Bearbeitung (Einzelpackungen)",
        "search": "🔍 Material suchen (Name oder Teilbegriff eingeben...)",
        "confirm_table": "✅ Tabellenänderungen übernehmen & speichern",
        "table_saved": "Änderungen übernommen und automatisch in Google Sheets gesichert!",
        "save_cloud": "☁️ Manuelles Cloud-Backup erzwingen",
        "sending": "Automatisches Backup in die Cloud läuft...",
        "save_success": "✅ Erfolgreich in der Datenbank gespeichert!",
        "save_error": "⚠️ Fehler beim automatischen Cloud-Backup (Code {code}).",
        "conn_error": "⚠️ Verbindungsfehler beim Backup: {e}",
        "overview": "📊 Gesamtübersicht & Fehlteile (summiert nach Material)",
        "empty_table": "Die Tabelle ist leer. Bitte oben im Inventar Positionen hinzufügen.",
        "print_pdf": "🖨 PDF-Bericht erstellen",
        "no_export": "Keine Daten zum Exportieren vorhanden.",
        "download_pdf": "📥 PDF-Bericht herunterladen",
        "pdf_title": "Bestandsliste (Gesamtsumme) - Schumann Tanks",
        "status_ok": "🟢 Vollständig",
        "status_miss": "🔴 Fehlt",
        "pkg_unit": "Stk./Pack.",
        # Překlady sloupců v tabulkách
        "col_mat": "Material",
        "col_loc": "Lagerort",
        "col_pck_size": "Stk. / Packung",
        "col_pck_cnt": "Packungen (Ist)",
        "col_req": "Soll (Stk.)",
        "col_tot": "Gesamt (Stk.)",
        "col_miss_pcs": "Fehlmenge (Stk.)",
        "col_miss_pck": "Fehlende Pack.",
        "col_stat": "Status",
        # Sloupce do PDF
        "pdf_cols": [("Material", 55), ("Lagerort", 35), ("Gesamt Stk", 25), ("Soll Stk", 25), ("Fehlt Stk", 25), ("Status", 25)]
    }
}

# --- BOČNÍ PANEL S PŘEPÍNAČEM JAZYKŮ ---
with st.sidebar:
    st.markdown("### 🌐 Jazyk / Sprache")
    selected_lang = st.radio("Vyberte jazyk / Sprache wählen:", ["Deutsch 🇩🇪", "Čeština 🇨🇿"], index=0, label_visibility="collapsed")
    st.divider()
    st.caption("🏗️ **Schumann Tank & Stahlbau**")
    st.caption("SiteArmor Inventory System v2.3 (Auto-Backup)")

t = LANGS[selected_lang]

# --- POMOCNÁ FUNKCE PRO AUTOMATICKÉ ZÁLOHOVÁNÍ ---
def sync_to_cloud():
    with st.spinner(t["sending"]):
        try:
            clean_df = st.session_state.df.fillna("")
            records = clean_df.to_dict(orient="records")
            r = requests.post(WEB_APP_URL, json=records, timeout=20)
            if r.status_code == 200:
                st.toast(t["save_success"], icon="☁️")
                return True
            else:
                st.error(t["save_error"].format(code=r.status_code))
                return False
        except Exception as e:
            st.error(t["conn_error"].format(e=e))
            return False

# --- HLAVIČKA A LOGO SCHUMANN TANKS POD ŠTÍTEM ---
st.title(t["title"])

logo_loaded = False
for ext in ["logo.png", "logo.svg", "logo.jpg", "logo.webp"]:
    if os.path.exists(ext):
        st.image(ext, width=240)
        logo_loaded = True
        break

if not logo_loaded:
    st.markdown(f"""
    <div style="display: flex; align-items: center; margin-top: -10px; margin-bottom: 20px; flex-wrap: wrap; gap: 12px;">
        <svg width="235" height="44" viewBox="0 0 235 44" xmlns="http://www.w3.org/2000/svg" style="border-radius: 4px; box-shadow: 0 2px 6px rgba(0,0,0,0.18);">
            <rect width="235" height="44" fill="#003865"/>
            <rect width="5" height="44" fill="#E67E22"/>
            <g transform="translate(14, 7)" stroke="#ffffff" stroke-width="1.5" fill="none">
                <path d="M2,8 L15,2 L28,8" stroke="#E67E22" stroke-width="2" fill="rgba(230,126,34,0.2)"/>
                <rect x="2" y="8" width="26" height="20" rx="1" fill="#004d8c"/>
                <line x1="2" y1="14" x2="28" y2="14" stroke-opacity="0.6"/>
                <line x1="2" y1="21" x2="28" y2="21" stroke-opacity="0.6"/>
                <line x1="10" y1="8" x2="10" y2="28" stroke-opacity="0.4"/>
                <line x1="20" y1="8" x2="20" y2="28" stroke-opacity="0.4"/>
            </g>
            <text x="52" y="21" font-family="Arial, Helvetica, sans-serif" font-size="16" font-weight="900" fill="#ffffff" letter-spacing="1.5">SCHUMANN</text>
            <text x="52" y="35" font-family="Arial, Helvetica, sans-serif" font-size="10" font-weight="bold" fill="#E67E22" letter-spacing="3.5">TANKS</text>
        </svg>
        <span style="color: #666; font-size: 15px; font-weight: 500;">| &nbsp;{t["subtitle"]}</span>
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

if st.session_state.get("auto_saved_msg"):
    st.success(st.session_state.pop("auto_saved_msg"))

# 2. RYCHLÝ PŘÍJEM (rozlišuje i různá balení stejného materiálu)
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
            
            # AUTOMATICKÁ ZÁLOHA DO GOOGLE TABULKY
            if sync_to_cloud():
                st.session_state["auto_saved_msg"] = t["add_success"].format(add_qty=add_qty, sel_mat=sel_label)
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
    submit_table = st.form_submit_button(t["confirm_table"], type="primary")

if submit_table:
    if search_query:
        st.session_state.df.update(edited_df)
        new_rows = edited_df.index.difference(st.session_state.df.index)
        if not new_rows.empty:
            st.session_state.df = pd.concat([st.session_state.df, edited_df.loc[new_rows]], ignore_index=True)
    else:
        st.session_state.df = edited_df.reset_index(drop=True)
    
    # AUTOMATICKÁ ZÁLOHA DO GOOGLE TABULKY HNED PO POTVRZENÍ ZMĚN
    if sync_to_cloud():
        st.session_state["auto_saved_msg"] = t["table_saved"]
    st.rerun()

# 4. RUČNÍ ULOŽENÍ DO CLOUDU
if st.button(t["save_cloud"]):
    if sync_to_cloud():
        st.success(t["save_success"])

st.divider()

# 5. VÝPOČTY (Automatické sčítání stejného materiálu napříč různými baleními)
st.subheader(t["overview"])
df_raw = st.session_state.df.copy()
df_raw = df_raw[df_raw["Materiál"].astype(str).str.strip() != ""]

if not df_raw.empty:
    for c in ["Ks v balení", "Počet balení", "Požadováno ks"]:
        df_raw[c] = pd.to_numeric(df_raw[c], errors="coerce").fillna(0)

    # Výpočet kusů pro každý jednotlivý řádek (krabici)
    df_raw["Row_Total"] = df_raw["Ks v balení"] * df_raw["Počet balení"]
    
    # Klíč pro sjednocení názvů (ignoruje mezery na konci a rozdíly malá/velká písmena)
    df_raw["Mat_Key"] = df_raw["Materiál"].astype(str).str.strip().str.upper()

    # Seskupení a sečtení podle materiálu
    df_grouped = df_raw.groupby("Mat_Key", as_index=False, sort=False).agg({
        "Materiál": lambda x: str(x.iloc[0]).strip(),
        "Umístění": lambda x: ", ".join(dict.fromkeys([str(v).strip() for v in x if str(v).strip() != ""])),
        "Row_Total": "sum",
        "Požadováno ks": "max",  # Vezme nejvyšší zadaný požadavek u daného materiálu
        "Ks v balení": "max"     # Pro orientační výpočet chybějících balení
    })

    df_grouped.rename(columns={"Row_Total": "Celkem ks"}, inplace=True)
    df_grouped["Chybí ks"] = (df_grouped["Požadováno ks"] - df_grouped["Celkem ks"]).clip(lower=0)
    df_grouped["Chybí balení"] = df_grouped.apply(
        lambda r: math.ceil(r["Chybí ks"] / r["Ks v balení"]) if r["Ks v balení"] > 0 else 0, axis=1
    )
    df_grouped["Stav"] = df_grouped["Chybí ks"].apply(lambda x: t["status_ok"] if x == 0 else t["status_miss"])

    df_display = df_grouped[["Materiál", "Umístění", "Celkem ks", "Požadováno ks", "Chybí ks", "Chybí balení", "Stav"]].rename(columns={
        "Materiál": t["col_mat"],
        "Umístění": t["col_loc"],
        "Celkem ks": t["col_tot"],
        "Požadováno ks": t["col_req"],
        "Chybí ks": t["col_miss_pcs"],
        "Chybí balení": t["col_miss_pck"],
        "Stav": t["col_stat"]
    })

    st.dataframe(df_display, use_container_width=True, hide_index=True)
else:
    df_grouped = pd.DataFrame()
    st.info(t["empty_table"])

# 6. PDF EXPORT (Tiskne sečtený přehled)
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
            stat_txt = "OK" if row["Chybí ks"] == 0 else ("Fehlt" if t["lang_code"] == "DE" else "Chybi")
            pdf.cell(cols_pdf[0][1], 8, clean_pdf_text(row["Materiál"]), border=1)
            pdf.cell(cols_pdf[1][1], 8, clean_pdf_text(row["Umístění"]), border=1)
            pdf.cell(cols_pdf[2][1], 8, str(int(row["Celkem ks"])), border=1, align="C")
            pdf.cell(cols_pdf[3][1], 8, str(int(row["Požadováno ks"])), border=1, align="C")
            pdf.cell(cols_pdf[4][1], 8, str(int(row["Chybí ks"])), border=1, align="C")
            pdf.cell(cols_pdf[5][1], 8, stat_txt, border=1, align="C")
            pdf.ln()
            
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        pdf.output(tmp.name)
        pdf_filename = "Bestandsliste_Schumann.pdf" if t["lang_code"] == "DE" else "Inventar_Schumann.pdf"
        with open(tmp.name, "rb") as f:
            st.download_button(t["download_pdf"], f, pdf_filename, "application/pdf")
