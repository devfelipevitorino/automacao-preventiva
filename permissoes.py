import subprocess
import time
import re

def run_subprocess_with_cancel(cancel_event, cmd, timeout=None):
    try:
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        start = time.time()
        while True:
            if cancel_event.is_set():
                proc.kill()
                return None, None, "cancelado"
            retcode = proc.poll()
            if retcode is not None:
                stdout, stderr = proc.communicate()
                return retcode, stdout, stderr
            if timeout and (time.time() - start) > timeout:
                proc.kill()
                return None, None, "timeout"
            time.sleep(0.1)
    except Exception as e:
        return None, None, str(e)


def configurar_sql_delayed_start(cancel_event, run_subprocess):
    check_cmd = r'reg query "HKLM\SYSTEM\CurrentControlSet\Services\MSSQL$SQLEXPRESS" /v DelayedAutoStart'
    ret, out, err = run_subprocess(cancel_event, check_cmd)
    if err == "cancelado":
        return "Serviço SQL Server Express (ATRASO NA INICIALIZAÇÃO) - Status: Cancelado pelo usuário", False
    if ret == 0 and "0x1" in out:
        return "Serviço SQL Server Express (ATRASO NA INICIALIZAÇÃO) - Status: Ação preventiva já feita anteriormente", False

    cmd = 'sc config "MSSQL$SQLEXPRESS" start= delayed-auto'
    ret, out, err = run_subprocess(cancel_event, cmd)
    if err == "cancelado":
        return "Serviço SQL Server Express (ATRASO NA INICIALIZAÇÃO) - Status: Cancelado pelo usuário", False
    if ret == 0:
        ret2, out2, err2 = run_subprocess(cancel_event, check_cmd)
        if err2 == "cancelado":
            return "Serviço SQL Server Express (ATRASO NA INICIALIZAÇÃO) - Status: Cancelado pelo usuário", False
        if ret2 == 0 and "0x1" in out2:
            return "Serviço SQL Server Express (ATRASO NA INICIALIZAÇÃO) - Status: Alterado com sucesso", True
        else:
            return "Serviço SQL Server Express (ATRASO NA INICIALIZAÇÃO) - Status: Tentou alterar mas não confirmou", False
    else:
        return f"Serviço SQL Server Express (ATRASO NA INICIALIZAÇÃO) - Status: Erro ao aplicar configuração: {err.strip() if err else ''}", False


def conceder_permissao(cancel_event, run_subprocess, pasta):
    grupos = ['Todos', 'Everyone', '*S-1-1-0']
    for grupo in grupos:
        if cancel_event.is_set():
            return f"Permissão na pasta {pasta} - Status: Cancelado pelo usuário", False

        try:
            check_cmd = f'icacls "{pasta}"'
            ret, out, err = run_subprocess(cancel_event, check_cmd)
            if err == "cancelado":
                return f"Permissão na pasta {pasta} - Status: Cancelado pelo usuário", False
            if ret == 0 and grupo in out and '(F)' in out:
                return f"Permissão na pasta {pasta} - Status: Ação preventiva já feita anteriormente", False

            if grupo == '*S-1-1-0':
                cmd = f'icacls "{pasta}" /grant {grupo}:(OI)(CI)F'
            else:
                cmd = f'icacls "{pasta}" /grant "{grupo}":(OI)(CI)F'

            timeout_val = 120 if 'appdata\\local' in pasta.lower() else 60
            ret2, out2, err2 = run_subprocess(cancel_event, cmd, timeout=timeout_val)
            if err2 == "cancelado":
                return f"Permissão na pasta {pasta} - Status: Cancelado pelo usuário", False
            if err2 == "timeout":
                return f"Permissão na pasta {pasta} - Status: Erro ao aplicar permissão (timeout)", False
            if ret2 == 0:
                return f"Permissão na pasta {pasta} - Status: Alterado com sucesso", True
            else:
                return f"Permissão na pasta {pasta} - Status: Erro ao aplicar permissão: {err2.strip() if err2 else ''}", False

        except Exception as e:
            return f"Permissão na pasta {pasta} - Status: Erro ao aplicar permissão: {e}", False

    return f"Permissão na pasta {pasta} - Status: Erro ao aplicar permissão", False


def desabilitar_conta_convidado(cancel_event, run_subprocess):
    list_cmd = 'net user'
    ret, out, err = run_subprocess(cancel_event, list_cmd)
    if err == "cancelado":
        return "Conta Convidado - Status: Cancelado pelo usuário", False
    if ret != 0:
        return "Conta Convidado - Status: Erro ao listar usuários", False

    contas = out.split()
    conta_convidado = None
    for nome_conta in ['guest', 'convidado']:
        for conta in contas:
            if conta.lower() == nome_conta:
                conta_convidado = conta
                break
        if conta_convidado:
            break

    if not conta_convidado:
        return "Conta Convidado - Status: Conta não existe ou foi renomeada", False

    check_cmd = f'net user "{conta_convidado}"'
    ret, out, err = run_subprocess(cancel_event, check_cmd)
    if err == "cancelado":
        return "Conta Convidado - Status: Cancelado pelo usuário", False
    if ret != 0:
        return "Conta Convidado - Status: Erro ao consultar status da conta", False

    ja_desativada = False
    for line in out.splitlines():
        if "Conta ativa" in line:
            valor = line.split("Conta ativa")[-1].strip().lower()
            if re.match(r'n.?o', valor):
                ja_desativada = True
            break

    if ja_desativada:
        return "Conta Convidado - Status: Ação preventiva já feita anteriormente", False

    cmd = f'net user "{conta_convidado}" /active:no'
    ret, out, err = run_subprocess(cancel_event, cmd)
    if err == "cancelado":
        return "Conta Convidado - Status: Cancelado pelo usuário", False
    if ret == 0:
        return "Conta Convidado - Status: Alterado com sucesso", True
    else:
        return f"Conta Convidado - Status: Erro: {err.strip() if err else ''}", False


def ativar_firewall_e_regras(cancel_event, run_subprocess):
    ret, out, err = run_subprocess(cancel_event, 'netsh advfirewall show allprofiles state')
    if err == "cancelado":
        return "Firewall e regras - Status: Cancelado pelo usuário", False
    if ret != 0:
        return f"Firewall e regras - Status: Erro ao verificar firewall: {err.strip() if err else ''}", False

    firewall_ativo = all(profile_state.upper() == "ON" for profile_state in
                         [line.split()[-1] for line in out.splitlines() if "State" in line])

    if not firewall_ativo:
        ret, out, err = run_subprocess(cancel_event, 'netsh advfirewall set allprofiles state on')
        if err == "cancelado":
            return "Firewall e regras - Status: Cancelado pelo usuário", False
        if ret != 0:
            return f"Firewall e regras - Status: Erro ao ativar firewall: {err.strip() if err else ''}", False

    regras = {
        1433: ["TCP"],
        5433: ["TCP"],
        7711: ["TCP"],
        4009: ["TCP"],
        8081: ["TCP"],
        3306: ["TCP"],
        135:  ["TCP"],
        443:  ["TCP"],
        1434: ["TCP", "UDP"]
    }

    regras_necessarias = []
    for porta, protocolos in regras.items():
        for protocolo in protocolos:
            regras_necessarias.append((f"SOFTCOM {porta} Entrada {protocolo}", "in", porta, protocolo))
            regras_necessarias.append((f"SOFTCOM {porta} Saida {protocolo}", "out", porta, protocolo))

    regras_faltando = []
    for nome_regra, direcao, porta, protocolo in regras_necessarias:
        cmd_verifica = f'netsh advfirewall firewall show rule name="{nome_regra}"'
        ret_r, out_r, err_r = run_subprocess(cancel_event, cmd_verifica)
        if ret_r != 0 or ("não encontrado" in (out_r or "").lower() or "no rules match" in (out_r or "").lower()):
            regras_faltando.append((nome_regra, direcao, porta, protocolo))

    if firewall_ativo and not regras_faltando:
        return "Firewall e regras - Status: Ação preventiva já feita anteriormente", False

    sucesso_total = True
    for nome_regra, direcao, porta, protocolo in regras_faltando:
        if cancel_event.is_set():
            return "Firewall e regras - Status: Cancelado pelo usuário", False
        cmd_add = (
            f'netsh advfirewall firewall add rule name="{nome_regra}" '
            f'dir={direcao} action=allow protocol={protocolo} localport={porta}'
        )
        ret_c, out_c, err_c = run_subprocess(cancel_event, cmd_add)
        if ret_c != 0:
            sucesso_total = False

    if sucesso_total:
        return "Firewall e regras - Status: Alterado com sucesso", True
    else:
        return "Firewall e regras - Status: Erro ao criar regras do firewall", False

        
def criar_tarefas_backup(cancel_event, run_subprocess):
    ret, out, err = run_subprocess(cancel_event, 'sc queryex SOFTCOMBACKUP')
    if cancel_event.is_set():
        return "Agendador Backup - Status: Cancelado pelo usuário", False

    if ret != 0 or ("não existe" in (out or "").lower() or "does not exist" in (out or "").lower()):
        return "Agendador Backup - Status: Serviço SOFTCOMBACKUP não encontrado", False

    horarios = ["07:00", "12:00", "16:00", "20:00"]
    tarefas_diarias = [
        (f"Iniciar_SOFTCOMBACKUP_{h.replace(':', '_')}", f"net start SOFTCOMBACKUP", "daily", h)
        for h in horarios
    ]

    tarefa_onstart = ("Iniciar_SOFTCOMBACKUP_Ao_Iniciar", "net start SOFTCOMBACKUP", "onstart", None)

    todas_tarefas = tarefas_diarias + [tarefa_onstart]

    tarefas_faltando = []

    for nome, comando, tipo, hora in todas_tarefas:
        if cancel_event.is_set():
            return "Agendador Backup - Status: Cancelado pelo usuário", False

        ret, out, err = run_subprocess(cancel_event, f'schtasks /Query /TN "{nome}"')
        if ret != 0 or ("não encontrado" in (out or "").lower() or "não existe" in (out or "").lower()):
            tarefas_faltando.append((nome, comando, tipo, hora))

    if not tarefas_faltando:
        return "Agendador Backup - Status: Ação preventiva já feita anteriormente", False

    sucesso_total = True
    for nome, comando, tipo, hora in tarefas_faltando:
        if cancel_event.is_set():
            return "Agendador Backup - Status: Cancelado pelo usuário", False

        if tipo == "daily" and hora:
            cmd = f'schtasks /create /tn "{nome}" /tr "{comando}" /sc daily /st {hora} /f'
        elif tipo == "onstart":
            cmd = f'schtasks /create /tn "{nome}" /tr "{comando}" /sc onstart /f'
        else:
            continue

        ret, out, err = run_subprocess(cancel_event, cmd)
        if ret != 0:
            sucesso_total = False

    if sucesso_total:
        return "Agendador Backup - Status: Tarefas criadas com sucesso", True
    else:
        return "Agendador Backup - Status: Erro ao criar algumas tarefas", False


def verificar_rede_wifi(cancel_event, run_subprocess):
    ret, out, err = run_subprocess(cancel_event, 'netsh wlan show interfaces')
    if err == "cancelado":
        return "REDE SEM FIO - Status: Cancelado pelo usuário", False
    if ret != 0:
        return f"REDE SEM FIO - Status: Erro ao verificar Wi-Fi: {err.strip() if err else ''}", False

    texto = out.lower()
    if "connected" in texto or "conectado" in texto:
        return "REDE SEM FIO - Status: Recomendação - Evitar uso de Wi-Fi", True
    else:
        return "REDE SEM FIO - Status: Computador conectado por cabo", False
