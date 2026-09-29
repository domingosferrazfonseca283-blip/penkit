import os
import socket
import sys
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

console = Console()


def result(description, status, detail=""):
    return {
        "description": description,
        "status": status,
        "detail": detail,
    }


def checks():
    results = []

    # SSH local
    try:
        sock = socket.socket()
        sock.settimeout(0.5)
        code = sock.connect_ex(("127.0.0.1", 22))
        sock.close()

        if code == 0:
            results.append(
                result(
                    "SSH local / porta 22",
                    "ATIVO",
                    "Existe um servico a escutar na porta 22.",
                )
            )
        else:
            results.append(
                result(
                    "SSH local / porta 22",
                    "FECHADO",
                    "Nao foi detetado listener local na porta 22.",
                )
            )

    except Exception as exc:
        results.append(
            result(
                "SSH local / porta 22",
                "N/D",
                str(exc),
            )
        )

    # Ficheiros
    for path in ("/etc/passwd", "/etc/shadow"):
        if not os.path.exists(path):
            continue

        try:
            with open(path, encoding="utf-8", errors="ignore") as f:
                f.readline()

            results.append(
                result(
                    f"Leitura de {path}",
                    "LEGIVEL",
                    "O processo atual conseguiu abrir o ficheiro.",
                )
            )

        except PermissionError:
            results.append(
                result(
                    f"Leitura de {path}",
                    "PROTEGIDO",
                    "O processo atual nao tem permissao de leitura.",
                )
            )

        except Exception as exc:
            results.append(
                result(
                    f"Leitura de {path}",
                    "N/D",
                    str(exc),
                )
            )

    # Disco
    try:
        stat = os.statvfs("/")
        total = stat.f_blocks * stat.f_frsize
        free = stat.f_bavail * stat.f_frsize
        used = total - free
        percent = used / total * 100 if total else 0

        status = "ATENCAO" if percent >= 90 else "NORMAL"

        results.append(
            result(
                "Espaco em disco",
                status,
                f"{percent:.1f}% utilizado.",
            )
        )

    except Exception as exc:
        results.append(
            result(
                "Espaco em disco",
                "N/D",
                str(exc),
            )
        )

    # Python
    version = sys.version_info

    results.append(
        result(
            "Versao Python",
            "INFO",
            f"{version.major}.{version.minor}.{version.micro}",
        )
    )

    # Home
    home = os.path.expanduser("~")

    try:
        mode = oct(os.stat(home).st_mode & 0o777)

        results.append(
            result(
                "Permissoes da HOME",
                "INFO",
                mode,
            )
        )

    except Exception as exc:
        results.append(
            result(
                "Permissoes da HOME",
                "N/D",
                str(exc),
            )
        )

    return results


def run():
    console.clear()

    console.print(
        Panel(
            "[bold cyan]Analise de Seguranca Local[/bold cyan]\n"
            "[dim]Inventario factual do ambiente atual[/dim]",
            border_style="cyan",
        )
    )

    console.print(
        "[yellow]Nenhuma alteracao sera feita no sistema.[/yellow]\n"
    )

    results = checks()

    table = Table(
        box=box.SIMPLE_HEAVY,
        border_style="cyan",
        header_style="bold magenta",
    )

    table.add_column("Estado", width=12, justify="center")
    table.add_column("Verificacao", width=30)
    table.add_column("Detalhe")

    for item in results:
        status = item["status"]

        color = {
            "NORMAL": "green",
            "PROTEGIDO": "green",
            "FECHADO": "green",
            "INFO": "cyan",
            "ATIVO": "yellow",
            "ATENCAO": "red",
            "LEGIVEL": "yellow",
            "N/D": "dim",
        }.get(status, "white")

        table.add_row(
            f"[bold {color}]{status}[/bold {color}]",
            item["description"],
            item["detail"],
        )

    console.print(table)

    os.makedirs("reports", exist_ok=True)

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    path = f"reports/seguranca_{timestamp}.txt"

    with open(path, "w", encoding="utf-8") as file:
        file.write("PENKIT - ANALISE DE SEGURANCA LOCAL\n")
        file.write(f"Data: {datetime.now()}\n")
        file.write("=" * 60 + "\n\n")

        for item in results:
            file.write(
                f"[{item['status']}] "
                f"{item['description']}: "
                f"{item['detail']}\n"
            )

    console.print(
        f"\n[dim]Relatorio: {os.path.abspath(path)}[/dim]"
    )

    input("\nEnter...")
