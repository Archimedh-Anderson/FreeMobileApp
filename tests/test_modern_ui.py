"""
Tests pour valider les nouvelles fonctionnalités UI modernisées
"""
import pytest
import sys
from pathlib import Path

# Ajouter le chemin du projet
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "streamlit_app"))

def test_normalize_kpi_fields_function_exists():
    """Test que la fonction _normalize_kpi_fields existe"""
    from pages.Classification_Mistral import _normalize_kpi_fields
    assert callable(_normalize_kpi_fields), "La fonction _normalize_kpi_fields doit exister"

def test_normalize_kpi_fields_basic():
    """Test de base de la fonction _normalize_kpi_fields"""
    import pandas as pd
    from pages.Classification_Mistral import _normalize_kpi_fields
    
    # Créer un DataFrame de test
    df = pd.DataFrame({
        'text': ['Test tweet 1', 'Test tweet 2'],
        'sentiment': ['POSITIVE', 'NEGATIVE'],
        'is_claim': ['YES', 'NO']
    })
    
    # Normaliser
    result = _normalize_kpi_fields(df)
    
    # Vérifications
    assert 'sentiment' in result.columns
    assert 'is_claim' in result.columns
    assert result['sentiment'].iloc[0] == 'POSITIF'
    assert result['is_claim'].iloc[0] == 'OUI'

def test_provider_cards_function_exists():
    """Test que la fonction _render_provider_cards existe"""
    from pages.Classification_Mistral import _render_provider_cards
    assert callable(_render_provider_cards), "La fonction _render_provider_cards doit exister"

def test_upload_section_function_exists():
    """Test que la fonction _section_upload existe"""
    from pages.Classification_Mistral import _section_upload
    assert callable(_section_upload), "La fonction _section_upload doit exister"

def test_css_loading_function_exists():
    """Test que la fonction _load_modern_css existe"""
    from pages.Classification_Mistral import _load_modern_css
    assert callable(_load_modern_css), "La fonction _load_modern_css doit exister"

def test_normalize_kpi_fields_missing_columns():
    """Test que _normalize_kpi_fields gère les colonnes manquantes"""
    import pandas as pd
    from pages.Classification_Mistral import _normalize_kpi_fields
    
    # DataFrame sans colonnes KPI
    df = pd.DataFrame({
        'text': ['Test tweet']
    })
    
    result = _normalize_kpi_fields(df)
    
    # Vérifier que les colonnes sont créées avec des valeurs par défaut
    assert 'sentiment' in result.columns
    assert 'is_claim' in result.columns
    assert 'urgence' in result.columns
    assert 'confidence' in result.columns

def test_normalize_kpi_fields_alternative_columns():
    """Test que _normalize_kpi_fields reconnaît les colonnes alternatives"""
    import pandas as pd
    from pages.Classification_Mistral import _normalize_kpi_fields
    
    # DataFrame avec colonnes alternatives
    df = pd.DataFrame({
        'text': ['Test tweet'],
        'priority': ['HIGH'],
        'category': ['FIBRE']
    })
    
    result = _normalize_kpi_fields(df)
    
    # Vérifier que les colonnes alternatives sont utilisées
    assert 'urgence' in result.columns
    assert result['urgence'].iloc[0] == 'ELEVEE'

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

