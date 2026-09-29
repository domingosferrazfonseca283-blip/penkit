
import os, json, hashlib, base64, socket, uuid
from datetime import datetime, date
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.align import Align
from rich.text import Text
from rich import box

console = Console()

LICENSE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", ".license"
)
MASTER_KEY = "PENKIT-ANGOLA-2024-MDF"

def gerar_hardware_id():
    try:
        dados = socket.gethostname() + str(uuid.getnode())
        return hashlib.sha256(dados.encode()).hexdigest()[:16].upper()
    except:
        return "UNKNOWN"

def gerar_chave_licenca(cliente, validade, hw_id, prefixo="STD"):
    payload = f"{cliente}:{validade}:{hw_id}:{MASTER_KEY}:{prefixo}"
    hash_val = hashlib.sha256(payload.encode()).hexdigest()[:24].upper()
    partes = [hash_val[i:i+6] for i in range(0, 24, 6)]
    return f"PK-{prefixo}-" + "-".join(partes)

def validar_chave(chave, cliente, validade, hw_id, prefixo="STD"):
    esperada = gerar_chave_licenca(cliente, validade, hw_id, prefixo)
    return chave.strip().upper() == esperada.upper()

def carregar_licenca():
    if not os.path.exists(LICENSE_PATH):
        return None
    try:
        with open(LICENSE_PATH, "r") as f:
            return json.load(f)
    except:
        return None

def guardar_licenca(dados):
    with open(LICENSE_PATH, "w") as f:
        json.dump(dados, f, indent=2)

def verificar_validade(licenca):
    try:
        validade = datetime.strptime(licenca["validade"], "%Y-%m-%d").date()
        hoje = date.today()
        dias = (validade - hoje).days
        return dias, validade
    except:
        return -1, None

def estado_licenca():
    lic = carregar_licenca()
    if not lic:
        return "sem_licenca", None, 0
    hw_id = gerar_hardware_id()
    if not validar_chave(
        lic.get("chave",""),
        lic.get("cliente",""),
        lic.get("validade",""),
        hw_id,
        lic.get("prefixo","STD")
    ):
        return "invalida", lic, 0
    dias, validade = verificar_validade(lic)
    if dias < 0:
        return "expirada", lic, dias
    return "activa", lic, dias

def mostrar_estado():
    estado, lic, dias = estado_licenca()
    hw_id = gerar_hardware_id()

    if estado == "activa":
        cor = "green"
        icon = "✓ LICENCA ACTIVA"
        detalhe = f"Expira em {dias} dia(s)"
    elif estado == "expirada":
        cor = "yellow"
        icon = "⚠ LICENCA EXPIRADA"
        detalhe = f"Expirou ha {abs(dias)} dia(s)"
    elif estado == "invalida":
        cor = "red"
        icon = "✗ LICENCA INVALIDA"
        detalhe = "Chave nao corresponde a este sistema"
    else:
        cor = "red"
        icon = "✗ SEM LICENCA"
        detalhe = "Instala uma licenca valida"

    t = Table(box=box.SIMPLE_HEAVY, border_style=cor,
              header_style=f"bold {cor}", expand=True)
    t.add_column("Campo", style=f"bold {cor}", width=16)
    t.add_column("Valor", style="white")

    t.add_row("Estado", f"[bold {cor}]{icon}[/bold {cor}]")
    t.add_row("Hardware ID", hw_id)

    if lic:
        t.add_row("Cliente",   lic.get("cliente", "?"))
        t.add_row("Tipo",      lic.get("prefixo", "STD"))
        t.add_row("Validade",  lic.get("validade", "?"))
        t.add_row("Detalhe",   detalhe)
    else:
        t.add_row("Detalhe", detalhe)

    console.print(t)
    return estado

def instalar_licenca():
    console.print()
    console.print("[dim]Para obteres uma licenca contacta o desenvolvedor.[/dim]")
    console.print()
    hw_id = gerar_hardware_id()
    console.print(f"[bold cyan]O teu Hardware ID:[/bold cyan] [bold white]{hw_id}[/bold white]")
    console.print("[dim]Envia este ID ao desenvolvedor para receberes a tua chave.[/dim]")
    console.print()

    cliente = console.input("[yellow]Nome do cliente/empresa: [/yellow]").strip()
    validade = console.input("[yellow]Validade (AAAA-MM-DD): [/yellow]").strip()
    prefixo_input = console.input("[yellow]Tipo (STD/PRO/ENT, Enter=STD): [/yellow]").strip().upper()
    prefixo = prefixo_input if prefixo_input in ["STD","PRO","ENT"] else "STD"
    chave = console.input("[yellow]Chave de licenca: [/yellow]").strip().upper()

    if validar_chave(chave, cliente, validade, hw_id, prefixo):
        dados = {
            "cliente":  cliente,
            "validade": validade,
            "prefixo":  prefixo,
            "chave":    chave,
            "hw_id":    hw_id,
            "instalada": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        guardar_licenca(dados)
        console.print(Panel(
            f"[bold green]Licenca instalada com sucesso![/bold green]\n"
            f"Cliente: {cliente} | Validade: {validade}",
            border_style="green"
        ))
    else:
        console.print(Panel(
            "[bold red]Chave invalida.[/bold red]\n"
            "Verifica o Hardware ID e os dados fornecidos.",
            border_style="red"
        ))

def gerar_licenca_admin():
    console.print()
    console.print("[bold magenta]MODO ADMINISTRADOR — Gerador de Licencas[/bold magenta]")
    console.print()

    senha = console.input("[yellow]Senha admin: [/yellow]").strip()
    if hashlib.sha256(senha.encode()).hexdigest() != hashlib.sha256("penkit-admin-mdf".encode()).hexdigest():
        console.print("[red]Senha incorrecta.[/red]")
        input("\nEnter..."); return

    hw_id_alvo = console.input("[yellow]Hardware ID do cliente: [/yellow]").strip().upper()
    cliente = console.input("[yellow]Nome do cliente: [/yellow]").strip()
    validade = console.input("[yellow]Validade (AAAA-MM-DD): [/yellow]").strip()
    prefixo_input = console.input("[yellow]Tipo (STD/PRO/ENT): [/yellow]").strip().upper()
    prefixo = prefixo_input if prefixo_input in ["STD","PRO","ENT"] else "STD"

    chave = gerar_chave_licenca(cliente, validade, hw_id_alvo, prefixo)

    console.print()
    console.print(Panel(
        f"[bold green]LICENCA GERADA[/bold green]\n\n"
        f"Cliente  : [cyan]{cliente}[/cyan]\n"
        f"Tipo     : [cyan]{prefixo}[/cyan]\n"
        f"Validade : [cyan]{validade}[/cyan]\n"
        f"HW ID    : [cyan]{hw_id_alvo}[/cyan]\n\n"
        f"[bold yellow]CHAVE:[/bold yellow]\n"
        f"[bold white]{chave}[/bold white]",
        border_style="green", title="[bold]Envia esta chave ao cliente[/bold]"
    ))

def run():
    console.clear()
    console.print(Panel(
        Align.center(Text("PENKIT LICENSE", style="bold cyan")),
        subtitle="[dim]Sistema de licenciamento[/dim]",
        border_style="cyan"
    ))
    console.print()

    estado = mostrar_estado()
    console.print()

    console.print("[bold yellow]1[/bold yellow] Instalar licenca")
    console.print("[bold yellow]2[/bold yellow] Gerar licenca (admin)")
    console.print("[bold red]0[/bold red] Voltar")
    console.print()

    op = console.input("[bold cyan]  > [/bold cyan]").strip()

    if op == "1":
        instalar_licenca()
    elif op == "2":
        gerar_licenca_admin()

    input("\nEnter para voltar...")
