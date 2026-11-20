"""Cena 3D do cartão do Atalaia no README da Galad (mesmo estúdio da abertura).

A ideia: o símbolo do Atalaia é o ponteiro de um relógio de sol (lâmina azul + sombra
em nanquim). Aqui ele vira peça de metal suspensa sobre um mostrador de pedra, e uma luz
dá a volta: a sombra DE VERDADE gira pelo mostrador como um ponteiro, passando pelas
marcas de hora. Uma das marcas é vermelha: o prazo. Sem texto explicativo; a manchete
vem por cima (texto-atalaia.html) e a imagem conta o resto: o tempo corre, alguém vigia.

Rodar (um Blender por vez no Mac de 8 GB), de dentro de render/:
  lockf /tmp/blender.lock /Applications/Blender.app/Contents/MacOS/Blender -b -P atalaia.py -- [teste]
"teste" renderiza só um quadro; sem ele, a animação inteira vai para quadros-atalaia/.
Depois: zsh montar.sh atalaia
"""
import math
import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))   # o Blender não procura módulos na pasta do script
import estudio as e  # noqa: E402

# O símbolo oficial, o mesmo que o sistema usa (assim o cartão nunca fica diferente da marca)
SVG = AQUI.parent.parent / "atalaia" / "src" / "main" / "resources" / "static" / "logo" / "atalaia-simbolo.svg"
QUADROS = 180         # 6 s a 30 qps: uma volta inteira da luz, em loop perfeito
                      # (com 24 qps e 5 s a sombra dava passos grandes e parecia travar)
ESCALA = 0.05         # 64 unidades do desenho viram ~3,2 m
RAIO = 3.8            # mostrador

# Cores do Atalaia (marca A · Protocolo): azul-carimbo, nanquim e o vermelho de destaque
AZUL, NANQUIM, VERMELHO = "#2438A6", "#141922", "#E0312B"

cena = e.cena_limpa(QUADROS, fps=30)
volta = [2 * math.pi * (f - 1) / QUADROS for f in range(1, QUADROS + 1)]   # 0 → 2π por quadro

# ── O símbolo ──
# Cada peça vem com a cor dela no SVG: a azul é a lâmina, a escura é a sombra
caminhos = re.findall(r'fill="([^"]+)" d="([^"]+)"', SVG.read_text())
# Azul um pouco mais claro que o da marca: metal escuro no estúdio escuro some
lamina = e.aspereza_variada(e.material("azul anodizado", "#3A55D6", 0.26, anisotropia=0.3), 0.18, 0.32)
sombra = e.aspereza_variada(e.material("grafite", "#3B4252", 0.34, anisotropia=0.5), 0.26, 0.42)
eixo = e.bpy.data.objects.new("símbolo", None)
cena.collection.objects.link(eixo)
for preenchimento, d in caminhos:
    azul = preenchimento.lower() == AZUL.lower()
    # A lâmina azul fica um pouco à frente da peça de sombra: dá profundidade ao girar
    obj = e.peca("lâmina" if azul else "sombra", e.pontos_svg(d), 0.30 if azul else 0.22,
                 lamina if azul else sombra, ESCALA, (33, 31), z0=0.06 if azul else 0.0,
                 chanfro=0.035, suave=True)
    obj.parent = eixo

# Suspenso sobre o centro do mostrador, de frente para a câmera.
# Balanço curto e flutuação leve, ambos em seno de uma volta (o quadro 120 encaixa no 1).
for f, a in enumerate(volta, start=1):
    eixo.location = (0, 0, 2.05 + 0.06 * math.sin(a))
    eixo.rotation_euler = (math.radians(90), 0, math.radians(10) * math.sin(a))
    eixo.keyframe_insert("location", frame=f)
    eixo.keyframe_insert("rotation_euler", frame=f)

# ── O mostrador: disco de pedra escura, um pouco mais claro que o chão para a sombra aparecer ──
e.bpy.ops.mesh.primitive_cylinder_add(vertices=128, radius=RAIO, depth=0.30, location=(0, 0, 0.15))
disco = e.bpy.context.object
# Pedra polida de leve: aspereza irregular e um grão fino, como basalto de bancada
disco.data.materials.append(e.aspereza_variada(e.material("pedra", "#1C2232", 0.55, metal=0.0),
                                               0.38, 0.66, escala=3.0, relevo=0.12))
disco.data.shade_smooth()
borda = disco.modifiers.new("chanfro", "BEVEL")
borda.width, borda.segments, borda.harden_normals = 0.035, 5, True   # a borda pega um fio de luz

# Aro de aço escovado em volta: dá corpo ao disco (fino demais, ele parecia um adesivo)
e.bpy.ops.mesh.primitive_cylinder_add(vertices=128, radius=RAIO + 0.09, depth=0.24, location=(0, 0, 0.12))
aro = e.bpy.context.object
aro.data.materials.append(e.aspereza_variada(e.material("aço do aro", "#AEB6C6", 0.3, anisotropia=0.8), 0.2, 0.36))
aro.data.shade_smooth()
aro_borda = aro.modifiers.new("chanfro", "BEVEL")
aro_borda.width, aro_borda.segments, aro_borda.harden_normals = 0.03, 5, True

# Marcas de hora: 24, as de 3 em 3 horas mais longas. A marca do prazo é vermelha e acesa.
metal_claro = e.material("aço claro", "#C9CFDA", 0.28)
prazo = e.material("prazo", VERMELHO, 0.4, metal=0.0, brilho=VERMELHO, forca=7.0)
MARCA_PRAZO = 4             # à direita da frente: a sombra passa por ela no meio do loop
for i in range(24):
    ang = 2 * math.pi * i / 24
    longa = i % 3 == 0 or i == MARCA_PRAZO   # o prazo também é marca longa, para aparecer
    comp = 0.55 if longa else 0.28
    r = RAIO - 0.18 - comp / 2
    e.bpy.ops.mesh.primitive_cube_add(size=1, location=(r * math.sin(ang), -r * math.cos(ang), 0.31))
    marca = e.bpy.context.object
    marca.scale = (0.05 if longa else 0.03, comp, 0.03)
    marca.rotation_euler = (0, 0, -ang)
    marca.data.materials.append(prazo if i == MARCA_PRAZO else metal_claro)
    canto = marca.modifiers.new("chanfro", "BEVEL")
    canto.width, canto.segments = 0.008, 2
    if i == MARCA_PRAZO:
        # A marca acesa ilumina de verdade a pedra em volta (mais crível que um brilho pintado)
        brasa = e.bpy.data.lights.new("luz do prazo", "POINT")
        brasa.energy, brasa.color, brasa.shadow_soft_size = 6, e.cor(VERMELHO)[:3], 0.2
        luz_prazo = e.bpy.data.objects.new("luz do prazo", brasa)
        cena.collection.objects.link(luz_prazo)
        luz_prazo.location = (r * math.sin(ang), -r * math.cos(ang), 0.48)

# Chão preto brilhante de vitrine: reflete o mostrador em vez de virar uma mancha azul
e.chao("#030408", aspereza=0.24)
e.fundo(cena, "#06090F")

# ── A luz que dá a volta: um refletor alto, de contorno nítido, como sol de meio da tarde ──
# (mais baixo, a sombra ficava comprida demais e saía do mostrador)
# A sombra do símbolo cai no mostrador e gira com ela, fazendo papel de ponteiro.
sol = e.luz(cena, "sol", 3200, 0.15, "#FFF3E2", (0, -4.6, 6.4), eixo, tipo="SPOT")
sol.data.spot_size, sol.data.spot_blend = math.radians(46), 0.3
alvo_sol = e.bpy.data.objects.new("centro do mostrador", None)   # mira o disco, não o símbolo
cena.collection.objects.link(alvo_sol)
sol.constraints["Track To"].target = alvo_sol
for f, a in enumerate(volta, start=1):
    sol.location = (4.6 * math.sin(a), -4.6 * math.cos(a), 6.4)
    sol.keyframe_insert("location", frame=f)

# Contornos frios fixos, para o metal nunca sumir quando o sol vai para trás
e.luz(cena, "contorno esquerdo", 220, 1.5, "#B8C6FF", (-4.5, 3.5, 3.6), eixo)
e.luz(cena, "contorno direito", 180, 1.5, "#B8C6FF", (4.5, 3.5, 3.0), eixo)
# Luz de frente fixa: a lâmina azul continua visível quando o sol está atrás
e.luz(cena, "frente", 650, 4, "#DCE3FF", (1.5, -7, 3.2), eixo)

# Painéis que só aparecem refletidos: dão ao metal os degradês de foto de produto
e.softbox(cena, "painel de cima", (0, 3, 6.5), (150, 0, 0), (7, 1.4), 5)
e.softbox(cena, "painel esquerdo", (-6, 1, 4.2), (0, 90, 0), (1.2, 5), 3, "#C9D6FF")
e.softbox(cena, "painel direito", (6, 1, 4.2), (0, -90, 0), (0.8, 5), 2, "#C9D6FF")

# Câmera um pouco acima, olhando de leve para baixo: o mostrador vira elipse e mostra a sombra.
# O conjunto fica na metade de baixo; a de cima é da manchete.
# Foco no símbolo; a borda do mostrador desfoca de leve, como numa lente de verdade.
e.camera(cena, (0, -18.5, 6.8), 76.5, lente=44, foco=eixo, abertura_f=0.8)
# Cycles (render físico) em 1600 px: o EEVEE em 1280 px saía com cara de plástico e pixelado
e.renderizar(cena, AQUI / "quadros-atalaia", quadro_teste=1, cycles=True, largura=1600, amostras=40)   # 40 + remoção de ruído: ~35 s/quadro
