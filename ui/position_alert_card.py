"""Affichage d’alertes de position déjà calculées."""
def afficher_alerte_position(st,alerte):
    rendu={"information":st.info,"vigilance":st.warning,"attention":st.error}.get(alerte["niveau"],st.info)
    rendu(f"**{alerte['symbole']} — {alerte['titre']}**\n\n{alerte['message']}\n\n{alerte['action_suggeree']}")
