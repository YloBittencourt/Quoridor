import Pyro5.api
from logica import LogicaQuoridor

Pyro5.config.SERIALIZER = "marshal"

@Pyro5.api.expose
class ServidorRPC:
    def __init__(self):
        self.jogo = LogicaQuoridor()

    def entrar(self, nome): return self.jogo.adicionar_jogador(nome)
    def obter_estado(self): return self.jogo.obter_estado()
    def mover(self, nome, r, c): return self.jogo.mover(nome, r, c)
    def colocar_parede(self, nome, orientacao, r, c): 
        return self.jogo.colocar_parede(nome, orientacao, r, c)

if __name__ == "__main__":
    daemon = Pyro5.api.Daemon()
    instancia_unica = ServidorRPC() 
    uri = daemon.register(instancia_unica)
    
    print("="*50)
    print("SERVIDOR QUORIDOR DISTRIBUÍDO INICIADO")
    print(f"URI: {uri}")
    print("Compartilhe esta URI com os clientes.")
    print("="*50)
    daemon.requestLoop()
