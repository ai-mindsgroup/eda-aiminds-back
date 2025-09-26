# Prompt Base para Criação da Estrutura de Diretórios

## Passo a Passo Inicial

1. **Crie a pasta raiz do projeto:**
   ```powershell
   mkdir eda-aiminds-i2a2
   ```

2. **Acesse a pasta criada:**
   ```powershell
   cd eda-aiminds-i2a2
   ```

3. **Abra o VSCode a partir da pasta raiz:**
   ```powershell
   code .
   ```

## Comandos para Criação das Pastas do Backend

Execute os comandos abaixo para criar toda a estrutura do backend:

```powershell
mkdir eda-aiminds-back && mkdir eda-aiminds-back\src && mkdir eda-aiminds-back\src\data && mkdir eda-aiminds-back\src\embeddings && mkdir eda-aiminds-back\src\vectorstore && mkdir eda-aiminds-back\src\rag && mkdir eda-aiminds-back\src\agent && mkdir eda-aiminds-back\src\api && mkdir eda-aiminds-back\src\utils && mkdir eda-aiminds-back\notebooks && mkdir eda-aiminds-back\configs && mkdir eda-aiminds-back\tests
```

## Criação da pasta de biblioteca auxiliar

Para incluir o código base do repositório semantic_search_langchain como biblioteca auxiliar, execute:

```powershell
mkdir semantic_search_langchain
```

Certifique-se de que a pasta `semantic_search_langchain` está listada no arquivo `.gitignore` do projeto raiz para evitar o versionamento pelo Git.

## Árvore de Diretórios Criada

```
eda-aiminds-i2a2/
├── eda-aiminds-back/
│   ├── src/
│   │   ├── data/
│   │   ├── embeddings/
│   │   ├── vectorstore/
│   │   ├── rag/
│   │   ├── agent/
│   │   ├── api/
│   │   └── utils/
│   ├── notebooks/
│   ├── configs/
│   ├── tests/
│   ├── README.md
│   ├── requirements.txt
│   └── .gitignore
└── semantic_search_langchain/
```

---
