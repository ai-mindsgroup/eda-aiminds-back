"""Script utilitário para execução fácil de testes e exemplos.

Este script facilita a execução de testes e exemplos após a reorganização
da estrutura de arquivos.
"""
import subprocess
import sys
from pathlib import Path
import os

# Definir diretório raiz do projeto
PROJECT_ROOT = Path(__file__).parent

def run_command(command, description):
    """Executa comando e mostra resultado."""
    print(f"\n=> {description}")
    print("-" * 50)
    
    try:
        # Usar o Python do ambiente virtual se disponível
        if (PROJECT_ROOT / ".venv" / "Scripts" / "python.exe").exists():
            python_cmd = str(PROJECT_ROOT / ".venv" / "Scripts" / "python.exe")
        else:
            python_cmd = sys.executable
        
        # Substituir 'python' pelo comando correto
        if command.startswith("python "):
            command = command.replace("python ", f'"{python_cmd}" ', 1)
        
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True,
            cwd=PROJECT_ROOT,
            encoding='utf-8',
            errors='replace'
        )
        
        if result.returncode == 0:
            print("SUCESSO")
            if result.stdout.strip():
                print(result.stdout[-300:])  # Últimos 300 chars
        else:
            print("ERRO")
            print(f"Codigo de saida: {result.returncode}")
            if result.stderr:
                print("STDERR:", result.stderr[-200:])  # Últimos 200 chars
                
    except Exception as e:
        print(f"Excecao: {str(e)}")

def main():
    """Menu principal."""
    print("EDA AI Minds - Utilitario de Testes e Exemplos")
    print("=" * 50)
    
    while True:
        print("\nOPCOES DISPONIVEIS:")
        print("1. Executar testes basicos")
        print("2. Executar exemplos rapidos") 
        print("3. Executar todos os testes")
        print("4. Executar todas as demonstracoes")
        print("5. Teste de funcionamento basico")
        print("6. Listar arquivos disponiveis")
        print("0. Sair")
        
        escolha = input("\nEscolha uma opcao (0-6): ").strip()
        
        if escolha == "0":
            print("Ate mais!")
            break
            
        elif escolha == "1":
            print("\nEXECUTANDO TESTES BASICOS")
            tests = [
                ("python tests/test_orchestrator_basic.py", "Teste basico do orquestrador"),
                ("python tests/test_data_loading_system.py", "Teste do sistema de carregamento"),
            ]
            
            for cmd, desc in tests:
                run_command(cmd, desc)
                
        elif escolha == "2":
            print("\nEXECUTANDO EXEMPLOS RAPIDOS")
            examples = [
                ("python examples/exemplo_orchestrator.py --quick", "Demo rapido do orquestrador"),
                ("python examples/demo_data_loading.py", "Demo do carregamento de dados"),
            ]
            
            for cmd, desc in examples:
                run_command(cmd, desc)
                
        elif escolha == "5":
            print("\nTESTE DE FUNCIONAMENTO BASICO")
            run_command(
                'python -c "from src.agent.orchestrator_agent import OrchestratorAgent; print(\'Sistema funcionando!\')"',
                "Verificacao basica de importacao"
            )
            
        elif escolha == "6":
            print("\nARQUIVOS DISPONIVEIS")
            print("\nTestes (tests/):")
            for f in sorted(Path("tests").glob("*.py")):
                print(f"  - {f.name}")
            
            print("\nExemplos (examples/):")
            for f in sorted(Path("examples").glob("*.py")):
                print(f"  - {f.name}")
                
        else:
            print("Opcao invalida! Tente novamente.")

if __name__ == "__main__":
    main()