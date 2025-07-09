import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
import re
import calendar
from collections import Counter
import numpy as np

# ----- MAPPING -----
mapping = {
    "Nettoyage": [
        "GARDIENNAGE ET MENAGE", "NETTOYAGE FIN DE CHANTIER", "DERATISATIONS / DESINSECTISATION",
        "ACHAT HYGYENE SDHE", "SERVICES DE NETTOYAGE", "BLANCHISSERIE"
    ],
    "Des employés": [
        "APPOINTEMENTS ET SALAIRES", "INDEMNITES ET AVANTAGES DIVERS", "COTISATIONS DE SECURITE SOCIALE",
        "COTISATIONS PREVOYANCE + SANTE", "PROVISION DES CP+CHARGES INITIAL", "PROVISION DES CP+CHARGES FINAL",
        "GRATIFICATIONS DE STAGE", "REMPLACEMENTS", "INCITATIONS"
    ],
    "Leasing": [
        "LOYER URBAN DEVELOPPEURS V", "LOYER URBAN DEVELOPPEURS - CHARGES LOCATIVES",
        "REDEVANCES DE CREDIT BAIL MATERIEL PS FITNESS", "LOYER MATERIEL VIA FPK MAROC",
        "LOCATION DISTRIBUTEUR KIT STORE"
    ],
    "Maintenance et entretien": [
        "ENTRET ET REPAR DES BIENS IMMOBILIERS", "MAINTENANCE IMAFLUIDE", "MAINTENANCE INCENDIE (par semestre)",
        "MAINTENANCE TECHNOGYM", "MAINTENANCE HYDROMASSAGE"
    ],
    "Publicité et relations publiques": [
        "DESIGN ET CREATIVITE", "AFFICHES pub", "FRAIS INAUGURATION / ANNIVERSAIRE",
        "RECEPTIONS", "DISTRIBUTION SUPPORTS PUBLICITAIRES", "EVENEMENTS", "CLIENT MYSTERE", "LOCATION ESPACE PUBLICITAIRES"
    ],
    "Services professionnels": [
        "HONORAIRES COMPTA (moore)", "HONORAIRES SOCIAL (moore)", "HONORAIRES DIVERS",
        "HONO PRESTATION FPK MAROC", "CONSEILS", "CONVENTION MEDECIN (1an)"
    ],
    "Achats et fournitures": [
        "ACHATS DE MARCHANDISES revente", "ACHAT ALIZEE", "ACHAT BOGOODS", "ACHAT GRAPOS",
        "ACHATS DE FOURNITURES DE BUREAU", "ACHAT TENUES",
        "ACHATS DE PETITS EQUIPEMENTS FOURNITURES", "PRODUITS DE NETTOYAGE", "EQUIPEMENTS D'ENTRAINEMENT EN PETITS GROUPES",
    ],
    "Fournitures": [
        "ACHATS LYDEC (EAU+ELECTRICITE)", "ELECTRICITE", "GAZ", "WATER", "DIVERS FOURNITURES"
    ],
    "Téléphones/ Communication": [
        "FRAIS DE TELECOMMUNICATION (orange)", "FRAIS DE TELECOMMUNICATION (Maroc Télécom)", "Téléphone", "Net / wifi"
    ],
    "Entraînement": [
        "COURS COLLECTIFS", "COÛTS DES COURS/PROGRAMMES", "RÉGIMES ALIMENTAIRES ET HÉBERGEMENT", "DIVERS ENTRAÎNEMENT"
    ],
    "Autres": [
        "SERVICES BANCAIRES", "FRAIS ET COMMISSIONS SUR SERVICES BANCAI", "FRAIS COMMISSION NAPS",
        "FRAIS COMMISSIONS CMI", "INSURANCE PREMIUMS", "TRANSPORT ET COURRIER", "SÉCURITÉ",
        "DROITS MUSICAUX", "TAXES ET REDEVANCES", "SANCTIONS ADMINISTRATIVES", "DÉSÉQUILIBRES",
        "INTERETS DES EMPRUNTS ET DETTES", "REDEVANCES FITNESS PARK France 3%", "DROITS D'ENREGISTREMENT ET DE TIMBRE", "ACHATS PRESTATION admin / RH"
    ]
}
SEGMENTS_ORDER = list(mapping.keys())
mapping = {str(k).strip(): [str(x).strip() for x in v] for k, v in mapping.items()}

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
st.title("💼 Analyse des Charges & Segments")

uploaded_file = st.file_uploader("🗂️ Importer le fichier Balance", type=["csv", "xlsx"])

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

        # -- SEGMENTS DETECTION --
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
            st.error("Colonne des intitulés non détectée. Vérifie la structure du fichier !")
            st.stop()

        # -- MOIS COLUMNS DETECTION --
        mois_cols = []
        mois_headers = []
        for idx, (h4, h5) in enumerate(zip(header4, header5)):
            if h4.startswith("Solde au") and h5 == "Débit":
                mois_cols.append(str(df.columns[idx]).strip().replace('\n','').replace('\r',''))
                mois_headers.append(h4)
        mois_names = [extract_month_name(h) for h in mois_headers]
        mois_names = [str(m).strip().replace('\n','').replace('\r','') for m in mois_names]
        mois_cols = [str(m).strip().replace('\n','').replace('\r','') for m in mois_cols]

        # -- FORMAT MONTANTS ULTIME --
        for col in mois_cols:
            df[col] = (
                df[col]
                .astype(str)
                .str.replace(r"[\s\u202f\t\r\n]", "", regex=True)
                .str.replace(",", ".", regex=False)
                .replace({"None": np.nan, "nan": np.nan, "": np.nan})
            )
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # -- AFFECTATION DES SEGMENTS --
        df["SEGMENT"] = df[detected_intitule_col].apply(get_segment)
        df["SEGMENT"] = pd.Categorical(df["SEGMENT"], categories=SEGMENTS_ORDER, ordered=True)
        df = df[df["SEGMENT"].notnull()]

        # -- TABLEAU GLOBAL (ANNUEL) --
        st.markdown("### 📊 Tableau annuel (somme de tous les mois) par segment")
        agg_annee = df.groupby("SEGMENT", observed=False)[mois_cols].sum(numeric_only=True)
        agg_annee = agg_annee.reindex(SEGMENTS_ORDER).fillna(0)
        agg_annee.columns = [str(c).strip().replace('\n','').replace('\r','') for c in agg_annee.columns]
        agg_annee["Total Année"] = agg_annee[mois_cols].sum(axis=1)
        display_agg_annee = agg_annee.copy()
        display_agg_annee.columns = [*mois_names, "Total Année"]
        display_agg_annee = display_agg_annee.applymap(mad_format)
        st.dataframe(display_agg_annee, use_container_width=True)

        # -- INTERACTION "POP-UP" DÉTAILS SEGMENT --
        st.markdown("### 🔍 Détail interactif par segment")
        segment_selected = st.selectbox(
            "Clique sur un segment pour voir le détail des lignes sources :",
            [s for s in SEGMENTS_ORDER if s in df['SEGMENT'].unique()]
        )
        if segment_selected:
            with st.expander(f"Détails pour le segment : {segment_selected}", expanded=True):
                lignes_segment = df[df['SEGMENT'] == segment_selected]
                display_cols = [detected_intitule_col] + mois_cols
                display_lignes = lignes_segment[display_cols].copy()
                for col in mois_cols:
                    display_lignes[col] = display_lignes[col].apply(mad_format)
                st.dataframe(display_lignes, use_container_width=True)

        # -- TABLEAU PAR MOIS --
        st.markdown("### 📅 Tableaux par mois (scroll horizontal)")
        tabs = st.tabs(mois_names)
        for i, col in enumerate(mois_cols):
            with tabs[i]:
                agg_mois = df.groupby("SEGMENT", observed=False)[[col]].sum(numeric_only=True)
                agg_mois = agg_mois.reindex(SEGMENTS_ORDER).fillna(0)
                agg_mois.columns = [mois_names[i]]
                agg_mois[mois_names[i]] = agg_mois[mois_names[i]].apply(mad_format)
                st.dataframe(agg_mois, use_container_width=True)

        # --- NOUVEAU BLOC : Multi-graph segments avec filtre date global ---
        st.markdown("### 🎛️ Compare plusieurs segments (période commune)")

        segments_available = [str(seg).replace("’", "").replace("'", "").replace('"', "").strip() for seg in SEGMENTS_ORDER]
        cols_mois_vraies = [c for c in agg_annee.columns if c != "Total Année"]

        # 1 seul slider période (commune à tous)
        if len(cols_mois_vraies) > 1:
            from_month, to_month = st.select_slider(
                "Sélectionne la période à afficher pour TOUS les graphiques (de ... à ...)",
                options=cols_mois_vraies,
                value=(cols_mois_vraies[0], cols_mois_vraies[-1]),
                key="slider_global"
            )
            idx_start = cols_mois_vraies.index(from_month)
            idx_end = cols_mois_vraies.index(to_month)
            if idx_start > idx_end:
                idx_start, idx_end = idx_end, idx_start
            selected_months = cols_mois_vraies[idx_start:idx_end+1]
        else:
            selected_months = cols_mois_vraies

        segments_selected = st.multiselect(
            "Sélectionne les segments à afficher",
            options=segments_available,
            default=[segments_available[0]],
            help="Ajoute un ou plusieurs segments. Chacun aura son propre graphique sur la période choisie !"
        )

        if segments_selected and selected_months:
            for seg in segments_selected:
                st.markdown(f"#### 📊 Segment : **{seg}** ({from_month} → {to_month})")
                bar_vals = agg_annee.loc[seg, selected_months].values
                fig, ax = plt.subplots(figsize=(min(8, 1 + 0.5*len(selected_months)), 4))
                ax.bar(selected_months, bar_vals, color="#4682b4")
                ax.set_ylabel("Montant (MAD)")
                ax.set_xlabel("Mois")
                ax.set_title(f"Variation de {seg}")
                for i, v in enumerate(bar_vals):
                    if not pd.isna(v) and v != 0:
                        ax.text(i, v, f"{int(v):,}", ha='center', va='bottom', fontsize=10)
                plt.xticks(rotation=45, ha="right")
                plt.tight_layout()
                st.pyplot(fig)
        else:
            st.info("Sélectionne au moins un segment ET une période pour voir les graphiques !")

        # -- TABLEAU CUMUL PÉRIODE SÉLECTIONNÉE (SLIDER) --
        st.markdown("### 🧮 Cumul des segments sur la période sélectionnée")
        if len(cols_mois_vraies) > 1:
            from_month, to_month = st.select_slider(
                "Sélectionne la période à cumuler (de ... à ...)",
                options=cols_mois_vraies,
                value=(cols_mois_vraies[0], cols_mois_vraies[-1]),
                key="slider_cumul"
            )
            idx_start = cols_mois_vraies.index(from_month)
            idx_end = cols_mois_vraies.index(to_month)
            if idx_start > idx_end:
                idx_start, idx_end = idx_end, idx_start
            selected_months = cols_mois_vraies[idx_start:idx_end+1]
        else:
            selected_months = cols_mois_vraies

        cumul_df = agg_annee[selected_months].sum(axis=1)
        cumul_table = pd.DataFrame({"CUMUL SELECTIONNÉ": cumul_df})
        cumul_table = cumul_table.applymap(mad_format)
        st.dataframe(cumul_table, use_container_width=True)

    except Exception as e:
        st.error(f"{e}")
