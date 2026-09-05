import threading
from collections import deque

class LogicaQuoridor:
    def __init__(self):
        # [CONCEITO SD: Exclusão Mútua Centralizada] 
        # Servidores RMI são multithread. O Lock impede condições de corrida 
        # garantindo que as threads operárias não corrompam os dicionários simultaneamente.

        self.lock = threading.Lock() # threading.Lock() para exclusão mútua
        self.jogadores = [] # Lista de nomes dos jogadores
        self.posicoes = {}  # Dicionário de posições dos jogadores, chave: nome, valor: (linha, coluna)
        self.estoque = {} # Dicionário de estoque de paredes dos jogadores, chave: nome, valor: número de paredes restantes
        self.paredes_h = set() # Conjunto de paredes horizontais, cada parede é representada por uma tupla (linha, coluna) indicando a posição da parede
        self.paredes_v = set() # Conjunto de paredes verticais, cada parede é representada por uma tupla (linha, coluna) indicando a posição da parede
        self.turno_idx = 0 # Índice do jogador cujo turno é atual
        self.iniciado = False # Indica se o jogo foi iniciado
        self.vencedor = None # Indica o nome do jogador vencedor, se houver

        # Configuração inicial dos jogadores e seus objetivos
        self.config_inicial = [
            {"start": (8, 4), "goal_row": 0, "goal_col": None}, # Jogador 1: Começa na linha 8, coluna 4, objetivo é chegar na linha 0
            {"start": (0, 4), "goal_row": 8, "goal_col": None}, # Jogador 2: Começa na linha 0, coluna 4, objetivo é chegar na linha 8
            {"start": (4, 0), "goal_row": None, "goal_col": 8}, # Jogador 3: Começa na linha 4, coluna 0, objetivo é chegar na coluna 8
            {"start": (4, 8), "goal_row": None, "goal_col": 0}  # Jogador 4: Começa na linha 4, coluna 8, objetivo é chegar na coluna 0
        ]
        self.objetivos = {}

    def adicionar_jogador(self, nome):
        # [CONCEITO SD: Região Crítica] O bloco 'with self.lock' protege a alteração de estado
        with self.lock:
            if self.iniciado: return "Erro: Jogo já iniciado."
            if nome in self.jogadores: return "Erro: Nome já existe."
            if len(self.jogadores) >= 4: return "Erro: Lotação máxima."

            # Adiciona o jogador à lista
            # define sua posição inicial, objetivo e estoque de paredes
            idx = len(self.jogadores)
            self.jogadores.append(nome)
            self.posicoes[nome] = self.config_inicial[idx]["start"]
            self.objetivos[nome] = self.config_inicial[idx]
            self.estoque[nome] = 5 

            # Se todos os 4 jogadores estiverem presentes, o jogo é marcado como iniciado
            if len(self.jogadores) == 4:
                self.iniciado = True
                
            return f"Sucesso: {nome} entrou. Aguardando..."

    
    def obter_estado(self):
        with self.lock:
            # O bloco 'with self.lock' protege a leitura de estado
            return {
                "jogadores": self.jogadores,
                "posicoes": self.posicoes,
                "paredes_h": list(self.paredes_h), # Converte o conjunto de paredes horizontais em lista para serialização
                "paredes_v": list(self.paredes_v), # Converte o conjunto de paredes verticais em lista para serialização
                "estoque": self.estoque, # Dicionário de estoque de paredes dos jogadores
                "turno": self.jogadores[self.turno_idx] if self.jogadores else None, # Indica o nome do jogador cujo turno é atual
                "iniciado": self.iniciado, # Indica se o jogo foi iniciado
                "vencedor": self.vencedor # Indica o nome do jogador vencedor, se houver
            }

    #  método _tem_parede é chamado dentro de mover() e colocar_parede(), que já estão protegidos pelo lock. 
    # Portanto, não é necessário adicionar um lock aqui.
    def _tem_parede(self, r1, c1, r2, c2):
        """Verifica se há parede bloqueando o movimento entre duas casas adjacentes."""
        if r2 == r1 + 1: return (r1, c1) in self.paredes_h or (r1, c1-1) in self.paredes_h # Verifica se há parede horizontal entre (r1, c1) e (r2, c2)
        if r2 == r1 - 1: return (r2, c1) in self.paredes_h or (r2, c1-1) in self.paredes_h # Verifica se há parede horizontal entre (r2, c1) e (r1, c1)
        if c2 == c1 + 1: return (r1, c1) in self.paredes_v or (r1-1, c1) in self.paredes_v # Verifica se há parede vertical entre (r1, c1) e (r2, c2)
        if c2 == c1 - 1: return (r1, c2) in self.paredes_v or (r1-1, c2) in self.paredes_v # Verifica se há parede vertical entre (r1, c2) e (r1, c1)
        return False

    # método mover é chamado dentro de mover() e colocar_parede(), que já estão protegidos pelo lock.
    def mover(self, nome, r, c):
        with self.lock:
            # O bloco 'with self.lock' protege a alteração de estado
            if not self.iniciado or self.vencedor: return "Jogo não está ativo."
            if nome != self.jogadores[self.turno_idx]: return "Não é seu turno."

            # Verifica se o movimento é válido
            r_atual, c_atual = self.posicoes[nome] # Posição atual do jogador
            dr = r - r_atual # Diferença de linha entre a posição atual e a posição desejada
            dc = c - c_atual # Diferença de coluna entre a posição atual e a posição desejada
            dist = abs(dr) + abs(dc) # Distância de Manhattan entre a posição atual e a posição desejada

            # Verifica se a posição desejada está dentro do tabuleiro e se a casa está ocupada
            if not (0 <= r < 9 and 0 <= c < 9): return "Fora do tabuleiro."
            if (r, c) in self.posicoes.values(): return "Casa ocupada."

            # Verifica se o movimento é simples
            if dist == 1:
                # Movimento simples
                if self._tem_parede(r_atual, c_atual, r, c): return "Parede bloqueia."

            # Verifica se o movimento é um pulo
            elif dist == 2:
                # Pulo em linha reta
                if abs(dr) == 2 or abs(dc) == 2:
                    rm, cm = r_atual + dr//2, c_atual + dc//2
                    if (rm, cm) not in self.posicoes.values(): return "Pulo requer um oponente na frente."
                    if self._tem_parede(r_atual, c_atual, rm, cm): return "Parede bloqueia o pulo."
                    if self._tem_parede(rm, cm, r, c): return "Parede bloqueia a aterrissagem."
                
                # Pulo diagonal (lateral)
                elif abs(dr) == 1 and abs(dc) == 1:
                    pulo_valido = False
                    
                    # Checa oponente no eixo horizontal
                    if (r_atual, c) in self.posicoes.values() and not self._tem_parede(r_atual, c_atual, r_atual, c):
                        reto_r, reto_c = r_atual, c + dc
                        # O pulo reto por cima do oponente está bloqueado?
                        bloqueado = not (0 <= reto_r < 9 and 0 <= reto_c < 9) or (reto_r, reto_c) in self.posicoes.values() or self._tem_parede(r_atual, c, reto_r, reto_c)
                        if bloqueado and not self._tem_parede(r_atual, c, r, c):
                            pulo_valido = True

                    # Checa oponente no eixo vertical
                    if not pulo_valido and (r, c_atual) in self.posicoes.values() and not self._tem_parede(r_atual, c_atual, r, c_atual):
                        reto_r, reto_c = r + dr, c_atual
                        # O pulo reto por cima do oponente está bloqueado?
                        bloqueado = not (0 <= reto_r < 9 and 0 <= reto_c < 9) or (reto_r, reto_c) in self.posicoes.values() or self._tem_parede(r, c_atual, reto_r, reto_c)
                        if bloqueado and not self._tem_parede(r, c_atual, r, c):
                            pulo_valido = True
                    
                    if not pulo_valido: return "Pulo diagonal inválido (falta oponente ou paredes bloqueiam)."
            else:
                return "Movimento inválido."

            # Se todas as verificações passarem, atualiza a posição do jogador, verifica vitória e passa o turno
            self.posicoes[nome] = (r, c)
            self._verificar_vitoria(nome, r, c)
            self._passar_turno()
            return "Movimento realizado."

    # método colocar_parede é chamado dentro de mover() e colocar_parede()
    # que já estão protegidos pelo lock.
    def colocar_parede(self, nome, orientacao, r, c):
        with self.lock:
            if not self.iniciado or self.vencedor: return "Jogo não está ativo." # Verifica se o jogo está ativo
            if nome != self.jogadores[self.turno_idx]: return "Não é seu turno." # Verifica se é o turno do jogador
            if self.estoque[nome] <= 0: return "Sem paredes." # Verifica se o jogador tem paredes restantes
            if not (0 <= r < 8 and 0 <= c < 8): return "Posição de parede inválida." # Verifica se a posição da parede está dentro do tabuleiro

            # Verifica se a parede pode ser colocada
            if orientacao == 'H':
                # Verifica se a parede horizontal sobrepõe outra parede
                if (r, c) in self.paredes_h or (r, c-1) in self.paredes_h or (r, c+1) in self.paredes_h or (r, c) in self.paredes_v:
                    return "Parede sobreposta."
                self.paredes_h.add((r, c))
            else:
                # Verifica se a parede vertical sobrepõe outra parede
                if (r, c) in self.paredes_v or (r-1, c) in self.paredes_v or (r+1, c) in self.paredes_v or (r, c) in self.paredes_h:
                    return "Parede sobreposta."
                self.paredes_v.add((r, c))

            # Verifica se todos os jogadores ainda têm um caminho livre para seu objetivo
            if not self._todos_tem_caminho():
                if orientacao == 'H': self.paredes_h.remove((r, c))
                else: self.paredes_v.remove((r, c))
                return "Erro: Parede bloqueia totalmente o caminho de um jogador."

            # Se todas as verificações passarem, decrementa o estoque de paredes do jogador e passa o turno
            self.estoque[nome] -= 1
            self._passar_turno()
            return "Parede colocada."

    # _todos_tem_caminho e _bfs_caminho_livre são métodos auxiliares 
    # para verificar se todos os jogadores ainda têm um caminho livre 
    # para seu objetivo após a colocação de uma parede.
    def _todos_tem_caminho(self):
        for jog in self.jogadores:
            if not self._bfs_caminho_livre(jog): return False
        return True

    def _bfs_caminho_livre(self, nome):
        start = self.posicoes[nome]
        obj = self.objetivos[nome]
        queue = deque([start])
        visited = set([start])

        # BFS (Busca em Largura) para verificar se há um caminho livre até o objetivo do jogador
        while queue:
            r, c = queue.popleft()
            if (obj["goal_row"] is not None and r == obj["goal_row"]) or \
               (obj["goal_col"] is not None and c == obj["goal_col"]):
                return True

            # Verifica os vizinhos possíveis (cima, baixo, esquerda, direita) e se há paredes bloqueando o caminho
            vizinhos = []
            if r < 8 and not ((r, c) in self.paredes_h or (r, c-1) in self.paredes_h): vizinhos.append((r+1, c))
            if r > 0 and not ((r-1, c) in self.paredes_h or (r-1, c-1) in self.paredes_h): vizinhos.append((r-1, c))
            if c < 8 and not ((r, c) in self.paredes_v or (r-1, c) in self.paredes_v): vizinhos.append((r, c+1))
            if c > 0 and not ((r, c-1) in self.paredes_v or (r-1, c-1) in self.paredes_v): vizinhos.append((r, c-1))
            
            for v in vizinhos:
                if v not in visited:
                    visited.add(v)
                    queue.append(v)
        return False

    # _verificar_vitoria e _passar_turno são métodos auxiliares 
    # para verificar se um jogador venceu e para passar o turno para o próximo jogador.
    def _verificar_vitoria(self, nome, r, c):
        obj = self.objetivos[nome]
        if (obj["goal_row"] is not None and r == obj["goal_row"]) or \
           (obj["goal_col"] is not None and c == obj["goal_col"]):
            self.vencedor = nome

    def _passar_turno(self):
        if not self.vencedor:
            self.turno_idx = (self.turno_idx + 1) % 4
