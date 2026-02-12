#!/bin/bash
# Navega até a pasta do projeto
cd /home/vagner/game_map

# 1. Atualiza o código do repositório (Pull)
git pull origin main

# 2. Executa o script de raspagem e processamento
/home/vagner/game_map/venv/bin/python /home/vagner/game_map/data_scraping.py

# 3. Adiciona os arquivos gerados (GeoJSONs e data.txt)
git add docs/

# 4. Faz o commit com a data e hora atual
git commit -m "Auto-update: $(date +'%Y-%m-%d %H:%M')"

# 5. Envia para o GitHub (Push)
git push origin main
