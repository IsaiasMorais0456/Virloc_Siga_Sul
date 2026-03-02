function conectar(){
                fetch('/conectar', { method: 'POST'})
                .then(response => response.json())
                .then(data =>{
                    if(data.status === 'erro') alert("Erro: " + data.msg);
                    else document.getElementById("terminal").innerHTML += data.msg + "\n";
                });
            }

            let historicoComandos = [];
            let historicoIndex = -1;

            function enviarComando(){
                const input = document.getElementById('inputComando');
                const cmd = input.value.trim();

            if (cmd !== "") {   
                fetch('/enviar', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ comando: cmd })
                }).then(() =>{
                    atualizarTerminal();
                });

                if(historicoComandos[historicoComandos.length - 1] !== cmd){
                    historicoComandos.push(cmd);
                }
            }
                historicoIndex = historicoComandos.length;
            
            }

            document.getElementById("inputComando").addEventListener("keydown",function(event){
                if(event.key === "Enter"){
                    enviarComando();
                    this.select();
                } else if(event.key ==="ArrowUp"){ // Permite navegar para cima no histórico de comandos
                    event.preventDefault();

                    if(historicoComandos.length === 0) return; // Se não houver comandos no histórico, não faz nada

                    if (historicoIndex === historicoComandos.length) { // Se o índice estiver no final do histórico, verifica se o comando atual é diferente do último comando do histórico
                       if (this.value === historicoComandos[historicoComandos.length - 1]) {
                            historicoIndex = Math.max(0, historicoComandos.length - 2); // Move o índice para o último comando do histórico
                    } else {
                            historicoIndex = historicoComandos.length - 1; // Move o índice para o último comando do histórico
                        }
                    } else if (historicoIndex > 0){
                        historicoIndex--;
                    }

                    this.value = historicoComandos[historicoIndex];
                    
                } else if(event.key === "ArrowDown"){ // Permite navegar para baixo no histórico de comandos
                    event.preventDefault();
                    if(historicoComandos.length > 0 && historicoIndex < historicoComandos.length - 1){
                        historicoIndex++;
                        this.value = historicoComandos[historicoIndex];
                    } else {
                        historicoIndex = historicoComandos.length;
                        this.value = "";
                    }
                }      
            });

            function limpar_terminal(){
                fetch('/limpar_terminal', { method: 'POST'})
                .then(response => response.json())
                .then(data => {
                    if(data.status === 'sucesso'){
                        document.getElementById("terminal").innerHTML = "";
                    } else {
                        alert("Erro: " + data.msg);
                    }
                });
            }

            function baixar_logs(){
                window.location.href = '/baixar_logs';
            }

            function desconectar(){
                fetch('/desconectar', { method: 'POST'})
                .then(response => response.json())
                .then(data =>{
                    if(data.status === 'erro') alert("Erro: " + data.msg);
                    else document.getElementById("terminal").innerHTML += data.msg + "\n";
                });
            }
            
            function atualizarTerminal(){
                fetch('/logs')
                .then(response => response.json())
                .then(data => {
                    const terminal = document.getElementById("terminal");

                    const linhasFormatadas = data.logs.map(linha => {
                        let linhaLimpa = linha.replace(/\n/g, '').trim();
                        if(linhaLimpa === '') return '';

                        let cor = 'white';
                        if(linhaLimpa.includes('[TX]')){
                            cor = '#28a745';
                        } else if(linhaLimpa.includes('[RX]')){
                            cor = '#17a2b8';
                        }

                        return `<div style="color: ${cor}; margin-bottom: 4px;">${linhaLimpa}</div>`;
                    }).filter(linha => linha !== '');
                    terminal.innerHTML = linhasFormatadas.join('');
                    terminal.scrollTop = terminal.scrollHeight;
                });
            }

            setInterval(atualizarTerminal, 300);