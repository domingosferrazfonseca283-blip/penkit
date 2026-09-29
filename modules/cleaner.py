import os
import shutil

from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    Progress,
    SpinnerColumn,
    BarColumn,
    TextColumn,
)
from rich.table import Table
from rich import box

console = Console()

TARGETS = [
    ("Cache pip", os.path.expanduser("~/.cache/pip")),
    ("Cache geral", os.path.expanduser("~/.cache")),
    ("/tmp", "/tmp"),
]


def get_size(path):
    total = 0

    try:
        if os.path.isfile(path):
            return os.path.getsize(path)

        for root, _, files in os.walk(path):
            for name in files:
                try:
                    total += os.path.getsize(
                        os.path.join(root, name)
                    )
                except OSError:
                    pass

    except OSError:
        pass

    return total


def fmt(value):
    value = float(value)

    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024:
            return f"{value:.1f} {unit}"
        value /= 1024

    return f"{value:.1f} TB"


def clear_directory(path):
    removed = 0
    failed = 0

    try:
        for name in os.listdir(path):
            target = os.path.join(path, name)

            try:
                if os.path.islink(target) or os.path.isfile(target):
                    os.remove(target)
                elif os.path.isdir(target):
                    shutil.rmtree(target)

                removed += 1

            except OSError:
                failed += 1

    except OSError:
        failed += 1

    return removed, failed


def run():
    console.clear()

    console.print(
        Panel(
            "[bold cyan]Limpeza do Sistema[/bold cyan]\n"
            "[dim]Limpeza de caches conhecidos e /tmp[/dim]",
            border_style="cyan",
        )
    )

    found = []

    for label, path in TARGETS:
        if os.path.exists(path):
            found.append(
                (label, path, get_size(path))
            )

    if not found:
        console.print("[green]Nenhuma area de limpeza encontrada.[/green]")
        input("\nEnter...")
        return

    table = Table(
        box=box.SIMPLE_HEAVY,
        border_style="cyan",
        header_style="bold magenta",
    )

    table.add_column("#", width=3, justify="center")
    table.add_column("Tipo")
    table.add_column("Caminho")
    table.add_column("Tamanho", justify="right")

    for index, (label, path, size) in enumerate(found, 1):
        table.add_row(
            str(index),
            label,
            path,
            fmt(size),
        )

    console.print(table)

    total = sum(
        size for _, _, size in found
    )

    console.print(
        f"\nTotal potencial: [bold yellow]{fmt(total)}[/bold yellow]"
    )

    confirm = console.input(
        "\n[red]Apagar o conteudo destas areas? "
        "Escreva LIMPAR: [/red]"
    ).strip()

    if confirm != "LIMPAR":
        console.print("[dim]Operacao cancelada.[/dim]")
        input("\nEnter...")
        return

    removed = 0
    failed = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[cyan]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        console=console,
    ) as progress:

        task = progress.add_task(
            "A limpar...",
            total=len(found),
        )

        for _, path, _ in found:
            r, f = clear_directory(path)
            removed += r
            failed += f
            progress.advance(task)

    console.print(
        Panel(
            f"[green]Limpeza concluida.[/green]\n"
            f"Itens removidos: {removed}\n"
            f"Falhas: {failed}",
            border_style="green",
        )
    )

    input("\nEnter...")
