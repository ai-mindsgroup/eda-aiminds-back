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
    # Garantir que imports funcionem tanto para 'src.*' quanto para 'utils.*' (pacotes dentro de src)
    env = os.environ.copy()
    repo_root = os.getcwd()
    src_dir = os.path.join(repo_root, 'src')
    existing_pp = env.get('PYTHONPATH', '')
    # Incluir repo_root (para imports 'src.*') e src_dir (para imports como 'utils.*')
    composed_pp = os.pathsep.join([p for p in [repo_root, src_dir, existing_pp] if p])
    env['PYTHONPATH'] = composed_pp
    subprocess.run([os.path.join(venv_dir, 'Scripts', 'python.exe'), interface_file], check=True, env=env)

if __name__ == '__main__':
    create_venv()
    install_requirements()
    run_interface()
