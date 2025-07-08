import streamlit as st
import pandas as pd
import io

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
            header5 = lines[4].split(sep)
            st.write("Ligne 4 :", header4)
            st.write("Ligne 5 :", header5)
        else:
            xls = pd.ExcelFile(uploaded_file)
            header4 = pd.read_excel(xls, header=None, nrows=4).iloc[3].astype(str).tolist()
            header5 = pd.read_excel(xls, header=None, nrows=5).iloc[4].astype(str).tolist()
            st.write("Ligne 4 :", header4)
            st.write("Ligne 5 :", header5)
    except Exception as e:
        st.error(f"{e}")
