import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import traceback
from collections import deque

from utils.youtube import search_youtube, get_playlist, resolve_url, format_duration, FFMPEG_OPTIONS, get_ffmpeg_executable
from utils.spotify import search_track, get_playlist_tracks, get_deezer_playlist_tracks
from utils.validators import (
    is_valid_youtube_url, is_valid_spotify_url, is_valid_deezer_url, is_valid_amazon_url,
    sanitize_search_query, MAX_QUEUE_SIZE, MAX_PLAYLIST_SIZE
)


class MusicQueue:
    def __init__(self):
        self.queue: deque[dict] = deque()
        self.current: dict | None = None
        self.is_playing = False

    def add(self, track: dict) -> bool:
        if len(self.queue) >= MAX_QUEUE_SIZE:
            return False
        self.queue.append(track)
        return True

    def next(self) -> dict | None:
        if self.queue:
            self.current = self.queue.popleft()
            return self.current
        self.current = None
        return None

    def clear(self):
        self.queue.clear()
        self.current = None
        self.is_playing = False

    def __len__(self):
        return len(self.queue)


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.queues: dict[int, MusicQueue] = {}

    def get_queue(self, guild_id: int) -> MusicQueue:
        if guild_id not in self.queues:
            self.queues[guild_id] = MusicQueue()
        return self.queues[guild_id]

    async def ensure_voice(self, interaction: discord.Interaction) -> discord.VoiceClient | None:
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.followup.send("Tu dois être dans un salon vocal d'abord !")
            return None

        channel = interaction.user.voice.channel
        guild = interaction.guild

        # Nettoie tout voice client existant (stale ou dans un autre channel)
        if guild.voice_client:
            vc = guild.voice_client
            if vc.is_connected() and vc.channel == channel:
                print(f"[ensure_voice] reuse guild={guild.id} channel={channel.id}")
                return vc
            print(f"[ensure_voice] cleanup stale guild={guild.id}")
            try:
                await vc.disconnect(force=True)
            except Exception:
                pass
            await asyncio.sleep(0.5)

        # Force Discord à réinitialiser l'état vocal (fix 4006 stale session)
        print(f"[ensure_voice] clear voice state guild={guild.id}")
        try:
            await guild.change_voice_state(channel=None)
            await asyncio.sleep(1.5)
        except Exception as e:
            print(f"[ensure_voice] clear failed (non-fatal) guild={guild.id} error={e!r}")

        print(f"[ensure_voice] connect guild={guild.id} channel={channel.id}")
        try:
            vc = await channel.connect(timeout=15, reconnect=False)
        except asyncio.TimeoutError:
            print(f"[ensure_voice] timeout guild={guild.id}")
            await interaction.followup.send("Connexion au vocal échouée (timeout). Réessaie.")
            return None
        except Exception as e:
            print(f"[ensure_voice] error guild={guild.id} error={e!r}")
            await interaction.followup.send(f"Impossible de rejoindre le salon vocal : {e}")
            return None

        print(f"[ensure_voice] connected={vc.is_connected()} guild={guild.id}")
        await interaction.channel.send(f"Yo, je suis là 🎧 **{channel.name}**")
        return vc

    def play_next(self, guild: discord.Guild, text_channel: discord.TextChannel):
        queue = self.get_queue(guild.id)
        track = queue.next()

        if not track or not guild.voice_client:
            print(f"[play_next] stop guild={guild.id} has_track={bool(track)} has_vc={bool(guild.voice_client)} queue_len={len(queue)}")
            queue.is_playing = False
            if guild.voice_client:
                asyncio.run_coroutine_threadsafe(
                    self._leave_empty(guild, text_channel), self.bot.loop
                )
            return

        async def _play():
            vc = guild.voice_client
            if not vc:
                print(f"[play_next] no voice client guild={guild.id}")
                return
            if not vc.is_connected():
                print(f"[play_next] voice not ready guild={guild.id}")
                queue.is_playing = False
                await text_channel.send("Connexion vocale perdue, tentative annulée.")
                return

            try:
                if track.get("is_url") and is_valid_youtube_url(track.get("url", "")):
                    print(f"[play_next] resolve url guild={guild.id} title={track.get('title', '?')}")
                    info = await resolve_url(track["url"])
                else:
                    query = track.get("query") or track.get("title", "")
                    print(f"[play_next] search guild={guild.id} query={query!r}")
                    info = await search_youtube(query)
            except Exception as e:
                print(f"[play_next] source resolution failed guild={guild.id} title={track.get('title', '?')} error={e!r}")
                traceback.print_exc()
                await text_channel.send(
                    f"Erreur lors du chargement de **{track.get('title', '?')}**, je passe au suivant."
                )
                self.play_next(guild, text_channel)
                return

            if not info:
                print(f"[play_next] no info guild={guild.id} title={track.get('title', '?')}")
                await text_channel.send(
                    f"Impossible de trouver **{track.get('title', '?')}**, je passe au suivant."
                )
                self.play_next(guild, text_channel)
                return

            print(f"[play_next] resolved guild={guild.id} title={info.get('title', '?')} stream={info.get('url', '')[:120]}")
            try:
                source = discord.FFmpegPCMAudio(
                    info["url"],
                    executable=get_ffmpeg_executable(),
                    **FFMPEG_OPTIONS,
                )
            except Exception as e:
                print(f"[play_next] ffmpeg source failed guild={guild.id} title={info.get('title', '?')} error={e!r}")
                traceback.print_exc()
                await text_channel.send(
                    f"Erreur FFmpeg sur **{track.get('title', '?')}**, je passe au suivant."
                )
                self.play_next(guild, text_channel)
                return
            queue.is_playing = True

            embed = discord.Embed(
                title="🎵 En train de jouer",
                description=f"**{info['title']}**",
                color=discord.Color.green()
            )
            if info.get("thumbnail"):
                embed.set_thumbnail(url=info["thumbnail"])
            if info.get("duration"):
                embed.add_field(name="Durée", value=format_duration(info["duration"]))
            if len(queue):
                embed.set_footer(text=f"{len(queue)} titre(s) dans la file")

            await text_channel.send(embed=embed)
            try:
                vc.play(source, after=lambda e: self._after_playback(guild, text_channel, e))
            except Exception as e:
                queue.is_playing = False
                print(f"[play_next] vc.play failed guild={guild.id} title={info.get('title', '?')} error={e!r}")
                traceback.print_exc()
                await text_channel.send(
                    f"Erreur de lecture vocale sur **{track.get('title', '?')}**, je passe au suivant."
                )
                self.play_next(guild, text_channel)
                return

        asyncio.run_coroutine_threadsafe(_play(), self.bot.loop)

    def _after_playback(self, guild: discord.Guild, text_channel: discord.TextChannel, error: Exception | None):
        queue = self.get_queue(guild.id)
        queue.is_playing = False
        print(f"[after_playback] guild={guild.id} error={error!r} queue_len={len(queue)}")

        if error:
            print(f"Erreur lecture Discord voice pour {guild.name}: {error}")

        self.play_next(guild, text_channel)

    async def _leave_empty(self, guild: discord.Guild, text_channel: discord.TextChannel):
        await asyncio.sleep(2)
        queue = self.get_queue(guild.id)
        if (
            guild.voice_client
            and not guild.voice_client.is_playing()
            and not guild.voice_client.is_paused()
            and queue.current is None
            and len(queue) == 0
        ):
            await text_channel.send("File vide, je me casse ! À plus 👋")
            queue.clear()
            await guild.voice_client.disconnect()

    # ── /play ──────────────────────────────────────────────────────────────────

    @app_commands.command(name="didiplay", description="Joue un titre (nom, artiste, ou lien YouTube)")
    @app_commands.describe(recherche="Nom du titre, artiste, ou lien YouTube")
    @app_commands.checks.cooldown(3, 10, key=lambda i: i.guild_id)
    async def play(self, interaction: discord.Interaction, recherche: str):
        await interaction.response.defer()

        recherche = sanitize_search_query(recherche)

        vc = await self.ensure_voice(interaction)
        if not vc:
            return

        queue = self.get_queue(interaction.guild.id)

        if len(queue) >= MAX_QUEUE_SIZE:
            await interaction.followup.send(
                f"La file est pleine ({MAX_QUEUE_SIZE} titres max). Utilise `/didiskip` pour avancer."
            )
            return

        # Lien YouTube direct — on valide le domaine
        if is_valid_youtube_url(recherche):
            track = {"title": recherche, "url": recherche, "is_url": True}

        # Recherche texte — via Deezer pour les métadonnées, puis YouTube pour l'audio
        else:
            spotify_result = await search_track(recherche)
            if spotify_result:
                track = {
                    "title": f"{spotify_result['artist']} - {spotify_result['title']}",
                    "query": spotify_result["query"],
                    "is_url": False,
                }
            else:
                track = {"title": recherche, "query": recherche, "is_url": False}

        queue.add(track)

        if not vc.is_playing():
            self.play_next(interaction.guild, interaction.channel)
            await interaction.followup.send(f"C'est parti pour **{track['title']}** !")
        else:
            await interaction.followup.send(
                f"**{track['title']}** ajouté à la file (position {len(queue)}) 🎶"
            )

    @play.error
    async def play_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(
                f"Doucement ! Réessaie dans {error.retry_after:.1f}s.", ephemeral=True
            )

    # ── /playlist ──────────────────────────────────────────────────────────────

    @app_commands.command(name="didiplaylist", description="Joue une playlist YouTube, Deezer, Spotify ou Amazon Music")
    @app_commands.describe(url="Lien ou nom de la playlist")
    @app_commands.checks.cooldown(1, 30, key=lambda i: i.guild_id)
    async def playlist(self, interaction: discord.Interaction, url: str):
        await interaction.response.defer()

        url = sanitize_search_query(url)

        vc = await self.ensure_voice(interaction)
        if not vc:
            return

        queue = self.get_queue(interaction.guild.id)
        tracks = []

        # YouTube playlist — domaine validé
        if is_valid_youtube_url(url) and ("playlist" in url or "watch" in url):
            await interaction.followup.send("Chargement de la playlist YouTube... ⏳")
            tracks = await get_playlist(url)

        # Deezer playlist
        elif is_valid_deezer_url(url) and "playlist" in url:
            await interaction.followup.send("Chargement de la playlist Deezer... ⏳")
            deezer_tracks = await get_deezer_playlist_tracks(url)
            tracks = [
                {"title": t["title"], "query": t["query"], "is_url": False}
                for t in deezer_tracks
            ]

        # Spotify playlist
        elif is_valid_spotify_url(url) and "playlist" in url:
            await interaction.followup.send("Chargement de la playlist Spotify... ⏳")
            spotify_tracks = await get_playlist_tracks(url)
            tracks = [
                {"title": t["title"], "query": t["query"], "is_url": False}
                for t in spotify_tracks
            ]

        # Amazon Music playlist
        elif is_valid_amazon_url(url):
            await interaction.followup.send("Chargement de la playlist Amazon Music... ⏳")
            from utils.amazon import get_amazon_playlist_tracks
            amazon_tracks = await get_amazon_playlist_tracks(url)
            tracks = [
                {"title": t["title"], "query": t["query"], "is_url": False}
                for t in amazon_tracks
            ]

        # Recherche par nom (pas d'URL)
        elif not url.startswith("http"):
            await interaction.followup.send(f"Recherche de la playlist **{url}**... ⏳")
            result = await search_youtube(f"playlist {url}")
            if result:
                tracks = [{"title": result["title"], "url": result["webpage_url"], "is_url": True}]
            else:
                await interaction.channel.send("Aucune playlist trouvée.")
                return

        else:
            await interaction.followup.send(
                "Lien non reconnu. Utilise un lien YouTube, Deezer, Spotify ou Amazon Music."
            )
            return

        if not tracks:
            await interaction.channel.send("La playlist est vide ou inaccessible.")
            return

        # Limite la taille de la playlist
        tracks = tracks[:MAX_PLAYLIST_SIZE]
        added = 0
        for t in tracks:
            if queue.add(t):
                added += 1
            else:
                break

        await interaction.channel.send(
            f"**{added} titres** ajoutés à la file 🎶 Let's go !"
            + (f" *(file limitée à {MAX_QUEUE_SIZE})*" if added < len(tracks) else "")
        )

        if not vc.is_playing():
            self.play_next(interaction.guild, interaction.channel)

    @playlist.error
    async def playlist_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(
                f"Attends {error.retry_after:.0f}s avant de charger une nouvelle playlist.", ephemeral=True
            )

    # ── /skip ──────────────────────────────────────────────────────────────────

    @app_commands.command(name="didiskip", description="Passe au titre suivant")
    async def skip(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if not vc or not vc.is_playing():
            await interaction.response.send_message("Rien en cours de lecture.")
            return
        vc.stop()
        await interaction.response.send_message("Skippé ⏭️")

    # ── /pause ─────────────────────────────────────────────────────────────────

    @app_commands.command(name="didipause", description="Met la musique en pause")
    async def pause(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc and vc.is_playing():
            vc.pause()
            await interaction.response.send_message("En pause ⏸️")
        else:
            await interaction.response.send_message("Rien à mettre en pause.")

    # ── /resume ────────────────────────────────────────────────────────────────

    @app_commands.command(name="didiresume", description="Reprend la lecture")
    async def resume(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc and vc.is_paused():
            vc.resume()
            await interaction.response.send_message("C'est reparti ▶️")
        else:
            await interaction.response.send_message("La musique n'est pas en pause.")

    # ── /queue ─────────────────────────────────────────────────────────────────

    @app_commands.command(name="didiqueue", description="Affiche la file d'attente")
    async def queue_cmd(self, interaction: discord.Interaction):
        queue = self.get_queue(interaction.guild.id)

        if not queue.current and not len(queue):
            await interaction.response.send_message("La file est vide.")
            return

        embed = discord.Embed(title="🎵 File d'attente", color=discord.Color.blurple())

        if queue.current:
            embed.add_field(
                name="En cours",
                value=f"▶️ {queue.current.get('title', 'Titre inconnu')}",
                inline=False
            )

        if len(queue):
            lines = []
            for i, track in enumerate(list(queue.queue)[:10], 1):
                lines.append(f"`{i}.` {track.get('title', 'Titre inconnu')}")
            if len(queue) > 10:
                lines.append(f"*... et {len(queue) - 10} autres titres*")
            embed.add_field(name="Suivants", value="\n".join(lines), inline=False)

        await interaction.response.send_message(embed=embed)

    # ── /leave ─────────────────────────────────────────────────────────────────

    @app_commands.command(name="didileave", description="Le bot quitte le salon vocal")
    async def leave(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc:
            self.get_queue(interaction.guild.id).clear()
            await vc.disconnect()
            await interaction.response.send_message("Ciao, à plus ! 👋")
        else:
            await interaction.response.send_message("Je suis pas dans un salon vocal.")

    @app_commands.command(name="didiout", description="Force l'arrêt du bot audio et réinitialise la file")
    async def emergency_reset(self, interaction: discord.Interaction):
        queue = self.get_queue(interaction.guild.id)
        vc = interaction.guild.voice_client

        queue.clear()

        if vc:
            try:
                if vc.is_playing() or vc.is_paused():
                    vc.stop()
            except Exception:
                pass

            try:
                await vc.disconnect(force=True)
            except TypeError:
                await vc.disconnect()
            except Exception as e:
                print(f"[didiout] disconnect failed guild={interaction.guild.id} error={e!r}")

        self.queues.pop(interaction.guild.id, None)
        await interaction.response.send_message("Reset forcé effectué. File vidée et vocal coupé.")


async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))
