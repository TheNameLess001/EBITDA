import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
from collections import Counter

# MAPPING À ADAPTER AVEC TES VRAIS INTITULÉS COLONNE !
mapping = {
    "ACHATS": [
        "ACHATS DE MARCHANDISES revente", "ACHAT ALIZEE", "ACHAT BOGOODS", "ACHAT GRAPOS", "ACHAT HYGYENE SDHE",
        "STOCK INITIAL", "STOCK FINAL", "ACHATS LYDEC (EAU+ELECTRICITE)", "ACHATS DE PETITS EQUIPEMENTS FOURNITURES",
        "ACHAT TENUES", "ACHATS DE FOURNITURES DE BUREAU"
    ],
    "SERVICES": [
        "CONVENTION MEDECIN (1an)", "HONORAIRES COMPTA (moore)", "HONORAIRES SOCIAL (moore)", "HONORAIRES DIVERS"
    ],
    # ... AJOUTE TOUS TES SEGMENTS ...
}
special_line = "INTERETS DES EMPRUNTS ET DETTES"

def get_segment(nom):
    for seg, lignes in mapping.items():
        if str(nom).strip().upper() in [x.strip().upper() for x in lignes]:
            return seg
    if str(nom).strip().upper() == special_line:
        return "INTERETS DES EMPRUNTS ET DETTES"
    return "Autres"

def make_unique(seq):
    counter = Counter()
    res = []
    for s in seq:
        if s in counter:
            counter[s] += 1
            res.append(f"{s}_{counter[s]}")
        else:
            counter[s] = 0
            res.append(s)
    return res

st.set_page_config(layout="wide")

uploaded_file = st.file_uploader("CSV/Excel", type=["csv", "xlsx"])

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            content = uploaded_file.read()
            encodings = ['utf-8', 'ISO-8859-1', 'latin1']
            for enc in encodings:
                try:
                    s = content.decode(enc)
                    break
                except:
                    continue
            lines = s.splitlines()
            sep_candidates = [';', ',', '\t', '|']
            sep = max(sep_candidates, key=lambda c: lines[3].count(c))
            header_row = lines[3].split(sep)
            header_row = [str(x).strip() for x in header_row]
            header_row = make_unique(header_row)
            data_lines = lines[5:]
            s_data = "\n".join(data_lines)
            file_buffer = io.StringIO(s_data)
            df = pd.read_csv(file_buffer, sep=sep, header=None)
            df.columns = header_row
        else:
            xls = pd.ExcelFile(uploaded_file)
            header_row = pd.read_excel(xls, header=None, nrows=4).iloc[3].astype(str).str.strip().tolist()
            header_row = make_unique(header_row)
            df = pd.read_excel(xls, header=None, skiprows=5)
            df.columns = header_row

        possible_cols = [col for col in df.columns]
        intitulé_col = st.selectbox("Colonne intitulé", possible_cols, 0)
        analyse_cols = [col for col in df.columns if col != intitulé_col]

        for col in analyse_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        df["SEGMENT"] = df[intitulé_col].apply(get_segment)

        agg_global = df.groupby("SEGMENT")[analyse_cols].sum(numeric_only=True)
        st.dataframe(agg_global, use_container_width=True)

        mois_selection = st.multiselect("Vue par mois :", analyse_cols, default=[analyse_cols[-1]])

        for col in mois_selection:
            agg = df.groupby("SEGMENT")[[col]].sum(numeric_only=True)
            st.dataframe(agg, use_container_width=True)
            total_par_segment = agg[col].sort_values(ascending=False)
            fig, ax = plt.subplots()
            bars = ax.bar(total_par_segment.index, total_par_segment.values)
            ax.set_title(f"Comparatif {col}")
            plt.xticks(rotation=45, ha="right")
            plt.tight_layout()
            st.pyplot(fig)

    except Exception as e:
        st.error(f"{e}")
