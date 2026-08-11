#!/bin/bash
# Bundla a stack pesada (GSAP+ScrollTrigger em cena, Three.js em campo).
#
# Roda À MÃO quando src/*.js muda. Não é build de deploy: a saída é versionada no
# nome, servida estática e cacheada pra sempre — os sites gerados só apontam pra ela.
# Um bundle por lib, de propósito: quem tem cena e não tem campo não baixa Three.
set -e
SAIDA="${1:-/var/www/sites/_lib}"
cd "$(dirname "$0")"
mkdir -p "$SAIDA"

for m in cena campo; do
  ./node_modules/.bin/esbuild "src/$m.js" --bundle --format=esm --minify \
    --target=es2020 --outfile="$SAIDA/$m-v1.js" --log-level=warning
done

cd "$SAIDA"
for f in cena-v1.js campo-v1.js; do
  printf "%-14s %7.1f KB bruto  %6.1f KB gzip\n" "$f" \
    "$(stat -c%s "$f" | awk '{print $1/1024}')" \
    "$(gzip -9c "$f" | wc -c | awk '{print $1/1024}')"
done
