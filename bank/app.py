from flask import Flask, request, jsonify
import requests
import threading
import time

# TO DO: 
# Implementar as transações atomicas

app = Flask(__name__)

banks = {1: 'localhost:5001',
         2: 'localhost:5002',
         3: 'localhost:5003'}
        #  4: 'localhost:5004',
        #  5: 'localhost:5005'}

# Formato:
# transactionPackage = {1: [transferCPF (string), receiverCPF (string), sourceBankId (int), destinationBankId (int), amount (int), operation ('this', 'other')]}

# transactionPackage = {1: ['0001', '0001', 2, 1, 10, 'other']}

transactionPackage = {}

# Estrutura de dados para armazenar os dados dos usuários
users = {   "0001": {
            "balance": 100,
            "name": "user1"
            },
            "0002": {
            "balance": 100,
            "name": "user1"
            }
        }
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
    data = request.get_json()
    receiverCPF = data.get('receiverCPF')
    amount = data.get('amount')

    if receiverCPF not in users.keys():
        return jsonify({'message': 'O cliente não existe nesse banco!'}), 404

    users[receiverCPF]['balance'] += amount
    return jsonify({'message': 'Transferência realizada com sucesso!'}), 200

@app.route('/transactions', methods=['POST'])
def createTransactions():
    global transactionPackage
    
    data = request.get_json()
    userCPF = str(data.get('userCPF'))
    receiverCPF = data.get('receiverCPF')
    transferCPF = data.get('transferCPF')
    sourceBankId = int(data.get('sourceBankId'))
    destinationBankId = int(data.get('destinationBankId'))
    operation = data.get('operation')
    amount = float(data.get('amount'))

    if userCPF in transactionPackage.keys():
        transactionPackage[userCPF].append({"userCPF": userCPF, "transferCPF": transferCPF, "receiverCPF": receiverCPF, "sourceBankId": sourceBankId, "destinationBankId": destinationBankId, "amount": amount, "operation": operation})
    else:
        transactionPackage[userCPF] = [{"userCPF": userCPF, "transferCPF": transferCPF, "receiverCPF": receiverCPF, "sourceBankId": sourceBankId, "destinationBankId": destinationBankId, "amount": amount, "operation": operation}]

    print(transactionPackage)

    return 'Operação criada!', 200

@app.route('/users', methods=['GET'])
def get_users():
    return jsonify(users), 200

# Rota que recebe o token:
@app.route('/token', methods=['POST'])
def token():
    global token_holder
    global id

    token_holder = True
    print("\nToken recebido!\n")
    return jsonify({'message': f'Token recebido no banco {id}'}), 200

# Função que faz o banco verificar se o cliente está cadastrado nele.
@app.route('/verify', methods=['POST'])
def verify():
    data = request.get_json()
    clientCPF = data.get('destinationCPF')
    if clientCPF in users.keys():
        return jsonify({'message': 'Cliente existe!'}), 200
    else:
        return jsonify({'message': 'Cliente não existe!'}), 404

@app.route('/run', methods=['POST'])
def runTransactions():
    global token_holder
    global users
    global transactionPackage
    global id
    global passingToken

    transactionsStatus = {}
    
    if token_holder:
        count = 0
        # Tradução da estrutura transactionPackage para as requisições de fato:
        for transaction in transactionPackage.values():
            for operation in transaction:
                count += 1
                # Verificando se o usuário existe neste banco:
                if operation["userCPF"] not in users.keys():
                    return jsonify({'message': f'O remetente não existe no banco {id}'})
                
                # Verificando se o valor da transferencia pode ser transferido:
                if users[operation["userCPF"]]['balance'] < operation["amount"]:
                    return jsonify({'message': f'O usuário de CPF {operation["userCPF"]} possui o saldo insuficiente!'})

                #Verificando se o destinatário existe:
                verifyStatusCode = verifyClientExists(operation["receiverCPF"], operation["destinationBankId"])
                
                if verifyStatusCode == 200:
                    if operation["operation"] == 'this':
                        postReturn = requests.post(f'http://localhost:{5000+operation["destinationBankId"]}/transfer', json={"receiverCPF": f"{operation["receiverCPF"]}", "amount": operation["amount"]})

                        if (postReturn.status_code != 200):
                            transactionsStatus[count] = ('O pacote de transações não pôde ser realizado!')
                        
                        else:
                            users[operation["transferCPF"]]['balance'] -= operation["amount"]
                            transactionsStatus[count] = (f'Transação n° {count} realizada com sucesso')
                    
                    elif operation["operation"] == 'other':
                        postReturn = requests.post(f'http://localhost:{5000+operation["sourceBankId"]}/transactions', json={"userCPF": operation["userCPF"], "transferCPF": f"{operation["transferCPF"]}", "receiverCPF": f"{operation["receiverCPF"]}", "sourceBankId": f"{operation["sourceBankId"]}", "destinationBankId": operation["destinationBankId"], "amount": operation["amount"], "operation": "this"})

                        if (postReturn.status_code != 200):
                            transactionsStatus[count] = ('O pacote de transações não pôde ser realizado!')
                        
                else:
                    transactionsStatus[count] = (f'O usuário de CPF {operation["receiverCPF"]} não existe no banco {operation["destinationBankId"]}')
        
        passingToken = True
        return jsonify(transactionsStatus)

def pass_token():
    global token_holder
    global passingToken
    global id

    attempts = 1
    nextId = 1

    while token_holder:
        next_instance = f'localhost:{5000+id+nextId}'

        # Caso queira colocar menos bancos, mudar aqui:
        if id+nextId >= 4:
            next_instance = 'localhost:5001'
            nextId = 1

        if next_instance != f'localhost:{5000+id}':
            print(f"\nTentando passar o token para {next_instance}\n")
            try:
                postReturn = requests.post(f'http://{next_instance}/token', json={})
                print(f'\n{postReturn.json()}\n')
                token_holder = False
                passingToken = False
            except Exception as e:
                print(f"\nErro ao passar o token para {next_instance}, tentando o próximo.\n")
                attempts += 1
                nextId += 1
                if attempts >= len(banks):
                    token_holder = False
                    print(f"Falha ao passar o token para todos os bancos. O banco {id} caiu! Aguardando token...")
                time.sleep(5)
        else:
            print(f"Falha ao passar o token para todos os bancos. O banco {id} caiu! Aguardando token...")
            token_holder = False


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
    global transactionPackage
    global id

    while True:
        if token_holder:
            if transactionPackage:
                postReturn = requests.post(f'http://localhost:{5000+id}/run', json={})
                if postReturn:
                    print(f'\n{postReturn.json()}\n')
                transactionPackage = {}

            pass_token()
            token_holder = False

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