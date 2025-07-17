# 🛡️ Automação Preventiva

## 📝 Descrição

Este projeto foi desenvolvido para apoiar e melhorar os processos de rotina no trabalho de Service Desk N1.  
Trata-se de uma aplicação em **Python com interface gráfica** que automatiza diversas ações preventivas relacionadas à infraestrutura de TI.

---

## 🎯 Objetivo

Padronizar e automatizar ações críticas de segurança e configuração em ambientes Windows, garantindo:
- 🔒 Menor risco de falhas manuais.
- 📋 Conformidade com políticas de segurança.
- ⏱️ Redução de tempo operacional.

---

## 📂 Estrutura do Projeto

- `main.py` – Arquivo principal que instancia a interface e inicia o programa.
- `aplicador.py` – Contém a classe `AplicadorPermissoes` que gerencia a interface gráfica, threads e execução das ações.
- `acoes_preventivas.py` – Módulo onde ficam implementadas as funções específicas que realizam as ações (ex.: configurar SQL, ativar firewall, conceder permissões).

---

## ⚙️ Funcionalidades

### 📁 Permissões em Pastas
- **O que faz:** Verifica e aplica permissões corretas em pastas críticas do sistema e do ERP.
- ✅ **Benefício:** Evita bloqueios de escrita/leitura por falta de permissões.

---

### 🔥 Regras de Firewall
- **O que faz:** Cria e aplica regras para liberar portas e serviços essenciais.
- 🛡️ **Benefício:** Garante comunicação segura sem abrir portas desnecessárias.

---

### 🚫 Desativação de Conta Convidado
- **O que faz:** Desativa a conta `Convidado` do Windows se estiver ativa.

---

### 💾 Inicialização do Backup (opcional)
- **O que faz:** Verifica se o serviço de backup contratado está configurado e ativo na inicialização.
- 🔄 **Benefício:** Garante continuidade de backups automáticos, conforme contrato.

---

## 🛠️ Detalhes Técnicos Importantes

- 🧵 **Threading e concorrência:** Utiliza `ThreadPoolExecutor` para acelerar a concessão de permissões, limitando o número máximo de threads para 2.
- ❌ **Cancelamento:** Um objeto `threading.Event()` sinaliza quando o usuário deseja cancelar a execução. As funções que realizam ações verificam esse evento para parar de forma controlada.

---

## 🚀 Benefícios Esperados

- ⚡ Redução de tempo de configuração em implantações.
- ✋ Menor probabilidade de erros manuais.
- 🏢 Padronização de segurança em todos os clientes.
- 🔧 Pronto para ser adaptado ou expandido (ex.: monitoramento, relatórios automáticos).

---

## 🖥️ Guia de Uso

1. ▶️ Execute o programa como **administrador**.
2. ✅ Clique em **Executar** para iniciar as ações preventivas.
3. 📊 Acompanhe o progresso na barra e nas mensagens.
4. 📄 Ao final, confira o resumo das ações que foram realmente aplicadas.

---

## 📦 Exemplo de Saída na Caixa de Mensagens

| 🛠️ Ação                                     | 📊 Status                      |
| ------------------------------------------- | ----------------------------- |
| Configurar inicialização atrasada do SQL    | Alterado com sucesso          |
| Desativar conta Convidado                   | Ação já feita anteriormente  |
| --- Ações realizadas ---                    |                               |
| SQL INICIALIZAÇÃO ATRASADA                  |                               |

---

## 📥 Executar

[⬇️ Download do Preventive Automation v1.0.7](https://github.com/devfelipevitorino/automacao-preventiva/releases/download/v1.0.7/acao_preventiva_v1.0.7.rar)
