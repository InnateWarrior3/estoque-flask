from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import json
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_32_caracteres_1234567890'

# Configuração do Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Classe Usuário
class User(UserMixin):
    def __init__(self, user_id, username, password):
        self.id = user_id
        self.username = username
        self.password = password

# Funções de carregamento/salvamento
def load_users():
    if not os.path.exists('data/users.json'):
        return {}
    try:
        with open('data/users.json', 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def save_users(users):
    os.makedirs('data', exist_ok=True)
    with open('data/users.json', 'w') as f:
        json.dump(users, f, indent=4)

def load_produtos():
    if not os.path.exists('data/produtos.json'):
        return {}
    try:
        with open('data/produtos.json', 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def save_produtos(produtos):
    os.makedirs('data', exist_ok=True)
    with open('data/produtos.json', 'w') as f:
        json.dump(produtos, f, indent=4)

# Loader de usuário
@login_manager.user_loader
def load_user(user_id):
    users = load_users()
    user_data = users.get(user_id)
    if user_data:
        return User(user_id, user_data['username'], user_data['password'])
    return None

# Rotas de autenticação
@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        users = load_users()
        for user_id, user_data in users.items():
            if user_data['username'] == username and check_password_hash(user_data['password'], password):
                user = User(user_id, username, user_data['password'])
                login_user(user)
                return redirect(url_for('estoque'))
        
        flash('Usuário ou senha incorretos')
    return render_template('login.html')

@app.route('/registrar', methods=['GET', 'POST'])
def registrar():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('As senhas não coincidem!')
            return redirect(url_for('registrar'))
        
        users = load_users()
        
        # Verificar se usuário já existe
        for user_id, user_data in users.items():
            if user_data['username'] == username:
                flash('Nome de usuário já está em uso!')
                return redirect(url_for('registrar'))
        
        # Criar novo usuário
        new_id = str(len(users) + 1)
        users[new_id] = {
            'username': username,
            'password': generate_password_hash(password)
        }
        save_users(users)
        
        flash('Registro realizado com sucesso! Faça login.')
        return redirect(url_for('login'))
    
    return render_template('registrar.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Rotas do estoque
@app.route('/estoque')
@login_required
def estoque():
    produtos = load_produtos()
    return render_template('estoque.html', produtos=produtos)

@app.route('/adicionar_produto', methods=['POST'])
@login_required
def adicionar_produto():
    nome = request.form['nome']
    quantidade = int(request.form['quantidade'])
    
    produtos = load_produtos()
    produto_id = str(len(produtos) + 1)
    produtos[produto_id] = {'nome': nome, 'quantidade': quantidade}
    save_produtos(produtos)
    
    return redirect(url_for('estoque'))

@app.route('/editar_produto/<produto_id>', methods=['POST'])
@login_required
def editar_produto(produto_id):
    produtos = load_produtos()
    if produto_id in produtos:
        produtos[produto_id]['nome'] = request.form['nome']
        produtos[produto_id]['quantidade'] = int(request.form['quantidade'])
        save_produtos(produtos)
    return redirect(url_for('estoque'))

@app.route('/remover_produto/<produto_id>')
@login_required
def remover_produto(produto_id):
    produtos = load_produtos()
    if produto_id in produtos:
        del produtos[produto_id]
        save_produtos(produtos)
    return redirect(url_for('estoque'))

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

if __name__ == '__main__':
    # Inicialização segura
    os.makedirs('data', exist_ok=True)
    # Criar usuário admin se não existir
    users = load_users()
    if not users:
        users = {
            '1': {
                'username': 'admin',
                'password': generate_password_hash('admin123')
            }
        }
        save_users(users)
    
    # Garantir arquivo de produtos
    if not os.path.exists('data/produtos.json'):
        save_produtos({})
    
    app.run(debug=True)