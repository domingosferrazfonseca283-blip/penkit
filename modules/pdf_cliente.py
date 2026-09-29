
import os, sys, socket, platform, subprocess, threading
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.align import Align
from rich.text import Text
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

def ping(ip):
    try:
        r=subprocess.run(["ping","-c","1","-W","400",ip],
            stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=1)
        return r.returncode==0
    except: return False

def scan_hosts(prefixo):
    encontrados=[]; lock=threading.Lock()
    def check(i):
        ip=f"{prefixo}.{i}"
        if ping(ip):
            with lock: encontrados.append(ip)
    threads=[threading.Thread(target=check,args=(i,),daemon=True) for i in range(1,255)]
    for t in threads: t.start()
    for t in threads: t.join(timeout=1.5)
    return sorted(encontrados,key=lambda x:int(x.split(".")[-1]))

def scan_portas_local():
    PORTAS={21:"FTP",22:"SSH",23:"Telnet",25:"SMTP",80:"HTTP",
            443:"HTTPS",3306:"MySQL",3389:"RDP",8080:"HTTP-Alt"}
    abertas=[]
    for p,nome in PORTAS.items():
        try:
            s=socket.socket(); s.settimeout(0.3)
            if s.connect_ex(("127.0.0.1",p))==0: abertas.append((p,nome))
            s.close()
        except: pass
    return abertas

def detectar_problemas(rp,dp,portas):
    problemas=[]; avisos=[]
    if rp>90: problemas.append("RAM critica — risco de colapso")
    elif rp>75: avisos.append("RAM elevada — desempenho degradado")
    if dp>90: problemas.append("Disco cheio — sistema pode parar")
    elif dp>75: avisos.append("Disco a encher — requer manutencao")
    CRITICAS={23:"Telnet sem cifra",21:"FTP sem cifra",4444:"Backdoor",5555:"ADB exposto"}
    for p,nome in portas:
        if p in CRITICAS: problemas.append(f"Porta critica aberta: {p} ({CRITICAS[p]})")
        elif p==3306: avisos.append("MySQL exposto localmente")
        elif p==3389: avisos.append("RDP activo — verifica autenticacao")
    return problemas, avisos

def gerar_pdf_cliente(dados, path_pdf):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                    Table, TableStyle, HRFlowable, PageBreak)
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

    PRETO   = colors.HexColor("#0a0a0f")
    CIANO   = colors.HexColor("#00e5ff")
    MAGENTA = colors.HexColor("#7c3aed")
    VERDE   = colors.HexColor("#059669")
    AMARELO = colors.HexColor("#d97706")
    VERM    = colors.HexColor("#dc2626")
    CINZA   = colors.HexColor("#1e293b")
    CINZA2  = colors.HexColor("#0f172a")
    BRANCO  = colors.HexColor("#e2e8f0")
    AZUL    = colors.HexColor("#1e40af")

    doc = SimpleDocTemplate(
        path_pdf, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=1.5*cm, bottomMargin=2*cm
    )

    def st(name, **kw):
        base = ParagraphStyle(name, **kw)
        return base

    s_tit  = st("tit",  fontSize=24, fontName="Helvetica-Bold",
                textColor=CIANO, alignment=TA_CENTER, spaceAfter=2)
    s_sub  = st("sub",  fontSize=11, fontName="Helvetica",
                textColor=BRANCO, alignment=TA_CENTER, spaceAfter=2)
    s_dat  = st("dat",  fontSize=9,  fontName="Helvetica",
                textColor=colors.HexColor("#64748b"), alignment=TA_CENTER, spaceAfter=12)
    s_sec  = st("sec",  fontSize=12, fontName="Helvetica-Bold",
                textColor=CIANO, spaceAfter=6, spaceBefore=14)
    s_bod  = st("bod",  fontSize=10, fontName="Helvetica",
                textColor=BRANCO, spaceAfter=4, leading=14)
    s_ok   = st("ok",   fontSize=10, fontName="Helvetica-Bold",
                textColor=VERDE,  spaceAfter=4)
    s_avi  = st("avi",  fontSize=10, fontName="Helvetica-Bold",
                textColor=AMARELO,spaceAfter=4)
    s_crit = st("crit", fontSize=10, fontName="Helvetica-Bold",
                textColor=VERM,   spaceAfter=4)
    s_rod  = st("rod",  fontSize=8,  fontName="Helvetica",
                textColor=colors.HexColor("#334155"), alignment=TA_CENTER)
    s_ass  = st("ass",  fontSize=9,  fontName="Helvetica",
                textColor=colors.HexColor("#64748b"), alignment=TA_CENTER)
    s_cli  = st("cli",  fontSize=14, fontName="Helvetica-Bold",
                textColor=BRANCO, spaceAfter=4)

    def tabela(linhas, col_w=None, cor_h=CIANO):
        if not col_w: col_w=[5*cm,11.5*cm]
        t=Table(linhas, colWidths=col_w)
        t.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0),CINZA),
            ("TEXTCOLOR",(0,0),(-1,0),cor_h),
            ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
            ("FONTSIZE",(0,0),(-1,0),9),
            ("BACKGROUND",(0,1),(-1,-1),CINZA2),
            ("TEXTCOLOR",(0,1),(-1,-1),BRANCO),
            ("FONTNAME",(0,1),(-1,-1),"Helvetica"),
            ("FONTSIZE",(0,1),(-1,-1),9),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[CINZA2,colors.HexColor("#111827")]),
            ("GRID",(0,0),(-1,-1),0.3,colors.HexColor("#1e3a5f")),
            ("LEFTPADDING",(0,0),(-1,-1),8),
            ("RIGHTPADDING",(0,0),(-1,-1),8),
            ("TOPPADDING",(0,0),(-1,-1),5),
            ("BOTTOMPADDING",(0,0),(-1,-1),5),
        ]))
        return t

    def barra_pdf(p, largura=16*cm):
        cor=VERDE if p<60 else AMARELO if p<85 else VERM
        preenchido=largura*p/100
        b=Table([[""]], colWidths=[preenchido], rowHeights=[0.3*cm])
        b.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,-1),cor),
            ("LEFTPADDING",(0,0),(-1,-1),0),
            ("RIGHTPADDING",(0,0),(-1,-1),0),
            ("TOPPADDING",(0,0),(-1,-1),0),
            ("BOTTOMPADDING",(0,0),(-1,-1),0),
        ]))
        return b

    h = []

    # Capa
    h.append(Spacer(1,1*cm))
    h.append(Paragraph("PENKIT", s_tit))
    h.append(Paragraph("Relatorio de Diagnostico Informatico", s_sub))
    h.append(Paragraph(f"Preparado por: {dados['tecnico']}  |  {dados['data']}", s_dat))
    h.append(HRFlowable(width="100%",thickness=1,color=CIANO,spaceAfter=16))

    # Info cliente
    h.append(Paragraph("INFORMACAO DO CLIENTE", s_sec))
    h.append(tabela([
        ["Campo",    "Detalhe"],
        ["Empresa",  dados["empresa"]],
        ["Contacto", dados["contacto"]],
        ["Morada",   dados["morada"]],
        ["Data",     dados["data"]],
        ["Tecnico",  dados["tecnico"]],
        ["Motivo",   dados["motivo"]],
    ]))
    h.append(Spacer(1,0.5*cm))

    # Pontuacao
    score=dados["score"]
    cor_s=VERDE if score>=80 else AMARELO if score>=60 else VERM
    label="SAUDAVEL" if score>=80 else "ATENCAO" if score>=60 else "EM RISCO"
    h.append(Paragraph("PONTUACAO DE SAUDE DO SISTEMA", s_sec))
    h.append(Paragraph(f"{score}/100 — {label}",
        st("sc", fontSize=20, fontName="Helvetica-Bold",
           textColor=cor_s, alignment=TA_CENTER, spaceAfter=6)))
    h.append(barra_pdf(score))
    h.append(Spacer(1,0.5*cm))

    # Sistema
    ru,rt,rp=dados["ram"]; du,dt,dp=dados["disk"]
    h.append(Paragraph("INFORMACAO DO SISTEMA", s_sec))
    h.append(tabela([
        ["Campo",    "Valor"],
        ["Hostname", dados["host"]],
        ["IP Local", dados["ip"]],
        ["Sistema",  dados["os"]],
        ["CPU",      f"{dados['cpu_modelo']} ({dados['cpu_nucleos']} nucleos)"],
        ["Uptime",   dados["uptime"]],
    ]))
    h.append(Spacer(1,0.4*cm))

    # Recursos
    h.append(Paragraph("RECURSOS DO SISTEMA", s_sec))
    h.append(Paragraph(f"RAM — {fmt(ru)} / {fmt(rt)}  ({rp:.1f}%)", s_bod))
    h.append(barra_pdf(rp))
    h.append(Spacer(1,0.3*cm))
    h.append(Paragraph(f"DISCO — {fmt(du)} / {fmt(dt)}  ({dp:.1f}%)", s_bod))
    h.append(barra_pdf(dp))
    h.append(Spacer(1,0.4*cm))

    # Rede
    h.append(Paragraph(f"REDE — {len(dados['hosts'])} dispositivo(s) detectado(s)", s_sec))
    if dados["hosts"]:
        linhas_hosts=[["IP","Estado"]]
        for hip in dados["hosts"][:15]:
            linhas_hosts.append([hip,"ONLINE"])
        if len(dados["hosts"])>15:
            linhas_hosts.append([f"+{len(dados['hosts'])-15} mais","..."])
        h.append(tabela(linhas_hosts, col_w=[8*cm,8.5*cm]))
    h.append(Spacer(1,0.4*cm))

    # Portas
    if dados["portas"]:
        h.append(Paragraph("PORTAS ABERTAS", s_sec))
        linhas_p=[["Porta","Servico"]]
        for p,nome in dados["portas"]:
            linhas_p.append([str(p),nome])
        h.append(tabela(linhas_p, col_w=[4*cm,12.5*cm], cor_h=AMARELO))
        h.append(Spacer(1,0.4*cm))

    # Problemas
    problemas=dados["problemas"]; avisos=dados["avisos"]
    h.append(Paragraph("ANALISE DE PROBLEMAS", s_sec))
    if not problemas and not avisos:
        h.append(Paragraph("+ Nenhum problema critico detectado.", s_ok))
    else:
        for p in problemas:
            h.append(Paragraph(f"[CRITICO] {p}", s_crit))
        for a in avisos:
            h.append(Paragraph(f"[AVISO] {a}", s_avi))
    h.append(Spacer(1,0.4*cm))

    # Accoes realizadas
    if dados.get("acoes"):
        h.append(Paragraph("ACCOES REALIZADAS", s_sec))
        linhas_a=[["Hora","Accao"]]
        for a in dados["acoes"]:
            linhas_a.append([a.get("hora","?"), a.get("acao","?")])
        h.append(tabela(linhas_a, col_w=[3*cm,13.5*cm]))
        h.append(Spacer(1,0.4*cm))

    # Recomendacoes
    h.append(Paragraph("RECOMENDACOES", s_sec))
    if problemas:
        h.append(Paragraph("1. Resolve os problemas criticos listados acima com urgencia.", s_bod))
    if avisos:
        h.append(Paragraph("2. Agenda manutencao preventiva para os avisos identificados.", s_bod))
    if not problemas and not avisos:
        h.append(Paragraph("Sistema em boas condicoes. Mantém monitorizacao regular.", s_bod))
    h.append(Paragraph("3. Realiza backup regular dos dados criticos da empresa.", s_bod))
    h.append(Paragraph("4. Agenda proxima visita de manutencao em 3 meses.", s_bod))
    h.append(Spacer(1,1*cm))

    # Assinatura
    h.append(HRFlowable(width="100%",thickness=0.5,
                        color=colors.HexColor("#1e3a5f"),spaceAfter=12))
    h.append(Paragraph(dados["tecnico"], s_ass))
    h.append(Paragraph("Tecnico de Informatica  |  PenKit Professional", s_ass))
    h.append(Spacer(1,0.3*cm))
    h.append(HRFlowable(width="100%",thickness=0.5,
                        color=colors.HexColor("#1e3a5f"),spaceAfter=8))
    h.append(Paragraph(
        f"Relatorio gerado por PenKit v2.0  |  {dados['data']}  |  Uso profissional autorizado",
        s_rod
    ))

    doc.build(h)

def run():
    console.clear()
    console.print(Panel(
        Align.center(Text("RELATORIO PDF DE CLIENTE", style="bold cyan")),
        subtitle="[dim]Gera PDF profissional para entregar ao cliente[/dim]",
        border_style="cyan"
    ))
    console.print()

    # Tenta carregar visita activa
    empresa=""; contacto=""; morada=""; motivo=""; acoes=[]
    try:
        sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from modules.visita import carregar_visitas
        visitas=[v for v in carregar_visitas() if v.get("estado")=="em_curso"]
        if visitas:
            v=visitas[-1]
            empresa=v.get("empresa","")
            contacto=v.get("contacto","")
            morada=v.get("morada","")
            motivo=v.get("motivo","")
            acoes=v.get("acoes",[])
            console.print(f"[dim]Visita activa encontrada: {empresa}[/dim]\n")
    except: pass

    if not empresa:
        empresa  = console.input("[yellow]Nome da empresa: [/yellow]").strip()
        contacto = console.input("[yellow]Contacto: [/yellow]").strip()
        morada   = console.input("[yellow]Morada: [/yellow]").strip()
        motivo   = console.input("[yellow]Motivo da visita: [/yellow]").strip()

    tecnico = console.input("[yellow]O teu nome (tecnico): [/yellow]").strip() or "Milton Fonseca"

    console.print()
    console.print("[yellow]A recolher dados do sistema...[/yellow]")

    ip=get_ip()
    ru,rt,rp=get_ram(); du,dt,dp=get_disk()
    cpu_m,cpu_n=get_cpu()
    portas=scan_portas_local()
    prefixo=ip.rsplit(".",1)[0] if ip!="offline" else "192.168.1"

    console.print("[yellow]A scannar rede...[/yellow]")
    hosts=scan_hosts(prefixo)
    problemas,avisos=detectar_problemas(rp,dp,portas)
    score=max(0,100-len(problemas)*20-len(avisos)*8)

    dados={
        "empresa":    empresa,
        "contacto":   contacto,
        "morada":     morada,
        "motivo":     motivo,
        "tecnico":    tecnico,
        "data":       datetime.now().strftime("%d/%m/%Y %H:%M"),
        "host":       socket.gethostname(),
        "ip":         ip,
        "os":         f"{platform.system()} {platform.release()}",
        "cpu_modelo": cpu_m,
        "cpu_nucleos":cpu_n,
        "uptime":     get_uptime(),
        "ram":        (ru,rt,rp),
        "disk":       (du,dt,dp),
        "hosts":      hosts,
        "portas":     portas,
        "problemas":  problemas,
        "avisos":     avisos,
        "score":      score,
        "acoes":      acoes,
    }

    console.print("[yellow]A gerar PDF...[/yellow]")
    os.makedirs("reports",exist_ok=True)
    ts=datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_empresa=empresa.replace(" ","_").replace("/","_")[:20]
    path_pdf=os.path.abspath(f"reports/relatorio_{nome_empresa}_{ts}.pdf")

    try:
        gerar_pdf_cliente(dados, path_pdf)
        console.print(Panel(
            f"[bold green]PDF gerado com sucesso![/bold green]\n\n"
            f"Ficheiro: [cyan]{path_pdf}[/cyan]\n\n"
            f"[dim]Copia para a pen drive ou imprime para o cliente.[/dim]",
            border_style="green"
        ))
    except Exception as e:
        console.print(Panel(f"[red]Erro: {e}[/red]",border_style="red"))

    input("\nEnter para voltar...")
