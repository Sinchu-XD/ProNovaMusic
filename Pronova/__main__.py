import asyncio
import sys

from traceback import format_exc

from Pronova.Utils.Logger import LOGGER
from Pronova.Utils.Check import (
    run_startup_checks,
    run_async_checks,
)


async def main():
    from Pronova.Database.Core import setup_database
    from Pronova.Bot.Core import bot, user, engine
    from Pronova.Player import idle
    from Pronova.UI.Plugins import Plugin

    import Pronova.Plugins

    try:
        LOGGER.info("Running startup diagnostics...")

        run_startup_checks()

    except Exception:
        LOGGER.critical(
            f"Startup diagnostics failed:\n{format_exc()}"
        )

        sys.exit(1)

    try:
        LOGGER.info("Setting up database...")

        await setup_database()

        await run_async_checks()

    except Exception:
        LOGGER.error(
            f"Database setup failed:\n{format_exc()}"
        )

        sys.exit(1)

    try:
        LOGGER.info("Starting bot client...")

        await bot.start()

        LOGGER.info("Bot client started.")

    except Exception:
        LOGGER.critical(
            f"Failed to start bot:\n{format_exc()}"
        )

        sys.exit(1)

    try:
        LOGGER.info("Starting user client...")

        await user.start()

        LOGGER.info("User client started.")

    except Exception:
        LOGGER.error(
            f"Failed to start user client:\n{format_exc()}"
        )

        sys.exit(1)

    try:
        LOGGER.info("Starting voice engine...")

        await engine.start()

        engine.vc.load_plugin(Plugin(bot))

        LOGGER.info("Voice engine started.")

    except Exception:
        LOGGER.critical(
            f"Failed to start voice engine:\n{format_exc()}"
        )

        sys.exit(1)

    LOGGER.info("ProNova Music Bot is running!")

    await idle()


if __name__ == "__main__":
    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        LOGGER.info("Bot stopped by user.")

    except Exception:
        LOGGER.critical(
            f"Fatal crash:\n{format_exc()}"
        )

        sys.exit(1)
