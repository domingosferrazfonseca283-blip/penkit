
import os, sys, socket, time, subprocess, re
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.align import Align
from rich.text import Text
from rich.columns import Columns
from rich.rule import Rule
from rich import box

console = Console()

FABRICANTES = {
    "00:50:56": "VMware",    "00:0c:29": "VMware",
    "00:1a:11": "Google",    "b8:27:eb": "Raspberry Pi",
    "dc:a6:32": "Raspberry Pi","00:17:88": "Philips Hue",
    "ac:84:c6": "Xiaomi",    "fc:64:ba": "Xiaomi",
    "28:6c:07": "Xiaomi",    "00:1b:63": "Apple",
    "a4:5e:60": "Apple",     "f0:18:98": "Apple",
    "00:50:f2": "Microsoft", "28:d2:44": "Samsung",
    "8c:77:12": "Samsung",   "00:23:14": "Asus",
    "10:bf:48": "Asus",      "e0:cb:4e": "Asus",
    "00:e0:4c": "Realtek",   "00:1d:60": "Acer",
    "74:d0:2b": "Huawei",    "00:18:82": "Huawei",
    "00:08:22": "Inpro",     "00:13:46": "Dell",
    "14:18:77": "Dell",      "00:1c:42": "Parallels",
}

def get_prefixo():
    try:
        s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        s.connect(("8.8.8.8",80)); ip=s.getsockname()[0]; s.close()
        return ip, ip.rsplit(".",1)[0]
    except: return None, None

def ping(ip):
    try:
        r=subprocess.run(
            ["ping","-c","1","-W","400",ip],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=1
        )
        return r.returncode==0
    except: return False

def get_mac(ip):
    try:
        result=subprocess.run(
            ["ip","neigh","show",ip],
            capture_output=True,text=True,timeout=2
        )
        match=re.search(r"([0-9a-f]{2}(?::[0-9a-f]{2}){5})",result.stdout)
        if match: return match.group(1).upper()
    except: pass
    try:
        with open("/proc/net/arp") as f:
            for line in f.readlines()[1:]:
                parts=line.split()
                if len(parts)>=4 and parts[0]==ip:
                    mac=parts[3]
                    if mac!="00:00:00:00:00:00": return mac.upper()
    except: pass
    return "??"

def get_hostname(ip):
    try:
        return socket.gethostbyaddr(ip)[0]
    except: return "?"

def get_fabricante(mac):
    if mac in ["??","00:00:00:00:00:00"]: return "?"
    prefixo=mac[:8].lower()
    return FABRICANTES.get(prefixo, "Desconhecido")

def get_net_traffic():
    try:
        ifaces={}
        for line in open("/proc/net/dev").readlines()[2:]:
            p=line.split()
            if len(p)>=10:
                nome=p[0].rstrip(":")
                if int(p[1])>0 or int(p[9])>0:
                    ifaces[nome]=(int(p[1]),int(p[9]))
        return ifaces
    except: return {}

def fmt_bytes(b):
    for u in ["B","KB","MB","GB"]:
        if b<1024: return f"{b:.1f}{u}"
        b/=1024
    return f"{b:.1f}TB"

def scan_rede(prefixo, progresso_cb=None):
    dispositivos=[]
    import threading

    lock=threading.Lock()
    encontrados=[]

    def verificar(i):
        ip=f"{prefixo}.{i}"
        if ping(ip):
            mac=get_mac(ip)
            hn=get_hostname(ip)
            fab=get_fabricante(mac)
            with lock:
                encontrados.append({
                    "ip":ip,"mac":mac,
                    "hostname":hn,"fabricante":fab,
                    "visto":datetime.now().strftime("%H:%M:%S")
                })
        if progresso_cb: progresso_cb()

    threads=[]
    for i in range(1,255):
        t=threading.Thread(target=verificar,args=(i,),daemon=True)
        threads.append(t)
        t.start()
        if len(threads)>=50:
            for th in threads: th.join(timeout=2)
            threads=[]

    for th in threads: th.join(timeout=2)

    encontrados.sort(key=lambda x: int(x["ip"].split(".")[-1]))
    return encontrados

def build_tabela(dispositivos, ip_local, alertas):
    t=Table(
        box=box.SIMPLE_HEAVY,
        border_style="cyan",
        header_style="bold magenta",
        title=f"[bold cyan]MAPA DE REDE[/bold cyan]  [dim]{len(dispositivos)} dispositivo(s)[/dim]",
        expand=True
    )
    t.add_column("IP",          style="bold cyan",   width=16)
    t.add_column("MAC",         style="dim white",   width=20)
    t.add_column("Fabricante",  style="white",       width=14)
    t.add_column("Hostname",    style="dim white",   width=18)
    t.add_column("Visto",       style="dim yellow",  width=10)
    t.add_column("Estado",      width=10, justify="center")

    for d in dispositivos:
        e_local = d["ip"]==ip_local
        novo    = d["ip"] in alertas
        estado  = "[bold green]LOCAL[/bold green]"  if e_local else                   "[bold yellow]NOVO![/bold yellow]" if novo    else                   "[green]ONLINE[/green]"
        t.add_row(
            f"[bold {'green' if e_local else 'cyan'}]{d['ip']}[/bold {'green' if e_local else 'cyan'}]",
            d["mac"], d["fabricante"], d["hostname"],
            d["visto"], estado
        )
    return t

def build_traffic(ifaces_antes, ifaces_agora):
    t=Table(
        box=box.SIMPLE_HEAVY,
        border_style="cyan",
        header_style="bold magenta",
        title="[bold cyan]TRAFEGO DE REDE[/bold cyan]",
        expand=True
    )
    t.add_column("Interface", style="bold yellow")
    t.add_column("Download",  style="bold green",  justify="right")
    t.add_column("Upload",    style="bold magenta", justify="right")
    t.add_column("Total RX",  style="dim white",    justify="right")
    t.add_column("Total TX",  style="dim white",    justify="right")

    for nome,(rx_now,tx_now) in ifaces_agora.items():
        rx_antes,tx_antes=ifaces_antes.get(nome,(rx_now,tx_now))
        delta_rx=max(0,rx_now-rx_antes)
        delta_tx=max(0,tx_now-tx_antes)
        t.add_row(
            nome,
            f"▼ {fmt_bytes(delta_rx)}/s",
            f"▲ {fmt_bytes(delta_tx)}/s",
            fmt_bytes(rx_now),
            fmt_bytes(tx_now),
        )
    return t

def run():
    console.clear()
    console.print(Panel(
        Align.center(Text("NETMAP — Mapa de Rede", style="bold cyan")),
        subtitle="[dim]Descobre e monitoriza dispositivos em tempo real[/dim]",
        border_style="cyan"
    ))
    console.print()

    ip_local, prefixo = get_prefixo()
    if not ip_local:
        console.print("[red]Sem ligacao a rede.[/red]")
        input("\nEnter..."); return

    console.print(f"[dim]Rede: {prefixo}.0/24  |  IP local: {ip_local}[/dim]")
    console.print()
    console.print("[bold yellow]1[/bold yellow] Scan completo da rede")
    console.print("[bold yellow]2[/bold yellow] Monitor de trafego em tempo real")
    console.print("[bold yellow]3[/bold yellow] Scan + Monitor (modo completo)")
    console.print("[bold red]0[/bold red] Voltar")
    console.print()

    op=console.input("[bold cyan]  > [/bold cyan]").strip()

    if op=="0": return

    elif op in ["1","3"]:
        console.clear()
        console.print(Panel(f"[bold cyan]A scannar {prefixo}.0/24...[/bold cyan]",border_style="cyan"))
        console.print("[dim]Isto pode demorar 30-60 segundos...[/dim]\n")

        contagem=[0]
        def prog(): contagem[0]+=1

        dispositivos_anteriores=set()
        dispositivos=scan_rede(prefixo, prog)
        alertas=set()

        console.clear()
        console.print(build_tabela(dispositivos, ip_local, alertas))
        console.print()

        os.makedirs("reports",exist_ok=True)
        ts=datetime.now().strftime("%Y%m%d_%H%M%S")
        log=f"reports/netmap_{ts}.txt"
        with open(log,"w") as f:
            f.write(f"PENKIT NETMAP — {datetime.now()}\n")
            f.write(f"Rede: {prefixo}.0/24\n"+"="*40+"\n")
            for d in dispositivos:
                f.write(f"{d['ip']}  {d['mac']}  {d['fabricante']}  {d['hostname']}\n")
        console.print(f"[dim]Log guardado: {os.path.abspath(log)}[/dim]")

        if op=="1":
            input("\nEnter para voltar...")
            return

        dispositivos_anteriores={d["ip"] for d in dispositivos}
        console.print("\n[dim]A iniciar monitor... Ctrl+C para parar[/dim]")
        time.sleep(1)

        if op in ["2","3"]:
            ifaces_antes=get_net_traffic()
            try:
                ciclo=0
                while True:
                    time.sleep(3)
                    ciclo+=1
                    ifaces_agora=get_net_traffic()

                    if ciclo%5==0 or op=="3":
                        novos=scan_rede(prefixo)
                        novos_ips={d["ip"] for d in novos}
                        alertas=novos_ips-dispositivos_anteriores

                        if alertas:
                            console.print()
                            for ip_novo in alertas:
                                console.print(Panel(
                                    f"[bold yellow]NOVO DISPOSITIVO DETECTADO: {ip_novo}[/bold yellow]",
                                    border_style="yellow"
                                ))
                            dispositivos=novos
                            dispositivos_anteriores=novos_ips

                    console.clear()
                    console.print(build_tabela(dispositivos,ip_local,alertas))
                    console.print()
                    console.print(build_traffic(ifaces_antes,ifaces_agora))
                    console.print()
                    console.print(f"[dim]Actualizado: {datetime.now().strftime('%H:%M:%S')}  |  Ctrl+C para parar[/dim]")
                    ifaces_antes=ifaces_agora

            except KeyboardInterrupt:
                console.print("\n[dim]Monitor encerrado.[/dim]")
            input("\nEnter para voltar...")
            return

    elif op=="2":
        ifaces_antes=get_net_traffic()
        console.print("[dim]A monitorizar trafego... Ctrl+C para parar[/dim]")
        try:
            while True:
                time.sleep(2)
                ifaces_agora=get_net_traffic()
                console.clear()
                console.print(build_traffic(ifaces_antes,ifaces_agora))
                console.print(f"\n[dim]{datetime.now().strftime('%H:%M:%S')}  |  Ctrl+C para parar[/dim]")
                ifaces_antes=ifaces_agora
        except KeyboardInterrupt:
            console.print("\n[dim]Monitor encerrado.[/dim]")
        input("\nEnter para voltar...")
