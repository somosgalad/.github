#!/bin/zsh
# Junta os quadros do Blender com a camada de texto num WebP animado.
# Uso: zsh montar.sh abertura   (ou: zsh montar.sh atalaia)
#   quadros-<cena>/q*.png  +  texto-<cena>.png  →  ../profile/imagens/<cena>.webp
# Por que WebP: o GitHub mostra no README, faz loop e fica bem menor que GIF (sem faixas no degradê).
# Antes: o Blender (<cena>.py) e o texto-<cena>.png (texto-<cena>.html, print pelo Edge com fundo transparente;
# o texto precisa ter a mesma largura dos quadros).
cd "$(dirname "$0")"
cena=${1:?diga a cena: abertura ou atalaia}
# Cada cena tem o seu ritmo e acabamento. O Atalaia saiu de 24 para 30 qps (a sombra dava passos
# e parecia travar) e de qualidade 72 para 88 (o degradê escuro abria em blocos, cara de pixel).
case $cena in
  atalaia) qps=30; qualidade=88 ;;
  *)       qps=24; qualidade=72 ;;
esac
ffmpeg -loglevel error -y -framerate $qps -pattern_type glob -i "quadros-$cena/q*.png" -i "texto-$cena.png" \
  -filter_complex "[0][1]overlay,format=yuva420p" -c:v libwebp_anim -loop 0 -quality $qualidade \
  -compression_level 6 "../profile/imagens/$cena.webp"
