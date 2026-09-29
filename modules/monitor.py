import time

import psutil

from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text


console = Console()


def safe_cpu_percent():
    try:
        return psutil.cpu_percent(interval=None)
    except (PermissionError, OSError):
        return None
    except Exception:
        return None


def safe_memory():
    try:
        return psutil.virtual_memory()
    except (PermissionError, OSError):
        return None
    except Exception:
        return None


def safe_disk():
    try:
        return psutil.disk_usage("/")
    except (PermissionError, OSError):
        return None
    except Exception:
        return None


def get_processes():
    processos = []

    try:
        for proc in psutil.process_iter(
            ["pid", "name", "memory_percent"]
        ):
            try:
                info = proc.info

                processos.append(
                    (
                        int(info.get("pid") or 0),
                        str(info.get("name") or "?"),
                        float(info.get("memory_percent") or 0),
                    )
                )

            except (
                psutil.NoSuchProcess,
                psutil.AccessDenied,
                psutil.ZombieProcess,
                PermissionError,
                OSError,
            ):
                continue

    except (PermissionError, OSError):
        return []

    processos.sort(key=lambda x: x[2], reverse=True)

    return processos[:12]


def make_resources():
    cpu = safe_cpu_percent()
    memory = safe_memory()
    disk = safe_disk()

    cpu_text = (
        f"{cpu:.1f}%"
        if cpu is not None
        else "indisponivel"
    )

    if memory is not None:
        ram_text = (
            f"{memory.percent:.1f}% "
            f"({memory.used / (1024 ** 3):.1f} GB / "
            f"{memory.total / (1024 ** 3):.1f} GB)"
        )
    else:
        ram_text = "indisponivel"

    if disk is not None:
        disk_text = (
            f"{disk.percent:.1f}% "
            f"({disk.used / (1024 ** 3):.1f} GB / "
            f"{disk.total / (1024 ** 3):.1f} GB)"
        )
    else:
        disk_text = "indisponivel"

    table = Table.grid(expand=True)

    table.add_column(ratio=1)
    table.add_column(ratio=1)
    table.add_column(ratio=1)

    table.add_row(
        Text(
            f"CPU\n{cpu_text}",
            style="bold cyan",
        ),
        Text(
            f"RAM\n{ram_text}",
            style="bold green",
        ),
        Text(
            f"DISCO\n{disk_text}",
            style="bold yellow",
        ),
    )

    return Panel(
        table,
        title="[bold cyan]RECURSOS DO SISTEMA[/bold cyan]",
        border_style="cyan",
    )


def make_processes():
    table = Table(
        expand=True,
        border_style="dim cyan",
    )

    table.add_column(
        "PID",
        justify="right",
        style="cyan",
        width=8,
    )

    table.add_column(
        "PROCESSO",
        style="white",
        no_wrap=True,
    )

    table.add_column(
        "RAM",
        justify="right",
        style="green",
        width=10,
    )

    processos = get_processes()

    if not processos:
        table.add_row(
            "-",
            "Nao foi possivel consultar os processos",
            "-",
        )
    else:
        for pid, nome, memoria in processos:
            table.add_row(
                str(pid),
                nome[:42],
                f"{memoria:.1f}%",
            )

    return Panel(
        table,
        title="[bold cyan]PROCESSOS — TOP RAM[/bold cyan]",
        border_style="cyan",
    )


def make_footer():
    return Panel(
        Text(
            "Monitor em Tempo Real\n"
            "Ctrl+C regressa ao PenKit OS",
            justify="center",
            style="dim white",
        ),
        border_style="dim cyan",
    )


def make_layout():
    layout = Layout()

    layout.split_column(
        Layout(name="resources", size=7),
        Layout(name="processes"),
        Layout(name="footer", size=5),
    )

    layout["resources"].update(make_resources())
    layout["processes"].update(make_processes())
    layout["footer"].update(make_footer())

    return layout


def run():
    console.clear()

    console.print(
        Panel(
            "[bold cyan]MONITOR EM TEMPO REAL[/bold cyan]\n"
            "[dim]Monitorizacao local do sistema hospedeiro[/dim]",
            border_style="cyan",
        )
    )

    try:
        psutil.cpu_percent(interval=None)
    except Exception:
        pass

    try:
        with Live(
            make_layout(),
            console=console,
            refresh_per_second=2,
            screen=False,
        ) as live:

            while True:
                time.sleep(0.5)

                try:
                    live.update(make_layout())
                except (
                    PermissionError,
                    OSError,
                ):
                    continue

    except KeyboardInterrupt:
        pass

    except Exception as exc:
        console.print(
            Panel(
                "[yellow]Monitor terminou com uma "
                "limitacao do sistema.[/yellow]\n\n"
                f"[dim]{type(exc).__name__}: {exc}[/dim]",
                border_style="yellow",
            )
        )

        try:
            input("\nEnter...")
        except KeyboardInterrupt:
            pass
