# Problema de Caracteres Estranhos no Terminal Windows

**Data**: 2025-10-21  
**Sistema**: Windows 10/11 + PowerShell  
**Status**: ⚠️ PARCIALMENTE RESOLVIDO

## O Problema

Ao executar testes Python no PowerShell do Windows, emojis e caracteres UTF-8 especiais aparecem corrompidos:

### Exemplos de Corrupção:
- 📊 → `≡ƒôè`
- ✅ → `Γ£à`
- 🔹 → `≡ƒôî`
- ─ → `ΓöÇ`
- ❌ → `Γ¥î`

### Saída no Terminal:
```
{"message": "≡ƒôè Query analisada: SIMPLE | Categoria: statistics"
Γ£à TESTE 2 PASSOU - Cache e hist├│rico funcionando
ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ (linhas de separação)
```

## Causa Raiz

O **Windows PowerShell usa codificação padrão Windows-1252** (ou similar), que **não suporta caracteres UTF-8 multibyte** como emojis.

Python gera logs em **UTF-8**, mas o PowerShell interpreta como **Windows-1252**, resultando em caracteres corrompidos.

## Solução Implementada

### 1. Reconfigurar stdout/stderr para UTF-8

**Arquivo**: `test_hybrid_processor_v2_etapa2_completo.py` (linhas 17-25)

```python
import sys
import os

# Configurar encoding UTF-8 para Windows PowerShell
if sys.platform == 'win32':
    # Configurar stdout/stderr para UTF-8
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')
    # Definir codepage UTF-8 no console Windows
    os.system('chcp 65001 > nul 2>&1')
```

### O que isso faz:
1. **`sys.stdout.reconfigure(encoding='utf-8')`**: Força Python a usar UTF-8 no stdout
2. **`sys.stderr.reconfigure(encoding='utf-8')`**: Força Python a usar UTF-8 no stderr
3. **`chcp 65001`**: Altera o codepage do console Windows para UTF-8 (65001)
4. **`> nul 2>&1`**: Suprime a mensagem "Active code page: 65001"

## Resultado da Correção

### ✅ Funcionou Parcialmente

**Saída Direta do Script**:
```python
python test.py
================================================================================
🧪 TESTE 6: VARIAÇÕES LINGUÍSTICAS - QUERYANALYZER
================================================================================
✅ 'Qual a média de Amount?...'
      → simple | statistics
```
✅ Emojis aparecem corretamente

**Saída Redirecionada/Filtrada**:
```powershell
python test.py 2>&1 | Select-String -Pattern "TESTE"
≡ƒº¬ TESTE 6: VARIA├ç├òES LINGU├ìSTICAS - QUERYANALYZER
```
❌ Ainda aparecem caracteres corrompidos

### Por que o redirecionamento ainda falha?

Quando você usa `2>&1 | Select-String`, o PowerShell:
1. **Captura** a saída do Python
2. **Reconverte** de UTF-8 para Windows-1252 internamente
3. **Passa** para `Select-String` em Windows-1252
4. **Exibe** caracteres corrompidos

## Soluções Alternativas

### Opção 1: Executar Diretamente (SEM Redirecionamento) ✅
```powershell
python test_hybrid_processor_v2_etapa2_completo.py
```
**Vantagem**: Emojis aparecem corretamente  
**Desvantagem**: Muito output (não filtrado)

### Opção 2: Configurar PowerShell para UTF-8 Permanentemente ⚠️
```powershell
# Adicionar ao perfil do PowerShell (~\Documents\PowerShell\Microsoft.PowerShell_profile.ps1)
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$PSDefaultParameterValues['Out-File:Encoding'] = 'utf8'
```

**Vantagem**: Funciona globalmente  
**Desvantagem**: Pode afetar outros scripts

### Opção 3: Usar Windows Terminal em vez de PowerShell Clássico ✅
O **Windows Terminal** suporta UTF-8 nativamente e exibe emojis corretamente.

```powershell
# Instalar Windows Terminal (se não tiver)
winget install Microsoft.WindowsTerminal
```

**Vantagem**: Suporte nativo a UTF-8, melhor renderização de emojis  
**Desvantagem**: Requer instalação separada

### Opção 4: Remover Emojis do Código (Não Recomendado) ❌
```python
logger.info("Query analisada: SIMPLE")  # Sem emoji
```

**Vantagem**: Funciona em qualquer terminal  
**Desvantagem**: Logs menos legíveis e visualmente menos atraentes

### Opção 5: Usar `Out-String -Width` com Encoding Explícito 🔄
```powershell
python test.py 2>&1 | Out-String -Width 200 | Select-String -Pattern "TESTE"
```

**Vantagem**: Às vezes preserva caracteres UTF-8  
**Desvantagem**: Inconsistente, depende da versão do PowerShell

## Recomendação Final

### Para Desenvolvimento Diário:
✅ **Use Windows Terminal** com PowerShell 7+
```powershell
wt powershell
python test_hybrid_processor_v2_etapa2_completo.py
```

### Para CI/CD (GitHub Actions, etc.):
✅ **Remova emojis dos logs críticos** OU use logging estruturado JSON
```python
# Em vez de:
logger.info("✅ Teste passou")

# Use:
logger.info("PASSED - Test completed successfully")
# OU
logger.info(json.dumps({"status": "passed", "message": "Test completed"}))
```

### Para Logs Locais:
✅ **Mantenha emojis** - são úteis para legibilidade
✅ **Execute diretamente** (sem redirecionamento) ou use Windows Terminal

## Limitações Conhecidas

1. **PowerShell 5.x** (versão padrão do Windows) tem suporte limitado a UTF-8
2. **Redirecionamento de saída** (`2>&1 | `) sempre converte para Windows-1252
3. **Compatibilidade retroativa**: Não podemos forçar todos os desenvolvedores a usar Windows Terminal

## Status Atual

✅ **Correção implementada**: `sys.stdout.reconfigure(encoding='utf-8')`  
⚠️ **Funciona**: Execução direta do script  
❌ **Não funciona**: Redirecionamento com `2>&1 |`  
📝 **Documentado**: Soluções alternativas fornecidas  

## Próximos Passos

- [ ] Considerar adicionar flag `--no-emoji` para execuções em ambientes CI/CD
- [ ] Documentar no README.md a necessidade de Windows Terminal para melhor experiência
- [ ] Avaliar migração de logs visuais (emojis) para logging estruturado JSON em produção

---

**Conclusão**: O problema foi **parcialmente resolvido**. Para melhor experiência, recomendamos usar **Windows Terminal** ou executar scripts **sem redirecionamento de saída**.
