
import os, socket, platform
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
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
                m=line.split(":",1)[-1].strip()[:45]
            if "processor" in line: n+=1
        return m, n
    except: return "?", 0

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

def scan_portas():
    abertas=[]
    PORTAS={21:"FTP",22:"SSH",23:"Telnet",25:"SMTP",
            3306:"MySQL",5432:"PostgreSQL",6379:"Redis",
            8080:"HTTP-Alt",27017:"MongoDB"}
    for p,nome in PORTAS.items():
        try:
            s=socket.socket(); s.settimeout(0.3)
            if s.connect_ex(("127.0.0.1",p))==0: abertas.append((p,nome))
            s.close()
        except: pass
    return abertas

def gerar_pdf(dados, path_pdf):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                    Table, TableStyle, HRFlowable)
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT

    PRETO    = colors.HexColor("#0a0a0f")
    CIANO    = colors.HexColor("#00e5ff")
    MAGENTA  = colors.HexColor("#cc00ff")
    VERDE    = colors.HexColor("#00ff99")
    AMARELO  = colors.HexColor("#ffcc00")
    VERMELHO = colors.HexColor("#ff4444")
    CINZA    = colors.HexColor("#1a1a2e")
    BRANCO   = colors.HexColor("#c8f0ff")

    doc = SimpleDocTemplate(
        path_pdf, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm
    )

    styles = getSampleStyleSheet()

    estilo_titulo = ParagraphStyle("titulo",
        fontSize=28, fontName="Helvetica-Bold",
        textColor=CIANO, alignment=TA_CENTER, spaceAfter=4)

    estilo_sub = ParagraphStyle("sub",
        fontSize=11, fontName="Helvetica",
        textColor=MAGENTA, alignment=TA_CENTER, spaceAfter=2)

    estilo_data = ParagraphStyle("data",
        fontSize=9, fontName="Helvetica",
        textColor=colors.HexColor("#557788"), alignment=TA_CENTER, spaceAfter=16)

    estilo_secao = ParagraphStyle("secao",
        fontSize=13, fontName="Helvetica-Bold",
        textColor=CIANO, spaceAfter=6, spaceBefore=14)

    estilo_corpo = ParagraphStyle("corpo",
        fontSize=10, fontName="Helvetica",
        textColor=BRANCO, spaceAfter=4, leading=14)

    estilo_aviso = ParagraphStyle("aviso",
        fontSize=10, fontName="Helvetica-Bold",
        textColor=AMARELO, spaceAfter=4)

    estilo_critico = ParagraphStyle("critico",
        fontSize=10, fontName="Helvetica-Bold",
        textColor=VERMELHO, spaceAfter=4)

    def tabela_dados(linhas, cor_header=CIANO):
        t = Table(linhas, colWidths=[5*cm, 11.5*cm])
        t.setStyle(TableStyle([
            ("BACKGROUND",  (0,0), (-1,0),  CINZA),
            ("TEXTCOLOR",   (0,0), (-1,0),  cor_header),
            ("FONTNAME",    (0,0), (-1,0),  "Helvetica-Bold"),
            ("FONTSIZE",    (0,0), (-1,0),  10),
            ("BACKGROUND",  (0,1), (-1,-1), colors.HexColor("#0d0d1a")),
            ("TEXTCOLOR",   (0,1), (-1,-1), BRANCO),
            ("FONTNAME",    (0,1), (-1,-1), "Helvetica"),
            ("FONTSIZE",    (0,1), (-1,-1), 9),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.HexColor("#0d0d1a"),colors.HexColor("#111122")]),
            ("GRID",        (0,0), (-1,-1), 0.3, colors.HexColor("#00e5ff22")),
            ("LEFTPADDING",  (0,0),(-1,-1), 8),
            ("RIGHTPADDING", (0,0),(-1,-1), 8),
            ("TOPPADDING",   (0,0),(-1,-1), 5),
            ("BOTTOMPADDING",(0,0),(-1,-1), 5),
            ("ROUNDEDCORNERS", [4]),
        ]))
        return t

    def barra_pdf(percent):
        largura = 11.5*cm
        preenchido = largura * percent / 100
        cor = VERDE if percent<60 else AMARELO if percent<85 else VERMELHO
        barra = Table(
            [[""]],
            colWidths=[preenchido],
            rowHeights=[0.35*cm]
        )
        barra.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,-1),cor),
            ("LEFTPADDING",(0,0),(-1,-1),0),
            ("RIGHTPADDING",(0,0),(-1,-1),0),
            ("TOPPADDING",(0,0),(-1,-1),0),
            ("BOTTOMPADDING",(0,0),(-1,-1),0),
        ]))
        return barra

    # Conteudo
    historia = []

    # Cabecalho
    historia.append(Paragraph("⬡ PENKIT", estilo_titulo))
    historia.append(Paragraph("Canivete Digital Portatil — Relatorio de Sistema", estilo_sub))
    historia.append(Paragraph(f"Gerado em {dados['data']}  |  {dados['ip']}", estilo_data))
    historia.append(HRFlowable(width="100%", thickness=0.5,
                               color=CIANO, spaceAfter=12))

    # Secao sistema
    historia.append(Paragraph("INFORMACAO DO SISTEMA", estilo_secao))
    historia.append(tabela_dados([
        ["Campo",       "Valor"],
        ["Hostname",    dados["hostname"]],
        ["IP Local",    dados["ip"]],
        ["Sistema Op.", dados["sistema"]],
        ["Arquitectura",dados["arch"]],
        ["Uptime",      dados["uptime"]],
        ["Processador", dados["cpu_modelo"]],
        ["Nucleos",     str(dados["cpu_nucleos"])],
    ]))
    historia.append(Spacer(1, 0.4*cm))

    # Secao recursos
    historia.append(Paragraph("RECURSOS DO SISTEMA", estilo_secao))

    ru,rt,rp = dados["ram_used"], dados["ram_total"], dados["ram_percent"]
    du,dt,dp = dados["disk_used"], dados["disk_total"], dados["disk_percent"]

    historia.append(Paragraph(f"RAM — {fmt(ru)} / {fmt(rt)}  ({rp:.1f}%)", estilo_corpo))
    historia.append(barra_pdf(rp))
    historia.append(Spacer(1, 0.3*cm))
    historia.append(Paragraph(f"DISCO — {fmt(du)} / {fmt(dt)}  ({dp:.1f}%)", estilo_corpo))
    historia.append(barra_pdf(dp))
    historia.append(Spacer(1, 0.4*cm))

    # Secao rede
    historia.append(Paragraph("REDE E PORTAS", estilo_secao))
    portas = dados["portas"]
    if portas:
        linhas_portas = [["Porta", "Servico"]]
        for p, nome in portas:
            linhas_portas.append([str(p), nome])
        historia.append(tabela_dados(linhas_portas, cor_header=AMARELO))
    else:
        historia.append(Paragraph("Nenhuma porta de risco detectada.", estilo_corpo))
    historia.append(Spacer(1, 0.4*cm))

    # Secao analise
    historia.append(Paragraph("ANALISE DE SAUDE", estilo_secao))
    score = dados["score"]
    cor_score = VERDE if score>=80 else AMARELO if score>=60 else VERMELHO
    historia.append(Paragraph(
        f"Pontuacao de Saude: {score}/100", estilo_secao))
    historia.append(barra_pdf(score))
    historia.append(Spacer(1, 0.3*cm))

    if rp > 85:
        historia.append(Paragraph("! RAM critica — risco de instabilidade.", estilo_critico))
    if dp > 85:
        historia.append(Paragraph("! Disco quase cheio — liberta espaco.", estilo_critico))
    if portas:
        historia.append(Paragraph(
            f"^ {len(portas)} porta(s) abertas detectadas — verifica cada servico.",
            estilo_aviso))
    if score >= 80:
        historia.append(Paragraph("+ Sistema saudavel. Mantm monitorizacao regular.", estilo_corpo))

    # Rodape
    historia.append(Spacer(1, 1*cm))
    historia.append(HRFlowable(width="100%", thickness=0.5,
                               color=colors.HexColor("#00e5ff33"), spaceAfter=8))
    historia.append(Paragraph(
        "Gerado por PenKit v2.0  —  Canivete Digital Portatil  —  Uso profissional autorizado",
        ParagraphStyle("rodape", fontSize=8, fontName="Helvetica",
                       textColor=colors.HexColor("#334455"), alignment=TA_CENTER)
    ))

    doc.build(historia)

def calcular_score(rp, dp, portas):
    score = 100
    if rp > 90: score -= 30
    elif rp > 75: score -= 15
    elif rp > 60: score -= 5
    if dp > 95: score -= 40
    elif dp > 85: score -= 20
    elif dp > 70: score -= 8
    RISCO = {23:25, 4444:25, 5555:20, 21:15, 3306:12,
             5432:10, 6379:10, 27017:10, 22:3, 25:3, 8080:3}
    for p,_ in portas:
        score -= RISCO.get(p, 5)
    return max(0, min(100, score))

def run():
    console.clear()
    console.print(Panel("[bold cyan]Relatorio PDF[/bold cyan]",
                        subtitle="[dim]Gera um PDF profissional com marca PenKit[/dim]",
                        border_style="cyan"))
    console.print()
    console.print("[yellow]A recolher dados do sistema...[/yellow]")

    ru,rt,rp = get_ram()
    du,dt,dp = get_disk()
    cpu_m,cpu_n = get_cpu()
    portas = scan_portas()
    score  = calcular_score(rp, dp, portas)

    dados = {
        "data":        datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "hostname":    socket.gethostname(),
        "ip":          get_ip(),
        "sistema":     f"{platform.system()} {platform.release()}",
        "arch":        platform.machine(),
        "uptime":      get_uptime(),
        "cpu_modelo":  cpu_m,
        "cpu_nucleos": cpu_n,
        "ram_used":    ru, "ram_total": rt, "ram_percent": rp,
        "disk_used":   du, "disk_total": dt, "disk_percent": dp,
        "portas":      portas,
        "score":       score,
    }

    os.makedirs("reports", exist_ok=True)
    ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
    path_pdf = os.path.abspath(f"reports/penkit_{ts}.pdf")

    console.print("[yellow]A gerar PDF...[/yellow]")
    try:
        gerar_pdf(dados, path_pdf)
        console.print(Panel(
            f"[bold green]PDF gerado com sucesso![/bold green]\n\n"
            f"[cyan]{path_pdf}[/cyan]\n\n"
            f"[dim]Copia para a pen drive ou abre num leitor de PDF.[/dim]",
            border_style="green"
        ))
    except Exception as e:
        console.print(Panel(f"[red]Erro ao gerar PDF: {e}[/red]", border_style="red"))

    input("\nEnter para voltar...")
