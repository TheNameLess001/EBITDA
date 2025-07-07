import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
from collections import Counter

# Ton mapping segments
mapping = {
    # ... Ton mapping ici ...
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

st.set_page_config(page_title="Analyse Charges EBITDA", layout="wide")
st.title("Analyse Charges EBITDA – Colonnes = Ligne 4 Only")

uploaded_file = st.file_uploader("Importe ton CSV ou Excel", type=["csv", "xlsx"])

if uploaded_file is not None:
    try:
        # --- 1. Lecture brute du header (ligne 4 uniquement) ---
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
            # Les données démarrent à la ligne 6 (index 5)
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

        # --- 2. Segment mapping ---
        df["SEGMENT"] = df.iloc[:, 0].apply(get_segment)

        st.success("Colonnes lues depuis la ligne 4 :")
        for i, c in enumerate(df.columns):
            st.write(f"Colonne {i} : '{c}'")
        st.write("Aperçu du dataframe :")
        st.dataframe(df.head(8))

        # --- 3. Sélection des colonnes à analyser ---
        possible_cols = [col for col in df.columns if col not in ["SEGMENT", "Intitulé", "Compte"]]
        cols_selection = st.multiselect("Sélectionne les colonnes à analyser :", possible_cols, default=possible_cols)

        if not cols_selection:
            st.warning("Aucune colonne sélectionnée, rien à afficher.")
            st.stop()

        # --- 4. Affichage des tableaux et graphes ---
        for col in cols_selection:
            try:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            except:
                pass
            agg = df.groupby("SEGMENT")[[col]].sum(numeric_only=True)
            agg_fmt = agg.applymap(lambda x: f"{x:,.0f} MAD" if pd.notnull(x) else "")
            st.subheader(f"Tableau général : {col} - Tous segments")
            st.dataframe(agg_fmt, use_container_width=True)
            for seg in agg.index:
                st.markdown(f"**{seg}**")
                st.dataframe(agg_fmt.loc[[seg]], use_container_width=True)
            if agg[col].sum() > 0:
                total_par_segment = agg[col].sort_values(ascending=False)
                fig, ax = plt.subplots()
                bars = ax.bar(total_par_segment.index, total_par_segment.values)
                ax.set_title(f"Comparatif segments ({col})")
                ax.set_xlabel("Segment")
                ax.set_ylabel("Somme (MAD)")
                ax.bar_label(bars, fmt='%.0f')
                plt.xticks(rotation=45, ha="right")
                plt.tight_layout()
                st.pyplot(fig)
            else:
                st.info(f"Colonne {col} : pas de données numériques à afficher.")

        if "INTERETS DES EMPRUNTS ET DETTES" in df["SEGMENT"].values:
            st.subheader("INTERETS DES EMPRUNTS ET DETTES :")
            st.dataframe(df[df["SEGMENT"] == "INTERETS DES EMPRUNTS ET DETTES"], use_container_width=True)

        if cols_selection:
            export_cols = cols_selection
            export = df.groupby("SEGMENT")[export_cols].sum()
            csv = export.to_csv().encode('utf-8')
            st.download_button("Télécharger le tableau agrégé", csv, "charges_agrégées.csv", "text/csv")

    except Exception as e:
        st.error(f"Erreur lors du traitement du fichier : {e}")

else:
    st.info("Uploade un fichier CSV ou Excel pour commencer l'analyse.")
