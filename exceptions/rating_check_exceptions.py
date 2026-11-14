from discord.app_commands import AppCommandError


class BaseRatingCheckError(AppCommandError):
    """Base exception for Rating Check related errors."""


class RatingCheckError(BaseRatingCheckError):
    """Base exception for Rating Check related errors."""

    details: str = "An error occurred"
    message: str = "執行指令時發生錯誤，請檢查輸入並重試。"
    user_error: bool = True

    def __init__(
        self,
        *,
        user_error: bool | None = None,
        details: str | None = None,
        message: str | None = None,
    ):
        payload = {
            "user_error": user_error if user_error is not None else self.user_error,
            "details": details or self.details,
            "message": message or self.message,
        }
        super().__init__(payload)


class WorldEndNotSupported(RatingCheckError):
    """Exception raised when a WorldEnd song is detected."""

    details: str = "Difficuly World's End is not supported for rating calculation."
    message: str = (
        "您是大佬！但是 World's End 的歌我們沒辦法計算Rating喔！請換一首歌試試看。"
    )
