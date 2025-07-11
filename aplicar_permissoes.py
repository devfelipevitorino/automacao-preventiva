import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, PhotoImage
import subprocess
import os
import sys
from string import ascii_uppercase
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Thread

MAX_WORKERS = 2

def log(msg):
    print(msg)

def configurar_sql_delayed_start():
    try:
        cmd = 'sc config "MSSQL$SQLEXPRESS" start= delayed-auto'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            log("Serviço SQL Server Express configurado para iniciar com atraso.")
            return True
        else:
            log(f"Erro ao configurar o serviço SQL: {result.stderr.strip()}")
            return False
    except Exception as e:
        log(f"Exceção ao configurar o serviço SQL: {e}")
        return False

def conceder_permissao(pasta):
    grupos = ['Todos', 'Everyone', '*S-1-1-0']
    for grupo in grupos:
        if grupo == '*S-1-1-0':
            cmd = f'icacls "{pasta}" /grant {grupo}:(OI)(CI)F'
        else:
            cmd = f'icacls "{pasta}" /grant "{grupo}":(OI)(CI)F'
        try:
            timeout_val = 120 if 'appdata\\local' in pasta.lower() else 60
            result = subprocess.run(cmd, shell=True, timeout=timeout_val, capture_output=True, text=True)
            if result.returncode == 0:
                log(f"Permissão concedida para '{grupo}' na pasta: {pasta}")
                return True
            else:
                log(f"Erro concedendo permissão para '{grupo}' na pasta: {pasta} - {result.stderr.strip()}")
        except subprocess.TimeoutExpired:
            log(f"Timeout ao conceder permissão para '{grupo}' na pasta: {pasta}")
        except Exception as e:
            log(f"Erro inesperado ao conceder permissão para '{grupo}' na pasta: {pasta} - {e}")
    return False

def atualizar_status(texto):
    status_label.config(text=texto)

def aplicar_permissoes_thread():
    botao.config(state="disabled")
    mensagens_text.config(state="normal")
    mensagens_text.delete("1.0", tk.END)
    atualizar_status("Configurando serviço SQL Server Express...")
    root.update_idletasks()

    progress_bar.start(10)

    sucesso_servico = configurar_sql_delayed_start()
    if sucesso_servico:
        mensagens_text.insert(tk.END, "Serviço SQL Server Express configurado para iniciar com atraso.\n")
    else:
        mensagens_text.insert(tk.END, "Falha ao configurar serviço SQL Server Express.\n")

    atualizar_status("Buscando pastas para processar...")
    root.update_idletasks()

    pasta_fixa = os.environ.get("LOCALAPPDATA")
    pastas_para_processar = []

    if pasta_fixa and os.path.exists(pasta_fixa):
        pastas_para_processar.append(pasta_fixa)
    else:
        mensagens_text.insert(tk.END, "LOCALAPPDATA não encontrado ou inacessível\n")

    discos = [f"{letra}:\\" for letra in ascii_uppercase if os.path.exists(f"{letra}:\\")]

    for disco in discos:
        try:
            with os.scandir(disco) as entries:
                for entry in entries:
                    if entry.is_dir(follow_symlinks=False) and entry.name.lower().startswith("softcom"):
                        pastas_para_processar.append(entry.path)
        except PermissionError:
            log(f"Sem permissão para acessar disco: {disco}")
        except Exception as e:
            log(f"Erro acessando disco {disco}: {e}")

    total = len(pastas_para_processar)

    progress_bar.stop()
    progress_bar.config(maximum=total if total > 0 else 1, mode='determinate')
    progress_bar["value"] = 0
    root.update_idletasks()

    atualizar_status("Iniciando aplicação de permissões...")
    root.update_idletasks()

    resultados = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(conceder_permissao, pasta): pasta for pasta in pastas_para_processar}

        for i, future in enumerate(as_completed(futures), start=1):
            pasta = futures[future]
            atualizar_status(f"Processando: {pasta}")
            try:
                sucesso = future.result()
            except Exception as e:
                sucesso = False
                log(f"Erro inesperado na thread para pasta {pasta}: {e}")

            status = "Sucesso" if sucesso else "Falha"
            resultados.append((pasta, status))
            mensagens_text.insert(tk.END, f"{status}: {pasta}\n")
            mensagens_text.see(tk.END)

            progress_bar["value"] = i
            root.update_idletasks()

    atualizar_status("Processo concluído")
    botao.config(state="normal")
    mensagens_text.config(state="disabled")
    messagebox.showinfo("Resultado", "Processo finalizado! Veja as mensagens na janela.")

def aplicar_permissoes():
    Thread(target=aplicar_permissoes_thread, daemon=True).start()

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Janela principal

root = tk.Tk()
root.title("Ação Preventiva - Softcom")

try:
    root.iconbitmap(resource_path("icone.ico"))
except Exception as e:
    log(f"Erro carregando icone .ico: {e}")

try:
    icone_img = PhotoImage(file=resource_path("icone.png"))
    root.iconphoto(True, icone_img)
except Exception as e:
    log(f"Erro carregando icone.png: {e}")

largura = 650
altura = 450
largura_tela = root.winfo_screenwidth()
altura_tela = root.winfo_screenheight()
pos_x = (largura_tela // 2) - (largura // 2)
pos_y = (altura_tela // 2) - (altura // 2)
root.geometry(f"{largura}x{altura}+{pos_x}+{pos_y}")
root.resizable(False, False)

cor_fundo = "#FFF9E5"
cor_primaria = "#FFC107"
cor_texto = "#333333"

root.configure(bg=cor_fundo)

FONT_TITLE = ("Calibri", 18, "bold")
FONT_NORMAL = ("Calibri", 13)
FONT_MONO = ("Consolas", 11)

titulo = tk.Label(root, text="Automatize as ações preventivas com um clique!",
                  font=FONT_TITLE, fg=cor_texto, bg=cor_fundo)
titulo.pack(pady=(20, 10))

botao = tk.Button(root, text="Executar", font=FONT_NORMAL,
                  bg=cor_primaria, fg=cor_texto, activebackground="#FFB300",
                  relief="flat", padx=20, pady=10, command=aplicar_permissoes)
botao.pack(pady=15)

progress_bar = ttk.Progressbar(root, length=560, mode="determinate")
progress_bar.pack(pady=15)

status_label = tk.Label(root, text="Clique em “Executar” e me deixe cuidar do resto!", font=FONT_NORMAL,
                        fg="#555555", bg=cor_fundo)
status_label.pack(pady=(0, 10))

mensagens_text = scrolledtext.ScrolledText(root, height=12, font=FONT_MONO,
                                           bg="white", fg=cor_texto, state="disabled")
mensagens_text.pack(padx=15, pady=(0, 20), fill="both", expand=True)

root.mainloop()
