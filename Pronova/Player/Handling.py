from traceback import format_exc

from pytgcalls.types import StreamEnded, ChatUpdate


def setup_handlers(core, plugin=None, on_end=None, on_vc_closed=None):

    @core.on_update()
    async def handler(_, update):
        try:

            if isinstance(update, StreamEnded):
                chat_id = update.chat_id

                print("STREAM ENDED:", chat_id)

                current = None

                try:
                    from Pronova.Utils.Queue import queue
                    current = await queue.get_current(chat_id)
                except Exception as e:
                    print("QUEUE ERROR:", e)

                if plugin and current:
                    try:
                        await plugin.on_song_end(chat_id, current)
                    except Exception as e:
                        print("PLUGIN ERROR:", e)

                if on_end:
                    try:
                        await on_end(chat_id)
                    except Exception as e:
                        print("PLAY NEXT ERROR:", e)

            elif isinstance(update, ChatUpdate):
                if update.status == ChatUpdate.Status.CLOSED_VOICE_CHAT:
                    chat_id = update.chat_id

                    print("VC CLOSED:", chat_id)

                    if plugin:
                        try:
                            await plugin.on_vc_closed(chat_id)
                        except Exception as e:
                            print("PLUGIN VC ERROR:", e)

                    if on_vc_closed:
                        try:
                            await on_vc_closed(chat_id)
                        except Exception as e:
                            print("VC CLOSED ERROR:", e)

        except Exception:
            print(f"[handler error]\n{format_exc()}")
