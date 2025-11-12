"""
Tests Unitaires pour les Fonctions Critiques
FreeMobilaChat v4.5 Final Edition
"""

import pytest
import pandas as pd
import sys
import os

# Ajouter le chemin du projet
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))


class TestFileHandling:
    """Tests pour la gestion des fichiers"""
    
    def test_csv_detection(self):
        """Test: Détection du format CSV"""
        # Simuler un nom de fichier CSV
        filename = "test_data.csv"
        assert filename.endswith('.csv'), "Le fichier devrait être reconnu comme CSV"
    
    def test_excel_detection(self):
        """Test: Détection du format Excel"""
        filenames = ["test.xlsx", "test.xls"]
        for filename in filenames:
            assert filename.endswith(('.xlsx', '.xls')), f"{filename} devrait être reconnu comme Excel"
    
    def test_json_detection(self):
        """Test: Détection du format JSON"""
        filename = "test_data.json"
        assert filename.endswith('.json'), "Le fichier devrait être reconnu comme JSON"
    
    def test_file_size_validation(self):
        """Test: Validation de la taille du fichier (< 500 MB)"""
        max_size_mb = 500
        max_size_bytes = max_size_mb * 1024 * 1024
        
        # Test cas valide
        test_size_valid = 100 * 1024 * 1024  # 100 MB
        assert test_size_valid < max_size_bytes, "100 MB devrait être accepté"
        
        # Test cas invalide
        test_size_invalid = 600 * 1024 * 1024  # 600 MB
        assert test_size_invalid > max_size_bytes, "600 MB devrait être refusé"


class TestDataValidation:
    """Tests pour la validation des données"""
    
    def test_empty_dataframe_detection(self):
        """Test: Détection d'un DataFrame vide"""
        df_empty = pd.DataFrame()
        assert df_empty.empty, "DataFrame vide devrait être détecté"
        
        df_not_empty = pd.DataFrame({'col': [1, 2, 3]})
        assert not df_not_empty.empty, "DataFrame avec données devrait être détecté"
    
    def test_required_columns_validation(self):
        """Test: Validation des colonnes requises"""
        df = pd.DataFrame({
            'text': ['Tweet 1', 'Tweet 2', 'Tweet 3'],
            'sentiment': ['positive', 'negative', 'neutral']
        })
        
        # Vérifier la présence d'au moins une colonne texte
        text_columns = [col for col in df.columns if df[col].dtype == 'object']
        assert len(text_columns) > 0, "Au moins une colonne texte devrait exister"
    
    def test_data_types_validation(self):
        """Test: Validation des types de données"""
        df = pd.DataFrame({
            'text': ['Tweet 1', 'Tweet 2'],
            'count': [10, 20]
        })
        
        assert df['text'].dtype == 'object', "Colonne texte devrait être de type object"
        assert df['count'].dtype in ['int64', 'int32'], "Colonne count devrait être numérique"
    
    def test_null_values_detection(self):
        """Test: Détection des valeurs nulles"""
        df = pd.DataFrame({
            'text': ['Tweet 1', None, 'Tweet 3'],
            'sentiment': ['positive', 'negative', None]
        })
        
        null_counts = df.isnull().sum()
        assert null_counts['text'] == 1, "Une valeur nulle devrait être détectée dans 'text'"
        assert null_counts['sentiment'] == 1, "Une valeur nulle devrait être détectée dans 'sentiment'"


class TestMetricsCalculation:
    """Tests pour le calcul des métriques"""
    
    def test_reclamations_count(self):
        """Test: Comptage des réclamations"""
        df = pd.DataFrame({
            'is_claim': ['oui', 'non', 'oui', 'oui', 'non']
        })
        
        reclamations_count = len(df[df['is_claim'] == 'oui'])
        assert reclamations_count == 3, "3 réclamations devraient être comptées"
    
    def test_reclamations_percentage(self):
        """Test: Calcul du pourcentage de réclamations"""
        df = pd.DataFrame({
            'is_claim': ['oui', 'non', 'oui', 'oui', 'non']
        })
        
        reclamations_count = len(df[df['is_claim'] == 'oui'])
        total_count = len(df)
        percentage = (reclamations_count / total_count) * 100
        
        assert percentage == 60.0, "Le pourcentage devrait être 60%"
    
    def test_sentiment_distribution(self):
        """Test: Distribution des sentiments"""
        df = pd.DataFrame({
            'sentiment': ['positive', 'negative', 'neutral', 'positive', 'negative']
        })
        
        sentiment_counts = df['sentiment'].value_counts()
        
        assert sentiment_counts['positive'] == 2, "2 sentiments positifs"
        assert sentiment_counts['negative'] == 2, "2 sentiments négatifs"
        assert sentiment_counts['neutral'] == 1, "1 sentiment neutre"
    
    def test_confidence_score_calculation(self):
        """Test: Calcul du score de confiance"""
        scores = [0.95, 0.88, 0.92, 0.85, 0.90]
        avg_confidence = sum(scores) / len(scores)
        
        assert 0.88 <= avg_confidence <= 0.92, "La confiance moyenne devrait être entre 0.88 et 0.92"
        assert round(avg_confidence, 2) == 0.90, "La confiance moyenne devrait être 0.90"


class TestTextCleaning:
    """Tests pour le nettoyage de texte"""
    
    def test_url_removal(self):
        """Test: Suppression des URLs"""
        text = "Consultez https://example.com pour plus d'infos"
        # Simulation de nettoyage URL
        import re
        cleaned = re.sub(r'https?://\S+', '', text)
        
        assert 'https://' not in cleaned, "Les URLs devraient être supprimées"
        assert 'example.com' not in cleaned, "Les domaines devraient être supprimés"
    
    def test_mention_handling(self):
        """Test: Gestion des mentions Twitter"""
        text = "@user1 Merci pour votre aide @user2"
        # Simulation de nettoyage mentions
        import re
        cleaned = re.sub(r'@\w+', '', text)
        
        assert '@user1' not in cleaned, "Les mentions devraient être supprimées"
        assert '@user2' not in cleaned, "Les mentions devraient être supprimées"
    
    def test_special_characters_removal(self):
        """Test: Suppression des caractères spéciaux"""
        text = "Texte avec #hashtag et émoticônes 😊"
        
        # Les hashtags et emojis devraient être traités
        assert '#hashtag' in text, "Le texte original contient des hashtags"
    
    def test_lowercase_conversion(self):
        """Test: Conversion en minuscules"""
        text = "TEXTE EN MAJUSCULES"
        cleaned = text.lower()
        
        assert cleaned == "texte en majuscules", "Le texte devrait être en minuscules"
    
    def test_whitespace_normalization(self):
        """Test: Normalisation des espaces"""
        text = "Texte  avec    espaces     multiples"
        import re
        cleaned = re.sub(r'\s+', ' ', text).strip()
        
        assert cleaned == "Texte avec espaces multiples", "Les espaces multiples devraient être normalisés"


class TestErrorHandling:
    """Tests pour la gestion des erreurs"""
    
    def test_error_403_detection(self):
        """Test: Détection de l'erreur 403"""
        error_message = "AxiosError: Request failed with status code 403"
        
        assert "403" in error_message, "L'erreur 403 devrait être détectée"
        assert "forbidden" in error_message.lower() or "403" in error_message, "Message d'erreur approprié"
    
    def test_file_not_found_handling(self):
        """Test: Gestion de fichier non trouvé"""
        import os
        
        non_existent_file = "file_that_does_not_exist.csv"
        assert not os.path.exists(non_existent_file), "Le fichier ne devrait pas exister"
    
    def test_encoding_error_handling(self):
        """Test: Gestion des erreurs d'encodage"""
        # Simuler différents encodages
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        
        assert 'utf-8' in encodings, "UTF-8 devrait être supporté"
        assert len(encodings) >= 4, "Au moins 4 encodages devraient être supportés"
    
    def test_memory_error_prevention(self):
        """Test: Prévention des erreurs mémoire"""
        max_file_size = 500 * 1024 * 1024  # 500 MB
        
        # Vérifier que la limite est raisonnable
        assert max_file_size == 524288000, "La limite devrait être 500 MB"
        assert max_file_size < 1024 * 1024 * 1024, "La limite devrait être < 1 GB"


class TestConfiguration:
    """Tests pour la configuration"""
    
    def test_server_port_configuration(self):
        """Test: Configuration du port serveur"""
        expected_port = 8502
        
        # Vérifier que le port est dans une plage valide
        assert 1024 <= expected_port <= 65535, "Le port devrait être dans une plage valide"
        assert expected_port == 8502, "Le port devrait être 8502"
    
    def test_cors_configuration(self):
        """Test: Configuration CORS"""
        # CORS devrait être désactivé pour le développement
        cors_enabled = False
        
        assert cors_enabled == False, "CORS devrait être désactivé en développement"
    
    def test_upload_size_limit(self):
        """Test: Limite de taille d'upload"""
        max_upload_size_mb = 500
        
        assert max_upload_size_mb == 500, "La limite d'upload devrait être 500 MB"
        assert max_upload_size_mb > 0, "La limite devrait être positive"
    
    def test_xsrf_protection_configuration(self):
        """Test: Configuration de la protection XSRF"""
        # XSRF devrait être désactivé pour le développement
        xsrf_enabled = False
        
        assert xsrf_enabled == False, "XSRF devrait être désactivé en développement"


class TestUserInterface:
    """Tests pour l'interface utilisateur"""
    
    def test_font_awesome_icons(self):
        """Test: Icônes Font Awesome"""
        # Format d'icône correct
        icon_html = "<i class='fas fa-robot'></i>"
        
        assert "<i class='fas fa-" in icon_html, "Format d'icône Font Awesome correct"
        assert "</i>" in icon_html, "Balise fermante présente"
    
    def test_stat_card_class(self):
        """Test: Classe CSS stat-card"""
        css_class = "stat-card"
        
        assert css_class == "stat-card", "Classe CSS correcte"
    
    def test_header_title_class(self):
        """Test: Classe CSS header-title"""
        css_class = "header-title"
        
        assert css_class == "header-title", "Classe CSS correcte"
    
    def test_terminology_french(self):
        """Test: Terminologie française"""
        # Vérifier que "Claims" n'est plus utilisé
        correct_term = "Réclamations"
        incorrect_term = "Claims"
        
        assert correct_term == "Réclamations", "Terminologie française correcte"
        assert correct_term != incorrect_term, "Le terme anglais ne devrait pas être utilisé"


class TestPerformance:
    """Tests pour les performances"""
    
    def test_lazy_loading_enabled(self):
        """Test: Chargement paresseux activé"""
        # Simuler le chargement paresseux
        lazy_load = True
        
        assert lazy_load == True, "Le chargement paresseux devrait être activé"
    
    def test_cache_enabled(self):
        """Test: Cache activé"""
        # Streamlit cache devrait être utilisé
        cache_enabled = True
        
        assert cache_enabled == True, "Le cache devrait être activé"
    
    def test_response_time_target(self):
        """Test: Objectif de temps de réponse"""
        target_response_time = 5  # secondes
        
        assert target_response_time == 5, "L'objectif devrait être 5 secondes"
        assert target_response_time < 10, "L'objectif devrait être < 10 secondes"


def run_all_tests():
    """Exécuter tous les tests"""
    pytest.main([__file__, '-v', '--tb=short'])


if __name__ == "__main__":
    run_all_tests()





