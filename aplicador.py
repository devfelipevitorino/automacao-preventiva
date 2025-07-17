import tkinter as tk
from tkinter import messagebox
from threading import Thread, Event
import queue
import os
from string import ascii_uppercase
from concurrent.futures import ThreadPoolExecutor, as_completed
import tkinter.ttk as ttk
import tkinter.scrolledtext

from permissoes import configurar_sql_delayed_start, conceder_permissao, run_subprocess_with_cancel, desabilitar_conta_convidado, ativar_firewall_e_regras, criar_tarefas_backup

MAX_WORKERS = 2

class AplicadorPermissoes:
    def __init__(self, root):
        self.root = root
        self.cancelar = Event()
        self.msg_queue = queue.Queue()
        self.acoes_realizadas = []

        self._setup_ui()
        self._start_msg_consumer()

    def _setup_ui(self):
        cor_fundo = "#FFF9E5"
        cor_primaria = "#FFC107"
        cor_texto = "#333333"

        self.root.configure(bg=cor_fundo)
        self.root.title("Ação Preventiva - Softcom")

        largura = 1000
        altura = 500
        largura_tela = self.root.winfo_screenwidth()
        altura_tela = self.root.winfo_screenheight()
        pos_x = (largura_tela // 2) - (largura // 2)
        pos_y = (altura_tela // 2) - (altura // 2)
        self.root.geometry(f"{largura}x{altura}+{pos_x}+{pos_y}")
        self.root.resizable(False, False)

        FONT_TITLE = ("Calibri", 18, "bold")
        FONT_NORMAL = ("Calibri", 13)
        FONT_MONO = ("Consolas", 10)

        titulo = tk.Label(self.root, text="Automatize as ações preventivas com um clique!",
                          font=FONT_TITLE, fg=cor_texto, bg=cor_fundo)
        titulo.pack(pady=(20, 10))

        frame_botoes = tk.Frame(self.root, bg=cor_fundo)
        frame_botoes.pack(pady=15)

        self.botao = tk.Button(frame_botoes, text="Executar", font=FONT_NORMAL,
                              bg=cor_primaria, fg=cor_texto, activebackground="#FFB300",
                              relief="flat", padx=20, pady=10, command=self.aplicar_permissoes)
        self.botao.pack(side="left", padx=10)

        self.botao_cancelar = tk.Button(frame_botoes, text="Cancelar", font=FONT_NORMAL,
                                       bg="#E53935", fg="white", activebackground="#D32F2F",
                                       relief="flat", padx=20, pady=10, command=self.cancelar_processamento)
        self.botao_cancelar.pack(side="left", padx=10)
        self.botao_cancelar.config(state="disabled")

        self.progress_bar = ttk.Progressbar(self.root, length=700, mode="determinate")
        self.progress_bar.pack(pady=15)

        self.status_label = tk.Label(self.root, text="Clique em “Executar” e me deixe cuidar do resto!", font=FONT_NORMAL,
                                fg="#555555", bg=cor_fundo)
        self.status_label.pack(pady=(0, 10))

        self.mensagens_text = tk.scrolledtext.ScrolledText(self.root, height=15, font=FONT_MONO,
                                                       bg="white", fg=cor_texto, state="disabled")
        self.mensagens_text.pack(padx=15, pady=(0, 20), fill="both", expand=True)

        self.mensagens_text.tag_config("header", font=("Consolas", 10, "bold"), foreground="#333333")
        self.mensagens_text.tag_config("sucesso", foreground="#2E7D32")
        self.mensagens_text.tag_config("ja_feito", foreground="#F9A825")
        self.mensagens_text.tag_config("erro", foreground="#C62828")

    def aplicar_permissoes_thread(self):
        self.cancelar.clear()
        self.acoes_realizadas.clear()
        self.botao.config(state="disabled")
        self.botao_cancelar.config(state="normal")
        self.mensagens_text.config(state="normal")
        self.mensagens_text.delete("1.0", "end")

        cabecalho = f"{'Ação':<90} | {'Status':<40}\n"
        separador = f"{'-'*90} | {'-'*40}\n"
        self.mensagens_text.insert("end", cabecalho, "header")
        self.mensagens_text.insert("end", separador, "header")

        self.atualizar_status("Configurando serviço SQL Server Express...")
        self.root.update_idletasks()

        self.progress_bar.start(10)

        msg_sql, sql_alterado = configurar_sql_delayed_start(self.cancelar, run_subprocess_with_cancel)
        self.adicionar_mensagem(msg_sql)
        if sql_alterado:
            self.acoes_realizadas.append("SQL ATRASO NA INICIALIZAÇÃO")

        self.atualizar_status("Verificando conta \"Convidado\"")
        self.root.update_idletasks()

        msg_guest, alterado_guest = desabilitar_conta_convidado(self.cancelar, run_subprocess_with_cancel)
        self.adicionar_mensagem(msg_guest)
        if alterado_guest:
            self.acoes_realizadas.append("ATIVAR FIREWALL CRIAR REGRAS - DESABILITAR CONTA CONVIDADO")

        self.atualizar_status("Verificando Firewall e criando regras")
        self.root.update_idletasks()

        msg_firewall, alterado_firewall = ativar_firewall_e_regras(self.cancelar, run_subprocess_with_cancel)
        self.adicionar_mensagem(msg_firewall)
        if alterado_firewall:
            self.acoes_realizadas.append("ATIVAR FIREWALL CRIAR REGRAS - DESABILITAR CONTA CONVIDADO")

        msg_backup, alterado_backup = criar_tarefas_backup(self.cancelar, run_subprocess_with_cancel)
        self.adicionar_mensagem(msg_backup)
        if alterado_backup:
            self.acoes_realizadas.append("CRIAR TAREFAS NO AGENDADOR DE TAREFAS DO WINDOWS PARA INICIAR SERVICOS (SQL, BACKUP CLOUD)")

        self.atualizar_status("Verificando tipo de rede (Wi-Fi / Cabeada)...")
        self.root.update_idletasks()

        self.atualizar_status("Buscando pastas para processar...")
        self.root.update_idletasks()

        pasta_fixa = os.environ.get("LOCALAPPDATA")
        pastas_para_processar = []

        if pasta_fixa and os.path.exists(pasta_fixa):
            pastas_para_processar.append(pasta_fixa)

        discos = [f"{letra}:\\" for letra in ascii_uppercase if os.path.exists(f"{letra}:\\")]

        for disco in discos:
            if self.cancelar.is_set():
                self.finalizar_processo_cancelado()
                return
            try:
                with os.scandir(disco) as entries:
                    for entry in entries:
                        if self.cancelar.is_set():
                            self.finalizar_processo_cancelado()
                            return
                        if entry.is_dir(follow_symlinks=False) and entry.name.lower().startswith("softcom"):
                            pastas_para_processar.append(entry.path)
            except Exception:
                pass

        pasta_program_files_x86 = r"C:\Program Files (x86)"
        if os.path.exists(pasta_program_files_x86):
            try:
                with os.scandir(pasta_program_files_x86) as entries:
                    for entry in entries:
                        if self.cancelar.is_set():
                            self.finalizar_processo_cancelado()
                            return
                        if entry.is_dir(follow_symlinks=False) and "softcom" in entry.name.lower():
                            pastas_para_processar.append(entry.path)
            except Exception:
                pass

        total = len(pastas_para_processar)

        self.progress_bar.stop()
        self.progress_bar.config(maximum=total if total > 0 else 1, mode="determinate")
        self.progress_bar["value"] = 0
        self.root.update_idletasks()

        self.atualizar_status("Iniciando aplicação de permissões...")

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {executor.submit(conceder_permissao, self.cancelar, run_subprocess_with_cancel, pasta): pasta for pasta in pastas_para_processar}

            for i, future in enumerate(as_completed(futures), start=1):
                if self.cancelar.is_set():
                    self.atualizar_status("Processo cancelado pelo usuário")
                    break

                pasta = futures[future]
                self.atualizar_status(f"Processando: {pasta}")
                try:
                    mensagem, alterado = future.result()
                    if alterado and "ATRIBUIR PERMISSÃO \"TODOS\"" not in self.acoes_realizadas:
                        self.acoes_realizadas.append("ATRIBUIR PERMISSÃO \"TODOS\"")
                except Exception as e:
                    mensagem = f"Permissão na pasta {pasta} - Status: Erro inesperado: {e}"

                self.adicionar_mensagem(mensagem)

                self.progress_bar["value"] = i
                self.root.update_idletasks()

        if self.cancelar.is_set():
            self.finalizar_processo_cancelado()
        else:
            self.finalizar_processo_concluido()

    def aplicar_permissoes(self):
        Thread(target=self.aplicar_permissoes_thread, daemon=True).start()

    def finalizar_processo_concluido(self):
        self.atualizar_status("Processo concluído")
        self.botao.config(state="normal")
        self.botao_cancelar.config(state="disabled")

        if self.acoes_realizadas:
            resumo = "\n------------------------------------\nAções preventivas aplicadas:\n" + "\n".join(self.acoes_realizadas) + "\n"
            self.adicionar_mensagem(resumo)

        messagebox.showinfo("Finalizado", "Processo finalizado! Veja as ações no final da lista.")

    def adicionar_linha_formatada(self, mensagem):
        if " - Status: " in mensagem:
            acao, status = mensagem.split(" - Status: ", 1)
        else:
            acao, status = mensagem, ""
        linha = f"{acao:<90} | {status:<40}\n"

        if "Alterado com sucesso" in status:
            self.mensagens_text.insert("end", linha, "sucesso")
        elif "Ação preventiva já feita anteriormente" in status:
            self.mensagens_text.insert("end", linha, "ja_feito")
        elif "Erro" in status or "Tentou alterar mas não confirmou" in status or "Cancelado" in status:
            self.mensagens_text.insert("end", linha, "erro")
        else:
            self.mensagens_text.insert("end", linha)

    def adicionar_mensagem(self, mensagem):
        self.msg_queue.put(mensagem)

    def consumir_mensagens(self):
        try:
            while True:
                msg = self.msg_queue.get_nowait()
                self.mensagens_text.config(state="normal")
                self.adicionar_linha_formatada(msg)
                self.mensagens_text.see("end")
                self.mensagens_text.config(state="disabled")
        except queue.Empty:
            pass
        self.root.after(300, self.consumir_mensagens)

    def atualizar_status(self, texto):
        self.status_label.config(text=texto)

    def cancelar_processamento(self):
        self.cancelar.set()
        self.botao_cancelar.config(state="disabled")
        self.atualizar_status("Cancelando processo...")

    def finalizar_processo_cancelado(self):
        self.atualizar_status("Processo cancelado pelo usuário")
        self.botao.config(state="normal")
        self.botao_cancelar.config(state="disabled")
        messagebox.showinfo("Cancelado", "Processo cancelado pelo usuário.")

    def _start_msg_consumer(self):
        self.root.after(300, self.consumir_mensagens)