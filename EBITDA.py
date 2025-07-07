import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io

mapping = {  # ... (mapping identique à avant) ...
    # [COLLE ICI TON DICT SEGMENTS]
}
special_line = "INTERETS DES EMPRUNTS ET DETTES"

def get_segment(nom):
    for seg, lignes in mapping.items():
        if str(nom).strip().upper() in [x.strip().upper() for x in lignes]:
            return seg
    if str(nom).strip().upper() == special_line:
        return "INTERETS DES EMPRUNTS ET DETTES"
    return "Autres"

st.set_page_config(page_title="Analyse Charges EBITDA", layout="wide")
st.title("Analyse des Charges - Import CSV à entêtes fusionnées (dates fin de mois + Débit/Crédit)")

uploaded_file = st.file_uploader("Importe ton CSV (ou Excel)", type=["csv", "xlsx"])

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
            # Détection séparateur sur la 6ème ligne réelle (index 5)
            sep_candidates = [';', ',', '\t', '|']
            sep = max(sep_candidates, key=lambda c: lines[5].count(c))
            # Nettoyage : récupérer lignes 4 et 5 pour les headers
            header_date = lines[3].split(sep)
            header_type = lines[4].split(sep)
            new_columns = []
            for date, sous in zip(header_date, header_type):
                if sous and sous.strip() != 'Intitulé':
                    col = f"{date.strip()} {sous.strip()}"
                elif sous:
                    col = sous.strip()
                elif date:
                    col = date.strip()
                else:
                    col = ''
                new_columns.append(col)
            # Lecture du dataframe : données réelles à partir de ligne 6 (index 5)
            data_lines = lines[5:]
            s_data = "\n".join(data_lines)
            file_buffer = io.StringIO(s_data)
            df = pd.read_csv(file_buffer, sep=sep, header=None)
            df.columns = new_columns
        else:
            # Excel direct : pandas gère mieux les colonnes fusionnées
            xls = pd.ExcelFile(uploaded_file)
            pre_header = pd.read_excel(xls, header=None, nrows=6)
            date_row = pre_header.iloc[3].fillna('')
            sous_row = pre_header.iloc[4].fillna('')
            new_columns = []
            for date, sous in zip(date_row, sous_row):
                if sous and sous != 'Intitulé':
                    col = f"{str(date).strip()} {str(sous).strip()}"
                elif sous:
                    col = sous.strip()
                elif date:
                    col = str(date).strip()
                else:
                    col = ''
                new_columns.append(col)
            df = pd.read_excel(xls, header=None, skiprows=5)
            df.columns = new_columns
        # Enlève colonnes vides
        df = df.loc[:, df.columns.notna() & (df.columns != '')]

        st.subheader("Aperçu fichier importé (colonnes reconstituées)")
        st.dataframe(df.head(20), use_container_width=True)

        df["SEGMENT"] = df.iloc[:, 0].apply(get_segment)
        debit_cols = [c for c in df.columns if "Débit" in c]
        credit_cols = [c for c in df.columns if "Crédit" in c or "Credit" in c]
        mois_possibles = sorted(set([c.split()[0] for c in debit_cols if c.split()[0] != 'Intitulé']))
        mois_selection = st.multiselect("Sélectionne les dates à afficher :", mois_possibles, default=mois_possibles[-1:] if mois_possibles else [])

        for mois in mois_selection:
            debit_col = next((c for c in debit_cols if mois == c.split()[0]), None)
            credit_col = next((c for c in credit_cols if mois == c.split()[0]), None)
            if debit_col and credit_col:
                agg = df.groupby("SEGMENT")[[debit_col, credit_col]].sum(numeric_only=True)
                st.subheader(f"Charges par segment - {mois}")
                st.dataframe(agg, use_container_width=True)
                # Graphe
                fig, ax = plt.subplots()
                agg[debit_col].plot(kind="bar", label="Débit", alpha=0.7, ax=ax)
                agg[credit_col].plot(kind="bar", label="Crédit", alpha=0.7, color="orange", ax=ax)
                plt.title(f"Débits & Crédits par segment ({mois})")
                plt.xlabel("Segment")
                plt.ylabel("Montant")
                plt.legend()
                plt.tight_layout()
                st.pyplot(fig)

        # Cas particulier :
        if "INTERETS DES EMPRUNTS ET DETTES" in df["SEGMENT"].values:
            st.subheader("INTERETS DES EMPRUNTS ET DETTES :")
            st.dataframe(df[df["SEGMENT"] == "INTERETS DES EMPRUNTS ET DETTES"], use_container_width=True)

        # Export CSV
        if mois_selection:
            export_cols = [c for c in debit_cols + credit_cols if any(m == c.split()[0] for m in mois_selection)]
            export = df.groupby("SEGMENT")[export_cols].sum()
            csv = export.to_csv().encode('utf-8')
            st.download_button("Télécharger le tableau agrégé", csv, "charges_agrégées.csv", "text/csv")

    except Exception as e:
        st.error(f"Erreur lors du traitement du fichier : {e}")
else:
    st.info("Uploade un fichier CSV ou Excel (2 lignes d'en-tête : date fin de mois + Débit/Crédit) pour commencer l'analyse.")
