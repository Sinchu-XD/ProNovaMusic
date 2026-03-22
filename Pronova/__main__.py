import asyncio

from Bot.Core import bot, user
from Pronova.Player.Core import EngineCore

from Pronova.UI.Plugin import Plugin

from Pronova.Plugins.Plays.play import play as play_module
#from Play import vplay as vplay_module


async def main():
    await bot.start()

    if user:
        await user.start()
        app = user
    else:
        app = bot

    core = EngineCore(app)

    plugin = Plugin(bot)

    core.plugin = plugin
    core.on_vc_closed = plugin.on_vc_closed

    await core.start()

    play_module.register(bot, core)
  #  vplay_module.register(bot, core)

    print("🚀 Music Bot Started Successfully")

    await asyncio.Event().wait()


if __name__ == "__main__":
    loop = bot.loop
    loop.run_until_complete(main())
