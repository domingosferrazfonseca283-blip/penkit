import os
import html
import socket
import platform
from datetime import datetime

import psutil

from rich.console import Console
from rich.panel import Panel

console = Console()


def fmt(value):
    value = float(value)

    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024:
            return f"{value:.1f} {unit}"
        value /= 1024

    return f"{value:.1f} TB"


def get_ip():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(1)
        sock.connect(("8.8.8.8", 80))
        ip = sock.getsockname()[0]
        sock.close()
        return ip
    except Exception:
        return "offline"


def get_uptime():
    try:
        seconds = int(float(open("/proc/uptime").read().split()[0]))

        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        minutes = (seconds % 3600) // 60

        return f"{days}d {hours}h {minutes}m"

    except Exception:
        return "?"


def run():
    console.clear()

    console.print(
        Panel(
            "[bold cyan]Relatorio HTML[/bold cyan]\n"
            "[dim]Snapshot real do sistema hospedeiro[/dim]",
            border_style="cyan",
        )
    )

    console.print("[yellow]A recolher dados...[/yellow]")

    now = datetime.now()

    hostname = html.escape(socket.gethostname())
    ip = html.escape(get_ip())

    operating_system = html.escape(
        f"{platform.system()} {platform.release()}"
    )

    architecture = html.escape(platform.machine())
    cpu_model = html.escape(
        platform.processor() or "Nao identificado"
    )

    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    cores = psutil.cpu_count(logical=True) or 0

    interfaces = psutil.net_io_counters(pernic=True)

    network_rows = []

    for name, counters in interfaces.items():
        network_rows.append(
            "<tr>"
            f"<td>{html.escape(name)}</td>"
            f"<td>{fmt(counters.bytes_recv)}</td>"
            f"<td>{fmt(counters.bytes_sent)}</td>"
            "</tr>"
        )

    if not network_rows:
        network_html = (
            "<tr><td colspan='3'>"
            "Sem interfaces disponiveis"
            "</td></tr>"
        )
    else:
        network_html = "".join(network_rows)

    if memory.percent < 60:
        ram_color = "#00ff99"
    elif memory.percent < 85:
        ram_color = "#ffcc00"
    else:
        ram_color = "#ff4444"

    if disk.percent < 60:
        disk_color = "#00ff99"
    elif disk.percent < 85:
        disk_color = "#ffcc00"
    else:
        disk_color = "#ff4444"

    css = """
* {
    box-sizing: border-box;
}

body {
    margin: 0;
    background: #080b10;
    color: #c9e8f5;
    font-family: monospace;
    padding: 30px 18px;
}

.container {
    max-width: 1050px;
    margin: auto;
}

header {
    text-align: center;
    margin-bottom: 30px;
}

h1 {
    color: #00e5ff;
    letter-spacing: 6px;
    margin-bottom: 8px;
}

.sub {
    color: #607987;
}

.grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 18px;
}

.card {
    background: #0d131a;
    border: 1px solid #00e5ff33;
    border-radius: 10px;
    padding: 20px;
}

h2 {
    color: #00e5ff;
    font-size: .9rem;
    letter-spacing: 2px;
    border-bottom: 1px solid #ffffff12;
    padding-bottom: 10px;
}

table {
    width: 100%;
    border-collapse: collapse;
}

td, th {
    padding: 8px 5px;
    border-bottom: 1px solid #ffffff0d;
    text-align: left;
}

td:first-child {
    color: #718995;
}

.bar {
    background: #ffffff10;
    height: 9px;
    border-radius: 5px;
    overflow: hidden;
}

.fill {
    height: 100%;
}

.value {
    margin-top: 7px;
    color: #a9bdc7;
}

footer {
    text-align: center;
    color: #40535e;
    margin-top: 35px;
}
"""

    html_doc = (
        "<!DOCTYPE html>\n"
        "<html lang='pt'>\n"
        "<head>\n"
        "<meta charset='UTF-8'>\n"
        "<meta name='viewport' "
        "content='width=device-width,initial-scale=1'>\n"
        "<title>PenKit - Relatorio de Sistema</title>\n"
        "<style>\n"
        + css +
        "\n</style>\n"
        "</head>\n"
        "<body>\n"
        "<div class='container'>\n"

        "<header>\n"
        "<h1>PENKIT</h1>\n"
        f"<div class='sub'>"
        f"Relatorio de Sistema — "
        f"{now.strftime('%d/%m/%Y %H:%M:%S')}"
        "</div>\n"
        "</header>\n"

        "<div class='grid'>\n"

        "<div class='card'>\n"
        "<h2>SISTEMA</h2>\n"
        "<table>\n"
        f"<tr><td>Hostname</td><td>{hostname}</td></tr>\n"
        f"<tr><td>IP</td><td>{ip}</td></tr>\n"
        f"<tr><td>OS</td><td>{operating_system}</td></tr>\n"
        f"<tr><td>Arquitetura</td><td>{architecture}</td></tr>\n"
        f"<tr><td>CPU</td><td>{cpu_model}</td></tr>\n"
        f"<tr><td>Threads</td><td>{cores}</td></tr>\n"
        f"<tr><td>Uptime</td><td>{get_uptime()}</td></tr>\n"
        f"<tr><td>Python</td><td>{platform.python_version()}</td></tr>\n"
        "</table>\n"
        "</div>\n"

        "<div class='card'>\n"
        "<h2>MEMORIA</h2>\n"
        "<div class='bar'>\n"
        f"<div class='fill' "
        f"style='width:{memory.percent:.1f}%;"
        f"background:{ram_color}'></div>\n"
        "</div>\n"
        f"<div class='value'>"
        f"{memory.percent:.1f}% — "
        f"{fmt(memory.used)} / {fmt(memory.total)}"
        "</div>\n"
        "</div>\n"

        "<div class='card'>\n"
        "<h2>DISCO</h2>\n"
        "<div class='bar'>\n"
        f"<div class='fill' "
        f"style='width:{disk.percent:.1f}%;"
        f"background:{disk_color}'></div>\n"
        "</div>\n"
        f"<div class='value'>"
        f"{disk.percent:.1f}% — "
        f"{fmt(disk.used)} / {fmt(disk.total)}"
        "</div>\n"
        "</div>\n"

        "<div class='card'>\n"
        "<h2>REDE</h2>\n"
        "<table>\n"
        "<tr><th>Interface</th>"
        "<th>RX</th><th>TX</th></tr>\n"
        f"{network_html}\n"
        "</table>\n"
        "</div>\n"

        "</div>\n"

        "<footer>\n"
        "PenKit OS v2.0 — Relatorio local\n"
        "</footer>\n"

        "</div>\n"
        "</body>\n"
        "</html>\n"
    )

    os.makedirs("reports", exist_ok=True)

    timestamp = now.strftime("%Y%m%d_%H%M%S")

    path = os.path.abspath(
        f"reports/relatorio_{timestamp}.html"
    )

    with open(path, "w", encoding="utf-8") as file:
        file.write(html_doc)

    console.print(
        Panel(
            "[green]Relatorio gerado com sucesso.[/green]\n\n"
            f"[cyan]{path}[/cyan]",
            border_style="green",
        )
    )

    input("\nEnter...")
