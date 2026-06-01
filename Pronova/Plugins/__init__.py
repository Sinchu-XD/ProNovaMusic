from traceback import format_exc
import logging

_LOGGER = logging.getLogger("Pronova.Plugins")


def _safe_import(module_name):
    try:
        __import__(module_name)
    except Exception:
        _LOGGER.error(f"[PLUGIN LOAD FAILED] {module_name}\n{format_exc()}")


_safe_import("Pronova.Plugins.Plays.play")
_safe_import("Pronova.Plugins.Plays.PlayMode")
_safe_import("Pronova.Plugins.Admins.Auth")
_safe_import("Pronova.Plugins.Admins.CallBacks")
_safe_import("Pronova.Plugins.Admins.Cont")
_safe_import("Pronova.Plugins.Sudo.Bans")
_safe_import("Pronova.Plugins.Sudo.Broadcast")
_safe_import("Pronova.Plugins.Sudo.Stats")
_safe_import("Pronova.Plugins.Sudo.Sudo")
_safe_import("Pronova.Plugins.Extra.Start")
_safe_import("Pronova.Plugins.Extra.Bots")
_safe_import("Pronova.Plugins.Extra.GcInfo")
_safe_import("Pronova.Plugins.Extra.Cricket")
