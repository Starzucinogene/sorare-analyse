import streamlit as st
import pandas as pd
import os
from sorare_graphql_scraper import scan_players

# --- INTERFACE ---
st.set_page_config(page_title="Analyse Sorare", layout="wide")
st.title("📊 Analyse des cartes Sorare via API GraphQL")

# --- ANALYSE EN DIRECT ---
if st.button("🚀 Lancer l'analyse en direct"):
    with st.spinner("Analyse en cours via API Sorare..."):
        df, alerts = scan_players()
        df.to_csv("sorare_cards.csv", index=False)
        st.success("Analyse terminée. Résultats mis à jour.")
        if alerts:
            st.warning(f"⚠️ Alertes détectées pour : {', '.join(alerts)}")

# --- CHARGEMENT CSV ---
if not os.path.exists("sorare_cards.csv"):
    st.warning("Aucune donnée détectée. Lancez une analyse.")
else:
    df = pd.read_csv("sorare_cards.csv")

    # Filtres
    st.sidebar.header("Filtres")
    max_eth = st.sidebar.slider("Prix max ETH", 0.0, float(df["min_price_eth"].max()), float(df["min_price_eth"].max()))
    df_filtered = df[df["min_price_eth"] <= max_eth]

    st.markdown(f"**{len(df_filtered)} cartes trouvées** sur {len(df)} totales")
    st.dataframe(df_filtered, use_container_width=True)

    st.download_button("📥 Télécharger CSV filtré", data=df_filtered.to_csv(index=False), file_name="sorare_filtre.csv")