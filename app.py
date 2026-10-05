import streamlit as st
import pandas as pd
from fpdf import FPDF
import tempfile
import requests
import json

st.set_page_config(page_title="SiteArmor Lite", page_icon="🛡️")
st.title("🛡️ SiteArmor Lite: Správa materiálu na stavbě")

# SEM VLOŽ URL ADRESU TVÉHO GOOGLE SCRIPTU (v uvozovkách):
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbyuQSbXqEFj4bCLxDzEnAFy47yzvyvbOC7MBbuGx2V4d531ML0BI0aUoJw3vsoLus2v/exec"

# Načtení dat z Google Tabulky
@st.cache_data(ttl=5)
def load_from_google():
    if WEB_APP_URL == "SEM_VLOZ_URL_Z_GOOGLE_SCRIPTS":
        # Výchozí data, pokud ještě není nastavena URL
        return pd.DataFrame([
            {"Materiál": "Flanched DN 150", "Počet": 10, "Balení": "Paleta 1"},
            {"Materiál": "Šrouby M16x60", "Počet": 120, "Balení": "Krabice 3"}
        ])
    try:
        response = requests.get(WEB_APP_URL)
        data = response.json()
        if data:
            return pd.DataFrame(data)
        else:
            return pd.DataFrame(columns=["Materiál", "Počet", "Balení"])
    except:
        st.error("Nepodařilo se načíst data z Google Tabulky. Zkontroluj připojení.")
        return pd.DataFrame(columns=["Materiál", "Počet", "Balení"])

# Inicializace dat
if 'material_data' not in st.session_state:
    st.session_state.material_data = load_from_google()

st.subheader("📋 Aktuální inventář / Seznam materiálu")
st.markdown("Uprav položky, přidej nové řádky a ulož změny jedním tlačítkem do cloudu.")

# Interaktivní tabulka
edited_df = st.data_editor(
    st.session_state.material_data, 
    num_rows="dynamic",
    use_container_width=True,
    key="data_editor"
)

# Tlačítko pro odeslání dat do Google Tabulky
if st.button("☁️ Uložit a odeslat do Google Tabulky", type="primary"):
    if WEB_APP_URL == "SEM_VLOZ_URL_Z_GOOGLE_SCRIPTS":
        st.warning("Nejprve v kódu nastav URL adresu Google skriptu!")
    else:
        with st.spinner("Ukládám do cloudu..."):
            # Převod tabulky na JSON
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
        
        pdf.set_font("Arial", "B", 12)
        pdf.cell(90, 10, "Material", border=1)
        pdf.cell(40, 10, "Pocet", border=1, align="C")
        pdf.cell(60, 10, "Baleni", border=1)
        pdf.ln()
        
        pdf.set_font("Arial", "", 12)
        for index, row in edited_df.iterrows():
            material_text = str(row["Materiál"]).encode('latin-1', 'replace').decode('latin-1')
            baleni_text = str(row["Balení"]).encode('latin-1', 'replace').decode('latin-1')
            
            pdf.cell(90, 10, material_text, border=1)
            pdf.cell(40, 10, str(row["Počet"]), border=1, align="C")
            pdf.cell(60, 10, baleni_text, border=1)
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
