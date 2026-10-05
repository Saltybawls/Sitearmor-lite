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
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbyuQSbXqEFj4bCLxDzEnAFy47yzvyvbOC7MBbuGx2V4d531ML0BI0aUoJw3vsoLus2v/exec"

# Načtení dat z Google Tabulky
@st.cache_data(ttl=5)
def load_from_google():
    if WEB_APP_URL == "SEM_VLOZ_URL_Z_GOOGLE_SCRIPTS":
        # Výchozí data s novými sloupci
        return pd.DataFrame([
            {"Materiál": "Šrouby M10", "Ks v balení": 50, "Počet balení": 20, "Požadováno ks": 1500},
            {"Materiál": "Flanched DN 150", "Ks v balení": 1, "Počet balení": 10, "Požadováno ks": 10}
        ])
    try:
        response = requests.get(WEB_APP_URL)
        data = response.json()
        if data:
            return pd.DataFrame(data)
        else:
            return pd.DataFrame(columns=["Materiál", "Ks v balení", "Počet balení", "Požadováno ks"])
    except:
        st.error("Nepodařilo se načíst data z Google Tabulky. Zkontroluj připojení.")
        return pd.DataFrame(columns=["Materiál", "Ks v balení", "Počet balení", "Požadováno ks"])

# Inicializace dat
if 'material_data' not in st.session_state:
    st.session_state.material_data = load_from_google()

st.subheader("📋 Aktuální inventář / Seznam materiálu")
st.markdown("Zadej kusy v balení, kolik balení dorazilo, a požadovaný stav. Výpočty proběhnou automaticky.")

# Interaktivní tabulka
edited_df = st.data_editor(
    st.session_state.material_data, 
    num_rows="dynamic",
    use_container_width=True,
    key="data_editor"
)

# Automatické výpočty pro přehled pod tabulkou
if not edited_df.empty:
    df_calc = edited_df.copy()
    
    # Ošetření číselných hodnot
    df_calc["Ks v balení"] = pd.to_numeric(df_calc["Ks v balení"], errors="coerce").fillna(0)
    df_calc["Počet balení"] = pd.to_numeric(df_calc["Počet balení"], errors="coerce").fillna(0)
    df_calc["Požadováno ks"] = pd.to_numeric(df_calc["Požadováno ks"], errors="coerce").fillna(0)
    
    # Výpočty
    df_calc["Celkem ks"] = df_calc["Ks v balení"] * df_calc["Počet balení"]
    df_calc["Chybí ks"] = df_calc["Požadováno ks"] - df_calc["Celkem ks"]
    df_calc["Chybí ks"] = df_calc["Chybí ks"].apply(lambda x: x if x > 0 else 0)
    
    # Výpočet chybějících balení (ochrana před dělením nulou)
    def calc_missing_packs(row):
        if row["Ks v balení"] > 0 and row["Chybí ks"] > 0:
            return math.ceil(row["Chybí ks"] / row["Ks v balení"])
        return 0

    df_calc["Chybí balení"] = df_calc.apply(calc_missing_packs, axis=1)

    st.markdown("### 📊 Přehled stavu a chybějícího materiálu")
    
    # Zobrazíme přehledovou tabulku včetně chybějících balení
    st.dataframe(
        df_calc[["Materiál", "Celkem ks", "Požadováno ks", "Chybí ks", "Chybí balení"]],
        use_container_width=True
    )

# Tlačítko pro odeslání dat do Google Tabulky
if st.button("☁️ Uložit a odeslat do Google Tabulky", type="primary"):
    if WEB_APP_URL == "SEM_VLOZ_URL_Z_GOOGLE_SCRIPTS":
        st.warning("Nejprve v kódu nastav URL adresu Google skriptu!")
    else:
        with st.spinner("Ukládám do cloudu..."):
            records = edited_df.to_dict(orient="records")
            try:
                response = requests.post(WEB_APP_URL, json=records)
                if response.status_code == 200:
                    st.session_state.material_data = edited_df
                    st.success("Data byla úspěšně uložena do Google Tabulky!")
                else:
                    st.error("Chyba při ukládání na server.")
            except Exception as e:
                st.error(f"Chyba připojení: {e}")

st.divider()

# Sekce pro export do PDF
st.subheader("🖨 Export inventáře do PDF")

if st.button("Generovat PDF soupis"):
    if edited_df.empty:
        st.warning("Tabulka je prázdná, není co exportovat.")
    else:
        pdf = FPDF()
        pdf.add_page()
        
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "SiteArmor - Inventarni soupis", ln=True, align="C")
        pdf.ln(10)
        
        pdf.set_font("Arial", "B", 9)
        pdf.cell(60, 10, "Material", border=1)
        pdf.cell(25, 10, "Ks/Bal", border=1, align="C")
        pdf.cell(25, 10, "Baleni", border=1, align="C")
        pdf.cell(25, 10, "Celkem ks", border=1, align="C")
        pdf.cell(25, 10, "Chybi ks", border=1, align="C")
        pdf.cell(30, 10, "Chybi bal.", border=1, align="C")
        pdf.ln()
        
        pdf.set_font("Arial", "", 9)
        for index, row in df_calc.iterrows():
            material_text = str(row["Materiál"]).encode('latin-1', 'replace').decode('latin-1')
            
            pdf.cell(60, 10, material_text, border=1)
            pdf.cell(25, 10, str(int(row["Ks v balení"])), border=1, align="C")
            pdf.cell(25, 10, str(int(row["Počet balení"])), border=1, align="C")
            pdf.cell(25, 10, str(int(row["Celkem ks"])), border=1, align="C")
            pdf.cell(25, 10, str(int(row["Chybí ks"])), border=1, align="C")
            pdf.cell(30, 10, str(int(row["Chybí balení"])), border=1, align="C")
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
