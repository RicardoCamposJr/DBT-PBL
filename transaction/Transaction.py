class Transaction:
    # Método inicializador (construtor)
    def __init__(self, transferCPF, receiverCPF, sourceBankId, destinationBankId, amount):
        self.transferCPF = transferCPF
        self.receiverCPF = receiverCPF
        self.sourceBankId = sourceBankId
        self.destinationBankId = destinationBankId
        self.amount = amount
