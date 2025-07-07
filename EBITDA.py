import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
from collections import Counter

# === MAPPING GROUPES (adapte ici si besoin) ===
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

        # Choix de la colonne d'intitulés charges (libellé) dans l'interface
        intitulé_col = st.selectbox("Colonne des intitulés (libellé charges)", df.columns)
        st.dataframe(df[intitulé_col], use_container_width=True)

        df["SEGMENT"] = df[intitulé_col].apply(get_segment)
        analyse_cols = [col for col in df.columns if col not in [intitulé_col, "SEGMENT"]]
        for col in analyse_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        agg = df.groupby("SEGMENT")[analyse_cols].sum(numeric_only=True)
        st.dataframe(agg, use_container_width=True)

        for seg in agg.index:
            st.subheader(seg)
            st.dataframe(agg.loc[[seg]], use_container_width=True)

        for col in analyse_cols:
            vals = agg[col].sort_values(ascending=False)
            fig, ax = plt.subplots()
            bars = ax.bar(vals.index, vals.values)
            ax.set_title(col)
            plt.xticks(rotation=45, ha="right")
            plt.tight_layout()
            st.pyplot(fig)

    except Exception as e:
        st.error(f"{e}")
