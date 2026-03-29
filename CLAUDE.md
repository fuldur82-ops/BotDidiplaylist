# Discord Music Bot — Contexte Projet

## Description
Bot Discord musical qui joue de la musique dans les salons vocaux.
Pas de login requis — recherche dans le catalogue public Spotify + streaming via YouTube/yt-dlp.

## Stack Technique
- **Langage** : Python
- **Bot Discord** : `discord.py` (slash commands)
- **Audio** : `yt-dlp` + `FFmpeg`
- **Métadonnées musique** : Spotify API (Client Credentials, sans login utilisateur)
- **Playlists** : YouTube (natif yt-dlp) + Amazon Music (scraping fragile)

## Fonctionnalités Prévues

### Commandes slash
| Commande | Description |
|----------|-------------|
| `/play <titre/artiste>` | Recherche et joue un titre |
| `/playlist <lien/nom>` | Joue une playlist YouTube ou Amazon |
| `/skip` | Passe au titre suivant |
| `/pause` | Met en pause |
| `/resume` | Reprend la lecture |
| `/queue` | Affiche la file d'attente |
| `/leave` | Le bot quitte le salon vocal |

### Comportement
- Le bot rejoint automatiquement le salon vocal de l'utilisateur qui appelle une commande
- Il envoie des messages dans le chat (arrivée, titre en cours, départ)
- File d'attente automatique
- Quitte seul si la file est vide

## Architecture des Fichiers
```
DiscordMusicBot/
├── CLAUDE.md           # Ce fichier
├── main.py             # Point d'entrée, init bot
├── cogs/
│   ├── music.py        # Commandes musicales
│   └── events.py       # Événements (join/leave)
├── utils/
│   ├── spotify.py      # Recherche Spotify API
│   ├── youtube.py      # Wrapper yt-dlp
│   └── amazon.py       # Scraping Amazon Music
├── .env                # Tokens (jamais commité)
└── requirements.txt    # Dépendances
```

## Variables d'environnement (.env)
```
DISCORD_TOKEN=...
SPOTIFY_CLIENT_ID=...
SPOTIFY_CLIENT_SECRET=...
```

## Sources Audio
| Source | Méthode | Fiabilité |
|--------|---------|-----------|
| YouTube (lien/nom) | yt-dlp natif | ✅ Parfait |
| Spotify (métadonnées) | API Client Credentials → YouTube | ✅ Bon |
| Amazon Music (playlist) | Scraping → YouTube | ⚠️ Fragile |

## Dépendances Python
```
discord.py
yt-dlp
spotipy
python-dotenv
ffmpeg-python
aiohttp
beautifulsoup4  # Pour scraping Amazon
```

## Notes Importantes
- Amazon Music utilise du DRM → impossible de streamer directement, on passe par YouTube
- Spotify sans login = accès catalogue public uniquement (pas de playlists privées)
- FFmpeg doit être installé sur la machine (pas via pip)
- yt-dlp remplace youtube-dl (plus maintenu)

## Commandes de Setup
```bash
pip install -r requirements.txt
# Installer FFmpeg séparément : https://ffmpeg.org/download.html
python main.py
```
