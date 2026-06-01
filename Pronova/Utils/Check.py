import os
import sys
import time
import socket
import shutil
import subprocess
from pathlib import Path
from traceback import format_exc

from Pronova.Utils.Logger import LOGGER
from Config import API_ID, API_HASH, BOT_TOKEN, SESSION_STRING, MONGO_URL, OWNER_ID, COOKIES_PATH

REQUIRED_ENV = {"API_ID": API_ID, "API_HASH": API_HASH, "BOT_TOKEN": BOT_TOKEN,
                "MONGO_URL": MONGO_URL, "OWNER_ID": OWNER_ID, "SESSION_STRING": SESSION_STRING}
COOKIE_PATH = COOKIES_PATH or "cookies.txt"
START_TIME = time.perf_counter()


def _mask(v):
    v = str(v or "")
    return "(empty)" if not v else ("*" * len(v) if len(v) <= 8 else f"{v[:2]}***{v[-2:]}")

def _run(cmd):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        out = (r.stdout.strip() or r.stderr.strip())
        return out.splitlines()[0] if r.returncode == 0 and out else None
    except Exception:
        return None


def _check_python():
    v = sys.version.replace("\n", " ")
    warn = sys.version_info < (3, 10)
    (LOGGER.warning if warn else LOGGER.info)(f"  Python {v}" + (" ← 3.10+ recommended" if warn else ""))

def _check_network():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=5)
        LOGGER.info("  Internet connection OK")
    except OSError:
        LOGGER.error("  No internet connection")

def _check_disk():
    free_gb = shutil.disk_usage("/").free / (1024 ** 3)
    fn = LOGGER.error if free_gb < 1 else LOGGER.warning if free_gb < 5 else LOGGER.info
    fn(f"  Free disk space: {free_gb:.2f} GB")

def _check_memory():
    try:
        import psutil
        gb = psutil.virtual_memory().available / (1024 ** 3)
        (LOGGER.warning if gb < 0.5 else LOGGER.info)(f"  Available RAM: {gb:.2f} GB")
    except ImportError:
        LOGGER.warning("  psutil not installed")

def _check_env():
    LOGGER.info("── Environment Variables ────────────────────────")
    missing = []
    for k, v in REQUIRED_ENV.items():
        if v in [None, "", 0]:
            LOGGER.error(f"  Missing required variable: {k}")
            missing.append(k)
        else:
            LOGGER.info(f"  {k} = {_mask(v)}")
    return missing


# ── Detailed checks ───────────────────────────────────────────────────────────

def _check_node():
    LOGGER.info("── Node.js ───────────────────────────────────────")
    node = _run("node --version")
    npm  = _run("npm --version")
    LOGGER.info(f"  Node.js {node}") if node else LOGGER.warning("  Node.js not found")
    LOGGER.info(f"  npm {npm}")      if npm  else LOGGER.warning("  npm not found")


def _check_ffmpeg():
    LOGGER.info("── FFmpeg ────────────────────────────────────────")
    v = _run("ffmpeg -version")
    LOGGER.info(f"  {v[:60]}") if v else LOGGER.error("  FFmpeg not found")


def _check_ytdlp():
    LOGGER.info("── yt-dlp ────────────────────────────────────────")
    v = _run("yt-dlp --version")
    LOGGER.info(f"  yt-dlp {v}") if v else LOGGER.error("  yt-dlp not found")


def _check_cookies():
    LOGGER.info("── Cookies ───────────────────────────────────────")

    env_content = os.environ.get("cookies.txt", "").strip()
    if env_content:
        try:
            dest = Path(COOKIE_PATH)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(env_content, encoding="utf-8")
            LOGGER.info(f"  Railway cookies env written to {COOKIE_PATH}")
        except Exception:
            LOGGER.error(f"  Failed to write cookies:\n{format_exc()}")
            return False

    cookie_file = Path(COOKIE_PATH)
    if not cookie_file.is_file():
        LOGGER.warning(f"  Cookies file not found: {COOKIE_PATH}")
        return False

    size = cookie_file.stat().st_size
    if size <= 10:
        LOGGER.warning(f"  Cookies file is empty: {COOKIE_PATH}")
        return False

    try:
        lines = cookie_file.read_text(encoding="utf-8", errors="ignore").splitlines()
        data_lines = [l for l in lines if l.strip() and not l.startswith("#")]

        valid, invalid, domains = 0, 0, set()
        for line in data_lines:
            parts = line.split("\t")
            if len(parts) >= 7:
                domains.add(parts[0].lstrip("."))
                valid += 1
            else:
                invalid += 1

        LOGGER.info(f"  File: {COOKIE_PATH} ({size} bytes) | Valid: {valid} | Domains: {', '.join(sorted(domains)) or 'none'}")
        if invalid:
            LOGGER.warning(f"  Invalid lines: {invalid}")

        yt = [l for l in data_lines if "youtube" in l or "google" in l]
        if yt:
            LOGGER.info(f"  YouTube cookie lines: {len(yt)}")
            for name in ["SAPISID", "LOGIN_INFO", "VISITOR_INFO1_LIVE", "__Secure-3PAPISID"]:
                fn = LOGGER.info if any(f"\t{name}\t" in l for l in yt) else LOGGER.warning
                fn(f"    {name} = {'found' if fn == LOGGER.info else 'NOT FOUND'}")
        else:
            LOGGER.warning("  No YouTube/Google cookies found")

        return True
    except Exception:
        LOGGER.error(f"  Failed to read cookies:\n{format_exc()}")
        return False


async def _check_mongo():
    LOGGER.info("── MongoDB ───────────────────────────────────────")
    try:
        from Pronova.Database import Core
        if Core.db is None:
            return LOGGER.error("  Database is not initialized")
        result = await Core.db.client.admin.command("ping")
        LOGGER.info("  MongoDB connection successful") if result.get("ok") == 1.0 else LOGGER.warning(f"  Ping: {result}")
        colls = await Core.db.list_collection_names()
        LOGGER.info(f"  Collections: {', '.join(colls)}") if colls else LOGGER.info("  No collections found")
    except Exception:
        LOGGER.error(f"  MongoDB connection failed:\n{format_exc()}")


# ── Entry points ──────────────────────────────────────────────────────────────

def run_startup_checks():
    LOGGER.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    LOGGER.info("         ProNova Music Bot Diagnostics           ")
    LOGGER.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    _check_python()
    _check_node()
    _check_ffmpeg()
    _check_ytdlp()
    _check_network()
    _check_disk()
    _check_memory()
    missing = _check_env()
    _check_cookies()

    elapsed = time.perf_counter() - START_TIME
    LOGGER.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    LOGGER.info(f"  Diagnostics completed in {elapsed:.2f} seconds")

    if missing:
        LOGGER.critical(f"  Missing required variables: {', '.join(missing)}")
        raise EnvironmentError(f"Missing required environment variables: {', '.join(missing)}")

    LOGGER.info("  Startup checks completed successfully")
    LOGGER.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")


async def run_async_checks():
    LOGGER.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    LOGGER.info("            Async Diagnostics Running            ")
    LOGGER.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    await _check_mongo()
    LOGGER.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
