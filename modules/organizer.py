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

CATEGORIES = {
    "Imagens": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp"],
    "Videos": [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv"],
    "Audio": [".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a"],
    "Documentos": [".pdf", ".doc", ".docx", ".txt", ".odt", ".md"],
    "Planilhas": [".xls", ".xlsx", ".csv"],
    "Codigo": [".py", ".js", ".html", ".css", ".java", ".c", ".cpp", ".sh", ".json"],
    "Comprimidos": [".zip", ".tar", ".gz", ".rar", ".7z"],
    "APKs": [".apk"],
}


def category_for(extension):
    extension = extension.lower()

    for category, extensions in CATEGORIES.items():
        if extension in extensions:
            return category

    return "Outros"


def unique_destination(path):
    if not os.path.exists(path):
        return path

    base, extension = os.path.splitext(path)
    counter = 2

    while True:
        candidate = f"{base}_{counter}{extension}"

        if not os.path.exists(candidate):
            return candidate

        counter += 1


def run():
    console.clear()

    console.print(
        Panel(
            "[bold cyan]Organizador de Ficheiros[/bold cyan]\n"
            "[dim]Organiza apenas ficheiros diretamente dentro da pasta escolhida[/dim]",
            border_style="cyan",
        )
    )

    default_home = os.path.expanduser("~")

    value = console.input(
        f"[yellow]Pasta "
        f"(Enter para {default_home}): [/yellow]"
    ).strip()

    folder = os.path.abspath(
        os.path.expanduser(value or default_home)
    )

    if not os.path.isdir(folder):
        console.print(
            f"[red]Pasta nao encontrada:[/red] {folder}"
        )
        input("\nEnter...")
        return

    files = []

    try:
        for name in os.listdir(folder):
            path = os.path.join(folder, name)

            if os.path.isfile(path) and not os.path.islink(path):
                files.append(
                    (name, path, os.path.splitext(name)[1])
                )
    except PermissionError:
        console.print("[red]Sem permissao para ler a pasta.[/red]")
        input("\nEnter...")
        return

    if not files:
        console.print("[yellow]Nenhum ficheiro encontrado.[/yellow]")
        input("\nEnter...")
        return

    summary = {}

    for _, _, extension in files:
        category = category_for(extension)
        summary[category] = summary.get(category, 0) + 1

    table = Table(
        box=box.SIMPLE_HEAVY,
        border_style="cyan",
        header_style="bold magenta",
    )

    table.add_column("Categoria")
    table.add_column("Ficheiros", justify="right")

    for category, count in sorted(
        summary.items(),
        key=lambda item: -item[1],
    ):
        table.add_row(category, str(count))

    table.add_row(
        "[cyan]TOTAL[/cyan]",
        f"[cyan]{len(files)}[/cyan]",
    )

    console.print(table)

    confirm = console.input(
        "\n[yellow]Organizar estes ficheiros? (s/N): [/yellow]"
    ).strip().lower()

    if confirm != "s":
        console.print("[dim]Operacao cancelada.[/dim]")
        input("\nEnter...")
        return

    moved = 0
    failed = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[cyan]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        console=console,
    ) as progress:

        task = progress.add_task(
            "A organizar...",
            total=len(files),
        )

        for name, source, extension in files:
            category = category_for(extension)
            directory = os.path.join(folder, category)

            try:
                os.makedirs(directory, exist_ok=True)

                destination = unique_destination(
                    os.path.join(directory, name)
                )

                shutil.move(source, destination)
                moved += 1

            except Exception:
                failed += 1

            progress.advance(task)

    console.print(
        Panel(
            f"[green]Organizacao concluida.[/green]\n"
            f"Movidos: {moved}\n"
            f"Falhas: {failed}",
            border_style="green",
        )
    )

    input("\nEnter...")
