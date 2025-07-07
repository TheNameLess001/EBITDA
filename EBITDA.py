import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
from collections import Counter

mapping = {
    # Mets ici ton mapping complet (copie les intitulés EXACTS de ta première colonne)
    "ACHATS": ["ACHATS DE MARCHANDISES revente", "ACHAT ALIZEE", ...],
    "SERVICES": ["CONVENTION MEDECIN (1an)", "HONORAIRES COMPTA (moore)", ...],
    # ...
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
uploaded_file = st.file_uploader("Fichier", type=["csv", "xlsx"])

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

        # 1. Afficher toutes les lignes de la première colonne (intitulés charges)
        st.dataframe(df.iloc[:, 0], use_container_width=True)

        # 2. Mapping segment
        df["SEGMENT"] = df.iloc[:, 0].apply(get_segment)
        analyse_cols = [col for col in df.columns if col not in [df.columns[0], "SEGMENT"]]

        # 3. Vue tableau pour chaque segment
        for seg in df["SEGMENT"].unique():
            sub_df = df[df["SEGMENT"] == seg]
            if len(sub_df) == 0 or seg == "":
                continue
            st.subheader(seg)
            agg = sub_df[analyse_cols].apply(pd.to_numeric, errors='coerce').sum().to_frame().T
            agg.index = [seg]
            st.dataframe(agg, use_container_width=True)

        # 4. Graphique pour chaque colonne/mois
        for col in analyse_cols:
            agg = df.groupby("SEGMENT")[[col]].sum(numeric_only=True)
            fig, ax = plt.subplots()
            bars = ax.bar(agg.index, agg[col])
            ax.set_title(col)
            plt.xticks(rotation=45, ha="right")
            plt.tight_layout()
            st.pyplot(fig)

    except Exception as e:
        st.error(f"{e}")
