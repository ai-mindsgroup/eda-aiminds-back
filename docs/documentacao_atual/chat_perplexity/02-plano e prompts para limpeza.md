<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# crie um plano e prompts para limpeza. Os tests que ficarem, garanta que estejam todos na pasta tests/

Segue o plano detalhado com prompts para limpeza dos arquivos de teste e debug obsoletos, garantindo que os testes ativos fiquem organizados na pasta `tests/`:

***

## Plano para Limpeza e Organização dos Arquivos de Teste e Debug

### Objetivo

Limpar o repositório removendo arquivos de teste e debug obsoletos e organizando os testes ativos na pasta `tests/`.

***

### Step 1 – Identificação dos testes e arquivos debug

- [ ] Verificar todos os arquivos de teste e debug no repositório, identificando quais são obsoletos e quais são ativos.
- [ ] Confirmar que testes ativos são funcionais e utilizados no pipeline.


### Step 2 – Organização dos testes ativos

- [ ] Garantir que todos os testes ativos estejam dentro da pasta `tests/`.
- [ ] Reorganizar quaisquer testes que estiverem fora desta pasta para dentro dela.


### Step 3 – Remoção dos arquivos obsoletos

- [ ] Apagar arquivos de teste antigos, duplicados ou não utilizados.
- [ ] Apagar arquivos de debug (.log, debug_*.py, etc.) que não são mais necessários.


### Step 4 – Validação do sistema após limpeza

- [ ] Rodar os testes automatizados para garantir integridade do código.
- [ ] Verificar se a execução do pipeline não foi afetada pela remoção.

***

## Prompts para agente Copilot

### Prompt para identificar arquivos de teste e debug obsoletos

```
[translate:Identifique no repositório todos os arquivos de teste e de debug que estão obsoletos, não são utilizados no pipeline atual ou estão duplicados.]

Liste esses arquivos e sugira a exclusão deles para limpar o repositório, evitando interferência no desenvolvimento atual.
```


### Prompt para organizar testes ativos

```
[translate:Garanta que todos os testes ativos e necessários estejam organizados na pasta 'tests/'.]

Se achar testes ativos fora dessa pasta, mova-os para dentro da estrutura correta mantendo a organização e integridade.
```


### Prompt para remoção segura

```
[translate:Remova os arquivos de teste e debug obsoletos identificados, apagando do sistema de arquivos e removendo referências no código e documentação.]

Garanta que após a remoção, o pipeline funcione corretamente e os testes ativos permaneçam intactos.
```


***

Deseja que eu gere esses prompts em arquivos para controle e uso direto? Posso também ajudar a criar scripts automatizados para essa limpeza.

