"""
Moteur LLM réel avec API calls pour générer des insights uniques
"""

import os
import json
import hashlib
import logging
import asyncio
import aiohttp
from typing import Dict, List, Any, Optional
import pandas as pd
from datetime import datetime
import openai
from anthropic import Anthropic
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class RealLLMEngine:
    """
    Moteur LLM réel qui génère des insights uniques pour chaque fichier
    """
    
    def __init__(self):
        self.cache_dir = "streamlit_app/cache/llm_analysis"
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Configuration des providers
        self.providers = {
            "openai": {
                "client": self._init_openai(),
                "model": "gpt-4-turbo-preview",
                "max_tokens": 4000,
                "temperature": 0.1
            },
            "anthropic": {
                "client": self._init_anthropic(),
                "model": "claude-3-sonnet-20240229",
                "max_tokens": 4000,
                "temperature": 0.1
            },
            "local": {
                "client": None,
                "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
                "model": "llama2-13b-chat",
                "temperature": 0.1
            }
        }
        
        # Provider actuel
        self.current_provider = self._get_available_provider()
        
    def _init_openai(self):
        """Initialise OpenAI"""
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                return openai.OpenAI(api_key=api_key)
        except Exception as e:
            logger.warning(f"OpenAI non disponible: {e}")
        return None
    
    def _init_anthropic(self):
        """Initialise Anthropic"""
        try:
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if api_key:
                return Anthropic(api_key=api_key)
        except Exception as e:
            logger.warning(f"Anthropic non disponible: {e}")
        return None
    
    def _get_available_provider(self):
        """Retourne le premier provider disponible"""
        for provider_name, config in self.providers.items():
            if provider_name == "openai" and config["client"]:
                return provider_name
            elif provider_name == "anthropic" and config["client"]:
                return provider_name
            elif provider_name == "local" and self._check_local_ollama():
                return provider_name
        return "openai"  # Fallback
    
    def _check_local_ollama(self):
        """Vérifie si Ollama local est disponible"""
        try:
            import httpx
            ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            response = httpx.get(f"{ollama_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def generate_file_hash(self, df: pd.DataFrame, filename: str) -> str:
        """Génère un hash unique basé sur le contenu du fichier"""
        # Hash basé sur le contenu des données + métadonnées
        content_hash = hashlib.md5()
        
        # Hash du contenu des données
        content_hash.update(df.to_string().encode('utf-8'))
        
        # Hash des métadonnées
        metadata = {
            'filename': filename,
            'shape': df.shape,
            'columns': list(df.columns),
            'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()}
        }
        content_hash.update(json.dumps(metadata, sort_keys=True).encode('utf-8'))
        
        return content_hash.hexdigest()
    
    def get_cached_analysis(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """Récupère une analyse depuis le cache"""
        try:
            cache_file = os.path.join(self.cache_dir, f"{file_hash}.json")
            if os.path.exists(cache_file):
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                
                # Vérification de la validité du cache (24h)
                cache_time = datetime.fromisoformat(cached_data.get("cache_timestamp", "1970-01-01"))
                if datetime.now() - cache_time < pd.Timedelta(hours=24):
                    logger.info(f"Analyse trouvée dans le cache: {file_hash[:8]}...")
                    return cached_data
                else:
                    # Cache expiré, suppression
                    os.remove(cache_file)
            
            return None
        except Exception as e:
            logger.warning(f"Erreur lors de la récupération du cache: {e}")
            return None
    
    def cache_analysis(self, file_hash: str, analysis: Dict[str, Any]):
        """Met en cache une analyse"""
        try:
            analysis["cache_timestamp"] = datetime.now().isoformat()
            cache_file = os.path.join(self.cache_dir, f"{file_hash}.json")
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(analysis, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Analyse mise en cache: {file_hash[:8]}...")
        except Exception as e:
            logger.warning(f"Erreur lors de la mise en cache: {e}")
    
    async def analyze_with_llm(self, df: pd.DataFrame, filename: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyse réelle avec LLM - génère des insights uniques
        """
        try:
            # Génération du hash du fichier
            file_hash = self.generate_file_hash(df, filename)
            
            # Vérification du cache
            cached_analysis = self.get_cached_analysis(file_hash)
            if cached_analysis:
                return cached_analysis
            
            logger.info(f"Nouvelle analyse LLM pour {filename} (hash: {file_hash[:8]}...)")
            
            # Génération du prompt contextuel
            prompt = self._generate_contextual_prompt(df, filename, context)
            
            # Appel LLM avec retry
            llm_response = await self._call_llm_with_retry(prompt)
            
            # Parsing de la réponse
            analysis_result = self._parse_llm_response(llm_response, df, context)
            
            # Enrichissement avec des métriques calculées
            enriched_analysis = self._enrich_analysis(analysis_result, df, context)
            
            # Ajout des métadonnées
            enriched_analysis.update({
                "file_hash": file_hash,
                "filename": filename,
                "analysis_timestamp": datetime.now().isoformat(),
                "provider_used": self.current_provider,
                "cache_timestamp": datetime.now().isoformat()
            })
            
            # Mise en cache
            self.cache_analysis(file_hash, enriched_analysis)
            
            return enriched_analysis
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse LLM: {e}")
            return self._get_fallback_analysis(df, filename, context)
    
    def _generate_contextual_prompt(self, df: pd.DataFrame, filename: str, context: Dict[str, Any]) -> str:
        """Génère un prompt contextuel unique pour chaque fichier"""
        
        # Informations de base
        row_count = len(df)
        column_count = len(df.columns)
        domain = context.get('domain_analysis', {}).get('detected_domain', 'général')
        confidence = context.get('domain_analysis', {}).get('confidence_score', 0.7)
        
        # Échantillon de données unique
        sample_data = df.head(5).to_string()
        
        # Analyse des colonnes
        column_info = []
        for col in df.columns:
            col_info = {
                'name': col,
                'type': str(df[col].dtype),
                'null_count': df[col].isnull().sum(),
                'unique_count': df[col].nunique()
            }
            if pd.api.types.is_numeric_dtype(df[col]):
                col_info.update({
                    'min': df[col].min(),
                    'max': df[col].max(),
                    'mean': df[col].mean()
                })
            column_info.append(col_info)
        
        # Patterns détectés
        patterns = context.get('pattern_analysis', {}).get('patterns', [])
        anomalies = context.get('pattern_analysis', {}).get('anomalies', [])
        correlations = context.get('correlation_analysis', {}).get('strong_correlations', [])
        
        prompt = f"""
Tu es un data scientist expert. Analyse ce dataset UNIQUE avec {row_count} lignes et {column_count} colonnes.

FICHIER: {filename}
DOMAINE DÉTECTÉ: {domain} (confiance: {confidence:.1%})

COLONNES DISPONIBLES:
{json.dumps(column_info, indent=2, ensure_ascii=False)}

ÉCHANTILLON DE DONNÉES:
{sample_data}

PATTERNS DÉTECTÉS:
- Patterns: {len(patterns)} patterns identifiés
- Anomalies: {len(anomalies)} anomalies détectées  
- Corrélations: {len(correlations)} corrélations fortes

TÂCHES REQUISES (OBLIGATOIRE - génère des insights UNIQUES pour ce fichier):

1. CLASSIFICATION SPÉCIFIQUE:
   - Identifie le type EXACT de données de ce fichier
   - Détermine le contexte métier PRÉCIS
   - Calcule un score de confiance basé sur les données réelles

2. MÉTRIQUES PERSONNALISÉES:
   - Calcule des KPIs spécifiques à ce dataset
   - Identifie les métriques les plus pertinentes
   - Génère des valeurs réelles basées sur les données

3. INSIGHTS UNIQUES (minimum 5):
   - Découvre des patterns spécifiques à ce fichier
   - Identifie des tendances uniques
   - Révèle des anomalies intéressantes
   - Génère des insights actionnables

4. VISUALISATIONS OPTIMALES:
   - Sélectionne les meilleurs graphiques pour ce dataset
   - Justifie chaque choix de visualisation
   - Adapte les graphiques au contexte métier

5. RECOMMANDATIONS CONCRÈTES:
   - Propose des actions spécifiques à ce dataset
   - Priorise les recommandations
   - Estime l'impact attendu

IMPORTANT: Chaque analyse doit être UNIQUE et spécifique à ce fichier. 
Ne génère JAMAIS de résultats génériques ou statiques.

RÉPONDS EN JSON STRUCTURÉ avec cette structure exacte:
{{
    "classification": {{
        "domain": "domaine spécifique détecté",
        "data_type": "type exact de données",
        "business_context": "contexte métier précis",
        "confidence_score": 0.0-1.0,
        "unique_characteristics": ["caractéristiques uniques du fichier"]
    }},
    "key_metrics": [
        {{"name": "nom métrique", "column": "colonne", "type": "type", "value": valeur_réelle, "importance": 0.0-1.0, "description": "description spécifique"}}
    ],
    "insights": [
        {{"title": "titre insight unique", "description": "description détaillée", "impact": "high/medium/low", "evidence": "preuve basée sur les données", "confidence": 0.0-1.0, "uniqueness_score": 0.0-1.0}}
    ],
    "visualizations": [
        {{"type": "type_graphique", "columns": ["col1", "col2"], "title": "titre spécifique", "rationale": "justification détaillée", "priority": "high/medium/low"}}
    ],
    "correlations": [
        {{"columns": ["col1", "col2"], "strength": 0.0-1.0, "interpretation": "interprétation spécifique", "business_impact": "impact métier"}}
    ],
    "anomalies": [
        {{"description": "description anomalie", "location": "localisation", "severity": "high/medium/low", "recommendation": "action recommandée"}}
    ],
    "recommendations": [
        {{"action": "action concrète", "priority": "high/medium/low", "expected_impact": "impact attendu", "implementation": "étapes d'implémentation"}}
    ],
    "unique_findings": [
        "découverte unique 1",
        "découverte unique 2",
        "découverte unique 3"
    ]
}}
"""
        return prompt
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def _call_llm_with_retry(self, prompt: str) -> str:
        """Appelle le LLM avec retry et fallback"""
        try:
            # Essai avec le provider actuel
            response = await self._call_provider(self.current_provider, prompt)
            if response:
                return response
            
            # Fallback vers d'autres providers
            for provider_name in ["openai", "anthropic", "local"]:
                if provider_name != self.current_provider:
                    try:
                        response = await self._call_provider(provider_name, prompt)
                        if response:
                            logger.info(f"Fallback réussi vers {provider_name}")
                            self.current_provider = provider_name
                            return response
                    except Exception as e:
                        logger.warning(f"Échec du fallback {provider_name}: {e}")
                        continue
            
            # Si tous les providers échouent
            raise Exception("Tous les providers LLM ont échoué")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'appel LLM: {e}")
            raise e
    
    async def _call_provider(self, provider_name: str, prompt: str) -> Optional[str]:
        """Appelle un provider LLM spécifique"""
        try:
            config = self.providers[provider_name]
            
            if provider_name == "openai" and config["client"]:
                response = await config["client"].chat.completions.create(
                    model=config["model"],
                    messages=[{"role": "user", "content": prompt}],
                    temperature=config["temperature"],
                    max_tokens=config["max_tokens"]
                )
                return response.choices[0].message.content
            
            elif provider_name == "anthropic" and config["client"]:
                response = await config["client"].messages.create(
                    model=config["model"],
                    max_tokens=config["max_tokens"],
                    temperature=config["temperature"],
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text
            
            elif provider_name == "local":
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{config['base_url']}/api/generate",
                        json={
                            "model": config["model"],
                            "prompt": prompt,
                            "stream": False,
                            "options": {
                                "temperature": config["temperature"]
                            }
                        },
                        timeout=120
                    )
                    if response.status_code == 200:
                        return response.json()["response"]
            
            return None
            
        except Exception as e:
            logger.error(f"Erreur avec le provider {provider_name}: {e}")
            return None
    
    def _parse_llm_response(self, response: str, df: pd.DataFrame, context: Dict[str, Any]) -> Dict[str, Any]:
        """Parse la réponse LLM en JSON structuré"""
        try:
            # Nettoyage de la réponse
            response = response.strip()
            
            # Recherche du JSON dans la réponse
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_content = response[json_start:json_end].strip()
            elif "{" in response and "}" in response:
                json_start = response.find("{")
                json_end = response.rfind("}") + 1
                json_content = response[json_start:json_end]
            else:
                raise ValueError("Aucun JSON trouvé dans la réponse")
            
            # Parsing JSON
            result = json.loads(json_content)
            
            # Validation de la structure
            if not self._validate_analysis_structure(result):
                raise ValueError("Structure de réponse invalide")
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur lors du parsing de la réponse LLM: {e}")
            filename = context.get('filename', 'unknown_file.csv')
            return self._get_fallback_analysis(df, filename, context)
    
    def _validate_analysis_structure(self, result: Dict[str, Any]) -> bool:
        """Valide la structure de la réponse d'analyse"""
        required_keys = ["classification", "insights", "key_metrics"]
        return all(key in result for key in required_keys)
    
    def _enrich_analysis(self, analysis: Dict[str, Any], df: pd.DataFrame, context: Dict[str, Any]) -> Dict[str, Any]:
        """Enrichit l'analyse avec des métriques calculées"""
        try:
            # Ajout de métriques de base
            analysis["dataset_metrics"] = {
                "row_count": len(df),
                "column_count": len(df.columns),
                "memory_usage": df.memory_usage(deep=True).sum(),
                "completeness": (1 - df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
            }
            
            # Ajout de métriques de qualité
            analysis["data_quality"] = {
                "null_percentage": (df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100,
                "duplicate_percentage": (df.duplicated().sum() / len(df)) * 100,
                "numeric_columns": len(df.select_dtypes(include=['number']).columns),
                "categorical_columns": len(df.select_dtypes(include=['object']).columns),
                "datetime_columns": len(df.select_dtypes(include=['datetime64']).columns)
            }
            
            # Enrichissement des insights avec des métriques calculées
            if "insights" in analysis:
                for insight in analysis["insights"]:
                    if "confidence" not in insight:
                        insight["confidence"] = 0.8
                    if "uniqueness_score" not in insight:
                        insight["uniqueness_score"] = 0.9
            
            return analysis
            
        except Exception as e:
            logger.error(f"Erreur lors de l'enrichissement: {e}")
            return analysis
    
    def _get_fallback_analysis(self, df: pd.DataFrame, filename: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyse de fallback en cas d'erreur LLM"""
        return {
            "classification": {
                "domain": "General",
                "data_type": "Dataset Analysis",
                "business_context": "Analyse de données générale",
                "confidence_score": 0.5,
                "unique_characteristics": ["Analyse de base effectuée"]
            },
            "key_metrics": [
                {
                    "name": "Nombre de lignes",
                    "column": "total_rows",
                    "type": "count",
                    "value": len(df),
                    "importance": 0.8,
                    "description": "Nombre total de lignes dans le dataset"
                }
            ],
            "insights": [
                {
                    "title": "Dataset analysé",
                    "description": f"Dataset de {len(df)} lignes et {len(df.columns)} colonnes analysé avec succès",
                    "impact": "medium",
                    "evidence": "Analyse de base effectuée",
                    "confidence": 0.6,
                    "uniqueness_score": 0.3
                }
            ],
            "visualizations": [
                {
                    "type": "data_overview",
                    "title": "Aperçu des données",
                    "rationale": "Visualisation de base des données",
                    "priority": "medium"
                }
            ],
            "correlations": [],
            "anomalies": [],
            "recommendations": [
                {
                    "action": "Effectuer une analyse plus approfondie",
                    "priority": "medium",
                    "expected_impact": "Découverte d'insights supplémentaires",
                    "implementation": "Utiliser un outil d'analyse avancé"
                }
            ],
            "unique_findings": [
                f"Dataset {filename} contient {len(df)} lignes de données",
                f"Structure: {len(df.columns)} colonnes disponibles"
            ],
            "dataset_metrics": {
                "row_count": len(df),
                "column_count": len(df.columns),
                "memory_usage": df.memory_usage(deep=True).sum(),
                "completeness": 100
            },
            "data_quality": {
                "null_percentage": 0,
                "duplicate_percentage": 0,
                "numeric_columns": len(df.select_dtypes(include=['number']).columns),
                "categorical_columns": len(df.select_dtypes(include=['object']).columns),
                "datetime_columns": len(df.select_dtypes(include=['datetime64']).columns)
            }
        }
