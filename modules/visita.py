
import os, json
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.align import Align
from rich.text import Text
from rich import box

console = Console()

VISITAS_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", ".visitas.json"
)

def carregar_visitas():
    if not os.path.exists(VISITAS_PATH):
        return []
    try:
        return json.load(open(VISITAS_PATH, "r", encoding="utf-8"))
    except: return []

def guardar_visitas(visitas):
    json.dump(visitas, open(VISITAS_PATH, "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)

def nova_visita():
    console.clear()
    console.print(Panel("[bold cyan]Nova Visita[/bold cyan]", border_style="cyan"))
    console.print()

    empresa  = console.input("[yellow]Nome da empresa: [/yellow]").strip()
    if not empresa: return None

    contacto = console.input("[yellow]Contacto (nome/telefone): [/yellow]").strip()
    morada   = console.input("[yellow]Morada/local: [/yellow]").strip()
    motivo   = console.input("[yellow]Motivo da visita: [/yellow]").strip()

    visita = {
        "id":        datetime.now().strftime("%Y%m%d%H%M%S"),
        "empresa":   empresa,
        "contacto":  contacto,
        "morada":    morada,
        "motivo":    motivo,
        "inicio":    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "fim":       None,
        "acoes":     [],
        "observacoes":"",
        "estado":    "em_curso",
    }

    visitas = carregar_visitas()
    visitas.append(visita)
    guardar_visitas(visitas)

    console.print()
    console.print(Panel(
        f"[bold green]Visita iniciada![/bold green]\n"
        f"Empresa : [cyan]{empresa}[/cyan]\n"
        f"Inicio  : [cyan]{visita['inicio']}[/cyan]",
        border_style="green"
    ))
    input("\nEnter para continuar...")
    return visita["id"]

def registar_acao(visita_id, acao):
    visitas = carregar_visitas()
    for v in visitas:
        if v["id"] == visita_id:
            v["acoes"].append({
                "hora": datetime.now().strftime("%H:%M:%S"),
                "acao": acao
            })
            guardar_visitas(visitas)
            return

def encerrar_visita(visita_id):
    console.clear()
    console.print(Panel("[bold cyan]Encerrar Visita[/bold cyan]", border_style="cyan"))
    console.print()

    obs = console.input("[yellow]Observacoes finais: [/yellow]").strip()

    visitas = carregar_visitas()
    for v in visitas:
        if v["id"] == visita_id:
            v["fim"]          = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            v["observacoes"]  = obs
            v["estado"]       = "concluida"

            inicio = datetime.strptime(v["inicio"], "%Y-%m-%d %H:%M:%S")
            fim    = datetime.strptime(v["fim"],    "%Y-%m-%d %H:%M:%S")
            delta  = fim - inicio
            mins   = int(delta.total_seconds() / 60)

            guardar_visitas(visitas)
            console.print(Panel(
                f"[bold green]Visita encerrada![/bold green]\n"
                f"Duracao : [cyan]{mins} minutos[/cyan]\n"
                f"Accoes  : [cyan]{len(v['acoes'])}[/cyan]",
                border_style="green"
            ))
            input("\nEnter para continuar...")
            return v
    return None

def listar_visitas():
    visitas = carregar_visitas()
    if not visitas:
        console.print("[dim]Nenhuma visita registada.[/dim]")
        return

    t = Table(box=box.SIMPLE_HEAVY, border_style="cyan",
              header_style="bold magenta", expand=True,
              title="[bold cyan]HISTORICO DE VISITAS[/bold cyan]")
    t.add_column("#",        width=4,  justify="center", style="bold yellow")
    t.add_column("Empresa",  width=20, style="bold white")
    t.add_column("Data",     width=12, style="cyan")
    t.add_column("Duracao",  width=10, style="dim white")
    t.add_column("Accoes",   width=8,  justify="center", style="green")
    t.add_column("Estado",   width=12, justify="center")

    for i, v in enumerate(reversed(visitas), 1):
        if v.get("fim") and v.get("inicio"):
            try:
                inicio = datetime.strptime(v["inicio"], "%Y-%m-%d %H:%M:%S")
                fim    = datetime.strptime(v["fim"],    "%Y-%m-%d %H:%M:%S")
                mins   = int((fim-inicio).total_seconds()/60)
                dur    = f"{mins}min"
            except: dur = "?"
        else:
            dur = "em curso"

        estado = v.get("estado","?")
        cor_estado = "green" if estado=="concluida" else "yellow"
        data = v["inicio"][:10] if v.get("inicio") else "?"

        t.add_row(
            str(i),
            v.get("empresa","?"),
            data,
            dur,
            str(len(v.get("acoes",[]))),
            f"[{cor_estado}]{estado}[/{cor_estado}]"
        )

    console.print(t)

def ver_visita(idx):
    visitas = carregar_visitas()
    visitas_rev = list(reversed(visitas))
    if idx < 1 or idx > len(visitas_rev):
        console.print("[red]Numero invalido.[/red]")
        return

    v = visitas_rev[idx-1]
    console.clear()
    console.print(Panel(
        f"[bold cyan]{v.get('empresa','?')}[/bold cyan]\n"
        f"[dim]Contacto: {v.get('contacto','?')} | Morada: {v.get('morada','?')}[/dim]\n"
        f"Motivo: {v.get('motivo','?')}\n"
        f"Inicio: {v.get('inicio','?')} | Fim: {v.get('fim','em curso')}\n"
        f"Observacoes: {v.get('observacoes','—')}",
        border_style="cyan",
        title="[bold]Detalhe da Visita[/bold]"
    ))
    console.print()

    acoes = v.get("acoes", [])
    if acoes:
        t = Table(box=box.SIMPLE_HEAVY, border_style="cyan",
                  header_style="bold magenta",
                  title="[bold cyan]Accoes Realizadas[/bold cyan]")
        t.add_column("Hora",  style="bold yellow", width=10)
        t.add_column("Accao", style="white")
        for a in acoes:
            t.add_row(a.get("hora","?"), a.get("acao","?"))
        console.print(t)
    else:
        console.print("[dim]Nenhuma accao registada.[/dim]")

def run():
    console.clear()
    console.print(Panel(
        Align.center(Text("PENKIT VISITAS", style="bold cyan")),
        subtitle="[dim]Gestao de visitas a clientes[/dim]",
        border_style="cyan"
    ))
    console.print()

    while True:
        listar_visitas()
        console.print()
        console.print("[bold yellow]1[/bold yellow] Nova visita")
        console.print("[bold yellow]2[/bold yellow] Ver detalhe de visita")
        console.print("[bold yellow]3[/bold yellow] Encerrar visita em curso")
        console.print("[bold yellow]4[/bold yellow] Registar accao em visita activa")
        console.print("[bold red]0[/bold red] Voltar")
        console.print()

        op = console.input("[bold cyan]  > [/bold cyan]").strip()

        if op == "0":
            break

        elif op == "1":
            nova_visita()

        elif op == "2":
            visitas = carregar_visitas()
            if not visitas:
                console.print("[yellow]Sem visitas.[/yellow]")
                input("\nEnter..."); continue
            num = console.input("[yellow]Numero da visita: [/yellow]").strip()
            try: ver_visita(int(num))
            except: console.print("[red]Numero invalido.[/red]")
            input("\nEnter para continuar...")

        elif op == "3":
            visitas = carregar_visitas()
            em_curso = [v for v in visitas if v.get("estado")=="em_curso"]
            if not em_curso:
                console.print("[yellow]Nenhuma visita em curso.[/yellow]")
                input("\nEnter..."); continue
            v = em_curso[-1]
            console.print(f"[dim]Visita activa: {v['empresa']}[/dim]")
            encerrar_visita(v["id"])

        elif op == "4":
            visitas = carregar_visitas()
            em_curso = [v for v in visitas if v.get("estado")=="em_curso"]
            if not em_curso:
                console.print("[yellow]Nenhuma visita em curso.[/yellow]")
                input("\nEnter..."); continue
            v = em_curso[-1]
            acao = console.input(f"[yellow]Accao realizada em {v['empresa']}: [/yellow]").strip()
            if acao:
                registar_acao(v["id"], acao)
                console.print("[green]Accao registada.[/green]")
            input("\nEnter...")

        console.clear()
        console.print(Panel(
            Align.center(Text("PENKIT VISITAS", style="bold cyan")),
            subtitle="[dim]Gestao de visitas a clientes[/dim]",
            border_style="cyan"
        ))
        console.print()
