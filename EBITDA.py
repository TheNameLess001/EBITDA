import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
import re
import calendar
from collections import Counter

mapping = {
    # ... Ton mapping complet ici ...
    "ACHATS": [
        "ACHATS DE MARCHANDISES revente", "ACHAT ALIZEE", "ACHAT BOGOODS", "ACHAT GRAPOS", "ACHAT HYGYENE SDHE",
        "STOCK INITIAL", "STOCK FINAL", "ACHATS LYDEC (EAU+ELECTRICITE)", "ACHATS DE PETITS EQUIPEMENTS FOURNITURES",
        "ACHAT TENUES", "ACHATS DE FOURNITURES DE BUREAU"
    ],
    # ... les autres groupes ...
    "INTERETS / FINANCE": [
        "INTERETS DES EMPRUNTS ET DETTES"
    ]
}
SEGMENTS_ORDER = list(mapping.keys())

def get_segment(nom):
    for seg, lignes in mapping.items():
        if isinstance(nom, str) and nom.strip().upper() in [x.strip().upper() for x in lignes]:
            return seg
    if isinstance(nom, str) and nom.strip().upper() == "INTERETS DES EMPRUNTS ET DETTES":
        return "INTERETS / FINANCE"
    return None

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

def mad_format(x):
    try:
        x = float(x)
        if pd.isna(x):
            return ""
        return "{:,.0f} MAD".replace(",", " ").format(x)
    except:
        return ""

def extract_month_name(header):
    m = re.search(r'Solde au (\d{2})[/-](\d{2})[/-](\d{4})', header)
    if m:
        month = int(m.group(2))
        year = m.group(3)
        return f"{calendar.month_name[month]} {year}"
    return header

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
            header4 = lines[3].split(sep)
            header4 = [str(x).strip() for x in header4]
            header4 = make_unique(header4)
            header5 = lines[4].split(sep)
            header5 = [str(x).strip() for x in header5]
            data_lines = lines[5:]
            s_data = "\n".join(data_lines)
            file_buffer = io.StringIO(s_data)
            df = pd.read_csv(file_buffer, sep=sep, header=None)
            df.columns = header4
        else:
            xls = pd.ExcelFile(uploaded_file)
            header4 = pd.read_excel(xls, header=None, nrows=4).iloc[3].astype(str).str.strip().tolist()
            header4 = make_unique(header4)
            header5 = pd.read_excel(xls, header=None, nrows=5).iloc[4].astype(str).str.strip().tolist()
            df = pd.read_excel(xls, header=None, skiprows=5)
            df.columns = header4

        # Détection colonne d’intitulés charges
        mapping_vals = set()
        for lignes in mapping.values():
            mapping_vals.update([x.strip().upper() for x in lignes])
        detected_intitule_col = None
        for col in df.columns:
            sample = df[col].astype(str).str.strip().str.upper()
            if sample.isin(mapping_vals).any():
                detected_intitule_col = col
                break
        if detected_intitule_col is None:
            st.error("Impossible de détecter la colonne d'intitulé charges automatiquement. Vérifie ton mapping et la structure du fichier.")
            st.stop()

        # Colonnes "Solde au ..."/Débit
        mois_cols = []
        mois_headers = []
        for idx, (h4, h5) in enumerate(zip(header4, header5)):
            if h4.startswith("Solde au") and h5 == "Débit":
                mois_cols.append(df.columns[idx])
                mois_headers.append(h4)
        mois_names = [extract_month_name(h) for h in mois_headers]

        # Nettoyage & conversion montants français/espaces
        for col in mois_cols:
            df[col] = (
                df[col].astype(str)
                .str.replace(",", ".", regex=False)
                .str.replace(" ", "", regex=False)
                .str.replace("\u202f", "", regex=False)
            )
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # Affecte le segment à chaque ligne
        df["SEGMENT"] = df[detected_intitule_col].apply(get_segment)

        # Filtrer pour ne garder QUE les lignes avec un segment connu (donc plus de "Autres" ni None)
        df = df[df["SEGMENT"].notnull()]
        df["SEGMENT"] = pd.Categorical(df["SEGMENT"], categories=SEGMENTS_ORDER, ordered=True)

        # Tableau global annuel
        agg_annee = df.groupby("SEGMENT", observed=False)[mois_cols].sum(numeric_only=True)
        agg_annee = agg_annee.reindex(SEGMENTS_ORDER).fillna(0)
        agg_annee["Total Année"] = agg_annee[mois_cols].sum(axis=1)
        display_agg_annee = agg_annee.copy()
        display_agg_annee.columns = [*mois_names, "Total Année"]
        display_agg_annee = display_agg_annee.applymap(mad_format)
        st.subheader("Tableau annuel (somme de tous les mois) par segment")
        st.dataframe(display_agg_annee, use_container_width=True)

        # Scroll horizontal sur les mois (vue détaillée)
        st.subheader("Tableaux par mois (scroll horizontal possible)")
        tabs = st.tabs(mois_names)
        for i, col in enumerate(mois_cols):
            with tabs[i]:
                agg_mois = df.groupby("SEGMENT", observed=False)[[col]].sum(numeric_only=True)
                agg_mois = agg_mois.reindex(SEGMENTS_ORDER).fillna(0)
                agg_mois.columns = [mois_names[i]]
                agg_mois[mois_names[i]] = agg_mois[mois_names[i]].apply(mad_format)
                st.dataframe(agg_mois, use_container_width=True)

        # GRAPHIQUE BAR CHART GROUPÉ
        st.subheader("Barres groupées : variation de chaque segment par mois")
        graph_df = agg_annee.loc[SEGMENTS_ORDER, mois_cols]
        graph_df.columns = mois_names
        graph_df = graph_df.T  # index = mois_names, columns = segments
        # Fillna (robuste, et arrondit si tu veux)
        graph_df = graph_df.fillna(0)
        fig, ax = plt.subplots(figsize=(min(14, 1.5+0.9*len(mois_names)), 7))
        bar_width = 0.8 / len(SEGMENTS_ORDER)
        indices = range(len(mois_names))
        for i, seg in enumerate(SEGMENTS_ORDER):
            bar_vals = graph_df[seg].values if seg in graph_df else [0]*len(mois_names)
            ax.bar([x + i*bar_width for x in indices], bar_vals, bar_width, label=seg)
        ax.set_xticks([x + bar_width*len(SEGMENTS_ORDER)/2 for x in indices])
        ax.set_xticklabels(mois_names, rotation=45, ha="right")
        ax.set_ylabel("Montant (MAD)")
        ax.set_xlabel("Mois")
        ax.set_title("Variation mensuelle des segments (barres groupées)")
        ax.legend(loc="upper left", bbox_to_anchor=(1,1))
        plt.tight_layout()
        st.pyplot(fig)

    except Exception as e:
        st.error(f"{e}")
