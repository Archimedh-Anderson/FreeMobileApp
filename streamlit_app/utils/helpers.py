"""
Fonctions utilitaires pour l'application
Helpers génériques et fonctions communes
"""

import os
import time
import hashlib
import io
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
from urllib.parse import urlparse

import pandas as pd
import requests
from requests import RequestException
import streamlit as st


def format_file_size(size_bytes: int) -> str:
    """Formate une taille de fichier en format lisible"""
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024.0 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1

    return f"{size_bytes:.1f} {size_names[i]}"


def get_file_extension(filename: str) -> str:
    """Extrait l'extension d'un fichier"""
    return os.path.splitext(filename)[1].lower()


def generate_batch_id() -> str:
    """Génère un ID de batch unique"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    random_suffix = hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
    return f"batch_{timestamp}_{random_suffix}"


def format_duration(seconds: float) -> str:
    """Formate une durée en format lisible"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}min"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def format_percentage(value: float, decimals: int = 1) -> str:
    """Formate un pourcentage"""
    return f"{value:.{decimals}f}%"


def format_number(value: Union[int, float], decimals: int = 0) -> str:
    """Formate un nombre avec séparateurs de milliers"""
    if isinstance(value, float):
        return f"{value:,.{decimals}f}"
    else:
        return f"{value:,}"


def get_current_timestamp() -> str:
    """Retourne le timestamp actuel formaté"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_time_ago(timestamp: str) -> str:
    """Calcule le temps écoulé depuis un timestamp"""
    try:
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
        diff = now - dt

        if diff.days > 0:
            return f"il y a {diff.days} jour{'s' if diff.days > 1 else ''}"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"il y a {hours} heure{'s' if hours > 1 else ''}"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"il y a {minutes} minute{'s' if minutes > 1 else ''}"
        else:
            return "à l'instant"
    except:
        return "inconnu"


def truncate_text(text: str, max_length: int = 100) -> str:
    """Tronque un texte à une longueur maximale"""
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def clean_filename(filename: str) -> str:
    """Nettoie un nom de fichier pour l'utilisation"""
    # Supprimer les caractères non autorisés
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, "_")

    # Limiter la longueur
    if len(filename) > 100:
        name, ext = os.path.splitext(filename)
        filename = name[: 100 - len(ext)] + ext

    return filename


def get_file_hash(file_content: bytes) -> str:
    """Calcule le hash d'un fichier"""
    return hashlib.md5(file_content).hexdigest()


def is_valid_email(email: str) -> bool:
    """Vérifie si un email est valide"""
    import re

    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def safe_get(dictionary: Dict[str, Any], key: str, default: Any = None) -> Any:
    """Récupère une valeur d'un dictionnaire de manière sécurisée"""
    try:
        return dictionary.get(key, default)
    except (AttributeError, TypeError):
        return default


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """Divise une liste en chunks de taille donnée"""
    return [lst[i : i + chunk_size] for i in range(0, len(lst), chunk_size)]


def flatten_dict(
    d: Dict[str, Any], parent_key: str = "", sep: str = "_"
) -> Dict[str, Any]:
    """Aplatit un dictionnaire imbriqué"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def create_progress_bar(progress: float, message: str = "") -> None:
    """Crée une barre de progression avec message"""
    st.progress(progress)
    if message:
        st.caption(message)


def show_loading_spinner(message: str = "Chargement..."):
    """Affiche un spinner de chargement"""
    with st.spinner(message):
        time.sleep(0.1)  # Petite pause pour afficher le spinner


def create_metric_card(
    title: str, value: str, delta: str = None, delta_color: str = "normal"
) -> str:
    """Crée une carte de métrique HTML"""

    delta_html = ""
    if delta:
        delta_class = f"delta-{delta_color}"
        delta_html = f'<div class="metric-delta {delta_class}">{delta}</div>'

    return f"""
    <div class="metric-card">
        <div class="metric-title">{title}</div>
        <div class="metric-value">{value}</div>
        {delta_html}
    </div>
    """


def create_status_badge(status: str, color: str = "blue") -> str:
    """Crée un badge de statut"""
    return f'<span class="status-badge status-{color}">{status}</span>'


def format_currency(amount: float, currency: str = "€") -> str:
    """Formate un montant en devise"""
    return f"{amount:,.2f} {currency}"


def get_file_type_icon(extension: str) -> str:
    """Retourne l'icône pour un type de fichier"""
    icons = {
        ".csv": "",
        ".xlsx": "",
        ".xls": "",
        ".json": "",
        ".parquet": "",
        ".txt": "",
        ".pdf": "",
    }
    return icons.get(extension.lower(), "")


def create_tooltip(text: str, tooltip: str) -> str:
    """Crée un élément avec tooltip"""
    return f'<span title="{tooltip}">{text}</span>'


def validate_session_state() -> bool:
    """Valide l'état de la session"""
    required_keys = ["user_role"]
    return all(key in st.session_state for key in required_keys)


def clear_session_data():
    """Nettoie les données de session"""
    keys_to_clear = [
        "uploaded_data",
        "uploaded_filename",
        "current_batch_id",
        "analysis_status",
        "kpi_data",
        "tweets_data",
        "file_info",
    ]

    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]


def get_user_agent() -> str:
    """Retourne un User-Agent pour les requêtes HTTP"""
    return "FreeMobilaChat/2.0.0 (Streamlit App)"


def create_download_link(data: bytes, filename: str, mime_type: str) -> str:
    """Crée un lien de téléchargement"""
    import base64

    b64 = base64.b64encode(data).decode()
    return f'<a href="data:{mime_type};base64,{b64}" download="{filename}">Télécharger {filename}</a>'


def format_relative_time(timestamp: str) -> str:
    """Formate un timestamp en temps relatif"""
    try:
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
        diff = now - dt

        if diff.days > 7:
            return dt.strftime("%d/%m/%Y")
        elif diff.days > 0:
            return f"il y a {diff.days}j"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"il y a {hours}h"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"il y a {minutes}min"
        else:
            return "maintenant"
    except:
        return "inconnu"


def create_emoji_icon(icon_name: str) -> str:
    """Retourne une icône pour un nom d'icône"""
    icons = {
        "upload": "",
        "analysis": "",
        "dashboard": "",
        "settings": "",
        "success": "",
        "error": "",
        "warning": "",
        "info": "",
        "loading": "",
        "download": "",
        "export": "",
        "chart": "",
        "table": "",
        "filter": "",
        "refresh": "",
        "delete": "",
        "edit": "",
        "save": "",
        "cancel": "",
        "confirm": "",
    }
    return icons.get(icon_name, "")


class InMemoryUploadedFile(io.BytesIO):
    """Objet mimant un UploadedFile Streamlit pour les imports distants."""

    def __init__(self, content: bytes, name: str, mime_type: str = "text/csv"):
        super().__init__(content)
        self.name = name
        self.type = mime_type
        self.mime_type = mime_type
        self.size = len(content)


def fetch_remote_dataset(
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    payload: Optional[Union[str, Dict[str, Any]]] = None,
    timeout: int = 15,
    max_size_mb: int = 500,
) -> Dict[str, Any]:
    """
    Récupère un fichier CSV distant (API/URL) et renvoie un fichier en mémoire.

    Args:
        url: Lien HTTP/HTTPS du fichier ou endpoint API.
        method: Méthode HTTP (GET/POST).
        headers: Headers personnalisés (ex: Authorization).
        payload: Corps de requête pour POST (dict ou JSON string).
        timeout: Timeout en secondes.
        max_size_mb: Taille maximale autorisée.

    Returns:
        Dict contenant le contenu, le nom détecté et un objet InMemoryUploadedFile.

    Raises:
        ValueError / RequestException si la récupération échoue.
    """

    if not url:
        raise ValueError("URL manquante.")

    parsed = urlparse(url.strip())
    if parsed.scheme not in ("http", "https"):
        raise ValueError("Seuls les protocoles HTTP/HTTPS sont supportés.")

    request_headers = headers.copy() if headers else {}
    request_headers.setdefault("User-Agent", get_user_agent())

    data = None
    if payload:
        if isinstance(payload, str):
            payload = payload.strip()
            if payload:
                try:
                    data = json.loads(payload)
                except json.JSONDecodeError:
                    data = payload
        else:
            data = payload

    try:
        response = requests.request(
            method.upper(),
            url.strip(),
            headers=request_headers,
            json=data if isinstance(data, dict) else None,
            data=None if isinstance(data, dict) else data,
            timeout=timeout,
        )
        response.raise_for_status()
    except RequestException as exc:
        raise ValueError(f"Erreur lors de l'appel distant: {exc}") from exc

    content = response.content
    size_mb = len(content) / (1024 * 1024)
    if size_mb > max_size_mb:
        raise ValueError(
            f"Fichier trop volumineux ({size_mb:.1f} MB). Limite: {max_size_mb} MB."
        )

    content_type = response.headers.get("Content-Type", "text/csv").split(";")[0]
    filename = os.path.basename(parsed.path) or "remote_dataset.csv"
    if not filename.lower().endswith(".csv"):
        filename = f"{filename}.csv"

    memory_file = InMemoryUploadedFile(content, filename, content_type)
    return {
        "content": content,
        "filename": filename,
        "mime_type": content_type,
        "size": len(content),
        "uploaded_file": memory_file,
        "source_url": url,
    }


def persist_remote_dataset(
    dataset: Dict[str, Any],
    base_dir: Union[str, Path] = "uploads/remote",
) -> Path:
    """
    Persist a remotely fetched dataset to disk for audit trail purposes.

    Args:
        dataset: Dict returned by fetch_remote_dataset.
        base_dir: Directory where files should be stored.

    Returns:
        Path to the saved CSV file.
    """

    base_path = Path(base_dir)
    base_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = clean_filename(dataset.get("filename", "remote_dataset.csv"))
    target_path = base_path / f"{timestamp}_{filename}"
    content: bytes = dataset.get("content", b"")
    target_path.write_bytes(content)

    manifest_entry = {
        "timestamp": timestamp,
        "filename": filename,
        "saved_path": str(target_path),
        "size_bytes": len(content),
        "source_url": dataset.get("source_url"),
        "mime_type": dataset.get("mime_type"),
    }

    manifest_path = base_path / "imports_manifest.jsonl"
    with manifest_path.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(manifest_entry, ensure_ascii=False) + "\n")

    return target_path
