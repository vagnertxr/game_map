# Slippi Ranked South America Map

Este projeto apresenta um mapa interativo dos jogadores de **Super Smash Bros. Melee** na América do Sul, utilizando dados coletados por meio de técnicas de web scraping

## 🗺️ Descrição

- **Coleta de Dados**: Utiliza Python para realizar scraping em um ranking online de jogadores disponível em [Slippi SA Leaderboard](https://caioicy.github.io/slsa/leaderboards/)
- **Armazenamento e Processamento**: Os dados coletados são processados e armazenados em um banco de dados **PostgreSQL com PostGIS**
- **Publicação de Dados Geoespaciais**: Os dados são disponibilizados em formato GeoJSON para consumo pela aplicação utilizando o **GeoServer**
- **Visualização Interativa**: O mapa é construído com a biblioteca JavaScript **MapLibre GL**, permitindo navegação fluida e exibição dos dados em tempo real

## 🚀 Tecnologias Utilizadas

- **Python**: Coleta e processamento de dados
- **PostgreSQL + PostGIS**: Banco de dados espacial
- **GeoServer**: Publicação de dados geoespaciais
- **MapLibre GL**: Visualização dos dados em mapa interativo

## 🖼️ Visualização

Você pode acessar o mapa interativo no seguinte link: [Slippi SA Ranked Map](https://vagnertxr.github.io/game_map/).
