
import os, time, socket, platform
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.align import Align
from rich.rule import Rule
from rich import box

console = Console()

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

def get_uptime_secs():
    try: return float(open("/proc/uptime").read().split()[0])
    except: return 0

def get_cpu_info():
    try:
        m="?"; n=0
        for line in open("/proc/cpuinfo"):
            if ("Hardware" in line or "model name" in line) and m=="?":
                m=line.split(":",1)[-1].strip()[:40]
            if "processor" in line: n+=1
        return m, n
    except: return "?", 0

def get_ip():
    try:
        s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        s.connect(("8.8.8.8",80)); ip=s.getsockname()[0]; s.close(); return ip
    except: return None

def fmt(b):
    for u in ["B","KB","MB","GB"]:
        if b<1024: return f"{b:.1f} {u}"
        b/=1024
    return f"{b:.1f} TB"

def scan_portas_suspeitas():
    abertas=[]
    for p in [21,22,23,25,3306,5432,6379,27017,4444,5555,8080]:
        try:
            s=socket.socket(); s.settimeout(0.3)
            if s.connect_ex(("127.0.0.1",p))==0: abertas.append(p)
            s.close()
        except: pass
    return abertas

PORTAS_NOMES={
    21:"FTP",22:"SSH",23:"Telnet (inseguro)",25:"SMTP",
    3306:"MySQL",5432:"PostgreSQL",6379:"Redis",
    27017:"MongoDB",4444:"Suspeita",5555:"ADB/Suspeita",
    8080:"HTTP alternativo"
}

PORTAS_RISCO={
    23:"critico",4444:"critico",5555:"alto",
    21:"alto",3306:"medio",5432:"medio",
    6379:"medio",27017:"medio",
    22:"baixo",25:"baixo",8080:"baixo"
}

def analisar_ram(usado,total,percent):
    obs=[]; score=100
    if percent>90:
        obs.append(("critico","RAM critica a {:.0f}% — sistema em risco de congelamento.".format(percent)))
        score-=30
    elif percent>75:
        obs.append(("alto","RAM elevada a {:.0f}% — desempenho pode degradar.".format(percent)))
        score-=15
    elif percent>60:
        obs.append(("medio","RAM a {:.0f}% — uso moderado, dentro do aceitavel.".format(percent)))
        score-=5
    else:
        obs.append(("ok","RAM a {:.0f}% — excelente. Sistema com folga.".format(percent)))
    return obs, score

def analisar_disco(usado,total,percent):
    obs=[]; score=100
    livre=total-usado
    if percent>95:
        obs.append(("critico","Disco quase cheio a {:.0f}%! Sistema pode parar de funcionar.".format(percent)))
        score-=40
    elif percent>85:
        obs.append(("alto","Disco a {:.0f}% — liberta espaco brevemente.".format(percent)))
        score-=20
    elif percent>70:
        obs.append(("medio","Disco a {:.0f}% — ainda seguro mas a encher.".format(percent)))
        score-=8
    else:
        obs.append(("ok","Disco a {:.0f}% — espaco suficiente disponivel.".format(percent)))
    return obs, score

def analisar_rede(portas):
    obs=[]; score=100
    ip=get_ip()
    if not ip:
        obs.append(("medio","Sem ligacao a internet detectada."))
        score-=5
    else:
        obs.append(("ok",f"Rede activa — IP: {ip}"))

    for p in portas:
        nome=PORTAS_NOMES.get(p,str(p))
        risco=PORTAS_RISCO.get(p,"medio")
        if risco=="critico":
            obs.append(("critico",f"Porta {p} ({nome}) aberta — risco critico! Fecha imediatamente."))
            score-=25
        elif risco=="alto":
            obs.append(("alto",f"Porta {p} ({nome}) aberta — verifica se e necessaria."))
            score-=15
        elif risco=="medio":
            obs.append(("medio",f"Porta {p} ({nome}) aberta — garante autenticacao activa."))
            score-=8
        else:
            obs.append(("baixo",f"Porta {p} ({nome}) aberta — risco baixo."))
            score-=3
    return obs, score

def analisar_uptime(secs):
    obs=[]; score=100
    dias=secs/86400
    if dias>30:
        obs.append(("medio",f"Sistema ligado ha {dias:.0f} dias — considera reiniciar para aplicar actualizacoes."))
        score-=5
    elif dias>7:
        obs.append(("baixo",f"Sistema ligado ha {dias:.0f} dias — normal para servidores."))
    else:
        obs.append(("ok",f"Uptime de {dias:.1f} dias — sistema recente."))
    return obs, score

def gerar_recomendacoes(todas_obs):
    recs=[]
    criticos=[o for n,o in todas_obs if n=="critico"]
    altos=[o for n,o in todas_obs if n=="alto"]
    medios=[o for n,o in todas_obs if n=="medio"]

    if criticos:
        recs.append(("[bold red]URGENTE[/bold red]","Resolve os problemas criticos antes de continuar."))
    if 3306 in [p for p in scan_portas_suspeitas()]:
        recs.append(("[bold yellow]SEGURANCA[/bold yellow]","MySQL exposto e o vector de ataque mais comum em PMEs angolanas."))
    if altos:
        recs.append(("[bold yellow]RECOMENDADO[/bold yellow]",f"{len(altos)} problema(s) de prioridade alta para resolver esta semana."))
    if not criticos and not altos:
        recs.append(("[bold green]SISTEMA SAUDAVEL[/bold green]","Nenhuma accao urgente necessaria. Mantm monitorizacao regular."))
    recs.append(("[bold cyan]DICA[/bold cyan]","Usa o modulo Backup para guardar os teus dados antes de qualquer intervencao."))
    return recs

COR_NIVEL={
    "critico":"bold red",
    "alto":"bold yellow",
    "medio":"yellow",
    "baixo":"dim white",
    "ok":"bold green",
}

ICONE_NIVEL={
    "critico":"[!]",
    "alto":"[^]",
    "medio":"[~]",
    "baixo":"[-]",
    "ok":"[+]",
}

def animacao_analise():
    import time
    fases=[
        "Recolhendo dados do sistema...",
        "Analisando memoria e disco...",
        "Verificando portas de rede...",
        "Calculando pontuacao de saude...",
        "Gerando relatorio inteligente...",
    ]
    for fase in fases:
        console.print(f"[dim cyan]  {fase}[/dim cyan]")
        time.sleep(0.4)
    console.print()

def run():
    console.clear()
    console.print(Panel(
        Align.center(Text("PENKIT ANALYST", style="bold cyan")),
        subtitle="[dim]Motor de analise inteligente[/dim]",
        border_style="cyan"
    ))
    console.print()
    animacao_analise()

    # Recolher dados
    ru,rt,rp = get_ram()
    du,dt,dp = get_disk()
    uptime   = get_uptime_secs()
    portas   = scan_portas_suspeitas()
    cpu_m,cpu_n = get_cpu_info()

    # Analisar
    obs_ram,   score_ram   = analisar_ram(ru,rt,rp)
    obs_disco, score_disco = analisar_disco(du,dt,dp)
    obs_rede,  score_rede  = analisar_rede(portas)
    obs_up,    score_up    = analisar_uptime(uptime)

    todas_obs = obs_ram + obs_disco + obs_rede + obs_up
    score_final = int((score_ram+score_disco+score_rede+score_up)/4)
    score_final = max(0, min(100, score_final))

    # Cor da pontuacao
    if score_final >= 80:
        score_cor, score_label = "bold green",  "SAUDAVEL"
    elif score_final >= 60:
        score_cor, score_label = "bold yellow", "ATENCAO"
    elif score_final >= 40:
        score_cor, score_label = "bold red",    "EM RISCO"
    else:
        score_cor, score_label = "bold red",    "CRITICO"

    # Header de pontuacao
    console.print(Rule(style="dim cyan"))
    console.print()
    console.print(Align.center(Text(
        f"Pontuacao de Saude do Sistema: {score_final}/100 — {score_label}",
        style=score_cor
    )))
    console.print()
    console.print(Rule(style="dim cyan"))
    console.print()

    # Tabela de observacoes
    secoes = [
        ("MEMORIA RAM",  obs_ram,   f"{rp:.1f}%"),
        ("DISCO",        obs_disco, f"{dp:.1f}%"),
        ("REDE",         obs_rede,  f"{len(portas)} porta(s)"),
        ("SISTEMA",      obs_up,    f"{uptime/3600:.0f}h ligado"),
    ]

    for titulo, obs, resumo in secoes:
        t=Table(
            box=box.SIMPLE_HEAVY,
            border_style="cyan",
            show_header=False,
            title=f"[bold cyan]{titulo}[/bold cyan]  [dim]{resumo}[/dim]",
            expand=True,
            padding=(0,1),
        )
        t.add_column("Icone", width=5, justify="center")
        t.add_column("Observacao")

        for nivel, texto in obs:
            cor   = COR_NIVEL.get(nivel,"white")
            icone = ICONE_NIVEL.get(nivel,"·")
            t.add_row(f"[{cor}]{icone}[/{cor}]", f"[{cor}]{texto}[/{cor}]")

        console.print(t)
        console.print()

    # Recomendacoes
    recs = gerar_recomendacoes(todas_obs)
    t2=Table(
        box=box.SIMPLE_HEAVY,
        border_style="magenta",
        show_header=False,
        title="[bold magenta]RECOMENDACOES[/bold magenta]",
        expand=True,
        padding=(0,1),
    )
    t2.add_column("Tipo", width=18)
    t2.add_column("Mensagem", style="white")
    for tipo, msg in recs:
        t2.add_row(tipo, msg)
    console.print(t2)
    console.print()

    # Guardar log
    os.makedirs("reports", exist_ok=True)
    ts=datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path=f"reports/analyst_{ts}.txt"
    with open(log_path,"w",encoding="utf-8") as f:
        f.write(f"PENKIT ANALYST — {datetime.now()}\n")
        f.write(f"Pontuacao: {score_final}/100 — {score_label}\n")
        f.write("="*50+"\n")
        for titulo, obs, resumo in secoes:
            f.write(f"\n{titulo} ({resumo}):\n")
            for nivel, texto in obs:
                f.write(f"  {ICONE_NIVEL.get(nivel,'·')} {texto}\n")
        f.write("\nRECOMENDACOES:\n")
        for tipo, msg in recs:
            f.write(f"  {msg}\n")

    console.print(f"[dim]Relatorio guardado: {os.path.abspath(log_path)}[/dim]")
    console.print()
    input("Enter para voltar...")
