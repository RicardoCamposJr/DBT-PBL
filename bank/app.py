from flask import Flask, request, jsonify
import requests
import threading
import time

# TO DO:
# Fazer rota de /receive;
# Implementar a tradução de transactionPackage para as transferências na rota /token;
# Implementar rota de transferencia em outro banco para utilizar na rota /token;

app = Flask(__name__)

banks = {1: 'localhost:5001',
         2: 'localhost:5002',
         3: 'localhost:5003',
         4: 'localhost:5004',
         5: 'localhost:5005'}

# Formato:
# transactionPackage = {1: ['otherBank' ou 'thisBank', transferCPF (string), receiverCPF (string), destinationBankId (int), amount (int)]}
transactionPackage = {1: ['thisBank', '0001', '0002', 1, 10]}

# Estrutura de dados para armazenar os dados dos usuários
users = {}
token_holder = False
bankId = 1
next_instance = ''
passingToken = False

@app.route('/user', methods=['POST'])
def create_user():
    data = request.get_json()
    user_id = data.get('cpf')
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
    cpf = data.get('cpf')
    amount = int(data.get('amount'))
    if cpf not in users.keys():
        return jsonify({'message': 'Usuário não encontrado'}), 404
    users[cpf]['balance'] += amount
    return jsonify({'message': 'Depósito realizado com sucesso'}), 200

@app.route('/transfer', methods=['POST'])
def transfer():
    global token_holder
    transferStatus = 'inconcluded'

    while transferStatus == 'inconcluded':
        if token_holder:
            data = request.get_json()
            transferCPF = data.get('transferCPF')
            receiverCPF = data.get('receiverCPF')
            bankId = data.get('destinationBankId')
            amount = data.get('amount')

            if transferCPF not in users:
                return jsonify({'message': 'O cliente não existe nesse banco!'}), 404
            if users[transferCPF]['balance'] < amount:
                return jsonify({'message': 'Saldo insuficiente'}), 400
            
            statusCode = verifyClientExists(receiverCPF, bankId)
            print(statusCode)

            if statusCode == 200:
                users[transferCPF]['balance'] -= amount
                transferStatus = 'concluded'
                return jsonify({'message': 'Transferência realizada com sucesso!'}), 200
            else:
                return jsonify({'message': 'Transferência não realizada!'}), 400


@app.route('/users', methods=['GET'])
def get_users():
    return jsonify(users), 200

@app.route('/register', methods=['POST'])
def register():
    global next_instance
    data = request.get_json()
    next_instance = data.get('next_instance')
    return jsonify({'message': 'Registrado com sucesso'}), 200

# Rota que recebe o token e realiza as transações:
@app.route('/token', methods=['POST'])
def token():
    global token_holder
    global passingToken
    global transactionPackage

    data = request.get_json()

    token_holder = True

    print("Token recebido")

    # Tradução da estrutura transactionPackage para as requisições de fato:
    for transaction in transactionPackage.values():
        # Transferencia desse banco para outro:
        if transaction[0] == 'thisBank':
            requests.post(f'http://localhost:{5000+bankId}/transfer', json={"transferCPF": f"{transaction[1]}","receiverCPF": f"{transaction[2]}","destinationBankId": transaction[3],"amount": transaction[4]})
        # Transferencia de outro banco para outro:
        else:
            requests.post(f'http://localhost:{5000+bankId}/outraRota', json={"transferCPF": f"{transaction[1]}","receiverCPF": f"{transaction[2]}","destinationBankId": transaction[3],"amount": transaction[4]})

    passingToken = True
    return jsonify({'message': 'Token processado e passado'}), 200

# Função que faz o banco verificar se o cliente está cadastrado nele.
@app.route('/verify', methods=['POST'])
def verify():
    data = request.get_json()
    clientCPF = data.get('destinationCPF')
    if clientCPF in users.keys():
        return jsonify({'message': 'Cliente existe!'}), 200
    else:
        return jsonify({'message': 'Cliente não existe!'}), 404

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
            time.sleep(5)

# Função que chama a rota '/verify' para checkar se o cliente está no outro banco:
def verifyClientExists(clientCPF, bankId):
    global id
    if bankId != id:
        postReturn = requests.post(f'http://localhost:{5000+bankId}/verify', json={'destinationCPF': clientCPF})
        return postReturn.status_code
    return 'Não é possível realizar transferências para o mesmo banco!'

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