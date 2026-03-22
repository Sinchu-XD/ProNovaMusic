from pytgcalls import filters
from pytgcalls.types import StreamEnded, ChatUpdate


def setup_handlers(core, on_end=None, on_vc_closed=None):

    @core.on_update(filters.stream_end())
    async def stream_end(_, update: StreamEnded):
        if on_end:
            await on_end(update.chat_id)

    @core.on_update(
        filters.chat_update(ChatUpdate.Status.CLOSED_VOICE_CHAT)
    )
    async def vc_closed(_, update: ChatUpdate):
        if on_vc_closed:
            await on_vc_closed(update.chat_id)
