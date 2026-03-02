import serial
import time
import re
import threading
from functions import calcular_checksum_XVM, criar_pacote_XVM, interagir_com_virloc, escutar_porta_Virloc


PORTA = "COM20"
VELOCIDADE = 115200

print(f"--- Comunicacao Virloc ---")
conexao = None
estado_virloc = {"id": "XXXX"}  
id_msg_atual = 0x8000

try:
    # Abre a porta replicando o IOCTL_SERIAL_GET_LINE_CONTROL do XVM
    conexao = serial.Serial(
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
    conexao.rts = False
    conexao.dtr = True
    
    # Replicando IOCTL_SERIAL_PURGE (Limpeza de buffers)
    conexao.reset_input_buffer()
    conexao.reset_output_buffer()
    

    print("Conexão com a porta estabelecida com sucesso!")

    time.sleep(0.5)  # Pequena pausa para garantir que a porta esteja pronta

    threading_escuta = threading.Thread(target=escutar_porta_Virloc, args=(conexao, estado_virloc), daemon=True)
    threading_escuta.start()

    interagir_com_virloc(conexao, "QSN", id_dispositivo=estado_virloc["id"], msg_id=id_msg_atual)
    id_msg_atual += 1

    time.sleep(1.5)  # Aguarda um pouco para receber a resposta do QSN e atualizar o ID do Virloc

    while True:

        comando_usuario = input().strip().upper()
        
        if comando_usuario == "SAIR":
            break

        if comando_usuario == "":
            continue

        interagir_com_virloc(conexao, comando_usuario, id_dispositivo=estado_virloc["id"], msg_id=id_msg_atual)
        id_msg_atual += 1


        if id_msg_atual > 0xFFFF:
            id_msg_atual = 0x8000

except Exception as e:
    print(f"\nErro: {e}")

finally:
    if conexao and conexao.is_open:
        conexao.close()
        print("\nConexão encerrada.")
    input("Pressione ENTER para sair...")