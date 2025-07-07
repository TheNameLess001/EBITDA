import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io

# Mapping segments
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

st.set_page_config(page_title="Analyse des Charges EBITDA", layout="wide")
st.title("Analyse des Charges - Fichiers à Deux Lignes d'En-tête (Date fin de mois + Débit/Crédit)")

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
            # Détection séparateur sur la 6ème ligne
            sep_candidates = [';', ',', '\t', '|']
            sep = max(sep_candidates, key=lambda c: lines[5].count(c))
            file_buffer = io.StringIO(s)
            pre_header = pd.read_csv(file_buffer, sep=sep, header=None, nrows=6)
            file_buffer.seek(0)
        else:
            pre_header = pd.read_excel(uploaded_file, header=None, nrows=6)

        # Reconstruire les colonnes : ligne 4 (dates), ligne 5 (Débit/Crédit/Intitulé)
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

        # Lecture du reste des données
        if uploaded_file.name.endswith('.csv'):
            file_buffer.seek(0)
            df = pd.read_csv(file_buffer, sep=sep, skiprows=5, header=None)
        else:
            df = pd.read_excel(uploaded_file, header=None, skiprows=5)
        df.columns = new_columns
        df = df.loc[:, df.columns.notna() & (df.columns != '')]

        st.subheader("Aperçu du fichier importé (colonnes reconstruites)")
        st.dataframe(df.head(20), use_container_width=True)

        # Mapping segment
        df["SEGMENT"] = df.iloc[:, 0].apply(get_segment)

        # Colonnes Débit/Crédit
        debit_cols = [c for c in df.columns if "Débit" in c]
        credit_cols = [c for c in df.columns if "Crédit" in c or "Credit" in c]

        # Dates (fin de mois) à sélectionner
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

        # Afficher INTERETS DES EMPRUNTS ET DETTES à part
        if "INTERETS DES EMPRUNTS ET DETTES" in df["SEGMENT"].values:
            st.subheader("INTERETS DES EMPRUNTS ET DETTES :")
            st.dataframe(df[df["SEGMENT"] == "INTERETS DES EMPRUNTS ET DETTES"], use_container_width=True)

        # Export CSV agrégé
        if mois_selection:
            export_cols = [c for c in debit_cols + credit_cols if any(m == c.split()[0] for m in mois_selection)]
            export = df.groupby("SEGMENT")[export_cols].sum()
            csv = export.to_csv().encode('utf-8')
            st.download_button("Télécharger le tableau agrégé", csv, "charges_agrégées.csv", "text/csv")

    except Exception as e:
        st.error(f"Erreur lors du traitement du fichier : {e}")
else:
    st.info("Uploade un fichier CSV ou Excel (2 lignes d'en-tête : date fin de mois + Débit/Crédit) pour commencer l'analyse.")
