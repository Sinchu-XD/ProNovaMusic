from pytgcalls import PyTgCalls

from Pronova.Player.Handling import setup_handlers


class EngineCore:
    def __init__(self, app):
        self.app = app
        self.core = PyTgCalls(app)

        self.plugin = None
        self.on_end = None
        self.on_vc_closed = None

    async def start(self):
        await self.core.start()

        setup_handlers(
            self.core,
            plugin=self.plugin,
            on_end=self.on_end,
            on_vc_closed=self.on_vc_closed
        )

    async def stop(self):
        await self.core.stop()
