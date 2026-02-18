import serial
import time
import datetime
import re

PORTA = "COM20"
VELOCIDADE = 115200

print(f"--- Comunicacao Virloc ---")

def calcular_checksum_XVM(pacote_parcial):
    checksum = 0
    for caractere in pacote_parcial:
        checksum = checksum ^ ord(caractere)
    return f"{checksum:02X}"

def criar_pacote_XVM(comando, id_dispositivo="XXXX", msg_id=0x8000):

    id_hex = f"{msg_id:04X}"
    pacote_sem_checksum = f">{comando};ID={id_dispositivo};#{id_hex};"
    checksum = calcular_checksum_XVM(pacote_sem_checksum)
    
    # O SEGREDO: O XVM manda <\r\n no final do pacote
    # O Virloc exige isso para considerar a mensagem recebida e enviar a resposta
    pacote_final = f"{pacote_sem_checksum}*{checksum}<\r\n" 
    return pacote_final

def interagir_com_virloc(conexao, comando_cru, id_dispositivo="XXXX", msg_id=0x8002):
    pacote_tx = criar_pacote_XVM(comando_cru, id_dispositivo, msg_id)
    agora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")[:-3]

    print(f"\n{agora} [TX] : {pacote_tx.strip()}") 
    conexao.write(pacote_tx.encode('utf-8'))
    inicio = time.time()
    buffer_rx = ""

    while time.time() - inicio < 3.0:
        if conexao.in_waiting > 0:
            dado = conexao.read(conexao.in_waiting).decode('utf-8', errors='ignore')
            buffer_rx += dado

            if "<" in buffer_rx and "\n" in buffer_rx:
                agora_rx = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                print(f"\n\n{agora_rx} [RX] : {buffer_rx}\n")
                return buffer_rx.strip()
        time.sleep(0.01)

    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} RX] TIMEOUT: Nenhuma resposta completa.")
    return buffer_rx.strip()

conexao = None
id_virloc_real = "xxxx"
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

    resposta_qsn = interagir_com_virloc(conexao, "QSN", id_virloc_real, id_msg_atual)
    id_msg_atual += 1

    match = re.search(r"ID=([A-Za-z0-9]+);", resposta_qsn)

    if match:
        id_virloc_real = match.group(1)
    else:
        print("Não foi possivel capturar o ID")


    # Prepara e envia o comando
    while True:

        comando_usuario = input("\nDigite o comando XVM (ou 'sair' para encerrar): ")
        
        if comando_usuario.lower() == "sair":
            break

        if comando_usuario == "":
            continue

        interagir_com_virloc(conexao, comando_usuario, id_dispositivo=id_virloc_real, msg_id=id_msg_atual)
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