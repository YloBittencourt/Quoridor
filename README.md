# Quoridor Distribuído - Sistemas Distribuídos (RMI)

Projeto prático da disciplina de Sistemas Distribuídos do curso de Ciência da Computação (UESC). Trata-se de uma versão distribuída do jogo de tabuleiro Quoridor para 4 jogadores, com comunicação via Invocação de Métodos Remotos (RMI).

## 🏛️ Arquitetura do Sistema

O projeto adota uma arquitetura rigorosa de três camadas, promovendo alta coesão e baixo acoplamento:

1. **O Domínio (`logica.py`):** Motor de regras isolado. Valida colisões, calcula a mecânica de saltos sobre oponentes e executa o algoritmo de Busca em Largura (BFS) para garantir a regra anti-aprisionamento do Quoridor.

2. **O Middleware (`servidor.py`):** Servidor centralizado com estado (*Stateful*). Expõe os métodos da lógica para a rede utilizando o framework **Pyro5** (Python Remote Objects). Garante **Exclusão Mútua** no acesso à memória compartilhada utilizando `threading.Lock`, protegendo as matrizes contra acessos paralelos das *threads* operárias do servidor.

3. **A Visão (`cliente.py`):** Processo cliente contendo uma arquitetura Multithread. A *Main Thread* executa o *Game Loop* do Pygame a 30 FPS. Paralelamente, uma *Worker Thread* realiza o *polling* síncrono com o servidor RMI. O uso do bloco `try/except` na thread de rede provê **Transparência de Falha**, impedindo que a interface gráfica congele em caso de queda do servidor.

## 📋 Checklist de Requisitos da Disciplina

Este projeto atende integralmente às especificações do trabalho prático e aborda os pilares teóricos da disciplina:

- [x] **Invocação de Métodos Remotos (RMI):** Utilização do framework Pyro5, substituindo Sockets brutos para abstrair a comunicação de rede (Transparência de Acesso).

- [x] **Arquitetura Multithread:** Cliente projetado com divisão de tarefas — a interface visual (Pygame) opera na *Main Thread*, enquanto uma *Worker Thread* realiza o *polling* síncrono com o servidor, prevenindo o congelamento da tela.

- [x] **Servidor com Estado (*Stateful*):** O motor lógico centralizado retém o histórico das partidas (posições, estoques de paredes e turnos) para processar o algoritmo BFS (Busca em Largura) que impede o aprisionamento de jogadores.

- [x] **Sincronização e Exclusão Mútua:** O middleware Pyro5 despacha requisições em paralelo. O acesso às variáveis globais do servidor é protegido por `threading.Lock()`, evitando a corrupção do estado do jogo por condições de corrida.

- [x] **Transparência de Falhas:** Blocos de proteção (`try/except`) na thread de rede do cliente garantem que indisponibilidades do servidor não resultem em "crashes" imediatos da aplicação local.

## 🚀 Requisitos e Execução

Certifique-se de estar utilizando Python 3.10+ e possuir as bibliotecas necessárias instaladas no seu ambiente virtual:

```bash
pip install Pyro5 pygame
```

## Passo a Passo para jogar
1. Iniciando o Servidor:
Abra um terminal e inicie o processo servidor. Ele imprimirá uma URI na tela.
```bash
python3 servidor.py
```
Copie a URI gerada (Ex: PYRO:obj_...)

2. Iniciando os Clientes:
Abra 4 terminais independentes (podem ser na mesma máquina). Em cada um deles, execute:

```bash 
python3 cliente.py
```

3. Conexão:
- Cole a URI do servidor na caixa de diálogo de cada cliente.

- Digite um nome único para cada jogador.

- O tabuleiro será renderizado no Pygame assim que o 4º jogador conectar.

## 🎮 Mecânica de Jogo
- Objetivo: Ser o primeiro a levar seu peão até a fita colorida no lado oposto do tabuleiro.

- Movimentação: Clique no centro da casa alvo. O sistema permite pulos retos e diagonais sobre oponentes conforme as regras oficiais.

- Paredes: Clique nas ranhuras entre as casas (beiradas) para posicionar paredes horizontais ou verticais. Cada jogador possui um estoque de 5 paredes.