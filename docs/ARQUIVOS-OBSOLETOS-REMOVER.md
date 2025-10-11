# 🗑️ ARQUIVOS OBSOLETOS IDENTIFICADOS - 05/10/2025

## 📋 ARQUIVOS PARA REMOÇÃO

### 1. Arquivos de Teste Obsoletos (Raiz do Projeto)

Estes arquivos estão na raiz e deveriam estar em `tests/`:

```
✅ REMOVER - Testes na raiz (devem estar em tests/)
- test_rag_agent.py
- test_intervalo_correcao.py
- test_generic_csv.py
- test_chunk_parsing.py
- teste_conformidade_acesso_dados.py
- teste_correcao_rag.py
- teste_geracao_histogramas_interface.py
- teste_integracao_semantic_router.py
```

### 2. Scripts de Debug Obsoletos (Raiz do Projeto)

```
✅ REMOVER - Scripts de debug na raiz
- debug_data_check.py
- debug_enrichment_direct.py
- debug_supabase_data.py
- check_db.py
- check_full_chunk.py
- clear_embeddings.py
```

### 3. Demos e Exemplos Obsoletos (Raiz do Projeto)

```
✅ REMOVER - Demos na raiz (já existem em examples/)
- analise_creditcard_dataset.py
- analise_distribuicao_variaveis.py
- demo_sistema_corrigido.py
- demonstracao_fluxo_supabase.py
- exemplo_funcionamento_pos_conformidade.py
- interface_interativa.py
- resposta_perguntas_usuario.py
```

### 4. Arquivos de Teste Obsoletos em tests/

```
✅ REMOVER - Testes que usam agentes/funcionalidades obsoletas
- tests/test_csv_agent.py (usa CSVAnalysisAgent deprecated)
- tests/test_embeddings_compliance.py (usa EmbeddingsAnalysisAgent)
- tests/test_verificacao_dados.py (duplicado)
- tests/test_verificacao_dados_corrigida.py (duplicado)
- tests/test_pergunta_original.py (específico para bug resolvido)
- tests/test_pergunta_simplificada.py (específico para bug resolvido)
- tests/test_sistema_generico.py (redundante)
- tests/test_workflow_completo.py (obsoleto)
- tests/memory/test_memory_integration.py (usa EmbeddingsAnalysisAgent)
```

### 5. Arquivos de Documentação Obsoletos

```
✅ JÁ REMOVIDOS
- docs/AUDITORIA-CODIGO-OBSOLETO.md ✅
- docs/CORRECOES-APLICADAS.md ✅

⚠️ MANTER (histórico)
- docs/2025-10-02_1700_sessao-desenvolvimento.md
- docs/2025-10-03_correcao-hard-coding-csv-generico.md
- docs/2025-10-03_correcoes-sistema-generico-csv.md
```

### 6. Arquivos Markdown de Análise (Raiz)

```
✅ MOVER para docs/
- analise-questao-02.md → docs/bugs/analise-questao-02.md ✅ (já movido)
```

---

## 🚀 AÇÃO: REMOVER ARQUIVOS OBSOLETOS

### Script PowerShell para Remoção Segura

```powershell
# Criar backup antes de remover
$backupDir = "backup-arquivos-obsoletos-$(Get-Date -Format 'yyyy-MM-dd-HHmm')"
New-Item -ItemType Directory -Path $backupDir -Force

# Lista de arquivos para remover (raiz do projeto)
$arquivosRaiz = @(
    "test_rag_agent.py",
    "test_intervalo_correcao.py",
    "test_generic_csv.py",
    "test_chunk_parsing.py",
    "teste_conformidade_acesso_dados.py",
    "teste_correcao_rag.py",
    "teste_geracao_histogramas_interface.py",
    "teste_integracao_semantic_router.py",
    "debug_data_check.py",
    "debug_enrichment_direct.py",
    "debug_supabase_data.py",
    "check_db.py",
    "check_full_chunk.py",
    "clear_embeddings.py",
    "analise_creditcard_dataset.py",
    "analise_distribuicao_variaveis.py",
    "demo_sistema_corrigido.py",
    "demonstracao_fluxo_supabase.py",
    "exemplo_funcionamento_pos_conformidade.py",
    "interface_interativa.py",
    "resposta_perguntas_usuario.py"
)

# Lista de arquivos para remover (tests/)
$arquivosTests = @(
    "tests/test_csv_agent.py",
    "tests/test_embeddings_compliance.py",
    "tests/test_verificacao_dados.py",
    "tests/test_verificacao_dados_corrigida.py",
    "tests/test_pergunta_original.py",
    "tests/test_pergunta_simplificada.py",
    "tests/test_sistema_generico.py",
    "tests/test_workflow_completo.py",
    "tests/memory/test_memory_integration.py"
)

# Backup e remoção (raiz)
foreach ($arquivo in $arquivosRaiz) {
    if (Test-Path $arquivo) {
        Copy-Item $arquivo "$backupDir\$arquivo" -Force
        Remove-Item $arquivo -Force
        Write-Host "✅ Removido: $arquivo" -ForegroundColor Green
    }
}

# Backup e remoção (tests/)
foreach ($arquivo in $arquivosTests) {
    if (Test-Path $arquivo) {
        $destino = "$backupDir\$(Split-Path $arquivo -Leaf)"
        Copy-Item $arquivo $destino -Force
        Remove-Item $arquivo -Force
        Write-Host "✅ Removido: $arquivo" -ForegroundColor Green
    }
}

Write-Host "`n📦 Backup criado em: $backupDir" -ForegroundColor Cyan
Write-Host "✅ Remoção concluída!" -ForegroundColor Green
```

---

## 📊 ESTATÍSTICAS

### Arquivos para Remover
| Categoria | Quantidade |
|-----------|------------|
| Testes na raiz | 8 |
| Scripts debug na raiz | 6 |
| Demos na raiz | 7 |
| Testes obsoletos em tests/ | 9 |
| **TOTAL** | **30 arquivos** |

### Tamanho Estimado
- **Aproximadamente 15-20 MB** de código obsoleto
- **Redução de ~30 arquivos** no projeto
- **Melhoria de clareza** e organização

---

## ✅ PRÓXIMOS PASSOS

1. **Executar script de backup e remoção**
2. **Atualizar imports** em arquivos que ainda referenciem código removido
3. **Validar testes** restantes: `pytest tests/ -v`
4. **Commit** com mensagem descritiva
5. **Atualizar documentação** se necessário

---

**Análise realizada em:** 05/10/2025  
**Status:** Pronto para execução
