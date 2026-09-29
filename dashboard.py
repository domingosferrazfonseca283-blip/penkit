
import os, sys, socket, time
from datetime import datetime
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.live import Live
from rich.align import Align
from rich.rule import Rule
from rich import box

console = Console()

MENU_ITEMS = [
    ("1", "Limpeza",        "cleaner"),
    ("2", "Processos",      "processes"),
    ("3", "Senhas",         "passwords"),
    ("4", "Organizador",    "organizer"),
    ("5", "Diagnostico",    "diagnostics"),
    ("6", "Relatorio HTML", "report"),
    ("7", "Monitor Live",   "monitor"),
    ("8", "Backup",         "backup"),
    ("9", "Seguranca",      "security"),
    ("A", "Auditoria",      "audit"),
    ("B", "PenKit Analyst", "analyst"),
    ("C", "Vault",          "vault"),
    ("D", "Relatorio PDF",  "pdf_report"),
    ("E", "Licenca",        "license"),
    ("F", "Mapa de Rede",   "netmap"),
    ("G", "Visitas",        "visita"),
    ("H", "Scan Total",     "scan_total"),
    ("I", "PDF Cliente",    "pdf_cliente"),
    ("0", "Sair",           None),
]

def get_ip():
    try:
        s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        s.connect(("8.8.8.8",80)); ip=s.getsockname()[0]; s.close(); return ip
    except: return "offline"

def get_ram():
    try:
        info={}
        for line in open("/proc/meminfo"):
            p=line.split()
            if len(p)>=2: info[p[0].rstrip(":")]=int(p[1])
        t=info.get("MemTotal",0)*1024; f=info.get("MemAvailable",0)*1024; u=t-f
        return u,t,(u/t*100) if t else 0
    except: return 0,0,0

def get_disk():
    try:
        st=os.statvfs("/"); t=st.f_blocks*st.f_frsize
        f=st.f_bavail*st.f_frsize; u=t-f
        return u,t,(u/t*100) if t else 0
    except: return 0,0,0

def get_cpu():
    try:
        m="?"; n=0
        for line in open("/proc/cpuinfo"):
            if ("Hardware" in line or "model name" in line) and m=="?":
                m=line.split(":",1)[-1].strip()[:28]
            if "processor" in line: n+=1
        return m,n
    except: return "?",0

def fmt(b):
    for u in ["B","KB","MB","GB"]:
        if b<1024: return f"{b:.1f}{u}"
        b/=1024
    return f"{b:.1f}TB"

def barra(p,w=16):
    f=int(w*p/100); bar="█"*f+"░"*(w-f)
    cor="green" if p<60 else "yellow" if p<85 else "red"
    return f"[{cor}]{bar}[/{cor}]"

def make_topbar():
    agora=datetime.now().strftime("%d/%m/%Y  %H:%M:%S")
    t=Table.grid(expand=True)
    t.add_column(justify="left")
    t.add_column(justify="center")
    t.add_column(justify="right")
    t.add_row(
        Text("  PenKit OS v2.0",style="bold cyan"),
        Text("CANIVETE DIGITAL PORTATIL",style="bold magenta"),
        Text(f"{get_ip()}  |  {agora}  ",style="bold green"),
    )
    return Panel(t,border_style="cyan",padding=(0,0))

def make_menu():
    t=Table(box=box.SIMPLE_HEAVY,border_style="cyan",
            header_style="bold magenta",show_header=True,
            title="[bold cyan]MODULOS[/bold cyan]",expand=True)
    t.add_column("#",width=3,justify="center")
    t.add_column("Funcao")
    CORES=[
        "yellow","red","green","cyan","blue","magenta",
        "bright_cyan","bright_yellow","bright_red","red",
        "bold cyan","bold green","bold magenta","bold yellow",
        "bold blue","dim white"
    ]
    for i,(key,name,_) in enumerate(MENU_ITEMS):
        cor=CORES[i] if i<len(CORES) else "white"
        if key=="0":
            t.add_row("[dim]0[/dim]","[dim]Sair[/dim]")
        else:
            t.add_row(f"[{cor}]{key}[/{cor}]",f"[{cor}]{name}[/{cor}]")
    return t

def make_resources():
    ru,rt,rp=get_ram(); du,dt,dp=get_disk(); cpu_m,cpu_n=get_cpu()
    t=Table(box=box.SIMPLE_HEAVY,border_style="cyan",
            header_style="bold magenta",show_header=True,
            title="[bold cyan]RECURSOS[/bold cyan]",expand=True)
    t.add_column("",style="bold yellow",width=7)
    t.add_column("Barra",width=18)
    t.add_column("%",width=6,justify="right")
    t.add_column("Info",style="dim white")
    t.add_row("RAM",  barra(rp),f"{rp:.1f}",f"{fmt(ru)}/{fmt(rt)}")
    t.add_row("DISCO",barra(dp),f"{dp:.1f}",f"{fmt(du)}/{fmt(dt)}")
    t.add_row("CPU",  "","",f"{cpu_n} nucleos")
    t.add_row("",     "","",f"[dim]{cpu_m}[/dim]")
    return t

def make_sysinfo():
    import platform
    try:
        secs=float(open("/proc/uptime").read().split()[0])
        h,r=divmod(int(secs),3600); m=r//60; d,h2=divmod(h,24)
        uptime=f"{d}d {h2}h {m}m"
    except: uptime="?"
    t=Table(box=box.SIMPLE_HEAVY,border_style="cyan",
            header_style="bold magenta",show_header=True,
            title="[bold cyan]SISTEMA[/bold cyan]",expand=True)
    t.add_column("Campo",style="bold yellow",width=10)
    t.add_column("Valor",style="white")
    t.add_row("Host",  socket.gethostname())
    t.add_row("IP",    get_ip())
    t.add_row("OS",    f"{platform.system()} {platform.release()}")
    t.add_row("Arch",  platform.machine())
    t.add_row("Uptime",uptime)
    return t

def make_layout():
    layout=Layout()
    layout.split_column(
        Layout(name="top",   size=3),
        Layout(name="middle",ratio=1),
        Layout(name="bottom",size=3),
    )
    layout["middle"].split_row(
        Layout(name="menu",     ratio=2),
        Layout(name="resources",ratio=3),
        Layout(name="sysinfo",  ratio=3),
    )
    layout["top"].update(make_topbar())
    layout["middle"]["menu"].update(make_menu())
    layout["middle"]["resources"].update(make_resources())
    layout["middle"]["sysinfo"].update(make_sysinfo())
    layout["bottom"].update(Panel(
        Align.center(Text(
            "  [1-9] Modulo   [A-F] Modulos extra   [0] Sair  ",
            style="bold cyan"
        )),
        border_style="cyan"
    ))
    return layout

def run_module(module_name):
    try:
        mod=__import__(f"modules.{module_name}",fromlist=[module_name])
        mod.run()
    except ImportError as e:
        console.print(Panel(f"[red]Modulo nao encontrado: {e}[/red]",border_style="red"))
        input("\nEnter...")
    except AttributeError:
        console.print(Panel(f"[yellow]Ainda nao implementado.[/yellow]",border_style="yellow"))
        input("\nEnter...")
    except Exception as e:
        console.print(Panel(f"[red]Erro: {e}[/red]",border_style="red"))
        input("\nEnter...")

def run():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))

    while True:
        with Live(make_layout(),console=console,
                  refresh_per_second=2,screen=True) as live:
            while True:
                live.update(make_layout())
                choice=console.input("\n[bold cyan]  OS> [/bold cyan]").strip().upper()
                if choice: break

        if choice=="0":
            console.clear()
            console.print(Panel("[bold cyan]PenKit OS encerrado. Ate logo.[/bold cyan]",border_style="cyan"))
            break

        matched=False
        for key,_,module_name in MENU_ITEMS:
            if choice==key and module_name:
                matched=True
                console.clear()
                run_module(module_name)
                break

        if not matched and choice!="0":
            console.clear()
            console.print(f"[red]Opcao invalida: {choice}[/red]")
            time.sleep(1)
