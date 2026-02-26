import asyncio
import json
import can
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI(title="Simulador J1939 - Virloc 8 Lab")

# Configuração do Barramento CAN Virtual (Memória do Python)
can_bus = can.Bus("virloc_lab", bustype="virtual")

# Estado Global do Veículo (Atualizado via WebSocket)
vehicle_state = {
    "profile": "standard", # "standard" ou "volvo"
    "rpm": 0,
    "speed": 0,
    "pedal": 0,
    "ignition": False,
    "clutch": False
}

# Lista de clientes WebSocket conectados (para broadcasting do Log)
connected_clients = []

def build_j1939_msg(pgn: int, payload: list) -> can.Message:
    """
    Constrói a mensagem CAN no padrão J1939 (ID Estendido de 29 bits).
    Lógica do ID: (Prioridade << 26) | (PGN << 8) | Source_Address
    """
    priority = 3
    source_address = 0  # 0 = Engine Controller
    arbitration_id = (priority << 26) | (pgn << 8) | source_address
    
    return can.Message(
        arbitration_id=arbitration_id,
        data=payload,
        is_extended_id=True
    )

async def can_injection_task():
    """
    Tarefa de background (Task) que roda a 10Hz.
    Injeta os dados na CAN e envia logs para a UI a 1Hz para não travar o navegador.
    """
    loop_counter = 0
    while True:
        if vehicle_state["ignition"]:
            msgs_to_send = []
            log_messages = []
            
            # --- SELEÇÃO DE PGNs POR PERFIL ---
            if vehicle_state["profile"] == "standard":
                pgn_rpm, pgn_spd, pgn_pdl = 61444, 65265, 61443
            else: # Volvo FMX500 Custom
                pgn_rpm, pgn_spd, pgn_pdl = 65343, 65472, 65311

            # 1. Montagem RPM (Resolução: 0.125 rpm/bit)
            rpm_raw = int(vehicle_state["rpm"] / 0.125)
            # Bytes 4 e 5 do J1939 (Little Endian)
            rpm_payload = [0xFF, 0xFF, 0xFF, rpm_raw & 0xFF, (rpm_raw >> 8) & 0xFF, 0xFF, 0xFF, 0xFF]
            msg_rpm = build_j1939_msg(pgn_rpm, rpm_payload)
            msgs_to_send.append(msg_rpm)

            # 2. Montagem Velocidade (Resolução: 1/256 km/h/bit)
            spd_raw = int(vehicle_state["speed"] * 256)
            # Bytes 2 e 3 do J1939
            spd_payload = [0xFF, spd_raw & 0xFF, (spd_raw >> 8) & 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
            msg_spd = build_j1939_msg(pgn_spd, spd_payload)
            msgs_to_send.append(msg_spd)

            # 3. Montagem Pedal (Resolução: 0.4 %/bit)
            pdl_raw = int(vehicle_state["pedal"] / 0.4)
            # Byte 2 do J1939
            pdl_payload = [0xFF, pdl_raw & 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
            msg_pdl = build_j1939_msg(pgn_pdl, pdl_payload)
            msgs_to_send.append(msg_pdl)

            # Injeção real no barramento (10Hz)
            for msg in msgs_to_send:
                can_bus.send(msg)

            # Envia log para o Frontend apenas a 1Hz (a cada 10 loops)
            if loop_counter % 10 == 0 and connected_clients:
                for msg in msgs_to_send:
                    hex_data = " ".join([f"{b:02X}" for b in msg.data])
                    pgn_extract = (msg.arbitration_id >> 8) & 0x3FFFF
                    log_messages.append(f"PGN {pgn_extract} | Payload: [{hex_data}]")
                
                # Broadcasting do log para todos os clientes
                for client in connected_clients:
                    try:
                        await client.send_text("\n".join(log_messages))
                    except:
                        pass

        loop_counter += 1
        await asyncio.sleep(0.1) # 100 milissegundos (10Hz)

@app.on_event("startup")
async def startup_event():
    # Inicia o motor de injeção CAN ao rodar o servidor
    asyncio.create_task(can_injection_task())

@app.get("/")
async def get():
    # Serve a página HTML diretamente
    with open("index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)
    try:
        while True:
            # Recebe as interações do painel (Slider, Checkbox, etc)
            data = await websocket.receive_text()
            ui_state = json.loads(data)
            
            # Atualiza o estado global
            vehicle_state["profile"] = ui_state.get("profile", vehicle_state["profile"])
            vehicle_state["rpm"] = int(ui_state.get("rpm", vehicle_state["rpm"]))
            vehicle_state["speed"] = int(ui_state.get("speed", vehicle_state["speed"]))
            vehicle_state["pedal"] = int(ui_state.get("pedal", vehicle_state["pedal"]))
            vehicle_state["ignition"] = bool(ui_state.get("ignition", vehicle_state["ignition"]))
            vehicle_state["clutch"] = bool(ui_state.get("clutch", vehicle_state["clutch"]))
            
    except WebSocketDisconnect:
        connected_clients.remove(websocket)