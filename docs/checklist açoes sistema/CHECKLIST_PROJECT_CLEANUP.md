<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# Sim por favor

Segue o conteúdo proposto do arquivo **CHECKLIST_PROJECT_CLEANUP.md**, pronto para ser adicionado à raiz do repositório e versionado. Ele foi desenhado para acompanhar o progresso das iterações, garantir a integração das funcionalidades no script principal e supervisionar a limpeza final do projeto.

***

# **CHECKLIST_PROJECT_CLEANUP.md**

## 🧭 EDA AI Minds – Controle de Refatoração e Limpeza

### **Objetivo Macro 1 – Agente funcional e interpretativo via LLM**

**Meta:** garantir que o agente interprete perguntas, gere respostas humanizadas e diretas, sem análises desnecessárias.

#### Step 1 – Diagnóstico e Preparação

- [ ] Confirmar que `src/agent/rag_data_agent_v4.py` é o módulo importado no `scripts/setup_and_run_interface_interativa_v3.py`.
- [ ] Verificar dependências de LangChain, Supabase e logging estruturado.
- [ ] Remover chamadas de teste externas e imports desnecessários.


#### Step 2 – Teste direto no script principal

- [ ] Adicionar bloco de testes dentro de `setup_and_run_interface_interativa_v3.py`:

```python
if __name__ == "__main__":
    print("🧠 Teste rápido de interpretação LLM")
    pergunta = "Qual o desvio padrão e variância do conjunto de dados?"
    resposta = agente.executar_instrucao(pergunta)
    print("Resposta:", resposta)
```

- [ ] Garantir logs de debug e re-tentativa de conexão LLM/Supabase.
- [ ] Validar fluxo de execução completo sem arquivos `test_*.py`.


#### Step 3 – Validação funcional integrada

- [ ] Testar múltiplas métricas numa única pergunta.
- [ ] Testar pedidos genéricos (“faça uma análise geral”) para LLM.
- [ ] Verificar formato e tom das respostas (humanizadas, sem prolixidade).
- [ ] Corrigir eventuais problemas diretamente no mesmo arquivo.


#### Step 4 – Documentação mínima viva

- [ ] Adicionar docstring inicial no script:
    - Data da última atualização.
    - Versão do agente utilizada.
    - Lista de módulos e funções integradas.
- [ ] Confirmar rastreamento no Git das alterações aplicadas.

***

### **Objetivo Macro 2 – Sanitização e Organização do Repositório**

**Meta:** manter o repositório limpo, com apenas versões estáveis e documentação viva.

#### Step 5 – Estrutura de limpeza e versionamento

- [ ] Criar branch `final-cleanup`.
- [ ] Realizar backup local da `main` antes das exclusões.
- [ ] Validar árvore de diretórios e dependências cruzadas.


#### Step 6 – Remoção e estruturação final

- [ ] Remover versões antigas (`v1`, `v2`, debug scripts).
- [ ] Deletar arquivos de teste (`test_*.py`) e logs (`*.log`).
- [ ] Excluir documentos e pastas antigas ou sem uso.
- [ ] Manter:
    - `src/agent/rag_data_agent_v4.py`
    - `scripts/setup_and_run_interface_interativa_v3.py`
    - Documentos centrais (`steps_correção.md`, `abstracao_camada_ia.pdf`)


#### Step 7 – Publicação e release final

- [ ] Atualizar README com a estrutura final do projeto.
- [ ] Confirmar execução estável do agente.
- [ ] Criar tag de versão:

```bash
git tag -a v5.0-release --message "Versão final limpa e integrada do agente"
git push origin v5.0-release
```


***

Deseja que este arquivo seja salvo automaticamente no repositório com o nome **CHECKLIST_PROJECT_CLEANUP.md** para iniciar o controle de progresso? Isso permitirá acompanhar e marcar o andamento diretamente no Git.

