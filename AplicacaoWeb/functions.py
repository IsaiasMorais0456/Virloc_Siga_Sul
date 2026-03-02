import datetime
import time
import re

def calcular_checksum_XVM(pacote_parcial):
    checksum = 0
    for caractere in pacote_parcial:
        checksum = checksum ^ ord(caractere)
    return f"{checksum:02X}" # Retorna o checksum como uma string hexadecimal de 2 dígitos


def criar_pacote_XVM(comando, id_dispositivo="XXXX", msg_id=0x8000):  #Função responsável por traduzir o que foi digitado e mandar pro virloc, seguindo o protocolo XVM
    id_hex = f"{msg_id:04X}" # Converte o ID da mensagem para hexadecimal, garantindo 4 dígitos (ex: 0x8000 -> "8000")
    pacote_sem_checksum = f">{comando};ID={id_dispositivo};#{id_hex};" # Formata o pacote sem o checksum, seguindo o padrão do XVM
    checksum = calcular_checksum_XVM(pacote_sem_checksum)
    
    pacote_final = f"{pacote_sem_checksum}*{checksum}<\r\n" # Adiciona o checksum e os caracteres de início e fim do pacote, conforme o protocolo XVM
    return pacote_final


def interagir_com_virloc(conexao, comando_cru, id_dispositivo, msg_id, lista_logs): # Função que recebe o pacote criado e então envia ao virloc, e 
    pacote_tx = criar_pacote_XVM(comando_cru, id_dispositivo, msg_id) 
    agora = datetime.datetime.now().strftime("%d-%m %H:%M:%S.%f")[:-3]

    log_msg = f"\n{agora} [TX] : {pacote_tx.strip()}" # Prepara a mensagem de log para exibir o pacote enviado, incluindo a data e hora do envio
    print(log_msg) 
    lista_logs.append(log_msg)

    conexao.write(pacote_tx.encode('utf-8'))

def escutar_porta_Virloc(conexao, estado_virloc, lista_logs, controle_thread): # Aqui implementamos o outro cérebro do código, uma escuta passiva que fica aguardando todas as mensagens que chegam do virloc
    buffer_rx = ""
    while controle_thread["rodando"]: 
        try:
            if conexao.in_waiting > 0:
                dado = conexao.read(conexao.in_waiting).decode('utf-8', errors='ignore')
                buffer_rx += dado

                if "<" in buffer_rx and "\n" in buffer_rx:
                    mensagens = buffer_rx.split("\n")
                    for msg in mensagens:
                        if "<" in msg:
                            agora_rx = datetime.datetime.now().strftime("%d-%m %H:%M:%S.%f")[:-3]
                            log_msg = f"\n\n{agora_rx} [RX] : {msg.strip()}\n"
                            print(log_msg)
                            lista_logs.append(log_msg)
                            
                            match = re.search(r"ID=([A-Za-z0-9]+);", msg)
                            if match:
                                id_encontrado = match.group(1)
                                if id_encontrado != "XXXX" and id_encontrado != estado_virloc["id"]:
                                    estado_virloc["id"] = id_encontrado

                    buffer_rx = ""  # Limpa o buffer após processar as mensagens 
        except Exception as e:
            break

        time.sleep(0.01)