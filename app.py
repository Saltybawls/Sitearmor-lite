import streamlit as st
import pandas as pd
from fpdf import FPDF
import tempfile
import requests
import json
import math

st.set_page_config(page_title="SiteArmor Lite", page_icon="🛡️")
st.title("🛡️ SiteArmor Lite: Správa materiálu na stavbě")

# SEM VLOŽ SVOJI URL ADRESU Z GOOGLE SCRIPTS:
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbz8_GOd-U9n7f9Q-LIQbRINu4n9ioarj4-V3RI2sEKq7UAwoKyrDnN7Q8MIN8voq1aY/exec"

# Načtení dat z Google Tabulky
@st.cache_data(ttl=5)
def load_from_google():
    default_df = pd.DataFrame([
        {"Materiál": "Šrouby M10", "Umístění": "Sklad A", "Ks v balení": 50, "Počet balení": 20, "Požadováno ks": 1500},
        {"Materiál": "Flanched DN 150", "Umístění": "1. patro", "Ks v balení": 1, "Počet balení": 10, "Požadováno ks": 10}
    ])
    
    if WEB_APP_URL == "SEM_VLOZ_URL_Z_GOOGLE_SCRIPTS":
        return default_df
    try:
        response = requests.get(WEB_APP_URL)
        data = response.json()
        if data:
            df = pd.DataFrame(data)
            required_cols = ["Materiál", "Umístění", "Ks v balení", "Počet balení", "Požadováno ks"]
            if "Umístění" not in df.columns:
                df["Umístění"] = "Hlavní sklad"
            if all(col in df.columns for col in ["Materiál", "Ks v balení", "Počet balení", "Požadováno ks"]):
                return df
        return default_df
    except:
        return default_df

# Inicializace dat v session_state
if 'material_data' not in st.session_state:
    st.session_state.material_data = load_from_google()

# --- RYCHLÝ PŘÍJEM MATERIÁLU (PŘIČÍTÁNÍ) ---
st.subheader("📦 Rychlý příjem materiálu na stavbu")
st.markdown("Přivezli novou dodávku? Vyber položku, zadej počet **nově přivezených balení** a rovnou se to přičte k aktuálnímu stavu.")

if not st.session_state.material_data.empty:
    with st.form("quick_add_form"):
        col_f1, col_f2, col_f3 = st.columns([2, 1, 1])
        
        material_list = st.session_state.material_data["Materiál"].tolist()
        selected_material = col_f1.selectbox("Vyber materiál", material_list)
        added_packs = col_f2.number_input("Přidat balení", min_value=1, value=1, step=1)
        submit_add = col_f3.form_submit_button("➕ Přičíst k zásobě")
        
        if submit_add:
            idx = st.session_state.material_data[st.session_state.material_data["Materiál"] == selected_material].index[0]
            current_packs = int(st.session_state.material_data.loc[idx, "Počet balení"])
            st.session_state.material_data.loc[idx, "Počet balení"] = current_packs + int(added_packs)
            st.success("Úspěšně přičteno! Nezapomeň dole uložit do cloudu.")
            st.rerun()

st.divider()

# --- HLAVNÍ INVENTÁŘ A VYHLEDÁVÁNÍ ---
st.subheader("📋 Kompletní inventář & Úprava dat")

search_query = st.text_input("🔍 Hledat v materiálu (napiš název nebo část...)", "")

df_to_edit = st.session_state.material_data.copy()
if search_query:
    df_to_edit = df_to_edit[df_to_edit["Materiál"].str.contains(search_query, case=False, na=False)]

edited_df = st.data_editor(
    df_to_edit, 
    num_rows="dynamic",
    use_container_width=True,
    key="data_editor"
)

if search_query and not edited_df.equals(df_to_edit):
    for idx, row in edited_df.iterrows():
        st.session_state.material_data.loc[idx] = row

if st.button("☁️ Uložit a odeslat do Google Tabulky", type="primary"):
    if WEB_APP_URL == "SEM_VLOZ_URL_Z_GOOGLE_SCRIPTS":
        st.warning("Nejprve v kódu nastav URL adresu Google skriptu!")
    else:
        with st.spinner("Ukládám do cloudu..."):
            records = st.session_state.material_data.to_dict(orient="records")
            try:
                response = requests.post(WEB_APP_URL, json=records)
                if response.status_code == 200:
                    st.success("Data byla úspěšně uložena do Google Tabulky!")
                else:
                    st.error("Chyba při ukládání na server.")
            except Exception as e:
                st.error(f"Chyba připojení: {e}")

st.divider()

# --- ANALYTICKÝ PŘEHLED S INDIKÁTORY ---
st.subheader("📊 Přehled stavu a chybějícího materiálu")

if not st.session_state.material_data.empty:
    df_calc = st.session_state.material_data.copy()
    
    for col in ["Ks v balení", "Počet balení", "Požadováno ks"]:
        if col not in df_calc.columns:
            df_calc[col] = 0

    df_calc["Ks v balení"] = pd.to_numeric(df_calc["Ks v balení"], errors="coerce").fillna(0)
    df_calc["Počet balení"] = pd.to_numeric(df_calc["Počet balení"], errors="coerce").fillna(0)
    df_calc["Požadováno ks"] = pd.to_numeric(df_calc["Požadováno ks"], errors="coerce").fillna(0)
    
    df_calc["Celkem ks"] = df_calc["Ks v balení"] * df_calc["Počet balení"]
    df_calc["Chybí ks"] = df_calc["Požadováno ks"] - df_calc["Celkem ks"]
    df_calc["Chybí ks"] = df_calc["Chybí ks"].apply(lambda x: x if x > 0 else 0)
    
    def calc_missing_packs(row):
        if row["Ks v balení"] > 0 and row["Chybí ks"] > 0:
            return math.ceil(row["Chybí ks"] / row["Ks v balení"])
        return 0

    df_calc["Chybí balení"] = df_calc.apply(calc_missing_packs, axis=1)

    def get_status(row):
        if row["Chybí ks"] == 0:
            return "🟢 Splněno"
        else:
            return "🔴 Chybí"

    df_calc["Stav"] = df_calc.apply(get_status, axis=1)

    st.dataframe(
        df_calc[["Materiál", "Umístění", "Celkem ks", "Požadováno ks", "Chybí ks", "Chybí balení", "Stav"]],
        use_container_width=True
    )

st.divider()

# --- EXPORT DO PDF ---
st.subheader("🖨 Export inventáře do PDF")

if st.button("Generovat PDF soupis"):
    if st.session_state.material_data.empty:
        st.warning("Tabulka je prázdná, není co exportovat.")
    else:
        pdf = FPDF()
        pdf.add_page()
        
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "SiteArmor - Inventarni soupis", ln=True, align="C")
        pdf.ln(10)
        
        pdf.set_font("Arial", "B", 8)
        pdf.cell(50, 10, "Material", border=1)
        pdf.cell(25, 10, "Umisteni", border=1)
        pdf.cell(20, 10, "Ks/Bal", border=1, align="C")
        pdf.cell(20, 10, "Baleni", border=1, align="C")
        pdf.cell(20, 10, "Celkem", border=1, align="C")
        pdf.cell(20, 10, "Chybi ks", border=1, align="C")
        pdf.cell(25, 10, "Chybi bal.", border=1, align="C")
        pdf.ln()
        
        pdf.set_font("Arial", "", 8)
        for index, row in df_calc.iterrows():
            mat_text = str(row["Materiál"]).encode('latin-1', 'replace').decode('latin-1')
            loc_text = str(row["Umístění"]).encode('latin-1', 'replace').decode('latin-1')
            
            pdf.cell(50, 10, mat_text, border=1)
            pdf.cell(25, 10, loc_text, border=1)
            pdf.cell(20, 10, str(int(row["Ks v balení"])), border=1, align="C")
            pdf.cell(20, 10, str(int(row["Počet balení"])), border=1, align="C")
            pdf.cell(20, 10, str(int(row["Celkem ks"])), border=1, align="C")
            pdf.cell(20, 10, str(int(row["Chybí ks"])), border=1, align="C")
            pdf.cell(25, 10, str(int(row["Chybí balení"])), border=1, align="C")
            pdf.ln()
            
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        pdf.output(temp_file.name)
        
        with open(temp_file.name, "rb") as file:
            st.download_button(
                label="📥 Stáhnout vygenerované PDF",
                data=file,
                file_name="site_armor_inventar.pdf",
                mime="application/pdf"
            )
        st.success("PDF bylo úspěšně připraveno ke stažení!")
