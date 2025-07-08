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
    "ACHATS": [
        "ACHATS DE MARCHANDISES revente", "ACHAT ALIZEE", "ACHAT BOGOODS", "ACHAT GRAPOS", "ACHAT HYGYENE SDHE",
        "STOCK INITIAL", "STOCK FINAL", "ACHATS LYDEC (EAU+ELECTRICITE)", "ACHATS DE PETITS EQUIPEMENTS FOURNITURES",
        "ACHAT TENUES", "ACHATS DE FOURNITURES DE BUREAU"
    ],
    "SERVICES RH / PRESTATIONS": [
        "CONVENTION MEDECIN (1an)", "ACHATS PRESTATION admin / RH", "SOUS TRAITANCE CENTRE D APPEL",
        "GARDIENNAGE ET MENAGE", "NETTOYAGE FIN DE CHANTIER", "DERATISATIONS / DESINSECTISATION"
    ],
    "COURS & ABONNEMENTS": [
        "COURS COLLECTIFS", "ABONT FP CLOUD FITNESS PARK France", "ABONT QR CODE FITNESS PARK France",
        "ABONT MG INSTORE MEDIA (1an)", "ABONT TSHOKO (1an)", "ABONT COMBO (1an)", "ABONT CENAREO (1an)",
        "RESAMANIA HEBERGEMENT SERVEUR", "RESAMANIA SMS", "ABONT HYROX 365", "MAINTENANCE HYDROMASSAGE",
        "ABONT LICENCE PLANET FITNESS"
    ],
    "LOYERS / LOCATIONS / REDEVANCES": [
        "LOYER URBAN DEVELOPPEURS V", "LOYER URBAN DEVELOPPEURS - CHARGES LOCATIVES",
        "REDEVANCES DE CREDIT BAIL MATERIEL PS FITNESS", "LOYER MATERIEL VIA FPK MAROC",
        "LOCATION DISTRIBUTEUR KIT STORE", "LOCATION ESPACE PUBLICITAIRES"
    ],
    "MAINTENANCE / ASSURANCES": [
        "ENTRET ET REPAR DES BIENS IMMOBILIERS", "MAINTENANCE IMAFLUIDE", "MAINTENANCE INCENDIE (par semestre)",
        "MAINTENANCE TECHNOGYM", "ASSURANCE RC CLUB SPORTIF (500 adhérents)",
        "ASSURANCE RC CLUB SPORTIF provision actif réel", "ASSURANCE MULTIRISQUE",
        "ASSURANCES ACCIDENTS DU TRAVAIL"
    ],
    "HONORAIRES / DIVERS": [
        "HONORAIRES COMPTA (moore)", "HONORAIRES SOCIAL (moore)", "HONORAIRES DIVERS", "HONO PRESTATION FPK MAROC"
    ],
    "REDEVANCES / FP FRANCE": [
        "REDEVANCES FITNESS PARK France 3%"
    ],
    "FRAIS / COMMUNICATION / MARKETING": [
        "VOYAGES ET DEPLACEMENTS", "RECEPTIONS", "FRAIS POSTAUX dhl", "FRAIS INAUGURATION / ANNIVERSAIRE",
        "FRAIS DE TELECOMMUNICATION (orange)", "FRAIS DE TELECOMMUNICATION (Maroc Télécom)", "CLIENT MYSTERE",
        "AFFICHES pub", "FRAIS ET COMMISSIONS SUR SERVICES BANCAI", "FRAIS COMMISSION NAPS",
        "FRAIS COMMISSIONS CMI", "TAXES ECRAN DEVANTURE (1an)", "DROITS D'ENREGISTREMENT ET DE TIMBRE"
    ],
    "PERSONNEL / CHARGES SOCIALES": [
        "APPOINTEMENTS ET SALAIRES", "INDEMNITES ET AVANTAGES DIVERS", "COTISATIONS DE SECURITE SOCIALE",
        "COTISATIONS PREVOYANCE + SANTE", "PROVISION DES CP+CHARGES INITIAL", "PROVISION DES CP+CHARGES FINAL",
        "GRATIFICATIONS DE STAGE"
    ],
    "CADEAUX / CHALLENGES": [
        "CADEAUX SALARIE ET CLIENT", "CHEQUES CADEAUX POUR CHALLENGES"
    ],
    "INTERETS / FINANCE": [
        "INTERETS DES EMPRUNTS ET DETTES"
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

        # Nettoyage extrême
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

        # -- GRAPHIQUE BARRES GROUPEES avec filtre live --
        st.markdown("### 🔎 Filtrer les segments affichés sur le graphique")
        segments_available = [str(seg).replace("’", "").replace("'", "").replace('"', "").strip() for seg in SEGMENTS_ORDER]
        # PATCH: ne garde QUE les mois réellement présents dans la data!
        cols_reel = [c for c in mois_names if c in agg_annee.columns]
        if len(cols_reel) < len(mois_names):
            st.warning(f"Colonnes mois absentes ou différentes dans la data: {set(mois_names) - set(cols_reel)}")
        graph_df = agg_annee.loc[SEGMENTS_ORDER, cols_reel]
        graph_df.columns = cols_reel
        indices = range(len(cols_reel))

        st.write("mois_names:", mois_names)
        st.write("agg_annee.columns:", list(agg_annee.columns))
        st.write("cols_reel utilisés:", cols_reel)
        st.write("graph_df preview:", graph_df.head())

        segments_with_data = [seg for seg in segments_available if graph_df.loc[seg].sum() > 0]
        default_selection = segments_with_data if segments_with_data else segments_available

        segments_selected = st.multiselect(
            "Sélectionne les segments à afficher",
            options=segments_available,
            default=default_selection
        )

        st.markdown("### 📈 Barres groupées : variation de chaque segment par mois")
        fig, ax = plt.subplots(figsize=(min(14, 2 + 0.9*len(cols_reel)), 7))
        if segments_selected:
            has_data = False
            bar_width = 0.8 / len(segments_selected)
            for i, seg in enumerate(segments_selected):
                if seg in graph_df.index:
                    bar_vals = graph_df.loc[seg].values
                    if np.nansum(bar_vals) != 0:
                        has_data = True
                    ax.bar([x + i*bar_width for x in indices], bar_vals, bar_width, label=seg)
                else:
                    ax.bar([x + i*bar_width for x in indices], [0]*len(cols_reel), bar_width, label=seg)
            ax.set_xticks([x + bar_width*len(segments_selected)/2 for x in indices])
            ax.set_xticklabels(cols_reel, rotation=45, ha="right")
            ax.set_ylabel("Montant (MAD)")
            ax.set_xlabel("Mois")
            ax.set_title("Variation mensuelle des segments sélectionnés")
            ax.legend(loc="upper left", bbox_to_anchor=(1,1))
            plt.tight_layout()
            if has_data:
                st.pyplot(fig)
            else:
                st.warning("Aucune donnée à afficher pour les segments sélectionnés !")
        else:
            st.warning("Sélectionne au moins un segment pour afficher le graphique.")

        # -- TABLEAU CUMUL PÉRIODE SÉLECTIONNÉE (SLIDER) --
        st.markdown("### 🧮 Cumul des segments sur la période sélectionnée")
        if len(cols_reel) > 1:
            from_month, to_month = st.select_slider(
                "Sélectionne la période à cumuler (de ... à ...)",
                options=cols_reel,
                value=(cols_reel[0], cols_reel[-1])
            )
            idx_start = cols_reel.index(from_month)
            idx_end = cols_reel.index(to_month)
            if idx_start > idx_end:
                idx_start, idx_end = idx_end, idx_start
            selected_months = cols_reel[idx_start:idx_end+1]
        else:
            selected_months = cols_reel

        cumul_df = agg_annee[selected_months].sum(axis=1)
        cumul_table = pd.DataFrame({"CUMUL SELECTIONNÉ": cumul_df})
        cumul_table = cumul_table.applymap(mad_format)
        st.dataframe(cumul_table, use_container_width=True)

    except Exception as e:
        st.error(f"{e}")
