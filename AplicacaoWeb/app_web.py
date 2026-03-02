import serial
import time
import re
import threading
from flask import Flask, render_template, jsonify, request
from functions import calcular_checksum_XVM, criar_pacote_XVM, interagir_com_virloc, escutar_porta_Virloc

app = Flask(__name__)

PORTA = "COM20"
VELOCIDADE = 115200
conexao_serial = None
thread_escuta = None

estado_virloc = {"id": "XXXX"}  
controle_thread = {"rodando": False}
id_msg_atual = 0x8000
historico_terminal = []


@app.route('/') # Rota principal para renderizar a página HTML
def index():
    return render_template('index.html')

@app.route('/conectar', methods=['POST']) # Rota para iniciar a conexão com o Virloc e começar a escutar a porta serial
def conectar():
    global conexao_serial, thread_escuta, id_msg_atual, estado_virloc # Variáveis globais para manter o estado da conexão, thread de escuta, ID da mensagem e estado do Virloc
    if conexao_serial and conexao_serial.is_open:
        return jsonify({"status": "erro", "msg": "Já conectado à porta."})
    
    try:
        # Abre a porta replicando o IOCTL_SERIAL_GET_LINE_CONTROL do XVM
        conexao_serial = serial.Serial(
        port=PORTA, 
        baudrate=VELOCIDADE, 
        timeout=1,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        xonxoff=False,
        rtscts=False, # Flow control = 0x0
        dsrdtr=False  # DTR é controlado manualmente abaixo
    )

    # Replicando IOCTL_SERIAL_CLR_RTS e IOCTL_SERIAL_SET_DTR
        conexao_serial.rts = False
        conexao_serial.dtr = True
        # Replicando IOCTL_SERIAL_PURGE (Limpeza de buffers)
        conexao_serial.reset_input_buffer()
        conexao_serial.reset_output_buffer()

        historico_terminal.append(f"Conexão com a porta {PORTA} estabelecida com sucesso!")
        time.sleep(1.0)  # Pequena pausa para garantir que a porta esteja pronta

        controle_thread["rodando"] = True # Inicia a escuta da porta serial em uma thread separada
        estado_virloc["id"] = "XXXX"  # Reseta o ID do Virloc para o valor padrão
        thread_escuta = threading.Thread(
            target=escutar_porta_Virloc,
            args=(conexao_serial, estado_virloc, historico_terminal, controle_thread),
            daemon=True
        ) # Thread daemon para garantir que ela seja encerrada quando o programa fechar
        thread_escuta.start()

        interagir_com_virloc(conexao_serial, "QSN", estado_virloc["id"], id_msg_atual, historico_terminal) # Envia o comando QSN para obter o ID do Virloc
        id_msg_atual += 1

        return jsonify({"status": "sucesso"})
    except Exception as e:
        return jsonify({"status": "erro", "msg": str(e)})
    


@app.route('/enviar', methods=['POST']) # Rota para enviar um comando digitado pelo usuário para o Virloc
def enviar():
    global id_msg_atual
    dados = request.get_json()
    comando = dados.get("comando", "").strip().upper()
    if not conexao_serial or not conexao_serial.is_open:
        return jsonify({"status": "erro", "msg": "Porta Fechada"})
    
    interagir_com_virloc(conexao_serial, comando, estado_virloc["id"], id_msg_atual, historico_terminal) # Envia o comando para o Virloc usando a função definida em functions.py
    id_msg_atual += 1 # Incrementa o ID da mensagem para a próxima comunicação

    return jsonify({"status": "ok"})
    
@app.route('/desconectar', methods=['POST']) # Rota para desconectar do Virloc e parar a escuta da porta serial
def desconectar():
    global conexao_serial, thread_escuta

    controle_thread["rodando"] = False # Sinaliza para a thread de escuta parar
    time.sleep(0.5)

    if conexao_serial and conexao_serial.is_open:
        conexao_serial.close()
        historico_terminal.append("Conexão com a porta serial encerrada.")
        return jsonify({"status": "sucesso"})

    return jsonify({"status": "erro", "msg": "Nenhuma conexão ativa"})

@app.route('/logs', methods=['GET'])
def get_logs():
    return jsonify({"logs": historico_terminal})

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)