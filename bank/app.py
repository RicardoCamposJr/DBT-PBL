from flask import Flask, request, jsonify
import requests
import threading
import time

app = Flask(__name__)

banks = {1: '192.168.25.105',
         2: '192.168.25.106',
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

    time.sleep(1)
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
        stop_event = threading.Event()

        # Iniciar a thread de contagem de 10 segundos
        timer_thread = threading.Thread(target=contar_10_segundos, args=(stop_event,))
        timer_thread.start()

        # Tradução da estrutura transactionPackage para as requisições de fato:
        for transaction in transactionPackage.values():

            if stop_event.is_set():
                print('O tempo de 10 segundos foi excedido. Algumas transações podem não ter sido realizadas.')
                return jsonify({'message': 'O tempo de 10 segundos foi excedido. Algumas transações podem não ter sido realizadas.'})
            
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
                            print(f'Transação n° {count} realizada com sucesso')
                    
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
    
# Função para contar 10 segundos
def contar_10_segundos(stop_event):
    time.sleep(10)
    stop_event.set()

def pass_token():
    global token_holder
    global passingToken
    global id

    attempts = 1
    nextId = 1

    while token_holder:
        # Caso queira colocar menos bancos, mudar aqui:
        if id+nextId >= 4:
            next_instance = f'{banks[1]}:5000'
            nextId = 1
        else:
            next_instance = f'{banks[id+nextId]}:{5000}'

        if next_instance != f'{banks[id]}:{5000}':
            print(f"\nTentando passar o token para {next_instance}\n")
            try:
                requests.post(f'http://{next_instance}/token', json={})
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
                    receiverCPF = input(f"Digite o CPF do destinatário: ")
                    sourceBankId = input(f"Digite o id do banco remetente: ")
                    destinationBankId = input(f"Digite o id do banco de destino: ")
                    amountTransfer = input(f"Digite o valor da transfêrencia: ")
                    operation = input(f"Digite se a transferencia será deste banco ou de outro: (this/other) ")

                    postReturn = requests.post(f'http://{banks[id]}:{5000}/transactions', json={"userCPF": userCPFLogged, "receiverCPF": receiverCPF,"transferCPF": userCPFLogged,"sourceBankId": sourceBankId,"destinationBankId": destinationBankId,"amount": amountTransfer,"operation": operation})
                    print(postReturn)

                    pack = input(f"Deseja incluir mais alguma operação no pacote? (s/n) ")
            
            else:
                print(f"\nPor favor faça o loggin!!\n")
        
        if valor == '5':
            postReturn = requests.get(f'http://{banks[id]}:{5000}/users')
            print(f"\n{postReturn.json()}\n")
        
        if valor == '6':
            log = False
            userCPFLogged = ''
            print(f"\nVolte sempre!!\n")
            

id = int(input('Digite o id desse banco: '))

if id != 3:
    next_instance = banks[1+id]
else:
    next_instance = banks[1]

if id == 1:
    token_holder = True
    passingToken = True

createAPIThread()

# Relativo ao token
threading.Thread(target= wait_token).start()

# Relativo a entrada do usuário:
thread_receber_valores = threading.Thread(target=receber_valores)
thread_receber_valores.daemon = True
thread_receber_valores.start()