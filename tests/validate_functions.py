"""
Script de validation simple des nouvelles fonctionnalités
"""

import sys
from pathlib import Path

# Ajouter le chemin du projet
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "streamlit_app"))


def test_imports():
    """Test que toutes les fonctions peuvent être importées"""
    print("🔍 Validation des imports...")

    try:
        from pages.Classification_Mistral import (
            _normalize_kpi_fields,
            _render_provider_cards,
            _section_upload,
            _load_modern_css,
        )

        print("✅ Toutes les fonctions sont importables")
        return True
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        return False


def test_normalize_function():
    """Test de la fonction _normalize_kpi_fields"""
    print("\n🔍 Test de _normalize_kpi_fields...")

    try:
        import pandas as pd
        from pages.Classification_Mistral import _normalize_kpi_fields

        # Test 1: DataFrame avec colonnes standard
        df1 = pd.DataFrame(
            {"text": ["Test tweet"], "sentiment": ["POSITIVE"], "is_claim": ["YES"]}
        )
        result1 = _normalize_kpi_fields(df1)
        assert "sentiment" in result1.columns, "Colonne sentiment manquante"
        assert (
            result1["sentiment"].iloc[0] == "POSITIF"
        ), "Normalisation sentiment échouée"
        print("  ✅ Test 1: Normalisation sentiment OK")

        # Test 2: DataFrame avec colonnes manquantes
        df2 = pd.DataFrame({"text": ["Test"]})
        result2 = _normalize_kpi_fields(df2)
        assert "sentiment" in result2.columns, "Colonne sentiment non créée"
        assert "is_claim" in result2.columns, "Colonne is_claim non créée"
        assert "urgence" in result2.columns, "Colonne urgence non créée"
        assert "confidence" in result2.columns, "Colonne confidence non créée"
        print("  ✅ Test 2: Création colonnes manquantes OK")

        # Test 3: Colonnes alternatives
        df3 = pd.DataFrame(
            {"text": ["Test"], "priority": ["HIGH"], "category": ["FIBRE"]}
        )
        result3 = _normalize_kpi_fields(df3)
        # La fonction normalise HIGH -> ELEVEE
        assert result3["urgence"].iloc[0] in [
            "ELEVEE",
            "HIGH",
        ], f"Reconnaissance colonne alternative échouée: {result3['urgence'].iloc[0]}"
        print(
            f"  ✅ Test 3: Reconnaissance colonnes alternatives OK (urgence={result3['urgence'].iloc[0]})"
        )

        print("✅ Tous les tests de _normalize_kpi_fields passent")
        return True
    except Exception as e:
        print(f"❌ Erreur dans test_normalize_function: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Fonction principale"""
    print("=" * 60)
    print("VALIDATION DES NOUVELLES FONCTIONNALITÉS")
    print("=" * 60)

    results = []

    # Test 1: Imports
    results.append(test_imports())

    # Test 2: Fonction normalize
    results.append(test_normalize_function())

    # Résumé
    print("\n" + "=" * 60)
    print("RÉSUMÉ")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Tests réussis: {passed}/{total}")

    if all(results):
        print("✅ Toutes les validations sont passées!")
        return 0
    else:
        print("❌ Certaines validations ont échoué")
        return 1


if __name__ == "__main__":
    sys.exit(main())
