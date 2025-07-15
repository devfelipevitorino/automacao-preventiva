# Automação Preventiva

## Descrição

Este projeto consiste em uma aplicação Python com interface gráfica para automatizar diversas ações preventivas relacionadas à infraestrutura de TI, como configuração do SQL Server Express, desativação da conta Convidado, configuração do firewall, criação de tarefas de backup e concessão de permissões em pastas específicas. O objetivo é facilitar a manutenção do ambiente Softcom com um clique, oferecendo feedback visual claro sobre o status de cada ação.

---

## Estrutura do Projeto

- `main.py`: arquivo principal que instancia a interface e inicia o programa.
- `aplicador.py`: contém a classe `AplicadorAcoesPreventivas` que gerencia a interface gráfica, threads e execução das ações.
- `acoes_preventivas.py`: módulo onde ficam implementadas as funções específicas que realizam as ações (exemplo: configurar SQL, ativar firewall, conceder permissões).

---

## Funcionalidades Principais

### Interface Gráfica (Tkinter)

- Tela centralizada, tamanho fixo de 950x480 px.
- Botões:
  - **Executar**: inicia as ações preventivas em threads para não travar a interface.
  - **Cancelar**: permite cancelar a execução em andamento.
- Barra de progresso visual indicando o andamento da concessão de permissões nas pastas Softcom.
- Caixa de texto com mensagens detalhadas e coloridas (sucesso, aviso, erro, cabeçalhos).
- Indicador de status textual que mostra o que está acontecendo.

### Execução das Ações Preventivas

- Funções executadas sequencialmente:
  - Configurar inicialização atrasada do SQL Server Express.
  - Desativar conta Convidado do Windows.
  - Ativar firewall e regras de segurança.
  - Criar tarefas agendadas de backup.
- Execução paralela:
  - Concessão de permissões em múltiplas pastas que contêm "Softcom" no nome, encontradas em diversas unidades e locais do sistema.

### Mensagens Formatadas

- Mensagens exibem a ação e o status em colunas alinhadas.
- Cores específicas para status:
  - Verde para ações alteradas com sucesso.
  - Amarelo para ações já feitas anteriormente.
  - Vermelho para erros, timeouts ou cancelamentos.
- Finaliza com um resumo das ações que foram realmente aplicadas.

---

## Detalhes Técnicos Importantes

- **Threading e concorrência:** Utiliza `ThreadPoolExecutor` para acelerar a concessão de permissões, limitando o número máximo de threads para 2.
- **Cancelamento:** Um objeto `threading.Event()` é utilizado para sinalizar quando o usuário deseja cancelar a execução. As funções que realizam ações devem verificar esse evento para parar quando solicitado.
- **Atualização da interface:** Como Tkinter não é thread-safe, toda atualização da interface ocorre dentro do thread principal usando métodos seguros, ou com uso de filas/métodos agendados com `root.after`.

---

## Guia de Uso

1. Execute o programa.
2. Clique em **Executar** para iniciar as ações preventivas.
3. Acompanhe o progresso na barra e nas mensagens.
4. Ao final, confira o resumo das ações que foram realmente aplicadas.

---

## Exemplo de Saída na Caixa de Mensagens

| Ação                                     | Status                      |
| ---------------------------------------- | --------------------------- |
| Configurar inicialização atrasada do SQL | Alterado com sucesso        |
| Desativar conta Convidado                | Ação já feita anteriormente |
| --- Ações realizadas ---                 |                             |
| SQL INICIALIZAÇÂO ATRASADA               |                             |


## Executar

[Download do Preventive Automation v1.0.4](https://github.com/devfelipevitorino/automacao-preventiva/releases/download/v1.0.4/acao_preventiva_v1.0.4.rar) 
