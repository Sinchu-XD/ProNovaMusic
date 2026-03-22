from traceback import format_exc
from pytgcalls.types import MediaStream, AudioQuality, VideoQuality


async def play(core, chat_id, stream, video=False, plugin=None, song=None):
    if not stream:
        raise Exception("Stream empty")

    try:
        if video:
            media = MediaStream(
                media_path=stream,
                audio_parameters=AudioQuality.STUDIO,
                video_parameters=VideoQuality.HD_720p
            )
        else:
            media = MediaStream(
                media_path=stream,
                audio_parameters=AudioQuality.STUDIO,
                video_flags=MediaStream.Flags.IGNORE
            )

        await core.play(chat_id, media)


        if plugin and song:
            await plugin.on_song_start(chat_id, song)

    except Exception:
        raise Exception(f"Play failed:\n{format_exc()}")
