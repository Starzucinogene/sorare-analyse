import streamlit as st
import pandas as pd
import os
import subprocess

# --- CONFIGURATION ---
CSV_PATH = "sorare_cards.csv"

# --- INTERFACE ---
st.set_page_config(page_title="Analyse Sorare", layout="wide")
st.title("📊 Analyse des cartes Sorare")

# --- BOUTON DE LANCEMENT ---
if st.button("🚀 Lancer l'analyse en direct"):
    with st.spinner("Analyse en cours... cela peut prendre 1 à 2 minutes..."):
        if result.returncode == 0:
            st.success("Analyse terminée avec succès.")
        else:
            st.error("Erreur pendant l'analyse :")
            st.code(result.stderr)

# --- CHARGEMENT DES DONNÉES ---
if not os.path.exists(CSV_PATH):
    st.warning("Aucune donnée CSV détectée. Lance d'abord une analyse.")
else:
    df = pd.read_csv(CSV_PATH)

    # Filtres
    st.sidebar.header("Filtres")
    markets = st.sidebar.multiselect("Marché", options=df["Marché"].unique(), default=df["Marché"].unique())
    positions = st.sidebar.multiselect("Poste", options=df["Poste"].unique(), default=df["Poste"].unique())
    rarities = st.sidebar.multiselect("Rareté", options=df["Rareté"].unique(), default=df["Rareté"].unique())
    max_price = st.sidebar.slider("Prix max ETH", 0.0, float(df["Prix API (ETH)"].max()), float(df["Prix API (ETH)"].max()))

    # Application des filtres
    df_filtered = df[
        (df["Marché"].isin(markets)) &
        (df["Poste"].isin(positions)) &
        (df["Rareté"].isin(rarities)) &
        (df["Prix API (ETH)"] <= max_price)
    ]

    st.markdown(f"**{len(df_filtered)} cartes trouvées** sur {len(df)} totales")
    st.dataframe(df_filtered, use_container_width=True)

    if st.button("📥 Télécharger CSV filtré"):
        st.download_button("Télécharger", data=df_filtered.to_csv(index=False), file_name="sorare_filtre.csv")