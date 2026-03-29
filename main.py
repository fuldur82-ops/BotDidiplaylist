import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import asyncio
import sys
from utils.youtube import get_ffmpeg_executable

load_dotenv()

REQUIRED_ENV_VARS = {
    "DISCORD_TOKEN": "Token du bot Discord (discord.com/developers)",
}

def check_credentials():
    missing = []
    for var, description in REQUIRED_ENV_VARS.items():
        value = os.getenv(var)
        if not value or value.startswith("ton_"):
            missing.append(f"  - {var} : {description}")
    if missing:
        print("❌ Credentials manquants dans le fichier .env :\n")
        print("\n".join(missing))
        print("\n➡️  Copie .env.example en .env et remplis les valeurs.")
        sys.exit(1)

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"✅ {bot.user} est en ligne !")
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.listening,
            name="/didiplay pour de la musique 🎵"
        )
    )
    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)} commandes slash synchronisées")
    except Exception as e:
        print(f"❌ Erreur sync commandes: {e}")
    try:
        import yt_dlp  # pré-chargement pour éviter le délai au premier /didiplay
        print("✅ yt-dlp pré-chargé")
    except Exception as e:
        print(f"⚠️ yt-dlp pré-chargement échoué: {e}")


    try:
        print(f"✅ ffmpeg: {get_ffmpeg_executable()}")
    except Exception as e:
        print(f"⚠️ ffmpeg introuvable: {e}")

@bot.event
async def on_voice_state_update(member, before, after):
    if member.id != bot.user.id:
        return
    print(
        "[voice_state] "
        f"guild={getattr(member.guild, 'id', None)} "
        f"before_channel={getattr(before.channel, 'id', None)} "
        f"after_channel={getattr(after.channel, 'id', None)} "
        f"self_mute={after.self_mute} self_deaf={after.self_deaf} "
        f"mute={after.mute} deaf={after.deaf}"
    )

async def main():
    async with bot:
        await bot.load_extension("cogs.music")
        await bot.start(os.getenv("DISCORD_TOKEN"))


if __name__ == "__main__":
    check_credentials()
    asyncio.run(main())
