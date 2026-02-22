## Slippi Ranked South America Map

Este projeto consiste em um mapa interativo dos jogadores de **[Slippi Netplay](https://slippi.gg)** na América do Sul, utilizando dados coletados por meio de técnicas de web scraping e processados em um sistema de banco de dados espaciais.

### Funcionamento e Arquitetura

O projeto é estruturado em um pipeline de dados (ETL) automatizado:

- **Coleta de Dados**: Utiliza Python para realizar scraping em um ranking online de jogadores disponível em [Slippi SA Leaderboard](https://caioicy.github.io/slsa/leaderboards/)
- **Armazenamento e Processamento**: Os dados coletados são processados e armazenados em um banco de dados **PostgreSQL com PostGIS**
- **Publicação de Dados Geoespaciais**: Os dados são disponibilizados em formato GeoJSON para consumo pela aplicação utilizando o **GeoServer**
- **Visualização Interativa**: O mapa é construído com a biblioteca JavaScript **MapLibre GL**, permitindo navegação fluida e exibição dos dados em tempo real 

### Automação
A rotina de atualização dos dados é executada semanalmente em um servidor local Linux.

**Fluxo de execução**:
- Sincronização semanal do repositório via rotina agendada
- Execução do script Python
- Atualização das tabelas espaciais no banco de dados local e sua disponibilização em camada no GeoServer
- Exportação dos arquivos GeoJSON atualizados localmente
- Deploy automático dos novos dados para o GitHub Pages

### Tecnologias Utilizadas

**Python**: Coleta e processamento de dados

**PostgreSQL + PostGIS**: Banco de dados espacial

**GeoServer**: Publicação de dados geoespaciais

**MapLibre GL**: Visualização dos dados em mapa interativo

O mapa interativo pode ser visualizado em: [vagnertxr.github.io/game_map/](https://vagnertxr.github.io/game_map/).
