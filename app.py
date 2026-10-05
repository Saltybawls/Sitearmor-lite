import streamlit as st
import pandas as pd
from fpdf import FPDF
import tempfile
import requests
import math

st.set_page_config(page_title="SiteArmor Lite", page_icon="🛡️")
st.title("🛡️ SiteArmor Lite")

# Tvoje Google Script URL
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbyuQSbXqEFj4bCLxDzEnAFy47yzvyvbOC7MBbuGx2V4d531ML0BI0aUoJw3vsoLus2v/exec"
COLS = ["Materiál", "Umístění", "Ks v balení", "Počet balení", "Požadováno ks"]

# 1. ČISTÉ NAČTENÍ DAT BEZ BALASTU (žádná cache, která to zasekávala)
def load_data():
    try:
        r = requests.get(WEB_APP_URL, timeout=3)
        df = pd.DataFrame(r.json())
    except:
        df = pd.DataFrame(columns=COLS) # Pokud Google neodpoví, vytvoří prázdnou tabulku
    
    # Pojistka: Vždy zajistíme správné sloupce, i když je tabulka zrovna prázdná
    for col in COLS:
        if col not in df.columns:
            df[col] = "" if col in ["Materiál", "Umístění"] else 0
    return df[COLS]

# Načteme data jen při startu aplikace
if "df" not in st.session_state:
    st.session_state.df = load_data()

# 2. RYCHLÝ PŘÍJEM (Zobrazí se jen, když v tabulce už nějaký materiál je)
mats = [m for m in st.session_state.df["Materiál"].unique() if str(m).strip() != ""]
if mats:
    st.subheader("📦 Rychlý příjem")
    with st.form("add_form"):
        c1, c2, c3 = st.columns([2, 1, 1])
        sel_mat = c1.selectbox("Vyber materiál", mats)
        add_qty = c2.number_input("Přidat balení", min_value=1, step=1)
        
        if c3.form_submit_button("➕ Přičíst"):
            idx = st.session_state.df[st.session_state.df["Materiál"] == sel_mat].index[0]
            curr = pd.to_numeric(st.session_state.df.loc[idx, "Počet balení"], errors="coerce") or 0
            st.session_state.df.loc[idx, "Počet balení"] = curr + add_qty
            st.success(f"Přidáno {add_qty} balení k {sel_mat}! Nezapomeň uložit do cloudu.")
            st.rerun()

st.divider()

# 3. HLAVNÍ TABULKA (s možností přidávat řádky úplně dole)
st.subheader("📋 Inventář")
edited_df = st.data_editor(st.session_state.df, num_rows="dynamic", use_container_width=True)
st.session_state.df = edited_df

# 4. ULOŽENÍ
if st.button("☁️ Uložit do cloudu", type="primary"):
    with st.spinner("Odesílám do Google Tabulky..."):
        try:
            records = st.session_state.df.to_dict(orient="records")
            requests.post(WEB_APP_URL, json=records, timeout=5)
            st.success("✅ Uloženo! Můžeš to zkontrolovat na Disku.")
        except Exception:
            st.error("Chyba při ukládání, zkontroluj připojení.")

st.divider()

# 5. VÝPOČTY (Automatický přehled, nedá se do něj psát, jen ukazuje data)
st.subheader("📊 Přehled stavu")
df_calc = st.session_state.df.copy()

# Převod sloupců na čísla
for c in ["Ks v balení", "Počet balení", "Požadováno ks"]:
    df_calc[c] = pd.to_numeric(df_calc[c], errors="coerce").fillna(0)

# Matematika
df_calc["Celkem ks"] = df_calc["Ks v balení"] * df_calc["Počet balení"]
df_calc["Chybí ks"] = (df_calc["Požadováno ks"] - df_calc["Celkem ks"]).clip(lower=0)
df_calc["Chybí balení"] = df_calc.apply(lambda r: math.ceil(r["Chybí ks"] / r["Ks v balení"]) if r["Ks v balení"] > 0 else 0, axis=1)
df_calc["Stav"] = df_calc["Chybí ks"].apply(lambda x: "🟢 Splněno" if x == 0 else "🔴 Chybí")

st.dataframe(df_calc[["Materiál", "Umístění", "Celkem ks", "Požadováno ks", "Chybí ks", "Chybí balení", "Stav"]], use_container_width=True)

# 6. PDF EXPORT (Kompaktní)
if st.button("🖨 Generovat PDF"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Inventarni soupis - SiteArmor", ln=True, align="C")
    pdf.ln(5)
    
    pdf.set_font("Arial", "B", 9)
    cols_pdf = [("Material", 50), ("Umisteni", 30), ("Ks/Bal", 20), ("Baleni", 20), ("Celkem", 20), ("Chybi", 20), ("Ch. bal", 20)]
    for name, w in cols_pdf:
        pdf.cell(w, 8, name, border=1, align="C")
    pdf.ln()
    
    pdf.set_font("Arial", "", 9)
    for _, row in df_calc.iterrows():
        pdf.cell(cols_pdf[0][1], 8, str(row["Materiál"]).encode('latin-1', 'replace').decode('latin-1'), border=1)
        pdf.cell(cols_pdf[1][1], 8, str(row["Umístění"]).encode('latin-1', 'replace').decode('latin-1'), border=1)
        pdf.cell(cols_pdf[2][1], 8, str(int(row["Ks v balení"])), border=1, align="C")
        pdf.cell(cols_pdf[3][1], 8, str(int(row["Počet balení"])), border=1, align="C")
        pdf.cell(cols_pdf[4][1], 8, str(int(row["Celkem ks"])), border=1, align="C")
        pdf.cell(cols_pdf[5][1], 8, str(int(row["Chybí ks"])), border=1, align="C")
        pdf.cell(cols_pdf[6][1], 8, str(int(row["Chybí balení"])), border=1, align="C")
        pdf.ln()
        
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(tmp.name)
    with open(tmp.name, "rb") as f:
        st.download_button("📥 Stáhnout PDF", f, "inventar.pdf", "application/pdf")
