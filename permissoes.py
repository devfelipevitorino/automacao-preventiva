import subprocess
import time

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
