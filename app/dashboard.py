from __future__ import annotations

import os
import sys

ROOT = "/home/runner/work/Prevision-de-la-Demande-Optimization-de-Stock/Prevision-de-la-Demande-Optimization-de-Stock"
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from pipeline import run_pipeline

try:
    import streamlit as st
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Streamlit n'est pas installé. Lancez `pip install streamlit`.") from exc


st.set_page_config(page_title="Prévision de la demande", layout="wide")
st.title("Prévision de la demande et optimisation des stocks")
st.caption("Prototype IA (M5 simplifié) : nettoyage, prévision et recommandation de commande")

default_csv = os.path.join(ROOT, "data", "sample_sales.csv")
input_path = st.text_input("Chemin du CSV de ventes", value=default_csv)
horizon = st.slider("Horizon de prévision (jours)", min_value=1, max_value=28, value=7)

if st.button("Exécuter le pipeline"):
    result = run_pipeline(input_path=input_path, horizon=horizon)
    st.subheader("Qualité des modèles")
    st.dataframe(result["evaluations"], use_container_width=True)

    st.subheader("Recommandations de commande")
    st.dataframe(result["recommendations"], use_container_width=True)

    st.metric("Lignes brutes", result["n_input_rows"])
    st.metric("Lignes après nettoyage", result["n_clean_rows"])
