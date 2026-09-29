import psutil
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

console = Console()


def run():
    console.clear()

    console.print(
        Panel(
            "[bold cyan]Gestor de Processos[/bold cyan]\n"
            "[dim]Processos reais do sistema hospedeiro[/dim]",
            border_style="cyan",
        )
    )

    processes = []

    for proc in psutil.process_iter(
        ["pid", "name", "cpu_percent", "memory_percent", "status"]
    ):
        try:
            info = proc.info
            processes.append(info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    processes.sort(
        key=lambda item: item.get("cpu_percent") or 0,
        reverse=True,
    )

    processes = processes[:25]

    table = Table(
        box=box.SIMPLE_HEAVY,
        border_style="cyan",
        header_style="bold magenta",
    )

    table.add_column("PID", width=8, justify="right")
    table.add_column("Nome", width=25)
    table.add_column("CPU%", width=8, justify="right")
    table.add_column("RAM%", width=8, justify="right")
    table.add_column("Estado", width=14)

    for item in processes:
        table.add_row(
            str(item.get("pid", "?")),
            str(item.get("name") or "?")[:25],
            f"{item.get('cpu_percent') or 0:.1f}",
            f"{item.get('memory_percent') or 0:.1f}",
            str(item.get("status") or "?"),
        )

    console.print(table)

    pid_text = console.input(
        "\n[yellow]PID a terminar "
        "(Enter para voltar): [/yellow]"
    ).strip()

    if not pid_text:
        return

    try:
        pid = int(pid_text)
        proc = psutil.Process(pid)
        name = proc.name()

        console.print(
            Panel(
                f"Processo selecionado:\n"
                f"[cyan]PID:[/cyan] {pid}\n"
                f"[cyan]Nome:[/cyan] {name}",
                border_style="yellow",
            )
        )

        confirm = console.input(
            "[red]Terminar este processo? "
            "Escreva TERMINAR: [/red]"
        ).strip()

        if confirm != "TERMINAR":
            console.print("[dim]Operacao cancelada.[/dim]")
            input("\nEnter...")
            return

        proc.terminate()

        try:
            proc.wait(timeout=3)
            console.print(
                Panel(
                    f"[green]Processo {pid} ({name}) terminado.[/green]",
                    border_style="green",
                )
            )
        except psutil.TimeoutExpired:
            console.print(
                "[yellow]O processo nao terminou no tempo esperado.[/yellow]"
            )

    except ValueError:
        console.print("[red]PID invalido.[/red]")

    except psutil.NoSuchProcess:
        console.print("[yellow]O processo ja nao existe.[/yellow]")

    except psutil.AccessDenied:
        console.print(
            "[red]Acesso negado pelo sistema. "
            "O PenKit nao vai forcar a terminacao.[/red]"
        )

    except Exception as exc:
        console.print(
            f"[red]Erro: {type(exc).__name__}: {exc}[/red]"
        )

    input("\nEnter...")
