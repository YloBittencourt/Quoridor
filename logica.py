import threading
from collections import deque

class LogicaQuoridor:
    def __init__(self):
        self.lock = threading.Lock()
        self.jogadores = [] 
        self.posicoes = {}  
        self.estoque = {}   
        self.paredes_h = set() 
        self.paredes_v = set() 
        self.turno_idx = 0
        self.iniciado = False
        self.vencedor = None
        
        self.config_inicial = [
            {"start": (8, 4), "goal_row": 0, "goal_col": None}, 
            {"start": (0, 4), "goal_row": 8, "goal_col": None}, 
            {"start": (4, 0), "goal_row": None, "goal_col": 8}, 
            {"start": (4, 8), "goal_row": None, "goal_col": 0}  
        ]
        self.objetivos = {}

    def adicionar_jogador(self, nome):
        with self.lock:
            if self.iniciado: return "Erro: Jogo já iniciado."
            if nome in self.jogadores: return "Erro: Nome já existe."
            if len(self.jogadores) >= 4: return "Erro: Lotação máxima."
            
            idx = len(self.jogadores)
            self.jogadores.append(nome)
            self.posicoes[nome] = self.config_inicial[idx]["start"]
            self.objetivos[nome] = self.config_inicial[idx]
            self.estoque[nome] = 5 
            
            if len(self.jogadores) == 4:
                self.iniciado = True
                
            return f"Sucesso: {nome} entrou. Aguardando..."

    def obter_estado(self):
        with self.lock:
            return {
                "jogadores": self.jogadores,
                "posicoes": self.posicoes,
                "paredes_h": list(self.paredes_h), 
                "paredes_v": list(self.paredes_v),
                "estoque": self.estoque,
                "turno": self.jogadores[self.turno_idx] if self.jogadores else None,
                "iniciado": self.iniciado,
                "vencedor": self.vencedor
            }

    def _tem_parede(self, r1, c1, r2, c2):
        """Verifica se há parede bloqueando o movimento entre duas casas adjacentes."""
        if r2 == r1 + 1: return (r1, c1) in self.paredes_h or (r1, c1-1) in self.paredes_h
        if r2 == r1 - 1: return (r2, c1) in self.paredes_h or (r2, c1-1) in self.paredes_h
        if c2 == c1 + 1: return (r1, c1) in self.paredes_v or (r1-1, c1) in self.paredes_v
        if c2 == c1 - 1: return (r1, c2) in self.paredes_v or (r1-1, c2) in self.paredes_v
        return False

    def mover(self, nome, r, c):
        with self.lock:
            if not self.iniciado or self.vencedor: return "Jogo não está ativo."
            if nome != self.jogadores[self.turno_idx]: return "Não é seu turno."
            
            r_atual, c_atual = self.posicoes[nome]
            dr = r - r_atual
            dc = c - c_atual
            dist = abs(dr) + abs(dc)
            
            if not (0 <= r < 9 and 0 <= c < 9): return "Fora do tabuleiro."
            if (r, c) in self.posicoes.values(): return "Casa ocupada."
            
            if dist == 1:
                # Movimento simples
                if self._tem_parede(r_atual, c_atual, r, c): return "Parede bloqueia."
            
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

            self.posicoes[nome] = (r, c)
            self._verificar_vitoria(nome, r, c)
            self._passar_turno()
            return "Movimento realizado."

    def colocar_parede(self, nome, orientacao, r, c):
        with self.lock:
            if not self.iniciado or self.vencedor: return "Jogo não está ativo."
            if nome != self.jogadores[self.turno_idx]: return "Não é seu turno."
            if self.estoque[nome] <= 0: return "Sem paredes."
            if not (0 <= r < 8 and 0 <= c < 8): return "Posição de parede inválida."

            if orientacao == 'H':
                if (r, c) in self.paredes_h or (r, c-1) in self.paredes_h or (r, c+1) in self.paredes_h or (r, c) in self.paredes_v:
                    return "Parede sobreposta."
                self.paredes_h.add((r, c))
            else:
                if (r, c) in self.paredes_v or (r-1, c) in self.paredes_v or (r+1, c) in self.paredes_v or (r, c) in self.paredes_h:
                    return "Parede sobreposta."
                self.paredes_v.add((r, c))

            if not self._todos_tem_caminho():
                if orientacao == 'H': self.paredes_h.remove((r, c))
                else: self.paredes_v.remove((r, c))
                return "Erro: Parede bloqueia totalmente o caminho de um jogador."

            self.estoque[nome] -= 1
            self._passar_turno()
            return "Parede colocada."

    def _todos_tem_caminho(self):
        for jog in self.jogadores:
            if not self._bfs_caminho_livre(jog): return False
        return True

    def _bfs_caminho_livre(self, nome):
        start = self.posicoes[nome]
        obj = self.objetivos[nome]
        queue = deque([start])
        visited = set([start])
        
        while queue:
            r, c = queue.popleft()
            if (obj["goal_row"] is not None and r == obj["goal_row"]) or \
               (obj["goal_col"] is not None and c == obj["goal_col"]):
                return True
                
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

    def _verificar_vitoria(self, nome, r, c):
        obj = self.objetivos[nome]
        if (obj["goal_row"] is not None and r == obj["goal_row"]) or \
           (obj["goal_col"] is not None and c == obj["goal_col"]):
            self.vencedor = nome

    def _passar_turno(self):
        if not self.vencedor:
            self.turno_idx = (self.turno_idx + 1) % 4
