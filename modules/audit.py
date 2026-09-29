
import os, socket, subprocess
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich import box
console = Console()
AVISO="""
╔══════════════════════════════════════════════╗
║      AUDITORIA AUTORIZADA APENAS             ║
║  So usar em redes com autorizacao explicita. ║
║  Toda a actividade fica registada em log.    ║
╚══════════════════════════════════════════════╝"""
PORTAS={21:"FTP",22:"SSH",23:"Telnet",25:"SMTP",53:"DNS",80:"HTTP",
        110:"POP3",443:"HTTPS",445:"SMB",3306:"MySQL",3389:"RDP",
        5432:"PostgreSQL",6379:"Redis",8080:"HTTP-Alt",27017:"MongoDB"}
def get_ip():
    try:
        s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); s.connect(("8.8.8.8",80)); ip=s.getsockname()[0]; s.close(); return ip,ip.rsplit(".",1)[0]
    except: return None,None
def ping(ip):
    try: return subprocess.run(["ping","-c","1","-W","500",ip],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=2).returncode==0
    except: return False
def scan(ip,porta):
    try:
        s=socket.socket(); s.settimeout(0.5); r=s.connect_ex((ip,porta)); s.close(); return r==0
    except: return False
def run():
    console.clear()
    console.print(Panel("[bold red]Auditoria de Rede[/bold red]",border_style="red"))
    console.print(AVISO,style="bold yellow")
    if console.input("[bold red]Digite AUTORIZO para continuar: [/bold red]").strip().upper()!="AUTORIZO":
        input("\nEnter..."); return
    operador=console.input("[yellow]O teu nome: [/yellow]").strip() or "Anonimo"
    ip_local,prefixo=get_ip()
    if not ip_local:
        console.print("[red]Sem rede.[/red]"); input("\nEnter..."); return
    alvo=console.input(f"[yellow]Prefixo de rede (Enter para {prefixo}): [/yellow]").strip() or prefixo
    inicio=datetime.now()
    console.print("\n[cyan]Fase 1 — Descoberta de hosts...[/cyan]")
    vivos=[]
    with Progress(SpinnerColumn(),TextColumn("[cyan]{task.description}"),BarColumn(),TextColumn("{task.completed}/{task.total}"),console=console) as p:
        task=p.add_task("Ping...",total=254)
        for i in range(1,255):
            if ping(f"{alvo}.{i}"): vivos.append(f"{alvo}.{i}")
            p.advance(task)
    if not vivos:
        console.print("[yellow]Nenhum host encontrado.[/yellow]"); input("\nEnter..."); return
    console.print(f"\n[green]{len(vivos)} host(s) encontrado(s)[/green]\n[cyan]Fase 2 — Scan de portas...[/cyan]\n")
    resultados=[]
    with Progress(SpinnerColumn(),TextColumn("[cyan]{task.description}"),BarColumn(),TextColumn("{task.completed}/{task.total}"),console=console) as p:
        task=p.add_task("Portas...",total=len(vivos))
        for ip in vivos:
            try: hn=socket.gethostbyaddr(ip)[0]
            except: hn="?"
            portas=[(pt,sv,scan(ip,pt)) for pt,sv in PORTAS.items()]
            resultados.append({"ip":ip,"hn":hn,"portas":portas}); p.advance(task)
    fim=datetime.now()
    t=Table(box=box.SIMPLE_HEAVY,border_style="red",header_style="bold magenta",title="[bold red]Resultado[/bold red]")
    t.add_column("IP",style="bold cyan"); t.add_column("Hostname",style="dim white"); t.add_column("Portas Abertas",style="bold green")
    log=[f"PENKIT AUDITORIA\nOperador:{operador}\nAlvo:{alvo}.0/24\nInicio:{inicio}\nFim:{fim}\n"+"="*40]
    for h in resultados:
        abertas=[f"{p}({s})" for p,s,a in h["portas"] if a]
        t.add_row(h["ip"],h["hn"],", ".join(abertas) or "[dim]nenhuma[/dim]")
        log.append(f"\nHost:{h['ip']} ({h['hn']})")
        for p,s,a in h["portas"]:
            if a: log.append(f"  [+] {p}/tcp {s}")
    console.print(t)
    os.makedirs("reports",exist_ok=True)
    ts=datetime.now().strftime("%Y%m%d_%H%M%S")
    open(f"reports/auditoria_{ts}.txt","w").write("\n".join(log))
    console.print(Panel(f"[green]Concluido! Log em reports/auditoria_{ts}.txt[/green]",border_style="green"))
    input("\nEnter...")
