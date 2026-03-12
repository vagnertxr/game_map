## Slippi Ranked South America Map 🐸

This project consists of an interactive map of **[Slippi Netplay](https://slippi.gg)** players in South America, using data collected through web scraping techniques and processed in a spatial database system.

The interactive map can be viewed at: [vagnertxr.github.io/game_map/](https://vagnertxr.github.io/game_map/).

### Functioning and Architecture

The project is structured as an automated data pipeline (ETL):

- **Data Collection**: Uses Python to scrape an online player ranking available at [Slippi SA Leaderboard](https://caioicy.github.io/slsa/leaderboards/)
- **Storage and Processing**: Collected data is processed and stored in a **PostgreSQL + PostGIS** database
- **Geospatial Data Publishing**: Data is made available in GeoJSON format for application consumption using **GeoServer**
- **Interactive Visualization**: The map is built with the **MapLibre GL** JavaScript library, allowing fluid navigation and real-time data display

### Automation
The data update routine is executed weekly on a local Linux server.

**Execution flow**:
- Weekly repository synchronization via scheduled routine
- Data scraping, processing and merging
- Update of spatial tables in the local database and its deployment as a layer in GeoServer
- Export of updated GeoJSON files locally
- Automatic deploy of new data to GitHub Pages

### Technologies Used

**Python**: Data collection and processing

**PostgreSQL + PostGIS**: Spatial database

**GeoServer**: Geospatial data publishing

**MapLibre GL**: Interactive map data visualization
