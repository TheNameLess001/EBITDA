# --- Multi-segments : chaque segment a son propre graph, mais filtre période global ---
st.markdown("### 🎛️ Compare plusieurs segments (période commune)")

segments_available = [str(seg).replace("’", "").replace("'", "").replace('"', "").strip() for seg in SEGMENTS_ORDER]
cols_mois_vraies = [c for c in agg_annee.columns if c != "Total Année"]

# 1 seul slider période (commune à tous)
if len(cols_mois_vraies) > 1:
    from_month, to_month = st.select_slider(
        "Sélectionne la période à afficher pour TOUS les graphiques (de ... à ...)",
        options=cols_mois_vraies,
        value=(cols_mois_vraies[0], cols_mois_vraies[-1]),
        key="slider_global"
    )
    idx_start = cols_mois_vraies.index(from_month)
    idx_end = cols_mois_vraies.index(to_month)
    if idx_start > idx_end:
        idx_start, idx_end = idx_end, idx_start
    selected_months = cols_mois_vraies[idx_start:idx_end+1]
else:
    selected_months = cols_mois_vraies

segments_selected = st.multiselect(
    "Sélectionne les segments à afficher",
    options=segments_available,
    default=[segments_available[0]],
    help="Ajoute un ou plusieurs segments. Chacun aura son propre graphique sur la période choisie !"
)

if segments_selected and selected_months:
    for seg in segments_selected:
        st.markdown(f"#### 📊 Segment : **{seg}** ({from_month} → {to_month})")

        bar_vals = agg_annee.loc[seg, selected_months].values
        fig, ax = plt.subplots(figsize=(min(8, 1 + 0.5*len(selected_months)), 4))
        ax.bar(selected_months, bar_vals, color="#4682b4")
        ax.set_ylabel("Montant (MAD)")
        ax.set_xlabel("Mois")
        ax.set_title(f"Variation de {seg}")
        for i, v in enumerate(bar_vals):
            if not pd.isna(v) and v != 0:
                ax.text(i, v, f"{int(v):,}", ha='center', va='bottom', fontsize=10)
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        st.pyplot(fig)
else:
    st.info("Sélectionne au moins un segment ET une période pour voir les graphiques !")
