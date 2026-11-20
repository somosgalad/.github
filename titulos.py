#!/usr/bin/env python3
"""Gera os títulos em pixel art do README da Galad (profile/imagens/titulo-*.svg).

A ideia é o farol da marca em miniatura: o título fica apagado no escuro, uma estrelinha de
latão acende à esquerda e o feixe dela passa por cima das letras, acendendo uma por uma.
Depois de um tempo apaga e recomeça (a seção fica lá embaixo: uma passada só ninguém veria).

Por que SVG com CSS: o README do GitHub não roda JavaScript nem carrega fonte de fora. Então a
fonte é desenhada aqui com quadradinhos e o movimento é só opacidade, em degraus (steps), como
animação de jogo antigo. A fonte pixel é a mesma do perfil da Nicolly
(~/Documents/namtech-publico/hipnostech/gerar.py), copiada para não depender de outro repositório.

Uso:  python3 titulos.py     (depois: commit + push)
"""
import unicodedata
from html import escape
from pathlib import Path

SAIDA = Path(__file__).parent / "profile" / "imagens"

# Cores da identidade da Galad
NOITE, APAGADO, BRUMA, LATAO, BRASA = "#101B3A", "#2E3A60", "#E8ECF2", "#C2A66B", "#FFE7B0"

LARGURA, ALTURA = 880, 56
PX = 4            # tamanho de um pixel da fonte, em unidades do SVG
X_TEXTO = 64      # onde a primeira letra começa (antes dela fica a estrela)
CICLO = 9         # segundos de uma volta inteira: passada do feixe, tempo aceso, apagar
VELOCIDADE = 420  # quantas unidades do SVG o feixe anda por segundo
INICIO = 0.5      # a estrela acende antes; o feixe sai depois

# Fonte pixel de 5 linhas (largura variável). "#" é pixel aceso.
LETRAS = {
    "A": ".#./#.#/###/#.#/#.#", "B": "##./#.#/##./#.#/##.", "C": ".##/#../#../#../.##",
    "D": "##./#.#/#.#/#.#/##.", "E": "###/#../##./#../###", "F": "###/#../##./#../#..",
    "G": ".##/#../#.#/#.#/.##", "H": "#.#/#.#/###/#.#/#.#", "I": "###/.#./.#./.#./###",
    "J": "..#/..#/..#/#.#/.#.", "K": "#.#/#.#/##./#.#/#.#", "L": "#../#../#../#../###",
    "M": "#...#/##.##/#.#.#/#...#/#...#", "N": "#..#/##.#/#.##/#..#/#..#",
    "O": ".#./#.#/#.#/#.#/.#.", "P": "##./#.#/##./#../#..", "Q": ".#./#.#/#.#/###/.##",
    "R": "##./#.#/##./#.#/#.#", "S": ".##/#../.#./..#/##.", "T": "###/.#./.#./.#./.#.",
    "U": "#.#/#.#/#.#/#.#/###", "V": "#.#/#.#/#.#/#.#/.#.", "W": "#...#/#...#/#.#.#/##.##/#...#",
    "X": "#.#/#.#/.#./#.#/#.#", "Y": "#.#/#.#/.#./.#./.#.", "Z": "###/..#/.#./#../###",
    "0": "###/#.#/#.#/#.#/###", "1": ".#./##./.#./.#./###", "2": "##./..#/.#./#../###",
    "3": "##./..#/.#./..#/##.", "4": "#.#/#.#/###/..#/..#", "5": "###/#../##./..#/##.",
    "6": ".##/#../###/#.#/###", "7": "###/..#/.#./.#./.#.", "8": "###/#.#/###/#.#/###",
    "9": "###/#.#/###/..#/##.", " ": "../../../../..", ",": "../../../.#/#.", ".": "././././#",
    "-": ".../.../###/.../...",
}
# Acentos ficam acima da letra (NFD separa "É" em "E" + acento)
ACENTOS = {"́": "..#/.#.", "̂": ".#./#.#"}   # agudo e circunflexo

# Estrela de 4 pontas da Galad, em pixel ("o" = miolo mais claro)
ESTRELA = ["...#...", "...#...", "..###..", "###o###", "..###..", "...#...", "...#..."]


def quadrados(pontos, lado=PX):
    """Uma lista de cantos (x, y) vira um caminho SVG de quadrados de `lado`."""
    return "".join(f"M{x},{y}h{lado}v{lado}h-{lado}z" for x, y in pontos)


def letras_em_pixels(frase):
    """Devolve, para cada letra, a lista de pixels acesos (em unidades da fonte) e a largura total."""
    letras, cursor, largura_anterior = [], 0, 0
    for sinal in unicodedata.normalize("NFD", frase.upper()):
        if sinal in ACENTOS:   # o acento não abre letra nova: entra na anterior
            linhas, topo, esquerda = ACENTOS[sinal].split("/"), -3, cursor - largura_anterior - 1
        else:
            linhas, topo, esquerda = LETRAS[sinal].split("/"), 0, cursor
            largura_anterior = len(linhas[0])
            cursor += largura_anterior + 1
            letras.append([])
        for j, linha in enumerate(linhas):
            letras[-1] += [(esquerda + i, topo + j) for i, p in enumerate(linha) if p == "#"]
    return letras, cursor - 1


def atraso(x):
    """Em que segundo o feixe passa pelo ponto x (é isso que sincroniza letra e feixe).
    Velocidade fixa: título curto acende rápido, título longo leva um pouco mais."""
    return INICIO + (x - X_TEXTO) / VELOCIDADE


def titulo(frase):
    letras, largura = letras_em_pixels(frase)
    y0 = (ALTURA - 5 * PX) // 2 + PX // 2   # texto centrado na altura (com espaço pro acento)
    fim = X_TEXTO + largura * PX + 3 * PX   # o feixe passa um pouco da última letra e some

    # Três camadas por letra: a apagada (sempre lá, para o título nunca sumir), a faísca de
    # latão (o instante em que a luz bate) e a acesa, que fica até o fim do ciclo.
    apagado, faiscas, acesas, regras = [], [], [], []
    for n, pixels in enumerate(p for p in letras if p):
        cantos = [(X_TEXTO + i * PX, y0 + j * PX) for i, j in pixels]
        caminho = quadrados(cantos)
        apagado.append(caminho)
        faiscas.append(f'<path class="faisca l{n}" fill="{LATAO}" d="{caminho}"/>')
        acesas.append(f'<path class="acesa l{n}" fill="{BRUMA}" d="{caminho}"/>')
        # O atraso vai numa regra de CSS por letra (.l0, .l1...) em vez de style="" no elemento:
        # fica tudo no <style> e o SVG continua simples de ler.
        regras.append(f".l{n}{{animation-delay:{atraso(min(x for x, _ in cantos)):.2f}s}}")

    # O feixe: uma barrinha de latão com um rastro mais fraco atrás. Anda em degraus de 2
    # pixels (steps) para parecer jogo antigo, e só aparece durante a passada.
    altura_feixe = 9 * PX
    topo = (ALTURA - altura_feixe) // 2
    barra = quadrados([(0, topo + k * PX) for k in range(9)])
    rastro = quadrados([(-dx, topo + k * PX) for k in range(1, 8) for dx in (PX, 2 * PX)])
    viagem = fim - X_TEXTO
    t_viagem = viagem / VELOCIDADE
    passo = 2 * PX
    p_ini = INICIO / CICLO * 100                    # % do ciclo em que o feixe sai
    p_fim = (INICIO + t_viagem) / CICLO * 100       # % em que ele chega no fim e some

    # A estrela, à esquerda, centrada na altura
    ex, ey = 18, ALTURA // 2 - 3 * PX
    raios = [(ex + i * PX, ey + j * PX) for j, l in enumerate(ESTRELA) for i, c in enumerate(l) if c == "#"]
    miolo = [(ex + i * PX, ey + j * PX) for j, l in enumerate(ESTRELA) for i, c in enumerate(l) if c == "o"]

    estilo = f"""
.faisca,.acesa{{opacity:0;animation:{CICLO}s steps(1,end) infinite}}
.faisca{{animation-name:faisca}}
.acesa{{animation-name:acende}}
@keyframes faisca{{0%{{opacity:1}}3%,100%{{opacity:0}}}}
@keyframes acende{{0%{{opacity:0}}3%,80%{{opacity:1}}81%,100%{{opacity:0}}}}
{"".join(regras)}
.feixe{{opacity:0;animation:varre {CICLO}s infinite}}
@keyframes varre{{
0%,{p_ini:.2f}%{{opacity:0;transform:translateX({X_TEXTO}px)}}
{p_ini + 0.01:.2f}%{{opacity:1;transform:translateX({X_TEXTO}px);animation-timing-function:steps({max(1, viagem // passo)},end)}}
{p_fim:.2f}%{{opacity:1;transform:translateX({fim}px)}}
{p_fim + 0.01:.2f}%,100%{{opacity:0;transform:translateX({fim}px)}}}}
.brilho{{animation:pisca {CICLO}s steps(1,end) infinite}}
@keyframes pisca{{0%,{p_ini:.0f}%{{opacity:.6}}{p_ini + 0.01:.2f}%,{p_fim + 6:.0f}%{{opacity:1}}{p_fim + 6.01:.2f}%,100%{{opacity:.8}}}}
/* Quem pediu menos movimento vê o título aceso e parado, sem feixe */
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}.feixe,.faisca{{display:none}}.acesa{{opacity:1}}}}"""

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {LARGURA} {ALTURA}" role="img" aria-label="{escape(frase)}" shape-rendering="crispEdges">
<title>{escape(frase)}</title>
<style>{estilo}
</style>
<rect width="{LARGURA}" height="{ALTURA}" fill="{NOITE}"/>
<path fill="{APAGADO}" d="{"".join(apagado)}"/>
{"".join(acesas)}
{"".join(faiscas)}
<g class="feixe"><path fill="{LATAO}" opacity=".35" d="{rastro}"/><path fill="{BRASA}" d="{barra}"/></g>
<g class="brilho"><path fill="{LATAO}" d="{quadrados(raios)}"/><path fill="{BRASA}" d="{quadrados(miolo)}"/></g>
</svg>
"""


# Arquivo → frase. Mudou um título no README? Mude aqui e rode de novo.
TITULOS = {
    "titulo-galad": "Galad",
    "titulo-atalaia": "Atalaia, nosso primeiro produto",
    "titulo-quem-faz": "Quem faz",
}

if __name__ == "__main__":
    for arquivo, frase in TITULOS.items():
        (SAIDA / f"{arquivo}.svg").write_text(titulo(frase))
        print("gerado", arquivo)
