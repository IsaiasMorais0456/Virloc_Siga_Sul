==================================================
        TERMINAL ASSINCRONO (PROTOCOLO XVM)
==================================================

O arquivo app.py serve como um comunicador Serial com rastreadores telemetria Virloc, foi pego a base do Terminal XVM para conseguir entender como os comandos em XVM funcionam e como ele consegue receber as informações do RX no equipamento Virloc

==================================================
            FUNCIONALIDADES PRINCIPAIS
==================================================
- Calculo do Checksum exigida pelo protocolo
- Envio automático de comando QSN pare capturar o ID do dispositivo e armazenar ele nas próximas mensagens automáticamente
- Envio e retorno de comandos via TX e RX
- Uma thread dedicada monitora a porta COM continuamente para recebimento automático das informações do equipamento
- O Usuário apenas digita um comando Cru "QID" e o python monta toda a estrutura do protocolo (>QID;ID=XXXX;#8000;*5D<).

==================================================
GUIA RÁPIDO - TERMINAL VIRLOC PYTHON (BANCADA)
==================================================

1. ATIVAR O AMBIENTE VIRTUAL (VENV)
Comando: .\venv\Scripts\activate.ps1

2. INSTALAR TODAS AS LIBS PRA RODAR O CODE
Comando: pip install requirements.txt

3. RODAR O CÓDIGO 
Comando: python app.py

