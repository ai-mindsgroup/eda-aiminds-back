#!/usr/bin/env python3
"""
Script para corrigir todas as importações relativas no projeto.

Converte:
- from analysis.xxx import yyy  →  from src.analysis.xxx import yyy
- from agent.xxx import yyy     →  from src.agent.xxx import yyy
- etc.
"""

import re
from pathlib import Path

# Módulos que precisam de prefixo 'src.'
MODULES_TO_FIX = [
    'agent',
    'vectorstore',
    'embeddings',
    'utils',
    'analysis',
    'memory',
    'llm',
    'security',
    'prompts',
    'data',
    'monitoring',
    'router',
    'services',
    'tools',
    'integrations',
    'api'
]

def fix_imports_in_file(file_path: Path) -> bool:
    """
    Corrige imports relativos em um arquivo.
    
    Returns:
        True se o arquivo foi modificado
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        modified = False
        
        # Para cada módulo, substituir import relativo por absoluto
        for module in MODULES_TO_FIX:
            # Padrão: from module.xxx import yyy
            # Mas NÃO substituir se já tiver 'src.'
            pattern = rf'^from {module}\.(\S+) import'
            replacement = rf'from src.{module}.\1 import'
            
            new_content, count = re.subn(
                pattern,
                replacement,
                content,
                flags=re.MULTILINE
            )
            
            if count > 0:
                content = new_content
                modified = True
                print(f"  ✅ {file_path.name}: Corrigido {count} import(s) de '{module}'")
        
        # Salvar se modificado
        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        
        return False
        
    except Exception as e:
        print(f"  ❌ Erro em {file_path}: {e}")
        return False


def main():
    """Corrige todos os arquivos Python em src/"""
    project_root = Path(__file__).parent
    src_dir = project_root / "src"
    
    if not src_dir.exists():
        print(f"❌ Diretório src/ não encontrado em {project_root}")
        return
    
    print("🔧 Corrigindo importações relativas em src/")
    print("=" * 60)
    
    # Encontrar todos os arquivos .py
    py_files = list(src_dir.rglob("*.py"))
    print(f"\n📂 Encontrados {len(py_files)} arquivos Python")
    
    modified_count = 0
    
    for py_file in py_files:
        if py_file.name == "__init__.py":
            continue  # Pular __init__.py por enquanto
        
        if fix_imports_in_file(py_file):
            modified_count += 1
    
    print("\n" + "=" * 60)
    print(f"✨ Concluído! {modified_count} arquivo(s) modificado(s)")
    
    if modified_count > 0:
        print("\n📝 Teste as importações com:")
        print("   python test_imports_v4.py")


if __name__ == "__main__":
    main()
