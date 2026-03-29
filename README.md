# BotDidi — Discord Music Bot

Bot Discord de musique déployé sur Discloud (après expiration Railway).

## Infos du projet

| Élément            | Valeur                                            |
| ------------------ | ------------------------------------------------- |
| Nom du bot         | BotDidi                                           |
| App ID Discord     | 1487847771733102794                               |
| GitHub             | fuldur82-ops/BotDidiplaylist                      |
| Hébergement actuel | Railway (trial ~30j) → Discloud (free, 100MB RAM) |
| Branche principale | main                                              |

## Lien d'invitation

```
https://discord.com/oauth2/authorize?client_id=1487847771733102794&permissions=3230720&scope=bot%20applications.commands
```

## Commandes

| Commande                                 | Description                  |
| ---------------------------------------- | ---------------------------- |
| `/didiplay <titre ou lien YouTube>`      | Joue un titre                |
| `/didiplaylist <lien YouTube ou Deezer>` | Joue une playlist            |
| `/didiskip`                              | Passe au titre suivant       |
| `/didipause`                             | Met en pause                 |
| `/didiresume`                            | Reprend la lecture           |
| `/didiqueue`                             | Affiche la file d'attente    |
| `/didileave`                             | Le bot quitte le salon vocal |

## Sources audio supportées

- Liens YouTube directs (`youtube.com/watch?v=...`)
- Playlists YouTube (`youtube.com/playlist?list=...`)
- Playlists Deezer (`deezer.com/playlist/...`)
- Recherche texte libre (ex: `/didiplay Drake Hotline Bling`)

> ⚠️ Les liens Spotify ne sont **pas** supportés (API payante).

## Architecture

```
main.py                  # Entrée, chargement du cog
cogs/music.py            # Commandes slash Discord
utils/youtube.py         # Recherche et résolution YouTube via yt-dlp
utils/spotify.py         # Recherche Deezer (API publique, sans clé)
utils/validators.py      # Validation URLs, limites (queue: 100, playlist: 100)
```

## Variables d'environnement

| Variable        | Description                           |
| --------------- | ------------------------------------- |
| `DISCORD_TOKEN` | Token du bot (discord.com/developers) |

## Déploiement

### Railway (actuel, trial)

- Auto-deploy sur push `main`
- nixpacks.toml : Python 3.11 + FFmpeg

### Discloud (prochain, gratuit)

- 100MB RAM free tier
- Déployer quand Railway expire
- Uploader le zip du projet ou connecter GitHub

## Notes techniques

- **Privileged Intents** activés dans le portail Discord : Presence, Server Members, Message Content
- **yt-dlp** importé en lazy loading pour économiser ~25MB RAM au démarrage
- **beautifulsoup4** supprimé (Amazon Music support retiré — fragile et inutilisé)
- FFmpeg tourne comme sous-processus séparé (hors comptage RAM Python)
