import Pyro5.api
import Pyro5.errors
import tkinter as tk
from tkinter import simpledialog, messagebox
import threading
import time
import pygame
import sys

# Cores do Tabuleiro e Peões
COR_MESA = (30, 30, 35)
COR_BASE_TABULEIRO = (60, 35, 20) 
COR_CASA_SOMBRA = (160, 110, 70)  
COR_CASA = (220, 170, 110)        
COR_PAREDE = (240, 200, 140)      
COR_PAREDE_BORDA = (50, 25, 10)
COR_TEXTO = (236, 240, 241)

# Cores dos Peões: (Cor Base Escura, Cor Brilho Clara)
# Índices: 0=Vermelho, 1=Azul, 2=Verde, 3=Amarelo
CORES_PEOES = [
    ((200, 40, 40), (255, 100, 100)),
    ((40, 100, 200), (100, 160, 255)), 
    ((40, 180, 80), (100, 240, 140)),
    ((220, 180, 20), (255, 230, 100))
]

# Responsável pela interface gráfica do cliente Quoridor
# incluindo conexão com o servidor, entrada do nome do jogador, desenho do tabuleiro e peões, e tratamento de eventos de clique.
class ClienteQuoridor:
    def __init__(self):
        root = tk.Tk()
        root.withdraw()

        # Solicita a URI do servidor e cria o proxy Pyro
        while True:
            # Solicita a URI do servidor ao usuário
            uri = simpledialog.askstring("Conexão", "URI do Servidor (ex: PYRO:...):", parent=root)
            if not uri: sys.exit() # Sai se o usuário cancelar
            # Limpa a URI de espaços e quebras de linha
            self.uri = uri.strip().replace("\n", "").replace("\r", "").replace(" ", "")
            try:
                # Cria o proxy Pyro e tenta se conectar ao servidor
                self.proxy = Pyro5.api.Proxy(self.uri)
                self.proxy._pyroBind() 
                break
            except Exception as e:
                messagebox.showerror("Erro de Rede", f"URI inválida ou Servidor offline.\n{e}", parent=root)
        # Solicita o nome do jogador e tenta entrar no jogo
        while True:
            # Solicita o nome do jogador ao usuário
            self.nome = simpledialog.askstring("Identificação", "Seu Nome:", parent=root)
            # Sai se o usuário cancelar ou não digitar nada
            if not self.nome: sys.exit()
            # Limpa o nome de espaços e quebras de linha
            self.nome = self.nome.strip()
            if self.nome: break
        
        try:
            # Tenta entrar no jogo com o nome fornecido
            msg = self.proxy.entrar(self.nome)
            if "Erro" in msg:
                messagebox.showerror("Acesso Negado", msg, parent=root)
                sys.exit()
        except Exception as e:
            messagebox.showerror("Falha Crítica", f"Falha ao conectar: {e}", parent=root)
            sys.exit()
            
        root.destroy() 

        # Inicializa o Pygame e configura a janela do jogo
        pygame.init()
        pygame.display.set_caption(f"Quoridor Distribuído - {self.nome}")
        
        self.largura = 620
        self.altura = 700
        self.tela = pygame.display.set_mode((self.largura, self.altura))
        self.clock = pygame.time.Clock()
        self.fonte_status = pygame.font.SysFont("Trebuchet MS", 26, bold=True)
        self.fonte_pequena = pygame.font.SysFont("Trebuchet MS", 16)
        
        self.estado = None
        self.rodando = True
        
        # Inicia a thread de polling para atualizar o estado do jogo
        threading.Thread(target=self.thread_polling, daemon=True).start()
        self.game_loop()

    # Thread de Polling
    # Responsável por atualizar o estado do jogo periodicamente
    def thread_polling(self):
        proxy_background = Pyro5.api.Proxy(self.uri) 
        # Mantém a thread rodando enquanto o cliente estiver ativo
        while self.rodando:
            try:
                # Obtém o estado atual do jogo do servidor
                novo_estado = proxy_background.obter_estado() 
                # Atualiza o estado local do cliente com o estado obtido do servidor
                self.estado = novo_estado
            except Exception:
                pass
            time.sleep(0.5) # Aguarda 0.5 segundos antes de tentar novamente

    # Desenha um peão 3D na tela do jogo
    def desenhar_peao_3d(self, x, y, cor_base, cor_brilho):
        pygame.draw.circle(self.tela, (30, 20, 10), (x + 3, y + 4), 18)
        cor_escura = (max(0, cor_base[0]-60), max(0, cor_base[1]-60), max(0, cor_base[2]-60))
        pygame.draw.circle(self.tela, cor_escura, (x, y), 18)
        pygame.draw.circle(self.tela, cor_base, (x, y), 15)
        pygame.draw.circle(self.tela, cor_brilho, (x - 5, y - 5), 5)

    # Desenha a tela do jogo
    def desenhar_tela(self):
        self.tela.fill(COR_MESA)
        if not self.estado:
            texto = self.fonte_status.render("Sincronizando com o servidor...", True, COR_TEXTO)
            self.tela.blit(texto, (150, 300))
            pygame.display.flip()
            return

        jogadores = self.estado["jogadores"]
        
        # 1. Textos de Status com Cor Dinâmica
        if self.estado["vencedor"]:
            txt = f"VENCEDOR: {self.estado['vencedor'].upper()}!"
            cor_txt = (255, 80, 80)
        elif self.estado["iniciado"]:
            turno_atual = self.estado["turno"]
            txt = f"Turno atual: {turno_atual}"
            idx_turno = jogadores.index(turno_atual)
            cor_txt = CORES_PEOES[idx_turno][1] 
        else:
            qtd = len(jogadores)
            txt = f"Aguardando jogadores... ({qtd}/4)"
            cor_txt = COR_TEXTO

        surface_txt = self.fonte_status.render(txt, True, cor_txt)
        self.tela.blit(surface_txt, (40, 15))
        
        if self.estado["iniciado"]:
            estoque = self.estado["estoque"].get(self.nome, 0)
            txt_estoque = self.fonte_pequena.render(f"Suas paredes restantes: {estoque}", True, (180, 180, 180))
            self.tela.blit(txt_estoque, (40, 48))

            # 2. Legenda de Cores
            for i, jog in enumerate(jogadores):
                cor_base = CORES_PEOES[i][0]
                x_legenda = 40 + (i * 135)
                pygame.draw.circle(self.tela, cor_base, (x_legenda, 80), 8)
                txt_legenda = self.fonte_pequena.render(f"{jog}", True, COR_TEXTO)
                self.tela.blit(txt_legenda, (x_legenda + 15, 71))

        # 3. Base do Tabuleiro 
        offset_x, offset_y = 40, 120 # Deslocado para Y=120 para caber a legenda
        tamanho_casa = 50
        espaco = 10 
        tamanho_total = tamanho_casa + espaco
        largura_tabuleiro = (9 * tamanho_total) - espaco

        # Desenha a borda do tabuleiro com sombra e cor base
        pygame.draw.rect(self.tela, (15, 10, 5), (offset_x-10, offset_y-10, largura_tabuleiro+24, largura_tabuleiro+24), border_radius=8)
        pygame.draw.rect(self.tela, COR_BASE_TABULEIRO, (offset_x-10, offset_y-10, largura_tabuleiro+20, largura_tabuleiro+20), border_radius=8)

        # 4. Fitas de Destino (Destacando onde cada jogador deve chegar)
        if self.estado["iniciado"]:
            if len(jogadores) > 0: # P0: Inicia embaixo, alvo é o TOPO
                pygame.draw.rect(self.tela, CORES_PEOES[0][0], (offset_x, offset_y - 8, largura_tabuleiro, 4))
            if len(jogadores) > 1: # P1: Inicia em cima, alvo é a BASE
                pygame.draw.rect(self.tela, CORES_PEOES[1][0], (offset_x, offset_y + largura_tabuleiro + 4, largura_tabuleiro, 4))
            if len(jogadores) > 2: # P2: Inicia na esquerda, alvo é a DIREITA
                pygame.draw.rect(self.tela, CORES_PEOES[2][0], (offset_x + largura_tabuleiro + 4, offset_y, 4, largura_tabuleiro))
            if len(jogadores) > 3: # P3: Inicia na direita, alvo é a ESQUERDA
                pygame.draw.rect(self.tela, CORES_PEOES[3][0], (offset_x - 8, offset_y, 4, largura_tabuleiro))

        # 5. Desenhar Casas 
        for r in range(9):
            for c in range(9):
                x = offset_x + c * tamanho_total
                y = offset_y + r * tamanho_total
                pygame.draw.rect(self.tela, COR_CASA_SOMBRA, (x, y+3, tamanho_casa, tamanho_casa), border_radius=4)
                pygame.draw.rect(self.tela, COR_CASA, (x, y, tamanho_casa, tamanho_casa), border_radius=4)

        # 6. Desenhar Paredes Colocadas
        for (r, c) in self.estado["paredes_h"]:
            x = offset_x + c * tamanho_total
            y = offset_y + r * tamanho_total + tamanho_casa
            pygame.draw.rect(self.tela, COR_PAREDE_BORDA, (x-2, y-2, tamanho_casa * 2 + espaco + 4, espaco + 4), border_radius=2)
            pygame.draw.rect(self.tela, COR_PAREDE, (x, y, tamanho_casa * 2 + espaco, espaco), border_radius=2)

        for (r, c) in self.estado["paredes_v"]:
            x = offset_x + c * tamanho_total + tamanho_casa
            y = offset_y + r * tamanho_total
            pygame.draw.rect(self.tela, COR_PAREDE_BORDA, (x-2, y-2, espaco + 4, tamanho_casa * 2 + espaco + 4), border_radius=2)
            pygame.draw.rect(self.tela, COR_PAREDE, (x, y, espaco, tamanho_casa * 2 + espaco), border_radius=2)

        # 7. Desenhar Peões 
        for i, jog in enumerate(jogadores):
            r, c = self.estado["posicoes"][jog]
            x = offset_x + c * tamanho_total + (tamanho_casa // 2)
            y = offset_y + r * tamanho_total + (tamanho_casa // 2)
            cor_base, cor_brilho = CORES_PEOES[i]
            self.desenhar_peao_3d(x, y, cor_base, cor_brilho)

        pygame.display.flip()

    # Trata o clique do mouse na tela do jogo
    def tratar_clique(self, pos):
        if not self.estado or not self.estado["iniciado"]: return
        if self.estado["turno"] != self.nome: return

        x, y = pos
        offset_x, offset_y = 40, 120 # Atualizado para 120
        tamanho_total = 60 

        x_rel = x - offset_x
        y_rel = y - offset_y

        # Verifica se o clique está fora do tabuleiro
        if x_rel < 0 or y_rel < 0 or x_rel > 540 or y_rel > 540:
            return 

        # Calcula a linha e coluna relativas ao tabuleiro
        c, c_resto = divmod(x_rel, tamanho_total)
        r, r_resto = divmod(y_rel, tamanho_total)

        # Determina se o clique é para mover o peão ou colocar uma parede
        if c_resto < 45 and r_resto < 45:
            self.proxy.mover(self.nome, r, c)
        else:
            if c_resto >= 45 and r < 8: 
                self.proxy.colocar_parede(self.nome, 'V', r, c)
            elif r_resto >= 45 and c < 8: 
                self.proxy.colocar_parede(self.nome, 'H', r, c)

    # Loop principal do jogo
    # Responsável por processar eventos e atualizar a tela
    def game_loop(self):
        while self.rodando:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.rodando = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1: 
                        self.tratar_clique(event.pos)
            
            self.desenhar_tela()
            self.clock.tick(30) 
            
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    Pyro5.config.SERIALIZER = "marshal"
    app = ClienteQuoridor()
