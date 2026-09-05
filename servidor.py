import Pyro5.api
from logica import LogicaQuoridor

# Configura o Pyro5 para usar o serializador "marshal" para comunicação eficiente
# Marshal: Um formato de serialização de dados que é mais rápido e eficiente do que o padrão do Pyro5
Pyro5.config.SERIALIZER = "marshal"

@Pyro5.api.expose # <--- RMI: Expõe a classe para a rede
class ServidorRMI:
    def __init__(self):
        self.jogo = LogicaQuoridor()

    def entrar(self, nome): return self.jogo.adicionar_jogador(nome) # Adiciona um jogador ao jogo
    def obter_estado(self): return self.jogo.obter_estado() # Retorna o estado atual do jogo
    def mover(self, nome, r, c): return self.jogo.mover(nome, r, c) # Move o peão do jogador para a posição (r, c)
    def colocar_parede(self, nome, orientacao, r, c):  # Coloca uma parede na posição (r, c) com a orientação especificada ('H' para horizontal, 'V' para vertical)
        return self.jogo.colocar_parede(nome, orientacao, r, c) # Retorna True se a ação foi bem-sucedida, False caso contrário

if __name__ == "__main__":
    # Cria um daemon Pyro5 para gerenciar a comunicação entre o servidor e os clientes
    # ... no bloco principal RMI ...
    daemon = Pyro5.api.Daemon() 
    # Registra a instância do servidor RMI no daemon e obtém a URI para os clientes se conectarem
    instancia_unica = ServidorRMI() 
    uri = daemon.register(instancia_unica)

    # Exibe informações sobre o servidor e a URI para os clientes se conectarem
    print("="*50)
    print("SERVIDOR QUORIDOR DISTRIBUÍDO INICIADO")
    print(f"URI: {uri}")
    print("Compartilhe esta URI com os clientes.")
    print("="*50)
    daemon.requestLoop()
