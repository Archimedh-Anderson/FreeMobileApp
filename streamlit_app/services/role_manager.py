"""
Service de Gestion des Rôles Utilisateurs - FreeMobilaChat
==========================================================

Module de gestion des rôles et des permissions utilisateur pour le système d'analyse.
Implémente trois rôles distincts avec des vues et fonctionnalités personnalisées.

Rôles disponibles:
- Agent SAV: Vue opérationnelle temps réel, priorisation des cas
- Manager: Supervision d'activité, suivi des volumes et KPI
- Data Analyst: Exploration des tendances, rapports stratégiques
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import streamlit as st


class UserRole(Enum):
    """Énumération des rôles utilisateur disponibles"""

    AGENT_SAV = "agent_sav"
    MANAGER = "manager"
    DATA_ANALYST = "data_analyst"
    DIRECTOR = "director"


@dataclass
class RoleConfiguration:
    """Configuration complète d'un rôle utilisateur"""

    role_id: str
    display_name: str
    description: str
    icon: str
    color: str
    permissions: List[str]
    features: List[str]
    dashboard_layout: str
    priority_metrics: List[str]


class RoleManager:
    """Gestionnaire central des rôles et permissions"""

    def __init__(self):
        """Initialise le gestionnaire de rôles avec les configurations"""
        self.roles = self._initialize_roles()
        self.current_role = None

    def _initialize_roles(self) -> Dict[str, RoleConfiguration]:
        """Initialise les configurations de tous les rôles"""
        return {
            UserRole.AGENT_SAV.value: RoleConfiguration(
                role_id="agent_sav",
                display_name="Agent SAV",
                description="Vue opérationnelle temps réel pour le traitement des réclamations",
                icon="fa-headset",
                color="#3182ce",
                permissions=[
                    "view_tickets",
                    "view_basic_stats",
                    "reply_customers",
                    "view_realtime_data",
                    "prioritize_claims",
                    "receive_urgent_alerts",
                    "process_tweets",
                    "view_classification",
                ],
                features=[
                    "realtime_stream",
                    "case_prioritization",
                    "urgent_alerts",
                    "quick_filters",
                    "tweet_details",
                    "action_buttons",
                ],
                dashboard_layout="operational",
                priority_metrics=[
                    "urgent_claims",
                    "unprocessed_claims",
                    "negative_sentiment",
                    "high_urgency",
                    "processing_time",
                ],
            ),
            UserRole.MANAGER.value: RoleConfiguration(
                role_id="manager",
                display_name="Manager",
                description="Supervision d'activité et monitoring des performances globales",
                icon="fa-chart-line",
                color="#38a169",
                permissions=[
                    "view_tickets",
                    "view_all_stats",
                    "export_data",
                    "manage_team",
                    "view_performance",
                    "view_global_stats",
                    "monitor_volumes",
                    "track_kpis",
                    "view_team_performance",
                    "access_quality_metrics",
                    "export_reports",
                    "view_trends",
                ],
                features=[
                    "global_dashboard",
                    "volume_tracking",
                    "kpi_monitoring",
                    "quality_control",
                    "trend_analysis",
                    "performance_charts",
                    "comparison_tools",
                ],
                dashboard_layout="strategic",
                priority_metrics=[
                    "total_claims",
                    "claim_rate",
                    "avg_confidence",
                    "sentiment_distribution",
                    "resolution_rate",
                    "team_performance",
                ],
            ),
            UserRole.DATA_ANALYST.value: RoleConfiguration(
                role_id="data_analyst",
                display_name="Data Analyst",
                description="Exploration avancée des données et analyses longitudinales",
                icon="fa-microscope",
                color="#805ad5",
                permissions=[
                    "view_tickets",
                    "view_all_stats",
                    "export_data",
                    "create_reports",
                    "access_advanced_analytics",
                    "export_datasets",
                    "create_custom_filters",
                    "view_correlations",
                    "access_ml_models",
                    "generate_reports",
                    "access_historical_data",
                ],
                features=[
                    "advanced_visualizations",
                    "data_extraction",
                    "longitudinal_analysis",
                    "correlation_matrix",
                    "clustering_tools",
                    "custom_dashboards",
                    "ml_insights",
                    "export_all_formats",
                ],
                dashboard_layout="analytical",
                priority_metrics=[
                    "data_quality",
                    "correlations",
                    "trend_indicators",
                    "anomaly_detection",
                    "predictive_scores",
                    "classification_accuracy",
                ],
            ),
            UserRole.DIRECTOR.value: RoleConfiguration(
                role_id="director",
                display_name="Director (Admin)",
                description="Accès administrateur complet à toutes les fonctionnalités",
                icon="fa-crown",
                color="#CC0000",
                permissions=[
                    "all",  # Accès total
                    "view_tickets",
                    "view_all_stats",
                    "export_data",
                    "manage_team",
                    "view_performance",
                    "create_reports",
                    "admin_access",
                    "system_configuration",
                ],
                features=[
                    "all_features",
                    "full_dashboard_access",
                    "team_management",
                    "performance_monitoring",
                    "system_settings",
                    "user_management",
                    "data_export_all",
                    "advanced_analytics",
                    "report_generation",
                ],
                dashboard_layout="administrative",
                priority_metrics=[
                    "all_metrics",
                    "system_health",
                    "team_performance",
                    "business_kpis",
                    "user_activity",
                    "data_quality",
                    "security_metrics",
                ],
            ),
        }

    def get_role_config(self, role: str) -> Optional[RoleConfiguration]:
        """Récupère la configuration d'un rôle spécifique"""
        return self.roles.get(role)

    def get_all_roles(self) -> List[RoleConfiguration]:
        """Retourne la liste de tous les rôles disponibles"""
        return list(self.roles.values())

    def has_permission(self, role: str, permission: str) -> bool:
        """Vérifie si un rôle possède une permission spécifique"""
        role_config = self.get_role_config(role)
        if role_config:
            return permission in role_config.permissions
        return False

    def has_feature(self, role: str, feature: str) -> bool:
        """Vérifie si un rôle a accès à une fonctionnalité"""
        role_config = self.get_role_config(role)
        if role_config:
            return feature in role_config.features
        return False

    def get_priority_metrics(self, role: str) -> List[str]:
        """Récupère les métriques prioritaires pour un rôle"""
        role_config = self.get_role_config(role)
        if role_config:
            return role_config.priority_metrics
        return []

    def set_current_role(self, role: str):
        """Définit le rôle actuel de l'utilisateur"""
        if role in self.roles:
            self.current_role = role
            st.session_state.current_role = role
        else:
            raise ValueError(f"Rôle invalide: {role}")

    def get_current_role(self) -> Optional[str]:
        """Récupère le rôle actuel de l'utilisateur"""
        return st.session_state.get("current_role", None)


class RoleUIManager:
    """Gestionnaire de l'interface utilisateur en fonction des rôles"""

    def __init__(self, role_manager: RoleManager):
        """Initialise le gestionnaire d'interface avec un RoleManager"""
        self.role_manager = role_manager

    def render_role_selector(self) -> str:
        """Affiche le sélecteur de rôle dans la sidebar"""
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 👤 Profil Utilisateur")

        roles = self.role_manager.get_all_roles()
        role_options = {role.display_name: role.role_id for role in roles}

        current_role = self.role_manager.get_current_role()
        current_display = None
        if current_role:
            config = self.role_manager.get_role_config(current_role)
            current_display = config.display_name if config else None

        selected_display = st.sidebar.selectbox(
            "Sélectionnez votre rôle:",
            options=list(role_options.keys()),
            index=(
                list(role_options.values()).index(current_role)
                if current_role and current_role in role_options.values()
                else 0
            ),
            help="Choisissez votre rôle pour adapter l'interface à vos besoins",
        )

        selected_role = role_options[selected_display]
        self.role_manager.set_current_role(selected_role)

        # Affichage de la description du rôle
        role_config = self.role_manager.get_role_config(selected_role)
        if role_config:
            st.sidebar.markdown(
                f"""
            <div style="background: linear-gradient(135deg, {role_config.color}22 0%, {role_config.color}11 100%); 
                        padding: 1rem; border-radius: 8px; margin-top: 0.5rem; border-left: 4px solid {role_config.color};">
                <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                    <i class="fas {role_config.icon}" style="color: {role_config.color}; font-size: 1.5rem; margin-right: 0.75rem;"></i>
                    <strong style="color: {role_config.color}; font-size: 1.1rem;">{role_config.display_name}</strong>
                </div>
                <p style="margin: 0; font-size: 0.85rem; color: #666; line-height: 1.4;">
                    {role_config.description}
                </p>
            </div>
            """,
                unsafe_allow_html=True,
            )

        return selected_role

    def render_role_permissions(self, role: str):
        """Affiche les permissions du rôle actuel"""
        role_config = self.role_manager.get_role_config(role)
        if not role_config:
            return

        with st.sidebar.expander("📋 Permissions & Fonctionnalités", expanded=False):
            st.markdown("**Permissions:**")
            for perm in role_config.permissions:
                perm_display = perm.replace("_", " ").title()
                st.markdown(f"✓ {perm_display}")

            st.markdown("**Fonctionnalités:**")
            for feat in role_config.features[:5]:  # Afficher les 5 premières
                feat_display = feat.replace("_", " ").title()
                st.markdown(f"• {feat_display}")

            if len(role_config.features) > 5:
                st.markdown(f"*+{len(role_config.features) - 5} autres...*")

    def get_filtered_metrics(
        self, role: str, all_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Filtre les métriques selon les priorités du rôle"""
        priority_metrics = self.role_manager.get_priority_metrics(role)
        filtered = {}

        for key, value in all_metrics.items():
            if any(metric in key for metric in priority_metrics):
                filtered[key] = value

        return (
            filtered if filtered else all_metrics
        )  # Retourner tout si aucun filtre ne correspond

    def render_role_specific_header(self, role: str, page_title: str):
        """Affiche un header personnalisé selon le rôle"""
        role_config = self.role_manager.get_role_config(role)
        if not role_config:
            return

        st.markdown(
            f"""
        <div style="background: linear-gradient(135deg, {role_config.color} 0%, {role_config.color}dd 100%); 
                    padding: 1rem 1.5rem; border-radius: 10px; margin-bottom: 1.5rem; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <div>
                    <h2 style="color: white; margin: 0; font-size: 1.8rem;">
                        <i class="fas {role_config.icon}" style="margin-right: 0.75rem;"></i>
                        {page_title}
                    </h2>
                    <p style="color: rgba(255,255,255,0.9); margin: 0.25rem 0 0 0; font-size: 0.95rem;">
                        Vue {role_config.display_name}
                    </p>
                </div>
                <div style="background: rgba(255,255,255,0.2); padding: 0.5rem 1rem; border-radius: 20px;">
                    <span style="color: white; font-size: 0.9rem; font-weight: 600;">
                        {role_config.display_name.upper()}
                    </span>
                </div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )


# Fonctions utilitaires pour l'intégration dans les pages
def initialize_role_system() -> tuple[RoleManager, RoleUIManager]:
    """Initialise le système de rôles pour une page"""
    if "role_manager" not in st.session_state:
        st.session_state.role_manager = RoleManager()
        st.session_state.role_ui_manager = RoleUIManager(st.session_state.role_manager)

    return st.session_state.role_manager, st.session_state.role_ui_manager


def get_current_role() -> Optional[str]:
    """Récupère le rôle actuel de l'utilisateur"""
    return st.session_state.get("current_role", None)


def check_permission(permission: str) -> bool:
    """Vérifie si l'utilisateur actuel a une permission"""
    if "role_manager" not in st.session_state:
        return False

    current_role = get_current_role()
    if not current_role:
        return False

    return st.session_state.role_manager.has_permission(current_role, permission)


def check_feature(feature: str) -> bool:
    """Vérifie si l'utilisateur actuel a accès à une fonctionnalité"""
    if "role_manager" not in st.session_state:
        return False

    current_role = get_current_role()
    if not current_role:
        return False

    return st.session_state.role_manager.has_feature(current_role, feature)
