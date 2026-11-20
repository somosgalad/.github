"""Cena 3D do símbolo da Galad para a abertura do README (estilo página de produto).

O símbolo vem do SVG da identidade (os caminhos são polígonos), vira peça de metal
com espessura e chanfro, e balança devagar sob uma luz de estúdio que dá a volta nele.
A luz que passa é a ideia do nome (Galad = luz), agora como luz de verdade.

Rodar (um Blender por vez no Mac de 8 GB), de dentro de render/:
  lockf /tmp/blender.lock /Applications/Blender.app/Contents/MacOS/Blender -b -P abertura.py -- [teste]
"teste" renderiza só um quadro; sem ele, a animação inteira vai para quadros-abertura/.
Depois: zsh montar.sh abertura
"""
import math
import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))   # o Blender não procura módulos na pasta do script
import estudio as e  # noqa: E402

SVG = AQUI.parent.parent / "marca-galad" / "identidade" / "svg" / "galad-simbolo-bruma.svg"
QUADROS = 96          # 4 s a 24 qps, em loop perfeito
ESCALA = 0.03         # 108 unidades do desenho viram ~3,2 m

cena = e.cena_limpa(QUADROS)

# ── O símbolo ──
caminhos = re.findall(r' d="([^"]+)"', SVG.read_text())
prata = e.material("prata escovada", "#B9C2D4", 0.30, anisotropia=0.6)
latao = e.material("latão polido", "#C2A66B", 0.14)
eixo = e.bpy.data.objects.new("símbolo", None)        # gira tudo junto
cena.collection.objects.link(eixo)
for i, d in enumerate(caminhos):
    estrela = i == len(caminhos) - 1
    obj = e.peca("estrela" if estrela else f"lua {i + 1}", e.pontos_svg(d),
                 0.34 if estrela else 0.22, latao if estrela else prata, ESCALA, (60, 60),
                 z0=0.04 if estrela else 0.0)       # a estrela sai um pouco para a frente
    obj.parent = eixo
eixo.location = (0, 0, 1.75)

# Em pé, de frente para a câmera, num balanço lento de um lado para o outro
# (seno com chave em todo quadro: o 96 encaixa no 1, sem tranco no fim do loop)
for f in range(1, QUADROS + 1):
    ang = math.radians(16) * math.sin(2 * math.pi * (f - 1) / QUADROS)
    eixo.rotation_euler = (math.radians(90), 0, ang)
    eixo.keyframe_insert("rotation_euler", frame=f)

e.chao("#0B1228")
e.fundo(cena, "#070B18")   # azul-noite quase preto

# A luz principal dá uma volta completa na frente e em cima do símbolo (loop perfeito):
# quando passa pela frente, acende o metal; quando vai para trás, vira luz de contorno.
chave = e.luz(cena, "luz que passa", 900, 1.6, "#FFF6E8", (0, -5, 4), eixo)
for f in range(1, QUADROS + 1):
    a = 2 * math.pi * (f - 1) / QUADROS
    chave.location = (5.5 * math.sin(a), -5.5 * math.cos(a), 3.4 + 0.8 * math.cos(a))
    chave.keyframe_insert("location", frame=f)
e.luz(cena, "contorno esquerdo", 260, 3, "#9FB2FF", (-4.5, 3.5, 3.2), eixo)
e.luz(cena, "contorno direito", 200, 3, "#9FB2FF", (4.5, 3.5, 2.6), eixo)
e.luz(cena, "preenchimento", 40, 6, "#C9D3FF", (0, -7, 1.2), eixo)
# Luz pequena e quente só para o latão da estrela brilhar
e.luz(cena, "brilho da estrela", 120, 0.5, "#FFE2B0", (0.8, -3.2, 2.6), eixo)

# Câmera: símbolo embaixo, céu livre em cima para o nome
e.camera(cena, (0, -13, 2.4), 90.6)
e.renderizar(cena, AQUI / "quadros-abertura", quadro_teste=13)
