import streamlit as st
import pandas as pd
from fpdf import FPDF
import tempfile
import os

st.set_page_config(page_title="SiteArmor Lite", page_icon="🛡️")
st.title("🛡️ SiteArmor Lite: Správa materiálu na stavbě")

# Inicializace stavu pro položky, ať se data smazáním/změnou neztrácí
if 'material_data' not in st.session_state:
    st.session_state.material_data = pd.DataFrame([
        {"Materiál": "Flanched DN 150", "Počet": 10, "Balení": "Paleta 1"},
        {"Materiál": "Šrouby M16x60", "Počet": 120, "Balení": "Krabice 3"},
        {"Materiál": "Těsnění DN 200", "Počet": 5, "Balení": "Sáček A"}
    ])

st.subheader("📋 Aktuální inventář / Seznam materiálu")
st.markdown("Zde můžeš přímo v tabulce měnit počty nebo balení, případně přidávat nové řádky.")

# Interaktivní tabulka, kde jde přímo přepisovat hodnoty
edited_df = st.data_editor(
    st.session_state.material_data, 
    num_rows="dynamic",
    use_container_width=True
)

# Uložení změn zpět do stavu
st.session_state.material_data = edited_df

st.divider()

# Sekce pro export do PDF
st.subheader("🖨️ Export inventáře do PDF")

if st.button("Generovat PDF soupis", type="primary"):
    if edited_df.empty:
        st.warning("Tabulka je prázdná, není co exportovat.")
    else:
        # Generování PDF pomocí FPDF
        pdf = FPDF()
        pdf.add_page()
        
        # Nastavení fontu
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
            
        # Uložení do dočasného souboru
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
