from flask import Flask, request, jsonify
import requests
import threading
import time
import logging

# Desabilita logging de requisições do Werkzeug
logging.getLogger('werkzeug').disabled = True

app = Flask(__name__)

banks = {1: '192.168.25.131',
         2: '192.168.25.105',
         3: '192.168.25.107'}

transactionPackage = {}

# Estrutura de dados para armazenar os dados dos usuários
users = {   "0001": {
            "balance": 100,
            "name": "user1",
            "password": "123"
            },
            "0002": {
            "balance": 100,
            "name": "user1",
            "password": "123"
            }
        }

token_holder = False
bankId = 1
next_instance = ''
passingToken = False
userCPFLogged = ''
log = False
fallen = False

# Lock para caso mais de um cliente realize requisições ao mesmo tempo.
transaction_lock = threading.Lock()

@app.route('/user', methods=['POST'])
def create_user():
    data = request.get_json()
    user_id = data.get('cpf')

    if user_id in users:
        print(f"\nUsuário já existe!!!\n")
        return jsonify({'message': 'Usuário já existe'}), 400
    
    users[user_id] = {
        'name': data.get('name'),
        'balance': 0,
        'password': data.get('password')
    }

    print(f"\nUsuário criado com sucesso!!!\n")
    return jsonify({'message': 'Usuário criado com sucesso'}), 201

@app.route('/deposit', methods=['POST'])
def deposit():
    data = request.get_json()
    cpf = data.get('cpf')
    amount = int(data.get('amount'))

    if cpf not in users.keys():
        return jsonify({'message': 'Usuário não encontrado'}), 404
    
    users[cpf]['balance'] += amount

    print(f"\nDepósito realizado com sucesso\n")
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

    with transaction_lock:
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
    global fallen

    token_holder = True

    if fallen:
        print(f'\nEste banco retornou!!!!\n')
    # Caso o banco retorne depois de ter caído.
    fallen = False

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
                    print(f'O remetente não existe no banco {id}')

                    transactionPackage[operation["userCPF"]].remove(operation)
                    return jsonify({'message': f'O remetente não existe no banco {id}'})
                
                # Verificando se o valor da transferencia pode ser transferido:
                if users[operation["userCPF"]]['balance'] < operation["amount"]:
                    print(f'O usuário de CPF {operation["userCPF"]} possui o saldo insuficiente!')

                    transactionPackage[operation["userCPF"]].remove(operation)
                    return jsonify({'message': f'O usuário de CPF {operation["userCPF"]} possui o saldo insuficiente!'})

                #Verificando se o destinatário existe:
                verifyStatusCode = verifyClientExists(operation["receiverCPF"], operation["destinationBankId"])

                if verifyStatusCode == 200:
                    if operation["operation"] == 'this':
                        postReturn = requests.post(f'http://{banks[operation["destinationBankId"]]}:{5000}/transfer', json={"receiverCPF": f"{operation['receiverCPF']}", "amount": operation['amount']})

                        if (postReturn.status_code != 200):
                            print('O pacote de transações não pôde ser realizado!')
                        
                        else:
                            users[operation["transferCPF"]]['balance'] -= operation["amount"]
                            print(f'Transação realizada com sucesso')
                    
                    elif operation["operation"] == 'other':
                        postReturn = requests.post(f'http://{banks[operation["sourceBankId"]]}:{5000}/transactions', json={"userCPF": operation["userCPF"],"transferCPF": f"{operation['transferCPF']}","receiverCPF": f"{operation['receiverCPF']}","sourceBankId": f"{operation['sourceBankId']}","destinationBankId": operation["destinationBankId"],"amount": operation["amount"],"operation": "this"})
                        if (postReturn.status_code != 200):
                            print('O pacote de transações não pôde ser realizado!')
                        
                else:
                    transactionsStatus[count] = (f'O usuário de CPF {operation["receiverCPF"]} não existe no banco {operation["destinationBankId"]}')

                # Removendo a transação que foi concluída
                transactionPackage[operation["userCPF"]].remove(operation)

        
        passingToken = True
        return jsonify(transactionsStatus)
    
def verify_time_without_token():
    global token_holder
    global id
    global banks
    global fallen

    count = 0

    while True:
        for s in range(10+(id**2)):

            time.sleep(1)
            count += 1

            if count == 10+(id**2):

                # Caso o banco não tenha caído, ele vai passar o token.
                if not fallen:
                    token_holder = True

                count = 0

def pass_token():
    global token_holder
    global passingToken
    global id
    global fallen

    attempts = 1
    nextId = 1

    while token_holder:
        # Caso queira colocar menos bancos, mudar aqui:
        if id+nextId >= len(banks) + 1:

            next_instance = f'{banks[1]}:5000'
            nextId = 1

        else:

            next_instance = f'{banks[id+nextId]}:{5000}'

        if next_instance != f'{banks[id]}:{5000}':

            try:
                requests.post(f'http://{next_instance}/token', json={})
                token_holder = False
                passingToken = False

            except Exception as e:

                print(f"Falha ao passar o token para o próximo banco com IP {next_instance}. Tentando o proximo...")
                
                attempts += 1
                nextId += 1

                if attempts >= len(banks):

                    attempts = 0
                    token_holder = False

                    # Variável que identifica que este banco caiu.
                    fallen = True

                    print(f"Falha ao passar o token para todos os bancos. O banco {id} caiu! Aguardando token...")
        else:
            token_holder = False

            # Variável que identifica que este banco caiu.
            fallen = True
            
            print(f"Falha ao passar o token para todos os bancos. O banco {id} caiu! Aguardando token...")
            
# Função que chama a rota '/verify' para checkar se o cliente está no outro banco:
def verifyClientExists(clientCPF, bankId):
    global id

    postReturn = requests.post(f'http://{banks[bankId]}:{5000}/verify', json={'destinationCPF': clientCPF})
    return postReturn.status_code

def wait_token():
    global token_holder
    global passingToken
    global transactionPackage
    global id

    while True:
        if token_holder:
            if transactionPackage.values():
                requests.post(f'http://{banks[id]}:{5000}/run', json={})

            pass_token()
            token_holder = False

# Thread para acionar a API
def createAPIThread():
    global id
    global banks

    APIThread = threading.Thread(target=app.run, args=('0.0.0.0', 5000), daemon=True)
    APIThread.start()

# Função que será executada na thread para receber valores do usuário
def receber_valores():
    time.sleep(2)
    global userCPFLogged
    global log
    global transactionPackage
    global id

    while True:
        valor = input(f"\nBem vindo ao sistema de bancos distribuídos, escolha uma das opções abaixo:\n[1] - Cadastrar usuário\n[2] - Entrar\n[3] - Depositar\n[4] - Criar transação\n[5] - Ver saldo dos clientes\n[6] - Sair\n")
        if valor == '1':
            name = input(f"Digite seu nome: ")
            cpf = input(f"Digite seu CPF: ")
            senha = input(f"Digite uma senha: ")

            postReturn = requests.post(f'http://{banks[id]}:{5000}/user', json={"cpf": cpf, "name": name, "password": senha})

            print(postReturn)
        
        if valor == '2':
            cpf = input(f"Digite seu CPF: ")
            senha = input(f"Digite uma senha: ")

            if cpf in users:
                print(f"\nBem vindo!!!\n")
                userCPFLogged = cpf
                log = True
            else:
                print(f"\nCPF ou senha inválidos!\n")
        
        if valor == '3':
            if log:
                amount = input(f"Digite o valor: ")

                postReturn = requests.post(f'http://{banks[id]}:{5000}/deposit', json={"cpf": cpf, "amount": amount})

                print(postReturn)
            else:
                print(f"\nPor favor faça o loggin!!\n")
        
        if valor == '4':
            if log:
                pack = 's'
                while pack == "s":

                    operation = input(f"Digite se a transferencia será deste banco ou de outro: (this/other) ")
                    
                    if operation == 'other':
                        sourceBankId = input(f"Digite o id do banco remetente: ")
                    else :
                        sourceBankId = id

                    destinationBankId = input(f"Digite o id do banco de destino: ")
                    receiverCPF = input(f"Digite o CPF do destinatário: ")
                    
                    amountTransfer = input(f"Digite o valor da transfêrencia: ")
                    
                    pack = input(f"Deseja incluir mais alguma operação? (s/n) ")
                    postReturn = requests.post(f'http://{banks[id]}:{5000}/transactions', json={"userCPF": userCPFLogged, "receiverCPF": receiverCPF,"transferCPF": userCPFLogged,"sourceBankId": sourceBankId,"destinationBankId": destinationBankId,"amount": amountTransfer,"operation": operation})
                    
                    print(postReturn)
            
            else:
                print(f"\nPor favor faça o loggin!!\n")
        
        if valor == '5':
            postReturn = requests.get(f'http://{banks[id]}:{5000}/users')
            print(f"\n{postReturn.json()}\n")
        
        if valor == '6':
            log = False
            userCPFLogged = ''
            print(f"\nVolte sempre!!\n")

# =======================================================
            
# Configuração inicial:


id = int(input('Digite o id desse banco: '))

if id != len(banks):
    next_instance = banks[1+id]
else:
    next_instance = banks[1]

if id == 1:
    token_holder = True
    passingToken = True

# =======================================================

# Threads utilizadas no projeto


createAPIThread()

# Relativo ao token.
threading.Thread(target= wait_token).start()

# Relativo ao tempo de espera para receber o token.
threading.Thread(target=verify_time_without_token).start()


# Relativo a entrada do usuário:
thread_receber_valores = threading.Thread(target=receber_valores)
thread_receber_valores.daemon = True
thread_receber_valores.start()

# =======================================================