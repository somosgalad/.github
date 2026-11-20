"""Peças de estúdio comuns às cenas 3D do README (abertura da Galad e cartão do Atalaia).

Por que um módulo: as duas cenas usam o mesmo "estúdio" (metal, peça extrudada do SVG,
luz de área mirando o objeto, câmera e render EEVEE). Assim o acabamento fica igual nas
duas e uma correção vale para ambas.
"""
import math
import re
import sys

import bmesh
import bpy


def modo_teste():
    """True quando o Blender foi chamado com "-- teste" (renderiza um quadro só)."""
    return "--" in sys.argv and "teste" in sys.argv[sys.argv.index("--") + 1:]


def cena_limpa(quadros, fps=24):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    # Chaves lineares, para o loop não "frear" no fim (vale para todas as chaves criadas depois)
    bpy.context.preferences.edit.keyframe_new_interpolation_type = "LINEAR"
    cena = bpy.context.scene
    cena.frame_start, cena.frame_end = 1, quadros
    cena.render.fps = fps
    return cena


def cor(hexa):
    """Hex da identidade para cor linear do Blender."""
    def lin(c):
        c /= 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return tuple(lin(int(hexa[i:i + 2], 16)) for i in (1, 3, 5)) + (1.0,)


def material(nome, base, aspereza, metal=1.0, anisotropia=0.0, brilho=None, forca=0.0):
    """Material simples. `brilho` (hex) + `forca` fazem a peça emitir luz própria."""
    m = bpy.data.materials.new(nome)
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = cor(base)
    p.inputs["Metallic"].default_value = metal
    p.inputs["Roughness"].default_value = aspereza
    p.inputs["Anisotropic"].default_value = anisotropia   # metal escovado
    if brilho:
        p.inputs["Emission Color"].default_value = cor(brilho)
        p.inputs["Emission Strength"].default_value = forca
    return m


def pontos_svg(d):
    """Lê um caminho SVG feito só de retas (M, L, l, Z, como os das marcas) e devolve os pontos.
    Aceita coordenadas absolutas e relativas ("l"), que é o que os SVGs otimizados usam."""
    pontos, modo = [], "M"
    for cmd, nums in re.findall(r"([MmLlZz])([^MmLlZz]*)", d):
        valores = list(map(float, re.findall(r"-?\d*\.?\d+", nums)))
        modo = cmd if cmd not in "Zz" else modo
        for x, y in zip(valores[::2], valores[1::2]):
            if modo.islower() and pontos:
                x, y = pontos[-1][0] + x, pontos[-1][1] + y
            pontos.append((x, y))
    if len(pontos) > 1 and pontos[0] == pontos[-1]:
        pontos.pop()
    return pontos


def aspereza_variada(mat, minimo, maximo, escala=6.0, relevo=0.0):
    """Troca a aspereza fixa por uma que varia de leve pela superfície (ruído).
    É o que tira a cara de "plástico de computador": metal e pedra de verdade nunca
    refletem por igual. `relevo` > 0 também dá uma textura mínima ao toque da luz."""
    nos, ligas = mat.node_tree.nodes, mat.node_tree.links
    p = nos["Principled BSDF"]
    ruido = nos.new("ShaderNodeTexNoise")
    ruido.inputs["Scale"].default_value = escala
    ruido.inputs["Detail"].default_value = 8.0
    faixa = nos.new("ShaderNodeMapRange")
    faixa.inputs["To Min"].default_value, faixa.inputs["To Max"].default_value = minimo, maximo
    ligas.new(ruido.outputs["Fac"], faixa.inputs["Value"])
    ligas.new(faixa.outputs["Result"], p.inputs["Roughness"])
    if relevo:
        bump = nos.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = relevo
        fino = nos.new("ShaderNodeTexNoise")
        fino.inputs["Scale"].default_value = escala * 40
        ligas.new(fino.outputs["Fac"], bump.inputs["Height"])
        ligas.new(bump.outputs["Normal"], p.inputs["Normal"])
    return mat


def softbox(cena, nome, local, rotacao_graus, tamanho, forca, cor_hex="#FFFFFF"):
    """Painel de luz que a câmera não vê, mas que aparece refletido no metal.
    É o truque das fotos de produto: o metal só parece metal quando tem algo para refletir."""
    bpy.ops.mesh.primitive_plane_add(size=1, location=local,
                                     rotation=tuple(math.radians(g) for g in rotacao_graus))
    obj = bpy.context.object
    obj.name = nome
    obj.scale = (*tamanho, 1)
    m = material(nome, "#000000", 1.0, metal=0.0, brilho=cor_hex, forca=forca)
    obj.data.materials.append(m)
    obj.visible_camera = False
    obj.visible_shadow = False
    return obj


def peca(nome, pontos, espessura, mat, escala, centro, z0=0.0, chanfro=0.025, suave=False):
    """Um polígono do SVG vira uma peça sólida, com chanfro para pegar brilho na borda.
    `suave`: sombreado liso no chanfro (sem facetas), mantendo as faces planas retas."""
    malha = bpy.data.meshes.new(nome)
    obj = bpy.data.objects.new(nome, malha)
    bpy.context.collection.objects.link(obj)
    bm = bmesh.new()
    cx, cy = centro
    # Centro do desenho na origem; o y do SVG desce, o do Blender sobe
    vs = [bm.verts.new(((x - cx) * escala, -(y - cy) * escala, z0)) for x, y in pontos]
    face = bm.faces.new(vs)
    ext = bmesh.ops.extrude_face_region(bm, geom=[face])
    novos = [g for g in ext["geom"] if isinstance(g, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, verts=novos, vec=(0, 0, espessura))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(malha)
    bm.free()
    obj.data.materials.append(mat)
    mod = obj.modifiers.new("chanfro", "BEVEL")
    mod.width, mod.segments, mod.limit_method = chanfro, 4, "ANGLE"
    if suave:
        malha.shade_smooth()
        mod.segments, mod.harden_normals = 6, True   # chanfro redondo, faces planas sem manchas
    return obj


def fundo(cena, hexa):
    mundo = bpy.data.worlds.new("fundo")
    cena.world = mundo
    mundo.use_nodes = True
    mundo.node_tree.nodes["Background"].inputs["Color"].default_value = cor(hexa)


def chao(hexa, aspereza=0.5):
    """Chão escuro e brilhante, para o reflexo de vitrine."""
    bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, 0))
    obj = bpy.context.object
    obj.data.materials.append(material("chão", hexa, aspereza, metal=0.0))
    return obj


def luz(cena, nome, energia, tamanho, cor_hex, local, alvo, tipo="AREA"):
    """Luz que sempre mira o `alvo` (assim dá para movê-la sem recalcular ângulos)."""
    dados = bpy.data.lights.new(nome, tipo)
    dados.energy, dados.color = energia, cor(cor_hex)[:3]
    if tipo == "AREA":
        dados.size = tamanho
    else:
        dados.shadow_soft_size = tamanho   # raio pequeno = sombra de contorno nítido
    obj = bpy.data.objects.new(nome, dados)
    cena.collection.objects.link(obj)
    obj.location = local
    mira = obj.constraints.new("TRACK_TO")
    mira.target, mira.track_axis, mira.up_axis = alvo, "TRACK_NEGATIVE_Z", "UP_Y"
    return obj


def camera(cena, local, inclinacao_graus, lente=42, foco=None, abertura_f=None):
    """`foco` (objeto) + `abertura_f` ligam a profundidade de campo: o que está fora do
    foco desfoca de leve, como numa lente de verdade."""
    dados = bpy.data.cameras.new("câmera")
    dados.lens = lente
    if foco is not None:
        dados.dof.use_dof = True
        dados.dof.focus_object = foco
        dados.dof.aperture_fstop = abertura_f or 4.0
    obj = bpy.data.objects.new("câmera", dados)
    cena.collection.objects.link(obj)
    cena.camera = obj
    obj.location = local
    obj.rotation_euler = (math.radians(inclinacao_graus), 0, 0)
    return obj


def renderizar(cena, pasta, quadro_teste, cycles=False, largura=1280, amostras=64):
    """Padrão: EEVEE com raytracing, segundos por quadro no M1 (usado na abertura).
    `cycles=True`: render físico pela GPU (Metal) com remoção de ruído; ~30 a 60 s por quadro
    no M1, mas luz, sombra macia e reflexo de verdade. Altura = metade da largura.
    No modo teste, um quadro vai para pasta/../teste-<nome>.png; senão, todos para pasta/q####.png."""
    if cycles:
        cena.render.engine = "CYCLES"
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = "METAL"
        prefs.get_devices()
        for d in prefs.devices:
            d.use = True
        cena.cycles.device = "GPU"
        cena.cycles.samples = amostras
        cena.cycles.use_denoising = True
        cena.cycles.denoiser = "OPENIMAGEDENOISE"
    else:
        cena.render.engine = "BLENDER_EEVEE"
        cena.eevee.use_raytracing = True
        cena.eevee.taa_render_samples = 32
    cena.render.resolution_x, cena.render.resolution_y = largura, largura // 2
    cena.view_settings.view_transform = "AgX"
    cena.view_settings.look = "AgX - Medium High Contrast"
    cena.render.image_settings.file_format = "PNG"
    if modo_teste():
        # "-- teste 60" renderiza o quadro 60; só "-- teste", o quadro padrão da cena
        numeros = [a for a in sys.argv[sys.argv.index("--") + 1:] if a.isdigit()]
        cena.frame_set(int(numeros[0]) if numeros else quadro_teste)
        cena.render.filepath = str(pasta.parent / f"teste-{pasta.name}.png")
        bpy.ops.render.render(write_still=True)
    else:
        cena.render.filepath = str(pasta / "q")
        bpy.ops.render.render(animation=True)
