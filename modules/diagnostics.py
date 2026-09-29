import os
import platform
import socket
import time

from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

console = Console()


def read_file(path, default=""):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return default


def get_ip():
    sock = None
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except Exception:
        return "offline"
    finally:
        if sock:
            sock.close()


def get_uptime():
    try:
        seconds = float(read_file("/proc/uptime").split()[0])
        seconds = int(seconds)

        days, rem = divmod(seconds, 86400)
        hours, rem = divmod(rem, 3600)
        minutes, secs = divmod(rem, 60)

        return f"{days}d {hours:02d}h {minutes:02d}m {secs:02d}s"
    except Exception:
        return "indisponível"


def get_memory():
    try:
        values = {}

        for line in read_file("/proc/meminfo").splitlines():
            parts = line.split()

            if len(parts) >= 2:
                key = parts[0].rstrip(":")
                values[key] = int(parts[1]) * 1024

        total = values.get("MemTotal", 0)
        available = values.get("MemAvailable", 0)

        used = max(0, total - available)
        percent = (used / total * 100) if total else 0

        return used, total, percent

    except Exception:
        return 0, 0, 0


def get_disk():
    try:
        stat = os.statvfs("/")

        total = stat.f_blocks * stat.f_frsize
        free = stat.f_bavail * stat.f_frsize
        used = total - free

        percent = (used / total * 100) if total else 0

        return used, total, percent

    except Exception:
        return 0, 0, 0


def get_cpu():
    try:
        model = "Desconhecido"
        cores = os.cpu_count() or 0

        for line in read_file("/proc/cpuinfo").splitlines():
            if ":" not in line:
                continue

            key, value = line.split(":", 1)

            if key.strip().lower() in (
                "model name",
                "hardware",
                "processor",
            ):
                model = value.strip()
                break

        return model, cores

    except Exception:
        return "Desconhecido", os.cpu_count() or 0


def get_cpu_usage():
    try:
        first = read_file("/proc/stat").splitlines()[0].split()

        values = [int(x) for x in first[1:]]
        total_1 = sum(values)
        idle_1 = values[3]

        time.sleep(0.15)

        second = read_file("/proc/stat").splitlines()[0].split()

        values = [int(x) for x in second[1:]]
        total_2 = sum(values)
        idle_2 = values[3]

        total_delta = total_2 - total_1
        idle_delta = idle_2 - idle_1

        if total_delta <= 0:
            return 0.0

        return max(
            0.0,
            min(100.0, 100.0 * (1 - idle_delta / total_delta))
        )

    except Exception:
        return 0.0


def get_network_interfaces():
    result = []

    try:
        lines = read_file("/proc/net/dev").splitlines()[2:]

        for line in lines:
            if ":" not in line:
                continue

            name, data = line.split(":", 1)
            parts = data.split()

            if len(parts) < 9:
                continue

            rx = int(parts[0])
            tx = int(parts[8])

            result.append((name.strip(), rx, tx))

    except Exception:
        pass

    return result


def format_bytes(value):
    value = float(value)

    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024:
            return f"{value:.1f} {unit}"
        value /= 1024

    return f"{value:.1f} PB"


def progress_bar(percent, width=24):
    percent = max(0, min(100, float(percent)))

    filled = int(width * percent / 100)
    empty = width - filled

    if percent < 60:
        color = "green"
    elif percent < 85:
        color = "yellow"
    else:
        color = "red"

    return (
        f"[{color}]"
        + "█" * filled
        + "[/]"
        + "░" * empty
        + f" [bold]{percent:5.1f}%[/bold]"
    )


def host_table():
    table = Table(
        box=box.SIMPLE_HEAVY,
        border_style="cyan",
        header_style="bold magenta",
        expand=True,
    )

    table.add_column("CAMPO", style="bold yellow", width=18)
    table.add_column("VALOR", style="white")

    table.add_row("Hostname", socket.gethostname())
    table.add_row("IP local", get_ip())
    table.add_row(
        "Sistema",
        f"{platform.system()} {platform.release()}",
    )
    table.add_row("Arquitetura", platform.machine())
    table.add_row("Python", platform.python_version())
    table.add_row("Processador", get_cpu()[0])
    table.add_row("Núcleos", str(get_cpu()[1]))
    table.add_row("Uptime", get_uptime())
    table.add_row(
        "Execução",
        datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
    )

    return table


def resource_table():
    ram_used, ram_total, ram_percent = get_memory()
    disk_used, disk_total, disk_percent = get_disk()
    cpu_percent = get_cpu_usage()

    table = Table(
        box=box.SIMPLE_HEAVY,
        border_style="cyan",
        header_style="bold magenta",
        expand=True,
    )

    table.add_column("RECURSO", style="bold yellow", width=12)
    table.add_column("UTILIZAÇÃO")
    table.add_column("DETALHE", style="dim white")

    table.add_row(
        "CPU",
        progress_bar(cpu_percent),
        f"{cpu_percent:.1f}%",
    )

    table.add_row(
        "RAM",
        progress_bar(ram_percent),
        f"{format_bytes(ram_used)} / {format_bytes(ram_total)}",
    )

    table.add_row(
        "DISCO",
        progress_bar(disk_percent),
        f"{format_bytes(disk_used)} / {format_bytes(disk_total)}",
    )

    return table


def network_table():
    interfaces = get_network_interfaces()

    table = Table(
        box=box.SIMPLE_HEAVY,
        border_style="cyan",
        header_style="bold magenta",
        expand=True,
    )

    table.add_column("INTERFACE", style="bold yellow")
    table.add_column("RX", justify="right", style="green")
    table.add_column("TX", justify="right", style="cyan")

    if not interfaces:
        table.add_row("-", "-", "-")
        return table

    for name, rx, tx in interfaces:
        table.add_row(
            name,
            format_bytes(rx),
            format_bytes(tx),
        )

    return table


def run():
    console.clear()

    console.print(
        Panel(
            "[bold cyan]PENKIT OS :: SYSTEM DIAGNOSTIC[/bold cyan]\n"
            "[dim]Leitura real do sistema hospedeiro[/dim]",
            border_style="cyan",
        )
    )

    console.print()
    console.print(
        Panel(
            host_table(),
            title="[bold cyan]HOST[/bold cyan]",
            border_style="cyan",
        )
    )

    console.print()
    console.print(
        Panel(
            resource_table(),
            title="[bold cyan]RECURSOS[/bold cyan]",
            border_style="cyan",
        )
    )

    console.print()
    console.print(
        Panel(
            network_table(),
            title="[bold cyan]REDE[/bold cyan]",
            border_style="cyan",
        )
    )

    console.print()
    console.print(
        "[dim]Os valores acima são obtidos diretamente do ambiente "
        "onde o PenKit está sendo executado.[/dim]"
    )

    console.input("\n[bold cyan]ENTER[/bold cyan] para voltar...")
