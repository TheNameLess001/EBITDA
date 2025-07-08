import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
import re
import calendar
from collections import Counter

# ----------- MAPPING -----------
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
special_line = "INTERETS DES EMPRUNTS ET DETTES"
SEGMENTS_ORDER = list(mapping.keys()) + ["Autres"]

def get_segment(nom):
    for seg, lignes in mapping.items():
        if isinstance(nom, str) and nom.strip().upper() in [x.strip().upper() for x in lignes]:
            return seg
    if isinstance(nom, str) and nom.strip().upper() == special_line:
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

        # S'assure que tous les segments sont présents (même à 0)
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

        # Affiche les lignes qui composent "Autres"
        autres_lignes = df[df["SEGMENT"] == "Autres"][detected_intitule_col].dropna().unique().tolist()
        with st.expander("Voir le détail du segment 'Autres' (intitulés non mappés)", expanded=False):
            if autres_lignes:
                st.write(", ".join(autres_lignes))
            else:
                st.write("Aucune ligne hors mapping !")

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

        # Graph comparatif live avec noms de mois lisibles
        st.subheader("Graphique comparatif : Choisis 2 à 12 mois à comparer")
        mois_selection = st.multiselect(
            "Sélectionne les mois à comparer (2 à 12 max)",
            options=mois_names,
            default=mois_names[:2],
            max_selections=12
        )
        # Mapping noms vers cols pour selection
        name_to_col = dict(zip(mois_names, mois_cols))
        if len(mois_selection) >= 2:
            fig, ax = plt.subplots(figsize=(max(8, 1.6*len(mois_selection)), 5))
            cols_to_plot = [name_to_col[m] for m in mois_selection]
            to_plot = agg_annee.loc[:, cols_to_plot]
            to_plot.columns = mois_selection
            to_plot = to_plot.fillna(0)
            to_plot.T.plot(kind="bar", ax=ax)
            plt.ylabel("Montant (MAD)")
            plt.xticks(rotation=45, ha="right")
            plt.legend(loc="best", bbox_to_anchor=(1,1))
            plt.tight_layout()
            st.pyplot(fig)
        else:
            st.info("Sélectionne au moins 2 mois pour comparer.")

    except Exception as e:
        st.error(f"{e}")
