import json
import os
import platform
import socket
from datetime import datetime


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_DIR = os.path.join(BASE_DIR, "data")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")


def ensure_dirs():
    for directory in (DATA_DIR, LOGS_DIR, REPORTS_DIR):
        os.makedirs(directory, exist_ok=True)


def timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def filename_timestamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def log(message, level="INFO"):
    ensure_dirs()

    line = (
        f"[{timestamp()}] "
        f"[{level.upper()}] "
        f"{message}\n"
    )

    path = os.path.join(LOGS_DIR, "penkit.log")

    try:
        with open(path, "a", encoding="utf-8") as file:
            file.write(line)
    except Exception:
        pass


def log_error(module, error):
    log(
        f"{module}: {type(error).__name__}: {error}",
        "ERROR",
    )


def save_json(filename, data):
    ensure_dirs()

    path = os.path.join(DATA_DIR, filename)

    with open(
        path,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False,
        )

    return path


def load_json(filename, default=None):
    ensure_dirs()

    path = os.path.join(DATA_DIR, filename)

    if not os.path.exists(path):
        return default

    try:
        with open(
            path,
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(file)

    except Exception:
        return default


def system_info():
    info = {
        "hostname": socket.gethostname(),
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "termux": os.path.isdir(
            "/data/data/com.termux/files"
        ),
        "timestamp": timestamp(),
    }

    return info


def get_local_ip():
    try:
        sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM,
        )

        sock.settimeout(1)

        sock.connect(("8.8.8.8", 80))

        ip = sock.getsockname()[0]

        sock.close()

        return ip

    except Exception:
        return "offline"


def runtime_info():
    info = system_info()

    info["local_ip"] = get_local_ip()
    info["base_dir"] = BASE_DIR
    info["data_dir"] = DATA_DIR
    info["logs_dir"] = LOGS_DIR
    info["reports_dir"] = REPORTS_DIR

    return info


def initialize():
    ensure_dirs()

    log("PenKit iniciado")

    return runtime_info()


def module_error(console, module, error):
    log_error(module, error)

    try:
        console.print(
            f"\n[bold red]Erro no modulo:[/bold red]\n"
            f"[yellow]{type(error).__name__}[/yellow]: "
            f"{error}\n"
            f"[dim]Registo guardado em logs/penkit.log[/dim]"
        )
    except Exception:
        pass


def safe_input(prompt="", default=""):
    try:
        value = input(prompt)
        return value.strip()

    except (KeyboardInterrupt, EOFError):
        return default
