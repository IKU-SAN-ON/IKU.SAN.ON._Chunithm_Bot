import aiohttp
import discord
from discord import app_commands
from discord.ext import commands
from exceptions.rating_check_exceptions import RatingCheckError, WorldEndNotSupported
from services.extractor_service import extract_rating_from_image, search_constant
from utils.calculate_rating import calculate_rating
from utils.embed import error_embed, info_embed


@app_commands.guild_install()
@app_commands.guild_only()
class RatingCheckCog(commands.GroupCog, name="rating"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_app_command_error(
        self,
        interaction: discord.Interaction,
        error: discord.app_commands.AppCommandError,
    ) -> None:
        """Global error handler for app commands in this cog."""

        if isinstance(error, RatingCheckError):
            embed = error_embed(
                description=error.args[0].get(
                    "message", "執行指令時發生錯誤，請檢查輸入並重試。"
                ),
            )

            if not interaction.response.is_done():
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.edit_original_response(embed=embed)

            return

        raise error  # Propagate to global handler if unhandled.

    @app_commands.command(
        name="img_check", description="從 CHUNITHM 結算圖片中計算 Rating 結果。"
    )
    @app_commands.describe(image="CHUNITHM 結算圖片")
    async def rating_check(
        self, interaction: discord.Interaction, image: discord.Attachment
    ):
        # defer deployment
        await interaction.response.defer()

        # prepare payload for extractor API
        data = aiohttp.FormData()
        data.add_field(
            "image",
            await image.read(),
            filename=image.filename,
            content_type=image.content_type,
        )
        result = await extract_rating_from_image(data)

        extracted_name: str | None = result.get("song_name")
        extracted_difficulty: str | None = result.get("difficulty")
        extracted_score: int | None = result.get("score")

        if extracted_difficulty == "WORLDEND":
            raise WorldEndNotSupported()
        if not extracted_name or not extracted_difficulty or not extracted_score:
            raise RatingCheckError(
                message="無法從圖片中提取資料。",
                details="Extractor API returned incomplete data.",
            )

        # search for constant using the extracted data
        constant_result = await search_constant(extracted_name, extracted_difficulty)
        if (
            constant_result.get("success") is False
            or constant_result.get("success") is None
        ):
            raise RatingCheckError(
                message="無法搜尋定數。",
                details=f"Web API returned error: {constant_result.get('error')}",
            )

        matches = constant_result.get("data") or []
        if not matches:
            raise RatingCheckError(
                message="找不到符合的歌曲，請確認圖片中的歌曲名稱是否正確。",
                details="getsongconst returned no matches.",
            )

        most_confident = matches[0]
        rating = calculate_rating(extracted_score, most_confident["constant"])
        isUnknown = most_confident["unknown"]

        embed = info_embed(title="Rating 計算結果")

        embed.add_field(name="偵測到的歌曲", value=f"{extracted_name}")
        embed.add_field(name="偵測到的難度", value=f"{extracted_difficulty}")
        embed.add_field(name="偵測到的分數", value=f"{extracted_score:,}")
        embed.add_field(
            name="預計定數", value=f"{most_confident['constant']:.2f}", inline=False
        )
        embed.add_field(name="計算出的 Rating", value=f"{rating:.2f}", inline=False)
        embed.set_footer(
            text="數據庫中貌似沒有找到定數呢～上面的是保底R值" if isUnknown else ""
        )

        await interaction.followup.send(embed=embed)


async def add(bot: commands.Bot):
    cog = RatingCheckCog(bot)
    await bot.add_cog(cog)
