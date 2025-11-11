"""
Moteur d'analyse IA adaptatif avec support multi-providers
"""

import asyncio
import json
import hashlib
import logging
from typing import Dict, List, Any, Optional, Union
import pandas as pd
from datetime import datetime, timedelta
import aiohttp
import openai
from anthropic import Anthropic
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
import os
from pathlib import Path

from .intelligent_data_inspector import IntelligentDataInspector
from .dynamic_prompt_generator import DynamicPromptGenerator
from .real_llm_engine import RealLLMEngine

logger = logging.getLogger(__name__)

class AdaptiveAnalysisEngine:
    """
    Moteur principal d'analyse avec IA contextuelle
    """
    
    def __init__(self, llm_provider: str = "openai"):
        self.inspector = IntelligentDataInspector()
        self.prompt_generator = DynamicPromptGenerator()
        self.real_llm_engine = RealLLMEngine()
        self.llm_provider = llm_provider
        self.llm_client = self._initialize_llm(llm_provider)
        self.cache_dir = Path("streamlit_app/cache/analysis")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuration des providers LLM
        self.llm_configs = {
            "openai": {
                "model": "gpt-4-turbo-preview",
                "temperature": 0.1,
                "max_tokens": 4000,
                "timeout": 60
            },
            "anthropic": {
                "model": "claude-3-sonnet-20240229",
                "temperature": 0.1,
                "max_tokens": 4000,
                "timeout": 60
            },
            "local": {
                "model": "llama2-13b-chat",
                "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
                "timeout": 120
            }
        }
        
        # Cache pour éviter les re-analyses
        self.analysis_cache = {}
        self.cache_ttl = timedelta(hours=24)

    def _initialize_llm(self, provider: str):
        """Initialise le client LLM selon le provider"""
        try:
            if provider == "openai":
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    logger.warning("OPENAI_API_KEY non trouvée, utilisation du fallback")
                    return None
                return openai.OpenAI(api_key=api_key)
            
            elif provider == "anthropic":
                api_key = os.getenv("ANTHROPIC_API_KEY")
                if not api_key:
                    logger.warning("ANTHROPIC_API_KEY non trouvée, utilisation du fallback")
                    return None
                return Anthropic(api_key=api_key)
            
            elif provider == "local":
                ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
                return httpx.AsyncClient(base_url=ollama_url, timeout=120)
            
            else:
                logger.warning(f"Provider {provider} non supporté, utilisation du fallback")
                return None
                
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation du LLM {provider}: {e}")
            return None

    async def analyze_dataset(self, df: pd.DataFrame, filename: str) -> Dict[str, Any]:
        """
        WORKFLOW COMPLET D'ANALYSE :
        
        1. Inspection automatique des données
        2. Génération contexte intelligent
        3. Création prompt personnalisé
        4. Analyse LLM adaptative
        5. Post-traitement et validation
        6. Génération visualisations dynamiques
        """
        try:
            logger.info(f"Début de l'analyse du dataset: {filename}")
            
            # Vérification du cache
            cache_key = self._generate_cache_key(df, filename)
            cached_result = self._get_cached_analysis(cache_key)
            if cached_result:
                logger.info("Résultat trouvé dans le cache")
                return cached_result
            
            # Phase 1: Inspection intelligente
            logger.info("Phase 1: Inspection intelligente des données")
            context = self.inspector.analyze_dataset_context(df)
            
            # Phase 2: Génération prompt adaptatif
            logger.info("Phase 2: Génération du prompt personnalisé")
            custom_prompt = self.prompt_generator.create_analysis_prompt(df, context, filename)
            
            # Phase 3: Analyse LLM RÉELLE avec API calls
            logger.info("Phase 3: Analyse LLM réelle avec API calls")
            analysis_result = await self.real_llm_engine.analyze_with_llm(df, filename, context)
            
            # Phase 4: Post-traitement intelligent
            logger.info("Phase 4: Post-traitement et enrichissement")
            enriched_analysis = self._enrich_analysis_results(analysis_result, df, context)
            
            # Phase 5: Génération visualisations adaptées
            logger.info("Phase 5: Génération des visualisations contextuelles")
            visualizations = self._generate_adaptive_visualizations(enriched_analysis, df)
            
            # Résultat final
            final_result = {
                "context": context,
                "analysis": enriched_analysis,
                "visualizations": visualizations,
                "metadata": self._generate_analysis_metadata(df, filename),
                "cache_key": cache_key,
                "analysis_timestamp": datetime.now().isoformat()
            }
            
            # Mise en cache
            self._cache_analysis(cache_key, final_result)
            
            logger.info(f"Analyse terminée avec succès pour {filename}")
            return final_result
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse du dataset {filename}: {e}")
            return self._get_fallback_analysis(df, filename)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def _execute_llm_analysis(self, prompt: str, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Exécute l'analyse LLM avec système de fallback intelligent
        """
        try:
            # Essai avec le provider principal
            if self.llm_client:
                result = await self._call_llm_provider(prompt)
                if result:
                    return result
            
            # Fallback vers d'autres providers
            for provider in ["anthropic", "openai", "local"]:
                if provider != self.llm_provider:
                    try:
                        fallback_client = self._initialize_llm(provider)
                        if fallback_client:
                            result = await self._call_llm_provider(prompt, fallback_client, provider)
                            if result:
                                logger.info(f"Analyse réussie avec le provider fallback: {provider}")
                                return result
                    except Exception as e:
                        logger.warning(f"Échec du fallback {provider}: {e}")
                        continue
            
            # Fallback vers analyse statistique classique
            logger.warning("Tous les providers LLM ont échoué, utilisation de l'analyse statistique")
            return self._get_statistical_analysis(df)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution de l'analyse LLM: {e}")
            return self._get_statistical_analysis(df)

    async def _call_llm_provider(self, prompt: str, client=None, provider=None) -> Optional[Dict[str, Any]]:
        """Appelle le provider LLM spécifique"""
        if client is None:
            client = self.llm_client
        if provider is None:
            provider = self.llm_provider
            
        try:
            if provider == "openai":
                response = await client.chat.completions.create(
                    model=self.llm_configs[provider]["model"],
                    messages=[{"role": "user", "content": prompt}],
                    temperature=self.llm_configs[provider]["temperature"],
                    max_tokens=self.llm_configs[provider]["max_tokens"]
                )
                content = response.choices[0].message.content
                
            elif provider == "anthropic":
                response = await client.messages.create(
                    model=self.llm_configs[provider]["model"],
                    max_tokens=self.llm_configs[provider]["max_tokens"],
                    temperature=self.llm_configs[provider]["temperature"],
                    messages=[{"role": "user", "content": prompt}]
                )
                content = response.content[0].text
                
            elif provider == "local":
                response = await client.post("/api/generate", json={
                    "model": self.llm_configs[provider]["model"],
                    "prompt": prompt,
                    "stream": False
                })
                content = response.json()["response"]
            
            else:
                return None
            
            # Parsing de la réponse JSON
            return self._parse_llm_response(content)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'appel du provider {provider}: {e}")
            return None

    def _parse_llm_response(self, content: str) -> Optional[Dict[str, Any]]:
        """Parse la réponse LLM en JSON structuré"""
        try:
            # Nettoyage du contenu
            content = content.strip()
            
            # Recherche du JSON dans la réponse
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                json_content = content[json_start:json_end].strip()
            elif "{" in content and "}" in content:
                json_start = content.find("{")
                json_end = content.rfind("}") + 1
                json_content = content[json_start:json_end]
            else:
                logger.warning("Aucun JSON trouvé dans la réponse LLM")
                return None
            
            # Parsing JSON
            result = json.loads(json_content)
            
            # Validation de la structure
            if self._validate_analysis_structure(result):
                return result
            else:
                logger.warning("Structure de réponse LLM invalide")
                return None
                
        except json.JSONDecodeError as e:
            logger.error(f"Erreur de parsing JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"Erreur lors du parsing de la réponse LLM: {e}")
            return None

    def _validate_analysis_structure(self, result: Dict[str, Any]) -> bool:
        """Valide la structure de la réponse d'analyse"""
        required_keys = ["classification", "insights", "visualizations"]
        return all(key in result for key in required_keys)

    def _enrich_analysis_results(self, analysis_result: Dict[str, Any], df: pd.DataFrame, context: Dict[str, Any]) -> Dict[str, Any]:
        """Enrichit les résultats d'analyse avec des métriques supplémentaires"""
        try:
            # Ajout de métriques calculées
            enriched = analysis_result.copy()
            
            # Métriques de base
            enriched["dataset_metrics"] = {
                "row_count": len(df),
                "column_count": len(df.columns),
                "memory_usage": df.memory_usage(deep=True).sum(),
                "completeness": (1 - df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
            }
            
            # Métriques de qualité des données
            enriched["data_quality"] = {
                "null_percentage": (df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100,
                "duplicate_percentage": (df.duplicated().sum() / len(df)) * 100,
                "numeric_columns": len(df.select_dtypes(include=['number']).columns),
                "categorical_columns": len(df.select_dtypes(include=['object']).columns),
                "datetime_columns": len(df.select_dtypes(include=['datetime64']).columns)
            }
            
            # Enrichissement des insights avec des métriques
            if "insights" in enriched:
                for insight in enriched["insights"]:
                    insight["confidence"] = self._calculate_insight_confidence(insight, df)
                    insight["business_impact"] = self._assess_business_impact(insight)
            
            # Enrichissement des visualisations
            if "visualizations" in enriched:
                for viz in enriched["visualizations"]:
                    viz["data_requirements"] = self._assess_visualization_requirements(viz, df)
                    viz["complexity"] = self._assess_visualization_complexity(viz)
            
            return enriched
            
        except Exception as e:
            logger.error(f"Erreur lors de l'enrichissement des résultats: {e}")
            return analysis_result

    def _calculate_insight_confidence(self, insight: Dict[str, Any], df: pd.DataFrame) -> float:
        """Calcule la confiance d'un insight basé sur les données"""
        # Logique simple de calcul de confiance
        base_confidence = 0.7
        
        # Ajustement basé sur la taille du dataset
        if len(df) > 1000:
            base_confidence += 0.1
        elif len(df) < 100:
            base_confidence -= 0.2
        
        # Ajustement basé sur la qualité des données
        null_percentage = (df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
        if null_percentage < 5:
            base_confidence += 0.1
        elif null_percentage > 20:
            base_confidence -= 0.2
        
        return min(max(base_confidence, 0.0), 1.0)

    def _assess_business_impact(self, insight: Dict[str, Any]) -> str:
        """Évalue l'impact business d'un insight"""
        impact_keywords = {
            "high": ["revenue", "profit", "cost", "efficiency", "growth", "performance"],
            "medium": ["optimization", "improvement", "trend", "pattern", "correlation"],
            "low": ["observation", "note", "detail", "information"]
        }
        
        insight_text = (insight.get("title", "") + " " + insight.get("description", "")).lower()
        
        for impact_level, keywords in impact_keywords.items():
            if any(keyword in insight_text for keyword in keywords):
                return impact_level
        
        return "medium"

    def _assess_visualization_requirements(self, viz: Dict[str, Any], df: pd.DataFrame) -> Dict[str, Any]:
        """Évalue les exigences de données pour une visualisation"""
        required_columns = viz.get("columns", [])
        available_columns = df.columns.tolist()
        
        missing_columns = [col for col in required_columns if col not in available_columns]
        
        return {
            "required_columns": required_columns,
            "available_columns": available_columns,
            "missing_columns": missing_columns,
            "feasibility": len(missing_columns) == 0
        }

    def _assess_visualization_complexity(self, viz: Dict[str, Any]) -> str:
        """Évalue la complexité d'une visualisation"""
        viz_type = viz.get("type", "").lower()
        
        simple_viz = ["bar_chart", "line_chart", "pie_chart", "histogram"]
        complex_viz = ["heatmap", "scatter_plot", "funnel", "cohort_analysis", "geographic_map"]
        
        if viz_type in simple_viz:
            return "simple"
        elif viz_type in complex_viz:
            return "complex"
        else:
            return "medium"

    def _generate_adaptive_visualizations(self, analysis: Dict[str, Any], df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Génère des visualisations adaptées au contexte"""
        try:
            visualizations = []
            
            # Récupération des visualisations suggérées par le LLM
            suggested_viz = analysis.get("visualizations", [])
            
            for viz in suggested_viz:
                # Vérification de la faisabilité
                data_reqs = self._assess_visualization_requirements(viz, df)
                if data_reqs["feasibility"]:
                    viz["status"] = "feasible"
                    viz["implementation"] = self._get_visualization_implementation(viz, df)
                else:
                    viz["status"] = "not_feasible"
                    viz["reason"] = f"Colonnes manquantes: {data_reqs['missing_columns']}"
                
                visualizations.append(viz)
            
            # Ajout de visualisations automatiques basées sur les données
            auto_viz = self._generate_automatic_visualizations(df, analysis)
            visualizations.extend(auto_viz)
            
            return visualizations
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération des visualisations: {e}")
            return []

    def _get_visualization_implementation(self, viz: Dict[str, Any], df: pd.DataFrame) -> Dict[str, Any]:
        """Génère l'implémentation d'une visualisation"""
        viz_type = viz.get("type", "")
        
        implementations = {
            "bar_chart": {
                "chart_type": "bar",
                "x_axis": viz.get("columns", [])[0] if viz.get("columns") else None,
                "y_axis": viz.get("columns", [])[1] if len(viz.get("columns", [])) > 1 else None
            },
            "line_chart": {
                "chart_type": "line",
                "x_axis": viz.get("columns", [])[0] if viz.get("columns") else None,
                "y_axis": viz.get("columns", [])[1] if len(viz.get("columns", [])) > 1 else None
            },
            "scatter_plot": {
                "chart_type": "scatter",
                "x_axis": viz.get("columns", [])[0] if viz.get("columns") else None,
                "y_axis": viz.get("columns", [])[1] if len(viz.get("columns", [])) > 1 else None
            },
            "pie_chart": {
                "chart_type": "pie",
                "values": viz.get("columns", [])[0] if viz.get("columns") else None
            }
        }
        
        return implementations.get(viz_type, {
            "chart_type": "unknown",
            "note": "Type de visualisation non supporté"
        })

    def _generate_automatic_visualizations(self, df: pd.DataFrame, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Génère des visualisations automatiques basées sur les données"""
        auto_viz = []
        
        # Distribution des colonnes numériques
        numeric_cols = df.select_dtypes(include=['number']).columns
        for col in numeric_cols[:3]:  # Limiter à 3 colonnes
            auto_viz.append({
                "type": "histogram",
                "title": f"Distribution de {col}",
                "columns": [col],
                "rationale": "Analyse automatique de la distribution",
                "status": "feasible",
                "implementation": {
                    "chart_type": "histogram",
                    "x_axis": col
                }
            })
        
        # Corrélations si plusieurs colonnes numériques
        if len(numeric_cols) >= 2:
            auto_viz.append({
                "type": "correlation_heatmap",
                "title": "Matrice de corrélation",
                "columns": list(numeric_cols),
                "rationale": "Analyse automatique des corrélations",
                "status": "feasible",
                "implementation": {
                    "chart_type": "heatmap",
                    "data_type": "correlation"
                }
            })
        
        return auto_viz

    def _generate_analysis_metadata(self, df: pd.DataFrame, filename: str) -> Dict[str, Any]:
        """Génère les métadonnées de l'analyse"""
        return {
            "filename": filename,
            "analysis_date": datetime.now().isoformat(),
            "dataset_size": len(df),
            "columns": list(df.columns),
            "data_types": df.dtypes.to_dict(),
            "llm_provider": self.llm_provider,
            "analysis_version": "1.0"
        }

    def _generate_cache_key(self, df: pd.DataFrame, filename: str) -> str:
        """Génère une clé de cache basée sur le contenu du dataset"""
        # Hash du contenu des données
        data_hash = hashlib.md5(df.to_string().encode()).hexdigest()
        
        # Hash du nom de fichier et de la configuration
        config_hash = hashlib.md5(f"{filename}_{self.llm_provider}".encode()).hexdigest()
        
        return f"{data_hash}_{config_hash}"

    def _get_cached_analysis(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Récupère une analyse depuis le cache"""
        try:
            cache_file = self.cache_dir / f"{cache_key}.json"
            if cache_file.exists():
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                
                # Vérification de la validité du cache
                cache_time = datetime.fromisoformat(cached_data.get("analysis_timestamp", "1970-01-01"))
                if datetime.now() - cache_time < self.cache_ttl:
                    return cached_data
                else:
                    # Cache expiré, suppression
                    cache_file.unlink()
            
            return None
            
        except Exception as e:
            logger.warning(f"Erreur lors de la récupération du cache: {e}")
            return None

    def _cache_analysis(self, cache_key: str, analysis_data: Dict[str, Any]) -> None:
        """Met en cache une analyse"""
        try:
            cache_file = self.cache_dir / f"{cache_key}.json"
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(analysis_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Analyse mise en cache: {cache_key}")
            
        except Exception as e:
            logger.warning(f"Erreur lors de la mise en cache: {e}")

    def _get_statistical_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyse statistique de fallback"""
        return {
            "classification": {
                "domain": "Statistical Analysis",
                "data_type": "Fallback Analysis",
                "business_context": "Analyse statistique automatique",
                "confidence_score": 0.6
            },
            "key_metrics": [
                {
                    "name": "Nombre de lignes",
                    "value": len(df),
                    "type": "count",
                    "importance": 0.8
                },
                {
                    "name": "Nombre de colonnes",
                    "value": len(df.columns),
                    "type": "count",
                    "importance": 0.7
                }
            ],
            "insights": [
                {
                    "title": "Taille du dataset",
                    "description": f"Dataset contenant {len(df)} lignes et {len(df.columns)} colonnes",
                    "impact": "medium",
                    "evidence": "Calcul statistique de base"
                }
            ],
            "visualizations": [
                {
                    "type": "data_overview",
                    "title": "Aperçu des données",
                    "rationale": "Visualisation de base des données"
                }
            ],
            "correlations": [],
            "anomalies": [],
            "recommendations": [
                {
                    "action": "Analyser les données avec un outil LLM",
                    "priority": "high",
                    "expected_impact": "Amélioration de l'analyse"
                }
            ]
        }

    def _get_fallback_analysis(self, df: pd.DataFrame, filename: str) -> Dict[str, Any]:
        """Analyse de fallback en cas d'erreur complète"""
        return {
            "context": {"error": "Erreur lors de l'analyse"},
            "analysis": self._get_statistical_analysis(df),
            "visualizations": [],
            "metadata": {
                "filename": filename,
                "analysis_date": datetime.now().isoformat(),
                "error": True
            },
            "analysis_timestamp": datetime.now().isoformat()
        }
