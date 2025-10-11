import subprocess
import sys
import os

# Caminhos
venv_dir = os.path.join(os.getcwd(), '.venv')
activate_script = os.path.join(venv_dir, 'Scripts', 'Activate.ps1')
requirements = os.path.join(os.getcwd(), 'requirements.txt')
interface_file = os.path.join(os.getcwd(), 'interface_interativa.py')

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

# 3. Executa interface_interativa.py
def run_interface():
    print('Executando interface_interativa.py...')
    subprocess.run([os.path.join(venv_dir, 'Scripts', 'python.exe'), interface_file], check=True)

if __name__ == '__main__':
    create_venv()
    install_requirements()
    run_interface()
