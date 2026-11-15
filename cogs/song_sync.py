import discord
from discord import app_commands
from discord.ext import commands
from services.song_sync_service import sync_songs
from utils.embed import info_embed


@app_commands.default_permissions(manage_roles=True)
@app_commands.guild_install()
@app_commands.guild_only()
class SongSyncCog(commands.GroupCog, name="song_sync"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_app_command_error(
        self,
        interaction: discord.Interaction,
        error: discord.app_commands.AppCommandError,
    ) -> None:
        """Global error handler for app commands in this cog."""

        embed = discord.Embed(
            title="同步歌曲資料庫時發生錯誤",
            description=str(error),
            color=discord.Color.red(),
        )

        if not interaction.response.is_done():
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.edit_original_response(embed=embed)

    @app_commands.command(name="sync", description="同步歌曲資料庫，更新歌曲資訊。")
    async def song_sync(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await sync_songs()

        embed = info_embed(
            title="歌曲資料庫同步完成",
            description="已成功同步歌曲資料庫，更新了歌曲資訊。",
        )

        await interaction.followup.send(embed=embed, ephemeral=True)


async def add(bot: commands.Bot):
    cog = SongSyncCog(bot)
    await bot.add_cog(cog)
