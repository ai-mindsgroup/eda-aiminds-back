import subprocess
import sys
import os

# Caminhos
venv_dir = os.path.join(os.getcwd(), '.venv')
activate_script = os.path.join(venv_dir, 'Scripts', 'Activate.ps1')
requirements = os.path.join(os.getcwd(), 'requirements.txt')
api_file = os.path.join(os.getcwd(), 'api_completa.py')

# 1. Cria ambiente virtual se não existir
def create_venv():
    if not os.path.exists(venv_dir):
        print('Criando ambiente virtual...')
        subprocess.run([sys.executable, '-m', 'venv', venv_dir], check=True)
    else:
        print('Ambiente virtual já existe.')

# 2. Instala requirements
def install_requirements():
    print('Instalando dependências...')
    subprocess.run([os.path.join(venv_dir, 'Scripts', 'python.exe'), '-m', 'pip', 'install', '-r', requirements, '--quiet'], check=True)

# 3. Sobe FastAPI (uvicorn)
def run_fastapi():
    print('Subindo FastAPI na porta 8011...')
    subprocess.run([os.path.join(venv_dir, 'Scripts', 'python.exe'), '-m', 'uvicorn', 'api_completa:app', '--host', '0.0.0.0', '--port', '8011'], check=True)

if __name__ == '__main__':
    create_venv()
    install_requirements()
    run_fastapi()
