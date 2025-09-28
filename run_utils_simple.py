#!/usr/bin/env python3
"""
EDA AI Minds - Utilitario Simples
Facilita execucao de testes e exemplos
"""
import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent

def run_command(command, description):
    """Executa comando."""
    print(f"\n=> {description}")
    print("-" * 30)
    
    try:
        # Python do venv
        venv_python = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"
        if venv_python.exists():
            python_cmd = str(venv_python)
        else:
            python_cmd = sys.executable
        
        # Preparar comando
        if command.startswith("python "):
            full_cmd = command.replace("python ", f'"{python_cmd}" ', 1)
        else:
            full_cmd = command
        
        # Executar
        result = subprocess.run(
            full_cmd,
            shell=True,
            cwd=PROJECT_ROOT
        )
        
        if result.returncode == 0:
            print("OK")
        else:
            print(f"ERRO: {result.returncode}")
            
    except Exception as e:
        print(f"ERRO: {e}")

def main():
    """Principal."""
    print("EDA AI Minds - Utilitario")
    print("=" * 30)
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
    else:
        print("\nComandos:")
        print("tests    - Testes basicos")
        print("examples - Exemplos")
        print("list     - Listar arquivos")
        cmd = input("\nComando: ")
    
    if cmd == "tests":
        print("TESTES BASICOS:")
        run_command("python tests/test_orchestrator_basic.py", "Teste orquestrador")
        
    elif cmd == "examples":
        print("EXEMPLOS:")
        run_command("python examples/exemplo_orchestrator.py --quick", "Demo rapido")
        
    elif cmd == "list":
        print("\nTESTS:")
        for f in sorted(Path("tests").glob("*.py")):
            print(f"  {f.name}")
        print("\nEXAMPLES:")
        for f in sorted(Path("examples").glob("*.py")):
            print(f"  {f.name}")
    
    else:
        print("Comando invalido!")

if __name__ == "__main__":
    main()