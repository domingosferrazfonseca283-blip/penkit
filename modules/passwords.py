import secrets
import string

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

console = Console()


def generate_password(
    length=16,
    symbols=True,
    numbers=True,
    uppercase=True,
):
    characters = string.ascii_lowercase

    if uppercase:
        characters += string.ascii_uppercase

    if numbers:
        characters += string.digits

    if symbols:
        characters += "!@#$%^&*()-_=+[]{}|;:,.<>?"

    return "".join(
        secrets.choice(characters)
        for _ in range(length)
    )


def strength(password):
    score = 0

    if len(password) >= 12:
        score += 1

    if len(password) >= 16:
        score += 1

    if any(c.isdigit() for c in password):
        score += 1

    if any(c.isupper() for c in password):
        score += 1

    if any(c in "!@#$%^&*()-_=+[]{}|;:,.<>?" for c in password):
        score += 1

    levels = [
        ("Fraca", "red"),
        ("Fraca", "red"),
        ("Media", "yellow"),
        ("Boa", "cyan"),
        ("Forte", "green"),
        ("Muito Forte", "bold green"),
    ]

    return levels[min(score, len(levels) - 1)]


def ask_bool(prompt):
    return (
        console.input(
            f"[yellow]{prompt} (S/n): [/yellow]"
        ).strip().lower()
        != "n"
    )


def run():
    console.clear()

    console.print(
        Panel(
            "[bold cyan]Gerador de Senhas[/bold cyan]\n"
            "[dim]Gera credenciais localmente usando o modulo secrets[/dim]",
            border_style="cyan",
        )
    )

    try:
        length = int(
            console.input(
                "[yellow]Comprimento (16): [/yellow]"
            ).strip() or "16"
        )
    except ValueError:
        length = 16

    length = max(8, min(length, 128))

    uppercase = ask_bool("Maiusculas?")
    numbers = ask_bool("Numeros?")
    symbols = ask_bool("Simbolos?")

    try:
        quantity = int(
            console.input(
                "[yellow]Quantidade (5): [/yellow]"
            ).strip() or "5"
        )
    except ValueError:
        quantity = 5

    quantity = max(1, min(quantity, 20))

    table = Table(
        box=box.SIMPLE_HEAVY,
        border_style="cyan",
        header_style="bold magenta",
    )

    table.add_column("#", width=3, justify="center")
    table.add_column("Senha", width=42)
    table.add_column("Forca", width=15, justify="center")

    for index in range(quantity):
        password = generate_password(
            length,
            symbols,
            numbers,
            uppercase,
        )

        label, color = strength(password)

        table.add_row(
            str(index + 1),
            password,
            f"[{color}]{label}[/{color}]",
        )

    console.print(table)

    console.print(
        "\n[dim]As senhas sao apresentadas apenas na sessao atual "
        "e nao sao guardadas pelo PenKit.[/dim]"
    )

    input("\nEnter...")
