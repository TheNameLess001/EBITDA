import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
import re
from collections import Counter

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

def detect_mois_cols(header_dates):
    # Repère les colonnes dont la ligne 4 est une date jj/mm/aaaa ou jj-mm-aaaa
    mois_cols = []
    for idx, val in enumerate(header_dates):
        if re.match(r'\d{2}[/-]\d{2}[/-]\d{4}', str(val).strip()):
            mois_cols.append(idx)
    return mois_cols

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
            header_dates = lines[3].split(sep)
            header_dates = [str(x).strip() for x in header_dates]
            st.write("Ligne 4 (header_dates):", header_dates)  # PATCH DEBUG
            header_dates = make_unique(header_dates)
            header_labels = lines[4].split(sep)
            data_lines = lines[5:]
            s_data = "\n".join(data_lines)
            file_buffer = io.StringIO(s_data)
            df = pd.read_csv(file_buffer, sep=sep, header=None)
            df.columns = header_dates
        else:
            xls = pd.ExcelFile(uploaded_file)
            header_dates = pd.read_excel(xls, header=None, nrows=4).iloc[3].astype(str).str.strip().tolist()
            st.write("Ligne 4 (header_dates):", header_dates)  # PATCH DEBUG
            header_dates = make_unique(header_dates)
            header_labels = pd.read_excel(xls, header=None, nrows=5).iloc[4].astype(str).str.strip().tolist()
            df = pd.read_excel(xls, header=None, skiprows=5)
            df.columns = header_dates

        # Détection colonne d’intitulé charges (par mapping)
        charge_names = set()
        for lignes in mapping.values():
            charge_names.update([x.strip().upper() for x in lignes])
        detected_intitule_col = None
        for col in df.columns:
            sample = df[col].astype(str).str.strip().str.upper()
            if sample.isin(charge_names).any():
                detected_intitule_col = col
                break
        if detected_intitule_col is None:
            st.error("Impossible de détecter la colonne d'intitulé charges automatiquement. Vérifie ton mapping et la structure du fichier.")
            st.stop()
        st.write(f"Colonne des intitulés détectée automatiquement : **{detected_intitule_col}**")
        st.dataframe(df[detected_intitule_col], use_container_width=True)

        # Détection colonne mois (via ligne 4 du header)
        mois_idx = detect_mois_cols(header_dates)
        mois_cols = [df.columns[idx] for idx in mois_idx]
        st.write(f"Colonnes mois détectées via la ligne 4 : {mois_cols}")

        # Mapping segments
        df["SEGMENT"] = df[detected_intitule_col].apply(get_segment)
        for col in mois_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        agg = df.groupby("SEGMENT")[mois_cols].sum(numeric_only=True)
        st.subheader("Tableau global – Tous mois, tous segments")
        st.dataframe(agg, use_container_width=True)

        for col in mois_cols:
            agg_mois = df.groupby("SEGMENT")[[col]].sum(numeric_only=True)
            st.subheader(f"Vue par segment – Mois {col}")
            st.dataframe(agg_mois, use_container_width=True)
            vals = agg_mois[col].sort_values(ascending=False)
            fig, ax = plt.subplots()
            bars = ax.bar(vals.index, vals.values)
            ax.set_title(f"Comparatif segments – {col}")
            plt.xticks(rotation=45, ha="right")
            plt.tight_layout()
            st.pyplot(fig)

    except Exception as e:
        st.error(f"{e}")
