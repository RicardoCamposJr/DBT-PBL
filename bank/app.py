from flask import Flask, request, jsonify
import requests
import threading
import time

app = Flask(__name__)

banks = {1: 'localhost:5001',
         2: 'localhost:5002',
         3: 'localhost:5003',
         4: 'localhost:5004',
         5: 'localhost:5005'}

# Estrutura de dados para armazenar os dados dos usuários
users = {}
token_holder = False
bankId = 1
next_instance = ''
passingToken = False

@app.route('/user', methods=['POST'])
def create_user():
    data = request.get_json()
    user_id = data.get('id')
    if user_id in users:
        return jsonify({'message': 'Usuário já existe'}), 400
    users[user_id] = {
        'name': data.get('name'),
        'balance': 0
    }
    return jsonify({'message': 'Usuário criado com sucesso'}), 201

@app.route('/deposit', methods=['POST'])
def deposit():
    data = request.get_json()
    user_id = data.get('id')
    amount = data.get('amount')
    if user_id not in users:
        return jsonify({'message': 'Usuário não encontrado'}), 404
    users[user_id]['balance'] += amount
    return jsonify({'message': 'Depósito realizado com sucesso'}), 200

@app.route('/transfer', methods=['POST'])
def transfer():
    data = request.get_json()
    from_user_id = data.get('from_id')
    to_user_id = data.get('to_id')
    amount = data.get('amount')
    if from_user_id not in users or to_user_id not in users:
        return jsonify({'message': 'Um ou ambos os usuários não foram encontrados'}), 404
    if users[from_user_id]['balance'] < amount:
        return jsonify({'message': 'Saldo insuficiente'}), 400
    users[from_user_id]['balance'] -= amount
    users[to_user_id]['balance'] += amount
    return jsonify({'message': 'Transferência realizada com sucesso'}), 200

@app.route('/users', methods=['GET'])
def get_users():
    return jsonify(users), 200

@app.route('/register', methods=['POST'])
def register():
    global next_instance
    data = request.get_json()
    next_instance = data.get('next_instance')
    return jsonify({'message': 'Registrado com sucesso'}), 200

@app.route('/token', methods=['POST'])
def token():
    global token_holder
    global passingToken
    data = request.get_json()
    token_holder = True
    print("Token recebido")
    # Processamento ou uso do token
    time.sleep(5)  # Simulação de tempo de uso do token
    passingToken = True
    return jsonify({'message': 'Token processado e passado'}), 200

def pass_token():
    global token_holder
    global passingToken
    while token_holder:
        print(f"Passando token para {next_instance}")
        try:
            if passingToken:
                postReturn = requests.post(f'http://{next_instance}/token', json={})
                print(postReturn)
                token_holder = False
                passingToken = False
        except Exception as e:
            print(f"Erro ao passar o token!")
            time.sleep(2)

def wait_token():
    global token_holder
    global passingToken
    while True:
        if token_holder and passingToken:
            pass_token()

# Thread para acionar a API
def createAPIThread():
    APIThread = threading.Thread(target=app.run, args=('0.0.0.0', 5000+id), daemon=True)
    APIThread.start()


id = int(input('Digite o id desse banco: '))

if id != 3:
    next_instance = banks[1+id]
else:
    next_instance = banks[1]

if id == 1:
    token_holder = True
    passingToken = True

createAPIThread()

threading.Thread(target= wait_token).start()