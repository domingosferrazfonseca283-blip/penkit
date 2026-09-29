
import os, json, hashlib, base64, getpass
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.align import Align
from rich.text import Text
from rich import box

console = Console()
VAULT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".vault")

def derivar_chave(senha, salt):
    return hashlib.pbkdf2_hmac("sha256", senha.encode(), salt, 200000)

def cifrar(texto, chave):
    dados = texto.encode()
    resultado = bytearray()
    for i, byte in enumerate(dados):
        resultado.append(byte ^ chave[i % len(chave)])
    return base64.b64encode(bytes(resultado)).decode()

def decifrar(texto_cifrado, chave):
    dados = base64.b64decode(texto_cifrado.encode())
    resultado = bytearray()
    for i, byte in enumerate(dados):
        resultado.append(byte ^ chave[i % len(chave)])
    return resultado.decode()

def carregar_vault(senha):
    if not os.path.exists(VAULT_PATH):
        return None, None
    try:
        with open(VAULT_PATH, "r") as f:
            dados = json.load(f)
        salt  = base64.b64decode(dados["salt"])
        chave = derivar_chave(senha, salt)
        texto = decifrar(dados["payload"], chave)
        entradas = json.loads(texto)
        return entradas, chave
    except:
        return False, None

def guardar_vault(entradas, chave, salt):
    payload   = cifrar(json.dumps(entradas), chave)
    salt_b64  = base64.b64encode(salt).decode()
    with open(VAULT_PATH, "w") as f:
        json.dump({"salt": salt_b64, "payload": payload}, f)

def criar_vault(senha):
    salt  = os.urandom(32)
    chave = derivar_chave(senha, salt)
    guardar_vault([], chave, salt)
    return chave, salt

def pedir_senha(confirmar=False):
    senha = getpass.getpass("  Senha do Vault: ")
    if confirmar:
        conf = getpass.getpass("  Confirma senha: ")
        if senha != conf:
            console.print("[red]As senhas nao coincidem.[/red]")
            return None
    return senha

def mostrar_entradas(entradas):
    if not entradas:
        console.print("[dim]Vault vazio. Adiciona a tua primeira entrada.[/dim]")
        return
    t = Table(box=box.SIMPLE_HEAVY, border_style="cyan",
              header_style="bold magenta", expand=True)
    t.add_column("#",       width=4,  justify="center", style="bold yellow")
    t.add_column("Tipo",    width=12, style="bold cyan")
    t.add_column("Titulo",  width=22, style="white")
    t.add_column("Data",    width=16, style="dim white")
    for i, e in enumerate(entradas, 1):
        t.add_row(str(i), e.get("tipo","nota"), e.get("titulo","?"),
                  e.get("data","?")[:16])
    console.print(t)

def menu_vault(entradas, chave, salt):
    while True:
        console.clear()
        console.print(Panel(
            Align.center(Text("PENKIT VAULT", style="bold cyan")),
            subtitle="[dim]Cofre encriptado de dados sensiveis[/dim]",
            border_style="cyan"
        ))
        console.print()
        mostrar_entradas(entradas)
        console.print()
        console.print("[bold yellow]1[/bold yellow] Adicionar entrada")
        console.print("[bold yellow]2[/bold yellow] Ver entrada")
        console.print("[bold yellow]3[/bold yellow] Apagar entrada")
        console.print("[bold red]0[/bold red] Fechar Vault")
        console.print()

        op = console.input("[bold cyan]  Vault> [/bold cyan]").strip()

        if op == "0":
            console.print("[dim]Vault fechado.[/dim]")
            break

        elif op == "1":
            console.print()
            tipos = ["credencial", "nota", "achado", "chave", "outro"]
            console.print("[dim]Tipos: " + ", ".join(f"{i+1}.{t}" for i,t in enumerate(tipos)) + "[/dim]")
            tipo_i = console.input("[yellow]Tipo (1-5, Enter=nota): [/yellow]").strip()
            try:   tipo = tipos[int(tipo_i)-1]
            except: tipo = "nota"

            titulo  = console.input("[yellow]Titulo: [/yellow]").strip()
            console.print("[dim]Conteudo (Enter em linha vazia para terminar):[/dim]")
            linhas = []
            while True:
                l = input("  ")
                if not l: break
                linhas.append(l)
            conteudo = "\n".join(linhas)

            entradas.append({
                "tipo":     tipo,
                "titulo":   titulo,
                "conteudo": conteudo,
                "data":     datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })
            guardar_vault(entradas, chave, salt)
            console.print(Panel("[green]Entrada guardada e encriptada.[/green]", border_style="green"))
            input("\nEnter para continuar...")

        elif op == "2":
            if not entradas:
                console.print("[yellow]Vault vazio.[/yellow]"); input("\nEnter..."); continue
            num = console.input("[yellow]Numero da entrada: [/yellow]").strip()
            try:
                e = entradas[int(num)-1]
                console.print()
                console.print(Panel(
                    f"[bold cyan]{e.get('titulo','?')}[/bold cyan]\n"
                    f"[dim]Tipo: {e.get('tipo','?')} | Data: {e.get('data','?')}[/dim]\n\n"
                    f"{e.get('conteudo','(vazio)')}",
                    border_style="cyan", title="[bold]Entrada[/bold]"
                ))
            except:
                console.print("[red]Numero invalido.[/red]")
            input("\nEnter para continuar...")

        elif op == "3":
            if not entradas:
                console.print("[yellow]Vault vazio.[/yellow]"); input("\nEnter..."); continue
            num = console.input("[yellow]Numero a apagar: [/yellow]").strip()
            try:
                e = entradas[int(num)-1]
                conf = console.input(f"[red]Apagar '{e.get('titulo','?')}'? (s/N): [/red]").strip().lower()
                if conf == "s":
                    entradas.pop(int(num)-1)
                    guardar_vault(entradas, chave, salt)
                    console.print("[green]Entrada apagada.[/green]")
            except:
                console.print("[red]Numero invalido.[/red]")
            input("\nEnter para continuar...")

def run():
    console.clear()
    console.print(Panel(
        Align.center(Text("PENKIT VAULT", style="bold cyan")),
        subtitle="[dim]Cofre encriptado — os teus dados ficam apenas aqui[/dim]",
        border_style="cyan"
    ))
    console.print()

    vault_existe = os.path.exists(VAULT_PATH)

    if not vault_existe:
        console.print("[yellow]Vault nao encontrado. Vamos criar um novo.[/yellow]")
        console.print("[dim]Escolhe uma senha forte — sem ela nao ha recuperacao.[/dim]")
        console.print()
        senha = pedir_senha(confirmar=True)
        if not senha:
            input("\nEnter para voltar..."); return
        chave, salt = criar_vault(senha)
        console.print(Panel("[green]Vault criado com sucesso![/green]", border_style="green"))
        input("\nEnter para entrar...")
        menu_vault([], chave, salt)
    else:
        senha = pedir_senha(confirmar=False)
        if not senha:
            input("\nEnter para voltar..."); return

        console.print("[dim]A decifrar...[/dim]")
        entradas, chave = carregar_vault(senha)

        if entradas is False:
            console.print(Panel("[bold red]Senha incorrecta ou Vault corrompido.[/bold red]", border_style="red"))
            input("\nEnter para voltar..."); return

        if entradas is None:
            console.print("[red]Erro ao carregar Vault.[/red]")
            input("\nEnter para voltar..."); return

        salt = base64.b64decode(json.load(open(VAULT_PATH))["salt"])
        menu_vault(entradas, chave, salt)
