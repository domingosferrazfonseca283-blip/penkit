
import time, os, sys, random
from rich.console import Console
from rich.text import Text
from rich.align import Align
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn, SpinnerColumn

console = Console()

BIOS_LINES = [
    ("PenKit BIOS v2.0.4  —  Copyright (C) 2024 PenKit Systems", "dim white"),
    ("CPU: Detecting processor...                    [OK]", "dim green"),
    ("RAM: Memory test...                            [OK]", "dim green"),
    ("STO: Storage controller initialized            [OK]", "dim green"),
    ("NET: Network interface found                   [OK]", "dim green"),
    ("SEC: Security module loaded                    [OK]", "dim green"),
    ("", ""),
    ("Booting PenKit OS...", "bold cyan"),
]

BOOT_MSGS = [
    "[  0.000000] PenKit OS kernel loading",
    "[  0.000123] ACPI: Core revision",
    "[  0.001204] Memory: available",
    "[  0.002341] PCI: Using configuration type 1",
    "[  0.004512] clocksource: tsc-early",
    "[  0.008901] NET: Registered PF_INET protocol family",
    "[  0.012453] Initializing cgroup subsys",
    "[  0.015678] Security framework initialized",
    "[  0.018234] Mount namespace initialized",
    "[  0.021456] Filesystem registry initialized",
    "[  0.024789] Loading PenKit modules...",
    "[  0.028123] Module: cleaner          [LOADED]",
    "[  0.031456] Module: processes        [LOADED]",
    "[  0.034789] Module: passwords        [LOADED]",
    "[  0.038123] Module: organizer        [LOADED]",
    "[  0.041456] Module: diagnostics      [LOADED]",
    "[  0.044789] Module: monitor          [LOADED]",
    "[  0.048123] Module: backup           [LOADED]",
    "[  0.051456] Module: security         [LOADED]",
    "[  0.054789] Module: audit            [LOADED]",
    "[  0.058123] Module: report           [LOADED]",
    "[  0.061456] All modules initialized successfully",
    "[  0.064789] Starting PenKit services...",
    "[  0.068123] Service: filesystem      [READY]",
    "[  0.071456] Service: network         [READY]",
    "[  0.074789] Service: security        [READY]",
    "[  0.078123] PenKit OS — System ready",
]

LOGO = """
██████╗ ███████╗███╗   ██╗██╗  ██╗██╗████████╗
██╔══██╗██╔════╝████╗  ██║██║ ██╔╝██║╚══██╔══╝
██████╔╝█████╗  ██╔██╗ ██║█████╔╝ ██║   ██║
██╔═══╝ ██╔══╝  ██║╚██╗██║██╔═██╗ ██║   ██║
██║     ███████╗██║ ╚████║██║  ██╗██║   ██║
╚═╝     ╚══════╝╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝   ╚═╝
"""

def bip():
    try:
        sys.stdout.write("\a")
        sys.stdout.flush()
    except:
        pass

def tela_bios():
    console.clear()
    time.sleep(0.3)
    for texto, estilo in BIOS_LINES:
        if texto == "":
            console.print()
        else:
            console.print(Text(texto, style=estilo))
        time.sleep(0.08)
    time.sleep(0.5)

def tela_boot():
    console.clear()
    for linha in BOOT_MSGS:
        cor = "dim green" if "[LOADED]" in linha or "[READY]" in linha else "dim white"
        if "All modules" in linha or "System ready" in linha:
            cor = "bold green"
        console.print(Text(linha, style=cor))
        delay = random.uniform(0.03, 0.09)
        time.sleep(delay)
    console.print()
    with Progress(
        TextColumn("  [bold cyan]Loading PenKit OS[/bold cyan]"),
        BarColumn(bar_width=40, style="cyan", complete_style="bold cyan"),
        TextColumn("[bold white]{task.percentage:.0f}%"),
        console=console,
        transient=False,
    ) as progress:
        task = progress.add_task("", total=100)
        for i in range(100):
            time.sleep(0.025)
            progress.advance(task)
    time.sleep(0.5)

def tela_login():
    console.clear()
    console.print()
    console.print(Align.center(Text(LOGO, style="bold cyan")))
    console.print(Align.center(Text("PenKit OS v2.0  —  Canivete Digital Portatil", style="bold magenta")))
    console.print()
    console.print(Align.center(Text("─" * 48, style="dim cyan")))
    console.print()

    tentativas = 0
    while True:
        user = console.input(Align.center("  [bold cyan]login:[/bold cyan] ")).strip()
        if not user:
            continue

        import getpass
        senha = getpass.getpass("  password: ")

        if user.lower() in ["domingos","admin"] and senha == "696969":
            console.print()
            console.print(Align.center(Text("Autenticacao bem sucedida", style="bold green")))
            bip()
            time.sleep(0.8)
            return True
        else:
            tentativas += 1
            console.print(Align.center(Text(f"Acesso negado. ({tentativas}/3)", style="bold red")))
            time.sleep(1)
            if tentativas >= 3:
                console.print(Align.center(Text("Sistema bloqueado.", style="bold red")))
                time.sleep(2)
                sys.exit(1)

def run():
    tela_bios()
    tela_boot()
    tela_login()
