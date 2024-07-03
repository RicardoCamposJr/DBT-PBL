# Relatório do PBL - Internet of Things

## Introdução:
<p style="text-align: justify;">
Este relatório tem como objetivo documentar o processo de aprendizado e construção do projeto sobre Transações Bancárias Distribuídas. No presente projeto, foi solicitado o desenvolvimento de um serviço que permita a comunicação entre diferentes bancos na rede de maneira distribuída. Essa abordagem foi utilizada para que o sistema inteiro não dependa de um nó central (como ocorre com o sistema de bancos atual), permitindo assim, uma maior interdependência entre eles.
<p style="text-align: justify;">
Para isso, foi decidido que o sistema deveria ser implementado através de API's Rest, facilitando a comunicação entre os diferentes nós (bancos).
<p style="text-align: justify;">
A aplicação consiste em uma interface amigável no terminal, para o usuário realizar o cadastro, login e logout, depósito em conta, transferência e checagem de saldo.
<p style="text-align: justify;">
Dessa forma, os bancos conseguem se comunicar e realizar diferentes transações sem necessitar de um orgão central. Realizando toda a comunicação de maneira distruibuída.

## Resultados e discussões:

<p style="text-align: justify;">
O sistema permite a criação de contas de usuário através de uma interface amigável pelo terminal. Para o cliente, basta inserir as informações solicitadas e ralizar o login na conta bancária. Após o login, é possível fazer o depósito em conta, checar o saldo e realizar transações.

<p style="text-align: justify;">
No presente projeto, é possível realizar transações entre diferentes bancos. Existem dois tipos de operações: do banco que o cliente está logado para outro; e de outros bancos para outros a partir do banco que o cliente está logado. Para especificar qual tipo de operação o usuário deseja realizar, na criação da transação, quando for perguntado qual o tipo de operação, o cliente pode inserir "this" (para transações partindo desse banco) ou "other" (para transações partindo de outros bancos). Assim, em um exemplo, o usuário está logado no banco 1 e deseja realizar uma transferencia de sua conta neste banco para o banco 2. Assim, na criação da transação, o cliente deve inserir o valor "this" quando for perguntado o tipo de operação. OBS.: O cliente deve inserir as demais informações anteriores para a conclusão da construção da operação.

<p style="text-align: justify;">
Os servidores (bancos) utilizam o protocolo de comunicação HTTP, utilizando API's Rest. Cada banco funciona em um IP específico e na mesma porta (5000). Assim, os bancos vão realizando as requisições de criação de transações e transferências entre si. Atendendo assim, um dos requisitos do barema deste projeto.

<p style="text-align: justify;">
A sincronização em um único servidor foi implementada utilizando a lógica de Token Ring. Assim, a concorrência em um servidor é tratada, já que somente o banco que detiver o token será capaz de realizar as transações. Explicando melhor a lógica de token ring nesse projeto, o banco 1 é configurado para iniciar o token na rede...

<div style="text-align: center;">

![alt text](image-1.png)

Figura 2: Diagrama estrutural do sistema

</div>

<p style="text-align: justify;">
Nesse contexto, a face do broker referente aos dispositivos utiliza a comunicação TCP para o envio de comandos advindos da interface pros dispositivos conectados aos sistema. Essa comunicação via TCP foi utilizada visando uma abordagem confiável, assegurando assim, a entrega das mensagens (comandos) para os dispositivos. De modo análogo, o broker também utiliza uma abordagem não confiável para o recebimento dos dados provenientes dos dispositivos, utilizando uma comunicação UDP para tal fim. A abordagem não confiável foi utilizada nesse contexto por conta do envio frequente de dados, assim, caso algum dado se perca no trajeto, outro dado logo em seguida será enviado, substituindo o dado perdido anteriormente. Na figura 1, é possível visualizar o fluxo de dados do sistema em uma requisição GET realizada a partir da interface.

<div style="text-align: center;">

![alt text](image.png)

Figura 1: Fluxo de dados de uma requisição GET

</div>



<p style="text-align: justify;">
Os dispositivos são implementados com as duas formas de comunicação, tanto TCP quanto UDP. Assim, eles são capazes de esperar comandos via TCP provenientes do broker e enviar comandos via UDP para o mesmo. Os dispositivos possuem os comandos de: Ligar, Mudar temperatura e Desligar. Ao ligar, o dispositivo começa a enviar dados via UDP ao broker (que por sua vez, manipula os dados e responde à interface). Ao desligar, o dispositivo para de enviar esses dados, mas ainda permanece em "stand by", podendo ligá-lo novamente. Esses comandos podem ser recebidos via broker ou utilizados via terminal, inserindo a escolha desejada.



<p style="text-align: justify;">
O broker e os dispositivos utilizam threads, que são unidades básicas de execução dentro de um processo em um sistema operacional. Essa abordagem foi utilizada para utilizar um processamento paralelo, já que é necessário realizar múltiplas tarefas simultaneamente. No broker, são criadas threads para a execução da API e uma thread para "escutar" cada dispositivo conectado, recebendo assim os dados via UDP. Para os dispositivos são criadas threads para: receber comandos via TCP do broker; threads para para o envio de dados via UDP; e threads para o recebimento de comandos via terminal por parte do usuário. Conseguindo assim, realizar todo o processamento paralelo do sistema, atendendo a todas as funcionalidades impostas pelo problema.Na figura 3, é possível ter uma visão top-down de quais threads são utilizadas por cada componente.

<div style="text-align: center;">

![alt text](image-2.png)

Figura 3: Threads dos componentes

</div>

<p style="text-align: justify;">
Para fins de confiabilidade, caso o cabo de rede de algum nó seja retirado do sistema fechado, o nó que foi excluído irá tentar reconectar-se ao componente no qual se comunicava. Assim como foi solicitado como parte da resolução do problema. A título de documentação e parametrização do projeto, o tempo de reconexão de um nó ao sistema, após a retirada do cabo de rede, se apresentou em torno de 35 segundos de espera. Após esse tempo de espera, o nó que foi desconectado se torna disponível na rede.

<p style="text-align: justify;">
Para uma melhor facilidade de execução e multiplicidade de componentes, foi-se utilizado o Docker. Assim, há a criação de contêineres a partir da imagem de cada nó presente no sistema. O docker, por padrão, constrói uma rede própria para os contêineres, desse modo, é necessário o espelhamento de portas entre os contêineres e o host (o computador rodando o docker). Assim, é possível acessar as aplicações na rede através do IP do host e a porta que está sendo mapeada no contêiner. Veja como como configurar e rodar o Docker do projeto, na seção de intalação desse relatório.

<p style="text-align: justify;">
Para todos os componentes desse sistema foram desenvolvidos contêineres Docker, para facilitar a execução de mais de uma instância. Da mesma forma, a API REST do broker foi projetada e testada usando o Postman para garantir a compatibilidade com a arquitetura REST.

### Observações:
<p style="text-align: justify;">

- Ao excluir o dispositivo pela interface, todas as threads dele são extintas, exceto a thread referente aos comandos via terminal. Diante disso, é necessário uma entrada qualquer pelo teclado, para a confirmação de retirada do dispositivo. Assim, o programa é encerrado por completo.
- Para todos os componentes do sistema, existe o tratamento de exceções caso o componente seja encerrado com o comando (CTRL + C) ou caso o terminal seja fechado.

## Instalação

- Baixe a aplicação do GitHub:
  - No terminal, rode: git clone https://github.com/RicardoCamposJr/IoT-PBL.git

- Entre na pasta "IoT-PBL/"

## Configuração com Docker:

- ### Interface:
  
  - #### 1 - Configurar o endereço do broker:
  
    1.1 - Localize a pasta "broker.js" dentro no caminho: view/src/broker.js.

    1.2 - Altere o valor da variável brokerIP para o IP que o broker será iniciado. E salve o arquivo.

        OBS.: O IP dessa variável pode ser 'localhost' ou o IP da sua máquina mesmo. Assim,
        para saber o IP da sua máquina, utilize o comando 'ipconfig' no terminal e use o 
        endereço IPv4. O valor da variável DEVE SER UMA STRING!

  - #### 2 - Construir a imagem docker da interface:

    No terminal, rode o comando: docker build --pull --rm -f "view\Dockerfile" -t interface-image "view"

    Assim, a imagem será construída e será referenciada como "interface-image".


  - #### 3 - Subir o container da imagem docker:

    No terminal, rode o comando: docker run --name interface -p 3000:3000 interface-image

    Aguarde até aparecer a mensagem "webpack compiled with 1 warning" no terminal.

    Assim, a aplicação irá estar disponível para uso no navegador, no endereço: 
      <IP_DA_SUA_MAQUINA>:3000

    OBS.: Não finalize o terminal, caso isso ocorra, a aplicação irá finalizar.

- ### Broker:

  - #### 1 - Construir a imagem docker do broker:

    - Em outro terminal, rode o comando: docker build --pull --rm -f "broker\Dockerfile" -t broker-image "broker"

    - Assim, a imagem será construída e será referenciada como "broker-image".

  - #### 2 - Subir o container da imagem docker:

    No terminal, rode o comando: docker run --name broker -p 8888:8888 -p 8889:8889/udp -p 8082:8082 broker-image

    Assim, a API do broker irá estar disponível para uso/testes no endereço: 
      <IP_DA_SUA_MAQUINA>:8082
    
    - #### 2.1 - Rotas:
  
      - GET: <IP_DA_SUA_MAQUINA>:8082/devices
        - Retorna todos os devices conectados no momento.
  
      - POST: <IP_DA_SUA_MAQUINA>:8082/set/<IP: string>/<temperatura: int>/
        - Muda a temperatura do device com o IP fornecido.

      - PATCH: <IP_DA_SUA_MAQUINA>:8082/power/<IP: string>/
        - Liga o device de acordo com o IP fornecido.
      
      - DELETE: <IP_DA_SUA_MAQUINA>:8082/delete/<string:ip>/
        - Deleta o device de acordo com o IP fornecido.

- ### Device:
  - #### 1 - Construir a imagem docker do device:

    Em outro terminal, rode o comando: docker build --pull --rm -f "device\Dockerfile" -t device-image "device"

    Assim, a imagem será construída e será referenciada como "device-image".

  - #### 2 - Subir o container da imagem docker:

    No terminal, rode o comando: docker run -it --name device device-image

    Adiante, configure o device inserindo as informações que forem requisitadas, como:
      - IP do broker: <IP_DA_SUA_MAQUINA>
      - Nome do dispositivo: ...

  Assim, o dispositivo irá se conectar ao broker, que por sua vez, responderá as requisições
  feitas pela interface via TCP. Note que, a visualização do device já está disponível
  na interface no navegador rodando no container docker.

  É possível manipular o device através do terminal com os comandos de Ligar, Definir temperatura
  e Desligar. Assim como, manipulá-lo pela interface.



## Configuração sem Docker:

-  Caso seu computador já possua as linguagens de programação utilizadas:
  
       - Node.js
       - Python

-  Para rodar a aplicação siga os seguintes passos:

    - Interface:
      -  Entre na pasta: "view/"
      -  No terminal, execute o comando: npm install
      -  E então, execute em seguida o comando: npm start
  
    - Broker:
      -  Entre na pasta: "broker/"
      -  No terminal, execute o comando: python broker.py

    - Device:
      -  Entre na pasta: "device/"
      -  No terminal, execute o comando: python device.py


## Postman:
-   O arquivo de testes de rotas do Postman está anexado a pasta raiz do projeto:
    - PBL.postman_collection.json
      