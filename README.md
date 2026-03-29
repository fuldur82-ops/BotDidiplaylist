# BotDidi - Discord Music Bot

Bot Discord de musique prepare pour un deploiement sur Discloud.

## Infos du projet

| Element | Valeur |
| --- | --- |
| Nom du bot | BotDidi |
| App ID Discord | 1487847771733102794 |
| GitHub | fuldur82-ops/BotDidiplaylist |
| Hebergement cible | Discloud |
| Branche principale | main |

## Lien d'invitation

```text
https://discord.com/oauth2/authorize?client_id=1487847771733102794&permissions=3230720&scope=bot%20applications.commands
```

## Commandes

| Commande | Description |
| --- | --- |
| `/didiplay <titre ou lien YouTube>` | Joue un titre |
| `/didiplaylist <lien YouTube ou Deezer>` | Joue une playlist |
| `/didiskip` | Passe au titre suivant |
| `/didipause` | Met en pause |
| `/didiresume` | Reprend la lecture |
| `/didiqueue` | Affiche la file d'attente |
| `/didileave` | Le bot quitte le salon vocal |
| `/didiout` | Reset d'urgence du vocal |

## Sources audio supportees

- Liens YouTube directs
- Playlists YouTube
- Playlists Deezer
- Recherche texte libre

Les liens Spotify ne sont pas supportes proprement dans l'etat actuel du projet.

## Architecture

```text
main.py                  # Entree, chargement du cog
cogs/music.py            # Commandes slash Discord
utils/youtube.py         # Recherche et resolution YouTube via yt-dlp
utils/spotify.py         # Recherche Deezer API publique
utils/validators.py      # Validation URLs et limites
discloud.config          # Configuration deploiement Discloud
.discloudignore          # Exclusions du zip d'upload
```

## Variables d'environnement

| Variable | Description |
| --- | --- |
| `DISCORD_TOKEN` | Token du bot |

## Deploiement Discloud

Le repo contient maintenant un [README.md](D:\DiscordMusicBot\README.md), un [discloud.config](D:\DiscordMusicBot\discloud.config) et un [.discloudignore](D:\DiscordMusicBot\.discloudignore) adaptes a Discloud.

Configuration utilisee :

- `NAME=BotDidi`
- `TYPE=bot`
- `MAIN=main.py`
- `RAM=100`
- `VERSION=current`
- `APT=ffmpeg, tools`
- `BUILD=pip install -r requirements.txt`
- `START=python main.py`

### Upload

1. Cree un fichier `.env` local avec `DISCORD_TOKEN=...`
2. Prepare un zip du projet en gardant `discloud.config` a la racine
3. N'inclus pas `.git`, `__pycache__`, `.venv`, `nixpacks.toml`, `Procfile`, `runtime.txt` ni `nul`
4. Uploade le zip sur Discloud

## Notes techniques

- FFmpeg est requis pour la lecture audio
- `imageio-ffmpeg` reste en fallback si besoin
- Les diagnostics Railway ont ete gardes pour debug tant que la migration n'est pas terminee
