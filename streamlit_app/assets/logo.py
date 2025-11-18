"""
Logo FreeMobilaChat - Génération SVG moderne
"""


def get_logo_svg(size="150", color="#CC0000"):
    """Génère le logo SVG FreeMobilaChat"""
    return f"""
    <svg width="{size}" height="{size}" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
        <defs>
            <linearGradient id="logoGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:{color};stop-opacity:1" />
                <stop offset="100%" style="stop-color:#8B0000;stop-opacity:1" />
            </linearGradient>
            <filter id="shadow">
                <feDropShadow dx="0" dy="4" stdDeviation="4" flood-opacity="0.3"/>
            </filter>
        </defs>
        
        <!-- Cercle extérieur -->
        <circle cx="100" cy="100" r="95" fill="url(#logoGradient)" filter="url(#shadow)"/>
        
        <!-- Chat bubble -->
        <path d="M 60 70 Q 60 50 80 50 L 120 50 Q 140 50 140 70 L 140 100 Q 140 120 120 120 L 90 120 L 70 140 L 70 120 Q 60 120 60 100 Z" 
              fill="white" opacity="0.95"/>
        
        <!-- Icône IA (circuit) -->
        <circle cx="85" cy="75" r="3" fill="{color}"/>
        <circle cx="115" cy="75" r="3" fill="{color}"/>
        <circle cx="100" cy="95" r="3" fill="{color}"/>
        <line x1="85" y1="75" x2="100" y2="95" stroke="{color}" stroke-width="2"/>
        <line x1="115" y1="75" x2="100" y2="95" stroke="{color}" stroke-width="2"/>
        
        <!-- Points de circuit -->
        <circle cx="70" cy="75" r="2" fill="{color}" opacity="0.6"/>
        <circle cx="130" cy="75" r="2" fill="{color}" opacity="0.6"/>
        <line x1="70" y1="75" x2="82" y2="75" stroke="{color}" stroke-width="1.5" opacity="0.6"/>
        <line x1="118" y1="75" x2="130" y2="75" stroke="{color}" stroke-width="1.5" opacity="0.6"/>
        
        <!-- Sparkles (étoiles IA) -->
        <path d="M 150 60 L 152 65 L 157 67 L 152 69 L 150 74 L 148 69 L 143 67 L 148 65 Z" fill="white" opacity="0.8"/>
        <path d="M 50 130 L 52 133 L 55 135 L 52 137 L 50 140 L 48 137 L 45 135 L 48 133 Z" fill="white" opacity="0.8"/>
        
        <!-- Texte "AI" -->
        <text x="100" y="115" font-family="Arial, sans-serif" font-size="14" font-weight="bold" 
              text-anchor="middle" fill="{color}">AI</text>
    </svg>
    """


def get_logo_html(size="80", show_text=True):
    """Génère le HTML complet du logo avec texte"""
    return f"""
    <div style="display: flex; align-items: center; gap: 1rem;">
        {get_logo_svg(size)}
        {f'''
        <div style="display: flex; flex-direction: column;">
            <span style="font-size: 2rem; font-weight: 900; color: #CC0000; letter-spacing: -1px; line-height: 1;">
                FreeMobila
            </span>
            <span style="font-size: 1.5rem; font-weight: 700; color: #8B0000; letter-spacing: 1px; line-height: 1;">
                CHAT
            </span>
        </div>
        ''' if show_text else ''}
    </div>
    """


def get_favicon_svg():
    """Génère une version favicon du logo"""
    return """
    <svg width="32" height="32" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
        <circle cx="100" cy="100" r="95" fill="#CC0000"/>
        <path d="M 60 70 Q 60 50 80 50 L 120 50 Q 140 50 140 70 L 140 100 Q 140 120 120 120 L 90 120 L 70 140 L 70 120 Q 60 120 60 100 Z" 
              fill="white" opacity="0.95"/>
        <circle cx="85" cy="75" r="3" fill="#CC0000"/>
        <circle cx="115" cy="75" r="3" fill="#CC0000"/>
        <circle cx="100" cy="95" r="3" fill="#CC0000"/>
    </svg>
    """
