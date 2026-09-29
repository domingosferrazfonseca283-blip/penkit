import os
import zipfile
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    Progress,
    SpinnerColumn,
    BarColumn,
    TextColumn,
)

console = Console()


def fmt(value):
    value = float(value)

    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024:
            return f"{value:.1f} {unit}"
        value /= 1024

    return f"{value:.1f} TB"


def run():
    console.clear()

    console.print(
        Panel(
            "[bold cyan]Backup Rapido[/bold cyan]\n"
            "[dim]Arquivo ZIP do diretorio selecionado[/dim]",
            border_style="cyan",
        )
    )

    home = os.path.expanduser("~")

    origem_input = console.input(
        f"[yellow]Pasta a fazer backup "
        f"(Enter para ~/PenKit): [/yellow]"
    ).strip()

    origem = os.path.abspath(
        os.path.expanduser(origem_input or "~/PenKit")
    )

    if not os.path.isdir(origem):
        console.print(
            f"[red]Pasta nao encontrada:[/red] {origem}"
        )
        input("\nEnter...")
        return

    destino_input = console.input(
        f"[yellow]Destino "
        f"(Enter para {home}): [/yellow]"
    ).strip()

    destino_dir = os.path.abspath(
        os.path.expanduser(destino_input or home)
    )

    try:
        os.makedirs(destino_dir, exist_ok=True)
    except Exception as exc:
        console.print(
            f"[red]Nao foi possivel criar o destino: {exc}[/red]"
        )
        input("\nEnter...")
        return

    nome = os.path.basename(origem.rstrip(os.sep))
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    zip_path = os.path.join(
        destino_dir,
        f"{nome}_backup_{timestamp}.zip",
    )

    files = []

    for root, dirs, filenames in os.walk(origem):
        dirs[:] = [
            d for d in dirs
            if not os.path.islink(os.path.join(root, d))
        ]

        for filename in filenames:
            path = os.path.join(root, filename)

            if os.path.islink(path):
                continue

            if os.path.abspath(path) == os.path.abspath(zip_path):
                continue

            files.append(path)

    if not files:
        console.print("[yellow]A pasta esta vazia.[/yellow]")
        input("\nEnter...")
        return

    total_size = 0

    for path in files:
        try:
            total_size += os.path.getsize(path)
        except OSError:
            pass

    console.print(
        f"\n[dim]{len(files)} ficheiro(s) encontrados[/dim]"
    )
    console.print(
        f"[dim]Tamanho original: {fmt(total_size)}[/dim]\n"
    )

    confirm = console.input(
        "[yellow]Criar backup? (s/N): [/yellow]"
    ).strip().lower()

    if confirm != "s":
        console.print("[dim]Operacao cancelada.[/dim]")
        input("\nEnter...")
        return

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[cyan]{task.description}"),
            BarColumn(),
            TextColumn("{task.completed}/{task.total}"),
            console=console,
        ) as progress:

            task = progress.add_task(
                "A comprimir...",
                total=len(files),
            )

            base = os.path.dirname(origem)

            with zipfile.ZipFile(
                zip_path,
                "w",
                compression=zipfile.ZIP_DEFLATED,
                compresslevel=6,
            ) as archive:

                for path in files:
                    relative = os.path.relpath(path, base)
                    archive.write(path, relative)
                    progress.advance(task)

        zip_size = os.path.getsize(zip_path)

        reduction = (
            (1 - zip_size / total_size) * 100
            if total_size
            else 0
        )

        console.print(
            Panel(
                "[green]Backup concluido![/green]\n\n"
                f"[cyan]Ficheiro:[/cyan] {zip_path}\n"
                f"[cyan]Original:[/cyan] {fmt(total_size)}\n"
                f"[cyan]ZIP:[/cyan] {fmt(zip_size)}\n"
                f"[cyan]Reducao:[/cyan] {reduction:.1f}%",
                border_style="green",
            )
        )

    except Exception as exc:
        if os.path.exists(zip_path):
            try:
                os.remove(zip_path)
            except OSError:
                pass

        console.print(
            Panel(
                f"[red]Backup falhou.[/red]\n"
                f"{type(exc).__name__}: {exc}",
                border_style="red",
            )
        )

    input("\nEnter...")
