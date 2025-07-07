import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
from collections import Counter

# ----------- MAPPING SEGMENTS (à adapter si besoin) -----------
mapping = {
    "ACHATS": [
        "ACHATS DE MARCHANDISES revente", "ACHAT ALIZEE", "ACHAT BOGOODS", "ACHAT GRAPOS", "ACHAT HYGYENE SDHE",
        "STOCK INITIAL", "STOCK FINAL", "ACHATS LYDEC (EAU+ELECTRICITE)", "ACHATS DE PETITS EQUIPEMENTS FOURNITURES",
        "ACHAT TENUES", "ACHATS DE FOURNITURES DE BUREAU"
    ],
    "Services professionnels": [
        "CONVENTION MEDECIN (1an)", "HONORAIRES COMPTA (moore)", "HONORAIRES SOCIAL (moore)",
        "HONORAIRES DIVERS", "HONO PRESTATION FPK MAROC"
    ],
    "Nettoyage": [
        "GARDIENNAGE ET MENAGE", "NETTOYAGE FIN DE CHANTIER", "DERATISATIONS / DESINSECTISATION"
    ],
    "Des employés": [
        "APPOINTEMENTS ET SALAIRES", "INDEMNITES ET AVANTAGES DIVERS", "COTISATIONS DE SECURITE SOCIALE",
        "COTISATIONS PREVOYANCE + SANTE", "PROVISION DES CP+CHARGES INITIAL", "PROVISION DES CP+CHARGES FINAL",
        "ASSURANCES ACCIDENTS DU TRAVAIL", "GRATIFICATIONS DE STAGE"
    ],
    "Entraînement": [
        "COURS COLLECTIFS", "ABONT FP CLOUD FITNESS PARK France", "ABONT QR CODE FITNESS PARK France",
        "ABONT MG INSTORE MEDIA (1an)", "ABONT TSHOKO (1an)", "ABONT COMBO (1an)", "ABONT CENAREO (1an)",
        "RESAMANIA HEBERGEMENT SERVEUR", "RESAMANIA SMS", "ABONT HYROX 365", "MAINTENANCE HYDROMASSAGE",
        "ABONT LICENCE PLANET FITNESS"
    ],
    "Commercialisation": [
        "AFFICHES pub", "LOCATION ESPACE PUBLICITAIRES", "FRAIS INAUGURATION / ANNIVERSAIRE", "CLIENT MYSTERE"
    ],
    "Téléphones/Communication": [
        "FRAIS DE TELECOMMUNICATION (orange)", "FRAIS DE TELECOMMUNICATION (Maroc Télécom)"
    ],
    "Autres": [
        "SOUS TRAITANCE CENTRE D APPEL", "LOYER URBAN DEVELOPPEURS V", "LOYER URBAN DEVELOPPEURS - CHARGES LOCATIVES",
        "REDEVANCES DE CREDIT BAIL MATERIEL PS FITNESS", "LOYER MATERIEL VIA FPK MAROC",
        "LOCATION DISTRIBUTEUR KIT STORE", "ENTRET ET REPAR DES BIENS IMMOBILIERS", "MAINTENANCE IMAFLUIDE",
        "MAINTENANCE INCENDIE (par semestre)", "MAINTENANCE TECHNOGYM", "ASSURANCE RC CLUB SPORTIF (500 adhérents)",
        "ASSURANCE RC CLUB SPORTIF provision actif réel", "ASSURANCE MULTIRISQUE", "REDEVANCES FITNESS PARK France 3%",
        "VOYAGES ET DEPLACEMENTS", "RECEPTIONS", "FRAIS POSTAUX dhl", "FRAIS ET COMMISSIONS SUR SERVICES BANCAI",
        "FRAIS COMMISSION NAPS", "FRAIS COMMISSIONS CMI", "TAXES ECRAN DEVANTURE (1an)",
        "DROITS D'ENREGISTREMENT ET DE TIMBRE", "CADEAUX SALARIE ET CLIENT", "CHEQUES CADEAUX POUR CHALLENGES"
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

st.set_page_config(page_title="Analyse Charges EBITDA", layout="wide")
st.title("Analyse des Charges EBITDA - Version Chérif (Debug & Rapport par segment)")

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
            sep_candidates = [';', ',', '\t', '|']
            sep = max(sep_candidates, key=lambda c: lines[5].count(c))
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
            new_columns = make_unique(new_columns)
            ignore_cols = [col for col in new_columns if "Cumul" in col or "Prévisionnel" in col or (col == "Intitulé" and new_columns.count("Intitulé") > 1)]
            cols_to_use = [col for col in new_columns if col not in ignore_cols]
            data_lines = lines[5:]
            s_data = "\n".join(data_lines)
            file_buffer = io.StringIO(s_data)
            df = pd.read_csv(file_buffer, sep=sep, header=None)
            df.columns = new_columns
            df = df[cols_to_use]
        else:
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
            new_columns = make_unique(new_columns)
            ignore_cols = [col for col in new_columns if "Cumul" in col or "Prévisionnel" in col or (col == "Intitulé" and new_columns.count("Intitulé") > 1)]
            cols_to_use = [col for col in new_columns if col not in ignore_cols]
            df = pd.read_excel(xls, header=None, skiprows=5)
            df.columns = new_columns
            df = df[cols_to_use]

        df = df.loc[:, df.columns.notna() & (df.columns != '')]

        # DEBUG : affichage des colonnes détectées
        st.write("**Colonnes détectées :**", list(df.columns))
        st.write("**Premières lignes du dataframe :**")
        st.dataframe(df.head(10))

        df["SEGMENT"] = df.iloc[:, 0].apply(get_segment)

        # Détection tolérante (accents/espaces)
        debit_cols = [c for c in df.columns if "debit" in c.lower() or "débit" in c.lower()]
        credit_cols = [c for c in df.columns if "credit" in c.lower() or "crédit" in c.lower()]
        st.write("**Colonnes identifiées comme Débit :**", debit_cols)
        st.write("**Colonnes identifiées comme Crédit :**", credit_cols)

        mois_possibles = sorted(set([c.split()[0] for c in debit_cols if c.split()[0].lower() != 'intitulé']))
        st.write("**Dates extraites :**", mois_possibles)
        if not mois_possibles:
            st.error("Aucune colonne 'Débit' ou 'Crédit' trouvée. Vérifie le nom exact des colonnes dans ton fichier.")
        else:
            mois_selection = st.multiselect("Sélectionne les dates à afficher :", mois_possibles, default=mois_possibles[-1:] if mois_possibles else [])

            # =========== AFFICHAGE PAR SEGMENT ===========
            for mois in mois_selection:
                debit_col = next((c for c in debit_cols if mois == c.split()[0]), None)
                credit_col = next((c for c in credit_cols if mois == c.split()[0]), None)
                if debit_col and credit_col:
                    agg = df.groupby("SEGMENT")[[debit_col, credit_col]].sum(numeric_only=True)
                    agg_fmt = agg.applymap(lambda x: f"{x:,.0f} MAD" if pd.notnull(x) else "")
                    st.subheader(f"🟦 Tableau général : {mois} - Tous segments")
                    st.dataframe(agg_fmt, use_container_width=True)
                    for seg in agg.index:
                        st.markdown(f"**{seg}**")
                        st.dataframe(agg_fmt.loc[[seg]], use_container_width=True)

                    total_par_segment = (agg[debit_col] - agg[credit_col]).sort_values(ascending=False)
                    fig, ax = plt.subplots()
                    bars = ax.bar(total_par_segment.index, total_par_segment.values)
                    ax.set_title(f"Comparatif segments ({mois}) - Total Débit - Crédit (MAD)")
                    ax.set_xlabel("Segment")
                    ax.set_ylabel("Somme (MAD)")
                    ax.bar_label(bars, fmt='%.0f')
                    plt.xticks(rotation=45, ha="right")
                    plt.tight_layout()
                    st.pyplot(fig)

            if "INTERETS DES EMPRUNTS ET DETTES" in df["SEGMENT"].values:
                st.subheader("INTERETS DES EMPRUNTS ET DETTES :")
                st.dataframe(df[df["SEGMENT"] == "INTERETS DES EMPRUNTS ET DETTES"], use_container_width=True)

            if mois_selection:
                export_cols = [c for c in debit_cols + credit_cols if any(m == c.split()[0] for m in mois_selection)]
                export = df.groupby("SEGMENT")[export_cols].sum()
                csv = export.to_csv().encode('utf-8')
                st.download_button("Télécharger le tableau agrégé", csv, "charges_agrégées.csv", "text/csv")

    except Exception as e:
        st.error(f"Erreur lors du traitement du fichier : {e}")

else:
    st.info("Uploade un fichier CSV ou Excel (2 lignes d'en-tête : date fin de mois + Débit/Crédit) pour commencer l'analyse.")
