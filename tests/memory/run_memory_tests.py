"""
Script de execução e configuração dos testes de memória.

Este módulo configura e executa todos os testes do sistema de memória,
fornecendo relatórios detalhados e configurações específicas.
"""

import pytest
import sys
import os
from datetime import datetime
from pathlib import Path
import subprocess
import json
from typing import Dict, List, Any

# Adicionar o diretório src ao path para importações
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

def setup_test_environment():
    """Configurar ambiente de teste."""
    print("🔧 Configurando ambiente de teste de memória...")
    
    # Verificar dependências
    required_packages = [
        "pytest",
        "pytest-asyncio", 
        "pandas",
        "supabase",
        "python-dotenv"
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Pacotes faltando: {', '.join(missing_packages)}")
        print(f"💡 Execute: pip install {' '.join(missing_packages)}")
        return False
    
    print("✅ Todas as dependências estão disponíveis")
    return True

def run_memory_tests(test_type: str = "all", verbose: bool = True) -> Dict[str, Any]:
    """
    Executar testes de memória.
    
    Args:
        test_type: Tipo de teste ("unit", "integration", "performance", "all")
        verbose: Se deve usar output verboso
    
    Returns:
        Resultado dos testes
    """
    print(f"🧪 Executando testes de memória: {test_type}")
    
    # Mapear tipos de teste para arquivos
    test_files = {
        "unit": ["test_memory_system.py"],
        "integration": ["test_memory_integration.py"],
        "performance": ["test_memory_performance.py"],
        "all": [
            "test_memory_system.py",
            "test_memory_integration.py", 
            "test_memory_performance.py"
        ]
    }
    
    if test_type not in test_files:
        print(f"❌ Tipo de teste inválido: {test_type}")
        return {"success": False, "error": "Invalid test type"}
    
    # Configurar argumentos do pytest
    pytest_args = []
    
    # Adicionar arquivos de teste
    test_dir = Path(__file__).parent
    for test_file in test_files[test_type]:
        file_path = test_dir / test_file
        if file_path.exists():
            pytest_args.append(str(file_path))
    
    # Configurações do pytest
    if verbose:
        pytest_args.extend(["-v", "-s"])
    else:
        pytest_args.append("-q")
    
    # Configurar para testes assíncronos
    pytest_args.extend([
        "--tb=short",
        "--asyncio-mode=auto"
    ])
    
    # Executar testes
    start_time = datetime.now()
    
    try:
        exit_code = pytest.main(pytest_args)
        success = exit_code == 0
    except Exception as e:
        print(f"❌ Erro ao executar testes: {e}")
        success = False
        exit_code = -1
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    result = {
        "success": success,
        "exit_code": exit_code,
        "duration_seconds": duration,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "test_type": test_type,
        "test_files": test_files[test_type]
    }
    
    if success:
        print(f"✅ Testes concluídos com sucesso em {duration:.2f}s")
    else:
        print(f"❌ Testes falharam (código: {exit_code}) em {duration:.2f}s")
    
    return result

def run_coverage_analysis():
    """Executar análise de cobertura de código."""
    print("📊 Executando análise de cobertura...")
    
    try:
        # Verificar se pytest-cov está disponível
        import pytest_cov
    except ImportError:
        print("⚠️ pytest-cov não encontrado. Instalando...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pytest-cov"])
    
    # Executar testes com cobertura
    test_dir = Path(__file__).parent
    coverage_args = [
        "--cov=src.memory",
        "--cov-report=html:tests/memory/coverage_html",
        "--cov-report=term-missing",
        str(test_dir / "test_memory_system.py"),
        str(test_dir / "test_memory_integration.py")
    ]
    
    try:
        exit_code = pytest.main(coverage_args)
        if exit_code == 0:
            print("✅ Análise de cobertura concluída")
            print("📁 Relatório HTML: tests/memory/coverage_html/index.html")
        else:
            print("❌ Erro na análise de cobertura")
        return exit_code == 0
    except Exception as e:
        print(f"❌ Erro ao executar cobertura: {e}")
        return False

def validate_memory_system():
    """Validar sistema de memória completo."""
    print("🔍 Validando sistema de memória...")
    
    validations = []
    
    # 1. Verificar estrutura de arquivos
    memory_dir = Path(__file__).parent.parent.parent / "src" / "memory"
    required_files = [
        "__init__.py",
        "base_memory.py",
        "supabase_memory.py", 
        "memory_types.py",
        "memory_utils.py"
    ]
    
    for file_name in required_files:
        file_path = memory_dir / file_name
        exists = file_path.exists()
        validations.append({
            "check": f"Arquivo {file_name}",
            "status": "✅" if exists else "❌",
            "passed": exists
        })
    
    # 2. Verificar migrations
    migrations_dir = Path(__file__).parent.parent.parent / "migrations"
    memory_migration = migrations_dir / "0005_agent_memory_tables.sql"
    migration_exists = memory_migration.exists()
    validations.append({
        "check": "Migration de memória",
        "status": "✅" if migration_exists else "❌",
        "passed": migration_exists
    })
    
    # 3. Verificar integração com agentes
    agent_dir = Path(__file__).parent.parent.parent / "src" / "agent"
    agent_files = ["base_agent.py", "orchestrator_agent.py", "csv_analysis_agent.py", "rag_agent.py"]
    
    for agent_file in agent_files:
        agent_path = agent_dir / agent_file
        if agent_path.exists():
            content = agent_path.read_text(encoding='utf-8')
            has_memory = "memory" in content.lower() or "MemoryMixin" in content
            validations.append({
                "check": f"Integração de memória em {agent_file}",
                "status": "✅" if has_memory else "❌", 
                "passed": has_memory
            })
        else:
            validations.append({
                "check": f"Arquivo {agent_file}",
                "status": "❌",
                "passed": False
            })
    
    # 4. Verificar testes
    test_files = ["test_memory_system.py", "test_memory_integration.py", "test_memory_performance.py"]
    for test_file in test_files:
        test_path = Path(__file__).parent / test_file
        exists = test_path.exists()
        validations.append({
            "check": f"Teste {test_file}",
            "status": "✅" if exists else "❌",
            "passed": exists
        })
    
    # Imprimir resultados
    print("\n📋 Resultado da Validação:")
    print("=" * 50)
    
    all_passed = True
    for validation in validations:
        print(f"{validation['status']} {validation['check']}")
        if not validation['passed']:
            all_passed = False
    
    print("=" * 50)
    
    if all_passed:
        print("🎉 Sistema de memória está completamente implementado!")
    else:
        failed_count = sum(1 for v in validations if not v['passed'])
        print(f"⚠️ {failed_count} verificações falharam")
    
    return all_passed, validations

def generate_test_report():
    """Gerar relatório completo de testes."""
    print("📝 Gerando relatório de testes...")
    
    # Executar validação
    system_valid, validations = validate_memory_system()
    
    # Executar testes
    test_results = {}
    for test_type in ["unit", "integration", "performance"]:
        print(f"\n--- Executando testes {test_type} ---")
        result = run_memory_tests(test_type, verbose=False)
        test_results[test_type] = result
    
    # Criar relatório
    report = {
        "timestamp": datetime.now().isoformat(),
        "system_validation": {
            "passed": system_valid,
            "details": validations
        },
        "test_results": test_results,
        "summary": {
            "total_test_types": len(test_results),
            "passed_test_types": sum(1 for r in test_results.values() if r.get('success', False)),
            "system_complete": system_valid,
            "total_duration": sum(r.get('duration_seconds', 0) for r in test_results.values())
        }
    }
    
    # Salvar relatório
    report_file = Path(__file__).parent / f"memory_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Relatório salvo: {report_file}")
    except Exception as e:
        print(f"❌ Erro ao salvar relatório: {e}")
    
    # Imprimir resumo
    print("\n📊 RESUMO FINAL:")
    print("=" * 50)
    print(f"Sistema válido: {'✅' if system_valid else '❌'}")
    print(f"Tipos de teste executados: {report['summary']['total_test_types']}")
    print(f"Tipos de teste aprovados: {report['summary']['passed_test_types']}")
    print(f"Duração total: {report['summary']['total_duration']:.2f}s")
    
    if system_valid and report['summary']['passed_test_types'] == report['summary']['total_test_types']:
        print("🎉 SISTEMA DE MEMÓRIA COMPLETAMENTE FUNCIONAL!")
    else:
        print("⚠️ Há problemas que precisam ser resolvidos")
    
    return report

def main():
    """Função principal."""
    print("🚀 Iniciando validação completa do sistema de memória")
    print("=" * 60)
    
    # Configurar ambiente
    if not setup_test_environment():
        print("❌ Falha na configuração do ambiente")
        return False
    
    # Gerar relatório completo
    report = generate_test_report()
    
    # Executar cobertura se tudo passou
    if report['summary']['system_complete'] and report['summary']['passed_test_types'] > 0:
        print("\n🔍 Executando análise de cobertura...")
        run_coverage_analysis()
    
    print("\n✨ Validação concluída!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)