
import os, sys, socket, platform, subprocess, threading, time
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.align import Align
from rich.text import Text
from rich.columns import Columns
from rich.rule import Rule
from rich import box

console = Console()

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
                m=line.split(":",1)[-1].strip()[:40]
            if "processor" in line: n+=1
        return m,n
    except: return "?",0

def get_uptime():
    try:
        secs=float(open("/proc/uptime").read().split()[0])
        h,r=divmod(int(secs),3600); m=r//60; d,h=divmod(h,24)
        return f"{d}d {h}h {m}m"
    except: return "?"

def fmt(b):
    for u in ["B","KB","MB","GB"]:
        if b<1024: return f"{b:.1f} {u}"
        b/=1024
    return f"{b:.1f} TB"

def barra(p,w=16):
    f=int(w*p/100); bar="█"*f+"░"*(w-f)
    cor="green" if p<60 else "yellow" if p<85 else "red"
    return f"[{cor}]{bar}[/{cor}]"

def ping(ip):
    try:
        r=subprocess.run(["ping","-c","1","-W","400",ip],
            stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=1)
        return r.returncode==0
    except: return False

def scan_hosts(prefixo):
    encontrados=[]
    lock=threading.Lock()
    def check(i):
        ip=f"{prefixo}.{i}"
        if ping(ip):
            with lock: encontrados.append(ip)
    threads=[threading.Thread(target=check,args=(i,),daemon=True) for i in range(1,255)]
    for t in threads: t.start()
    for t in threads: t.join(timeout=1.5)
    return sorted(encontrados, key=lambda x: int(x.split(".")[-1]))

def scan_portas(ip):
    PORTAS={21:"FTP",22:"SSH",23:"Telnet",25:"SMTP",
            80:"HTTP",443:"HTTPS",3306:"MySQL",
            3389:"RDP",5432:"PostgreSQL",8080:"HTTP-Alt"}
    abertas=[]
    for p,nome in PORTAS.items():
        try:
            s=socket.socket(); s.settimeout(0.4)
            if s.connect_ex((ip,p))==0: abertas.append((p,nome))
            s.close()
        except: pass
    return abertas

def detectar_problemas(ram_p, disk_p, portas_locais, hosts):
    problemas=[]
    avisos=[]

    if ram_p > 90:
        problemas.append("RAM critica — risco de colapso do sistema")
    elif ram_p > 75:
        avisos.append("RAM elevada — desempenho degradado")

    if disk_p > 90:
        problemas.append("Disco quase cheio — sistema pode parar")
    elif disk_p > 75:
        avisos.append("Disco a encher — liberta espaco em breve")

    PORTAS_CRITICAS={23:"Telnet (sem cifra)",4444:"Backdoor",
                     5555:"ADB exposto",21:"FTP (sem cifra)"}
    for p,nome in portas_locais:
        if p in PORTAS_CRITICAS:
            problemas.append(f"Porta critica aberta: {p} ({PORTAS_CRITICAS[p]})")
        elif p == 3306:
            avisos.append("MySQL exposto — verifica autenticacao")
        elif p == 3389:
            avisos.append("RDP activo — garante senha forte")

    if len(hosts) > 20:
        avisos.append(f"Rede densa: {len(hosts)} dispositivos — verifica intrusos")
    elif len(hosts) > 50:
        problemas.append(f"Rede muito densa: {len(hosts)} dispositivos")

    return problemas, avisos

def run():
    console.clear()
    console.print(Panel(
        Align.center(Text("SCAN TOTAL", style="bold cyan")),
        subtitle="[dim]Diagnostico completo do sistema e rede[/dim]",
        border_style="cyan"
    ))
    console.print()

    empresa = console.input(
        "[yellow]Nome da empresa (Enter para ignorar): [/yellow]"
    ).strip() or "Cliente"

    inicio = datetime.now()
    console.print()

    resultados = {}

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold cyan]{task.description}"),
        BarColumn(),
        TextColumn("[bold white]{task.percentage:.0f}%"),
        console=console,
    ) as progress:
        task = progress.add_task("A executar scan completo...", total=6)

        # 1 — Sistema
        progress.update(task, description="Sistema e hardware...")
        cpu_m, cpu_n = get_cpu()
        resultados["cpu_modelo"]  = cpu_m
        resultados["cpu_nucleos"] = cpu_n
        resultados["os"]   = f"{platform.system()} {platform.release()}"
        resultados["arch"] = platform.machine()
        resultados["host"] = socket.gethostname()
        resultados["uptime"] = get_uptime()
        time.sleep(0.3)
        progress.advance(task)

        # 2 — RAM
        progress.update(task, description="Memoria RAM...")
        ru,rt,rp = get_ram()
        resultados["ram"] = (ru,rt,rp)
        time.sleep(0.3)
        progress.advance(task)

        # 3 — Disco
        progress.update(task, description="Disco e armazenamento...")
        du,dt,dp = get_disk()
        resultados["disk"] = (du,dt,dp)
        time.sleep(0.3)
        progress.advance(task)

        # 4 — Rede local
        progress.update(task, description="Interfaces de rede...")
        ip = get_ip()
        resultados["ip"] = ip
        ifaces = {}
        try:
            for line in open("/proc/net/dev").readlines()[2:]:
                p=line.split()
                if len(p)>=10:
                    nome=p[0].rstrip(":")
                    if int(p[1])>0 or int(p[9])>0:
                        ifaces[nome]=(int(p[1]),int(p[9]))
        except: pass
        resultados["ifaces"] = ifaces
        time.sleep(0.3)
        progress.advance(task)

        # 5 — Portas locais
        progress.update(task, description="Portas abertas localmente...")
        portas_locais = scan_portas("127.0.0.1")
        resultados["portas_locais"] = portas_locais
        time.sleep(0.3)
        progress.advance(task)

        # 6 — Hosts na rede
        progress.update(task, description="Dispositivos na rede...")
        prefixo = ip.rsplit(".",1)[0] if ip != "offline" else "192.168.1"
        hosts = scan_hosts(prefixo)
        resultados["hosts"]   = hosts
        resultados["prefixo"] = prefixo
        progress.advance(task)

    duracao = int((datetime.now()-inicio).total_seconds())
    console.clear()

    # --- RESULTADOS ---
    ru,rt,rp = resultados["ram"]
    du,dt,dp = resultados["disk"]
    problemas, avisos = detectar_problemas(
        rp, dp, resultados["portas_locais"], resultados["hosts"]
    )
    score = max(0, 100 - len(problemas)*20 - len(avisos)*8)
    cor_score = "green" if score>=80 else "yellow" if score>=60 else "red"

    # Header
    console.print(Panel(
        Align.center(Text(
            f"SCAN TOTAL — {empresa}  |  {datetime.now().strftime('%d/%m/%Y %H:%M')}  |  {duracao}s",
            style="bold cyan"
        )),
        border_style="cyan"
    ))
    console.print()

    # Pontuacao
    console.print(Align.center(Text(
        f"Pontuacao de Saude: {score}/100",
        style=f"bold {cor_score}"
    )))
    console.print()
    console.print(Rule(style="dim cyan"))
    console.print()

    # Sistema
    t1=Table(box=box.SIMPLE_HEAVY,border_style="cyan",
             header_style="bold magenta",
             title="[bold cyan]SISTEMA[/bold cyan]",expand=True)
    t1.add_column("Campo",style="bold yellow",width=12)
    t1.add_column("Valor",style="white")
    t1.add_row("Host",    resultados["host"])
    t1.add_row("IP",      resultados["ip"])
    t1.add_row("OS",      resultados["os"])
    t1.add_row("CPU",     f"{resultados['cpu_modelo']} ({resultados['cpu_nucleos']} nucleos)")
    t1.add_row("Uptime",  resultados["uptime"])

    # Recursos
    t2=Table(box=box.SIMPLE_HEAVY,border_style="cyan",
             header_style="bold magenta",
             title="[bold cyan]RECURSOS[/bold cyan]",expand=True)
    t2.add_column("",style="bold yellow",width=7)
    t2.add_column("Barra",width=18)
    t2.add_column("Uso",style="dim white")
    t2.add_row("RAM",  barra(rp), f"{rp:.1f}% ({fmt(ru)}/{fmt(rt)})")
    t2.add_row("DISCO",barra(dp), f"{dp:.1f}% ({fmt(du)}/{fmt(dt)})")

    console.print(Columns([t1,t2]))
    console.print()

    # Rede
    t3=Table(box=box.SIMPLE_HEAVY,border_style="cyan",
             header_style="bold magenta",
             title=f"[bold cyan]REDE — {len(resultados['hosts'])} dispositivo(s)[/bold cyan]",
             expand=True)
    t3.add_column("IP",style="bold cyan")
    t3.add_column("Estado",style="green",justify="center")
    for h in resultados["hosts"][:10]:
        t3.add_row(h,"[green]ONLINE[/green]")
    if len(resultados["hosts"])>10:
        t3.add_row(f"[dim]+{len(resultados['hosts'])-10} mais...[/dim]","")

    # Portas
    t4=Table(box=box.SIMPLE_HEAVY,border_style="cyan",
             header_style="bold magenta",
             title="[bold cyan]PORTAS ABERTAS[/bold cyan]",expand=True)
    t4.add_column("Porta",style="bold yellow",width=8)
    t4.add_column("Servico",style="white")
    if resultados["portas_locais"]:
        for p,nome in resultados["portas_locais"]:
            t4.add_row(str(p),nome)
    else:
        t4.add_row("[dim]Nenhuma[/dim]","")

    console.print(Columns([t3,t4]))
    console.print()

    # Problemas
    if problemas or avisos:
        t5=Table(box=box.SIMPLE_HEAVY,border_style="red",
                 header_style="bold red",
                 title="[bold red]PROBLEMAS DETECTADOS[/bold red]",expand=True)
        t5.add_column("Nivel",width=10,justify="center")
        t5.add_column("Descricao",style="white")
        for p in problemas:
            t5.add_row("[bold red]CRITICO[/bold red]",p)
        for a in avisos:
            t5.add_row("[bold yellow]AVISO[/bold yellow]",a)
        console.print(t5)
        console.print()
    else:
        console.print(Panel(
            "[bold green]Nenhum problema critico detectado.[/bold green]",
            border_style="green"
        ))
        console.print()

    # Guardar log
    os.makedirs("reports",exist_ok=True)
    ts=datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path=f"reports/scan_total_{ts}.txt"
    with open(log_path,"w",encoding="utf-8") as f:
        f.write(f"PENKIT SCAN TOTAL\n")
        f.write(f"Empresa : {empresa}\n")
        f.write(f"Data    : {datetime.now()}\n")
        f.write(f"Score   : {score}/100\n")
        f.write("="*50+"\n")
        f.write(f"Host: {resultados['host']} | IP: {resultados['ip']}\n")
        f.write(f"RAM: {rp:.1f}% | Disco: {dp:.1f}%\n")
        f.write(f"Dispositivos na rede: {len(resultados['hosts'])}\n")
        f.write("\nPROBLEMAS:\n")
        for p in problemas: f.write(f"  [!] {p}\n")
        f.write("\nAVISOS:\n")
        for a in avisos: f.write(f"  [~] {a}\n")

    console.print(f"[dim]Relatorio guardado: {os.path.abspath(log_path)}[/dim]")
    console.print()

    # Registar na visita activa se existir
    try:
        sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from modules.visita import carregar_visitas, registar_acao
        visitas=[v for v in carregar_visitas() if v.get("estado")=="em_curso"]
        if visitas:
            registar_acao(visitas[-1]["id"],
                f"Scan Total — Score {score}/100 — {len(problemas)} problema(s)")
            console.print(f"[dim]Accao registada na visita: {visitas[-1]['empresa']}[/dim]")
    except: pass

    input("\nEnter para voltar...")
