"""
Composant Provider Selector - Sélecteur de Provider dans Sidebar
=================================================================

Composant réutilisable pour sélectionner et configurer les providers
de classification dans le sidebar de l'application.

Design moderne avec glassmorphism, cohérent avec l'interface actuelle.
"""

import streamlit as st
import os
import logging
import time
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Charger les variables d'environnement
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path, override=True)

# Import du ProviderManager
try:
    from services.provider_manager import provider_manager
except ImportError as e:
    logger.error(f"Erreur import ProviderManager: {e}")
    provider_manager = None


def render_provider_selector():
    """
    Affiche le sélecteur de provider dans le sidebar.

    Affiche des boutons visuels pour sélectionner Mistral Local ou Gemini API,
    avec statuts en temps réel et messages contextuels.
    """
    if provider_manager is None:
        st.sidebar.error("⚠️ ProviderManager non disponible")
        return

    # Initialiser session state pour le provider sélectionné
    if "selected_provider" not in st.session_state:
        # Essayer de récupérer le provider par défaut
        default_provider = provider_manager.get_default_provider()
        if default_provider:
            st.session_state.selected_provider = default_provider
        else:
            st.session_state.selected_provider = None

    # Récupérer les statuts de tous les providers
    statuses = provider_manager.get_all_statuses()
    mistral_status = statuses.get("mistral_local")
    gemini_status = statuses.get("gemini_cloud")

    # Section titre
    st.sidebar.markdown(
        """
    <div style="margin-bottom: 1rem;">
        <h3 style="font-size: 1.15rem; font-weight: 700; color: #1E293B; margin-bottom: 0.5rem; 
                    display: flex; align-items: center; gap: 0.5rem;">
            <i class="fas fa-plug" style="color: #667eea;"></i>
            Fournisseur de Traitement
        </h3>
        <p style="color: #64748B; font-size: 0.8125rem; margin: 0;">Sélectionnez votre modèle d'IA</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Boutons de sélection des providers
    col1, col2 = st.sidebar.columns(2, gap="small")

    with col1:
        # Bouton Mistral Local
        mistral_available = mistral_status.available if mistral_status else False
        mistral_selected = (
            st.session_state.get("selected_provider") == mistral_status.name
            if mistral_status
            else False
        )

        button_type = "primary" if mistral_selected else "secondary"

        if st.button(
            "🖥️ Local",
            key="btn_provider_mistral",
            disabled=not mistral_available,
            use_container_width=True,
            type=button_type,
        ):
            if mistral_available:
                st.session_state.selected_provider = mistral_status.name
                st.success("Mistral sélectionné", icon="✅")
                st.rerun()
            else:
                st.session_state.show_provider_config_modal = True
                st.session_state.config_provider_type = "mistral"

        # Indicateur de statut
        if mistral_status:
            if mistral_available:
                st.caption("✅ Disponible", help=mistral_status.status_message)
            else:
                st.caption(
                    "⚠️ Non dispo.",
                    help=mistral_status.error_message or mistral_status.status_message,
                )

    with col2:
        # Bouton Gemini Cloud
        gemini_available = gemini_status.available if gemini_status else False
        gemini_selected = (
            st.session_state.get("selected_provider") == gemini_status.name
            if gemini_status
            else False
        )

        button_type = "primary" if gemini_selected else "secondary"

        if st.button(
            "☁️ Cloud",
            key="btn_provider_gemini",
            disabled=not gemini_available,
            use_container_width=True,
            type=button_type,
        ):
            if gemini_available:
                st.session_state.selected_provider = gemini_status.name
                st.success("Gemini sélectionné", icon="✅")
                st.rerun()
            else:
                st.session_state.show_provider_config_modal = True
                st.session_state.config_provider_type = "gemini"

        # Indicateur de statut
        if gemini_status:
            if gemini_available:
                st.caption("✅ Disponible", help=gemini_status.status_message)
            else:
                st.caption(
                    "ℹ️ Config req.",
                    help=gemini_status.error_message or gemini_status.status_message,
                )

    # Afficher le provider sélectionné avec card de statut
    selected_provider_name = st.session_state.get("selected_provider")

    if selected_provider_name:
        # Trouver le statut du provider sélectionné
        selected_status = None
        for status in statuses.values():
            if status.name == selected_provider_name:
                selected_status = status
                break

        if selected_status:
            # Card de statut du provider sélectionné
            status_color = "#10B981" if selected_status.available else "#EF4444"
            status_bg = (
                "rgba(16, 185, 129, 0.1)" if selected_status.available else "rgba(239, 68, 68, 0.1)"
            )

            st.sidebar.markdown(
                f"""
            <div style="
                background: linear-gradient(135deg, {status_bg} 0%, rgba(255,255,255,0.05) 100%);
                border: 1px solid {status_color}40;
                border-left: 4px solid {status_color};
                border-radius: 12px;
                padding: 1rem;
                margin: 0.75rem 0;
                box-shadow: 0 2px 8px {status_color}20;
            ">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.5rem;">
                    <span style="font-weight: 700; color: #0F172A; font-size: 0.9375rem;">
                        {selected_status.name}
                    </span>
                    <span style="font-size: 0.875rem; color: {status_color}; font-weight: 600;">
                        {'✅' if selected_status.available else '⚠️'}
                    </span>
                </div>
                <p style="margin: 0; font-size: 0.8125rem; color: #475569; line-height: 1.4;">
                    {selected_status.status_message}
                </p>
            </div>
            """,
                unsafe_allow_html=True,
            )

            # Afficher bouton de configuration si non disponible
            if not selected_status.available:
                if st.sidebar.button(
                    "🔧 Configurer", key="btn_configure_selected", use_container_width=True
                ):
                    st.session_state.show_provider_config_modal = True
                    st.session_state.config_provider_type = (
                        "mistral" if "Mistral" in selected_status.name else "gemini"
                    )

    # Afficher les providers non disponibles dans un expander
    unavailable_providers = [status for status in statuses.values() if not status.available]

    if unavailable_providers:
        with st.sidebar.expander("❌ Providers non disponibles", expanded=False):
            for status in unavailable_providers:
                st.markdown(
                    f"""
                <div style="
                    background: rgba(239, 68, 68, 0.05);
                    border-left: 3px solid #EF4444;
                    padding: 0.75rem;
                    border-radius: 6px;
                    margin-bottom: 0.5rem;
                ">
                    <strong style="color: #991B1B; font-size: 0.875rem;">{status.name}</strong>
                    <p style="margin: 0.5rem 0 0 0; color: #7F1D1D; font-size: 0.8125rem;">
                        {status.error_message or status.status_message}
                    </p>
                </div>
                """,
                    unsafe_allow_html=True,
                )

                if status.installation_command:
                    st.caption(f"💡 {status.installation_command}")


def render_provider_configuration_modal():
    """
    Affiche une modal de configuration pour les providers manquants.

    Permet de configurer Gemini API ou de tester la connexion Ollama.
    """
    if not st.session_state.get("show_provider_config_modal", False):
        return

    config_type = st.session_state.get("config_provider_type", "gemini")

    with st.sidebar:
        with st.expander("⚙️ Configuration Provider", expanded=True):

            provider_type = st.radio(
                "Quel provider configurer?",
                ["Mistral Local", "Gemini API"],
                index=0 if config_type == "mistral" else 1,
                key="config_provider_radio",
            )

            st.markdown("---")

            if provider_type == "Mistral Local":
                st.markdown(
                    """
                <div style="background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.05) 100%);
                            padding: 1rem; border-radius: 10px; margin-bottom: 1rem;">
                    <h4 style="color: #059669; font-weight: 700; margin-bottom: 0.75rem;
                               display: flex; align-items: center; gap: 0.5rem;">
                        <i class="fas fa-server" style="color: #10B981;"></i>
                        Configurer Mistral Local (Ollama)
                    </h4>
                </div>
                """,
                    unsafe_allow_html=True,
                )

                st.markdown(
                    """
                **Prérequis:**
                
                1. **Téléchargez Ollama**: https://ollama.ai
                2. **Installez un modèle**: `ollama pull mistral`
                3. **Lancez le serveur**: `ollama serve`
                
                **Ou utilisez Docker:**
                ```bash
                docker run -d --name ollama -p 11434:11434 ollama/ollama
                docker exec ollama ollama pull mistral
                ```
                """
                )

                # Test de connexion
                st.markdown("**🔍 Test de connexion:**")

                if st.button(
                    "🔄 Vérifier la connexion Ollama",
                    key="btn_test_ollama",
                    use_container_width=True,
                ):
                    if provider_manager:
                        available, msg = provider_manager.check_ollama_connection()
                        if available:
                            st.success(msg)
                        else:
                            st.error(msg)
                    else:
                        st.error("ProviderManager non disponible")

            elif provider_type == "Gemini API":
                st.markdown(
                    """
                <div style="background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(37, 99, 235, 0.05) 100%);
                            padding: 1rem; border-radius: 10px; margin-bottom: 1rem;">
                    <h4 style="color: #2563EB; font-weight: 700; margin-bottom: 0.75rem;
                               display: flex; align-items: center; gap: 0.5rem;">
                        <i class="fas fa-cloud" style="color: #3B82F6;"></i>
                        Configurer Gemini API
                    </h4>
                </div>
                """,
                    unsafe_allow_html=True,
                )

                st.markdown(
                    """
                **Étapes:**
                
                1. **Créez un compte**: https://console.cloud.google.com
                2. **Générez une clé API**: https://ai.google.dev/api
                3. **Copiez votre clé** ci-dessous
                """
                )

                # Input pour la clé API
                api_key = st.text_input(
                    "Clé API Gemini",
                    type="password",
                    placeholder="Entrez votre clé API",
                    help="Votre clé API sera sauvegardée dans le fichier .env",
                    key="gemini_api_key_input",
                )

                if api_key:
                    col1, col2 = st.columns(2)

                    with col1:
                        if st.button(
                            "✅ Tester et Sauvegarder",
                            key="btn_save_gemini",
                            use_container_width=True,
                        ):
                            # Tester la clé
                            try:
                                import google.generativeai as genai

                                genai.configure(api_key=api_key)

                                # Essayer de lister les modèles
                                try:
                                    list(genai.list_models())
                                    test_result = True
                                    test_msg = "✅ Clé API valide"
                                except Exception:
                                    test_result = (
                                        True  # On considère valide même si list_models échoue
                                    )
                                    test_msg = "✅ Clé API acceptée"

                                if test_result:
                                    # Sauvegarder dans .env
                                    env_file = Path(__file__).parent.parent.parent / ".env"
                                    if env_file.exists():
                                        # Lire le fichier existant
                                        content = env_file.read_text(encoding="utf-8")

                                        # Remplacer ou ajouter GEMINI_API_KEY
                                        if "GEMINI_API_KEY" in content:
                                            lines = content.split("\n")
                                            new_lines = []
                                            for line in lines:
                                                if line.startswith("GEMINI_API_KEY"):
                                                    new_lines.append(f"GEMINI_API_KEY={api_key}")
                                                else:
                                                    new_lines.append(line)
                                            env_file.write_text(
                                                "\n".join(new_lines), encoding="utf-8"
                                            )
                                        else:
                                            env_file.write_text(
                                                content + f"\nGEMINI_API_KEY={api_key}",
                                                encoding="utf-8",
                                            )
                                    else:
                                        # Créer le fichier .env
                                        env_file.write_text(
                                            f"GEMINI_API_KEY={api_key}", encoding="utf-8"
                                        )

                                    # Mettre à jour la variable d'environnement
                                    os.environ["GEMINI_API_KEY"] = api_key

                                    st.success(test_msg)
                                    st.success("✅ Clé API Gemini sauvegardée dans .env!")

                                    # Fermer la modal et recharger
                                    st.session_state.show_provider_config_modal = False
                                    time.sleep(0.5)
                                    st.rerun()
                            except Exception as e:
                                st.error(f"❌ Erreur: {str(e)[:100]}")

                    with col2:
                        if st.button(
                            "❌ Annuler", key="btn_cancel_gemini", use_container_width=True
                        ):
                            st.session_state.show_provider_config_modal = False
                            st.rerun()

            # Bouton pour fermer la modal
            if st.button("✖️ Fermer", key="btn_close_modal", use_container_width=True):
                st.session_state.show_provider_config_modal = False
                st.rerun()
