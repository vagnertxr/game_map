# Slippi Ranked SA Map - Script para Data Scraping
# Busca e processa os dados de jogadores do site SLSA Leaderboards
# extrai códigos de país e códigos Slippi Connect, e popula um banco de dados PostgreSQL + PostGIS
#
# por Vagner Teixeira
# vagnertxr.github.io
# 2024 


# importando todas as bibliotecas necessárias
import pandas as pd
import psycopg2
import re
import os
import requests
import json
from dotenv import load_dotenv
from io import StringIO
from bs4 import BeautifulSoup
from datetime import datetime
print("Bibliotecas importadas com sucesso!")

# ... rest of the imports ...

# direcionando o diretório base
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
output_path = os.path.join(BASE_DIR, 'docs', 'data.geojson')

# conectando ao site e lendo o html
url = "https://caioicy.github.io/slsa/leaderboards/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36"
}
response = requests.get(url, headers=headers)
response.encoding = 'utf-8'
html = response.text
soup = BeautifulSoup(html, 'html.parser')
print("SLSA Leaderboards lido com sucesso!")


# convertendo a tabela do html do site em um dataframe e tratando os dados
# a tabela é extraída usando BeautifulSoup e depois convertida para um DataFrame do pandas
# StringIO evita "File name too long" no Linux: pandas não interpreta o HTML como caminho de arquivo
tabela = soup.find('table')
df = pd.read_html(StringIO(str(tabela)), flavor='html5lib')[0]


# Extração de dados do JSON embutido
script_tag = soup.find('script', {'type': 'application/json', 'data-url': '/slsa/data.json'})
code_map = {}
slug_map = {}

if script_tag:
    try:
        data_json = json.loads(script_tag.string)
        if isinstance(data_json.get('body'), str):
            body_data = json.loads(data_json['body'])
        else:
            body_data = data_json.get('body', {})
        
        code_map = body_data.get('codeMap', {})
        slug_map = body_data.get('slugMap', {})
        print(f"JSON extraído: {len(code_map)} jogadores no codeMap, {len(slug_map)} no slugMap")
    except Exception as e:
        print(f"Erro ao processar JSON: {e}")

# Mapear connectCode para o personagem mais usado
char_mapping = {}
for code, info in code_map.items():
    try:
        chars = info.get('account', {}).get('rankedNetplayProfile', {}).get('characters', [])
        if chars:
            # encontrar o personagem com maior gameCount
            most_used = max(chars, key=lambda x: x.get('gameCount', 0))
            char_mapping[code] = most_used.get('character')
    except:
        continue

# tratamento dos dados
df['RANK'] = df['RANK'].astype(str).str.replace('NEW!', '', regex=False).str.extract(r'(\d+)')
rating_parts = df['RATING'].str.extract(r'(\d+)\s+(\w+\s*\w*)')
df['RATING_NUMBER'] = rating_parts[0]
df['RATING_ELO'] = rating_parts[1]

# Extrair código do jogador do nome (ex: "Nome CODE#123")
df['PLAYER_CODE'] = df['PLAYER'].str.extract(r'([A-Za-z]+#\d+)')
df['MOST_USED_CHARACTER'] = df['PLAYER_CODE'].map(char_mapping)
df.drop(columns=['CHARACTERS'], inplace=True)


# conexão com o banco (variáveis de ambiente no servidor)
load_dotenv()

db_config = {
    "database": os.environ.get("DB_NAME"),
    "host": os.environ.get("DB_HOST"),
    "user": os.environ.get("DB_USER"),
    "password": os.environ.get("DB_PASSWORD"),
    "port": os.environ.get("DB_PORT"),
}
conexao = psycopg2.connect(**db_config)
cursor = conexao.cursor()


# criando tabela base (recria sempre)
cursor.execute("DROP TABLE IF EXISTS melee CASCADE;")
cursor.execute('''
    CREATE TABLE melee (
        ID SERIAL PRIMARY KEY,
        RANK INT,
        PLAYER VARCHAR(255),
        RATING_NUMBER INT,
        RATING_ELO VARCHAR(255),
        SETS VARCHAR(255),
        MOST_USED_CHARACTER VARCHAR(255)
    )
''')


# inserção dos dados
query_insert_melee = "INSERT INTO melee (RANK, PLAYER, RATING_NUMBER, RATING_ELO, SETS, MOST_USED_CHARACTER) VALUES (%s, %s, %s, %s, %s, %s)"
melee_data = [(row['RANK'], row['PLAYER'], row['RATING_NUMBER'], row['RATING_ELO'], row['W / L'], row['MOST_USED_CHARACTER']) for _, row in df.iterrows()]
cursor.executemany(query_insert_melee, melee_data)
conexao.commit()


# preparar html_string para extração
html_string = html


# Extrair slippiConnectCodes + countryCode de forma robusta
# Alguns JSONs embutidos usam aspas escapadas (\") dentro do HTML; lidamos com ambos os casos.
country_codes = []
slippi_connect_codes = []


# função auxiliar para processar um bloco slugMap (texto já com aspas normais)
def process_slugmap_block(block_text):
    codes = []
    countries = []
    for m in re.finditer(r'"([^\"]+)"\s*:\s*\{(.*?)\}(?:,|$)', block_text, flags=re.DOTALL):
        obj = m.group(2)
        scs = re.findall(r'"([A-Za-z]+#\d+)"', obj)
        if not scs:
            continue
        sc = scs[0]
        cc_m = re.search(r'countryCode"\s*:\s*"([^\"]+)"', obj)
        cc = cc_m.group(1).strip() if cc_m else None
        codes.append(sc)
        countries.append(cc)
    return codes, countries


# tentar forma "normal" primeiro
sm_match = re.search(r'"slugMap"\s*:\s*\{(.*?)\}\s*,\s*"leaderboard"', html_string, flags=re.DOTALL)
if sm_match:
    block = sm_match.group(1)
    codes, countries = process_slugmap_block(block)
    slippi_connect_codes.extend(codes)
    country_codes.extend(countries)
else:
    # tentar detectar conteúdo com aspas escapadas (\") e desserializar as aspas
    if '\\"slugMap\\"' in html_string:
        # transformar \" em " para facilitar regex
        unescaped = html_string.replace('\\\"', '"')
        sm2 = re.search(r'"slugMap"\s*:\s*\{(.*?)\}\s*,\s*"leaderboard"', unescaped, flags=re.DOTALL)
        if sm2:
            block = sm2.group(1)
            codes, countries = process_slugmap_block(block)
            slippi_connect_codes.extend(codes)
            country_codes.extend(countries)


# fallback: procurar arrays slippiConnectCodes diretamente no documento
if not slippi_connect_codes:
    for m in re.finditer(r'"slippiConnectCodes"\s*:\s*\[([^\]]*)\]', html_string, flags=re.DOTALL):
        arr = m.group(1)
        scs = re.findall(r'"([A-Za-z]+#\d+)"', arr)
        if not scs:
            continue
        sc = scs[0]
        # procurar countryCode nas proximidades
        start = max(0, m.start()-400)
        end = min(len(html_string), m.end()+400)
        snippet = html_string[start:end]
        cc_m = re.search(r'countryCode"\s*:\s*"([^\"]+)"', snippet)
        cc = cc_m.group(1).strip() if cc_m else None
        slippi_connect_codes.append(sc)
        country_codes.append(cc)


# trims e estatísticas
if slippi_connect_codes:
    tamanho_minimo = min(len(country_codes), len(slippi_connect_codes))
    country_codes = country_codes[:tamanho_minimo]
    slippi_connect_codes = slippi_connect_codes[:tamanho_minimo]
else:
    country_codes = []
    slippi_connect_codes = []


print(f"Players com código de país encontrados na base: {len([c for c in country_codes if c])}")
print(f"Players ativos na temporada atual: {len(slippi_connect_codes)}")
print(f"Primeiros 3 códigos encontrados: {slippi_connect_codes[:3]}")


# salvar dumps de depuração
os.makedirs('debug', exist_ok=True)
pd.DataFrame({'codes': slippi_connect_codes}).to_csv(os.path.join('debug', 'codigos_brutos.csv'), index=False)
pd.DataFrame({'paises': country_codes}).to_csv(os.path.join('debug', 'paises_brutos.csv'), index=False)
pd.DataFrame({'CountryCode': country_codes, 'SlippiConnectCodes': slippi_connect_codes}).to_csv(os.path.join('debug', 'df_paises_raw.csv'), index=False)
pd.DataFrame(list(char_mapping.items()), columns=['ConnectCode', 'MostUsedCharacter']).to_csv(os.path.join('debug', 'character_mapping.csv'), index=False)
df.to_csv(os.path.join('debug', 'melee_table.csv'), index=False)


# substituir dataframe original por df_paises filtrado (apenas CountryCode válidos)
df_paises = pd.DataFrame({'CountryCode': country_codes, 'SlippiConnectCodes': slippi_connect_codes})
df_paises = df_paises[df_paises['CountryCode'].notnull() & (df_paises['CountryCode'] != '')]


# limpeza e separação de Nome/Código no SQL
cursor.execute('''
ALTER TABLE melee ADD COLUMN PLAYER_NAME VARCHAR(255);
ALTER TABLE melee ADD COLUMN PLAYER_CODE VARCHAR(255);
UPDATE melee SET PLAYER_NAME = REGEXP_REPLACE(PLAYER, ' [A-Za-z#0-9]+$', '');
UPDATE melee SET PLAYER_CODE = REGEXP_REPLACE(PLAYER, '^.+ ', '');
ALTER TABLE melee DROP COLUMN PLAYER;
''')


# criando e populando a tabela de países
cursor.execute("DROP TABLE IF EXISTS melee_paises;")
cursor.execute('''
    CREATE TABLE melee_paises (
        ID SERIAL PRIMARY KEY,
        COUNTRYCODE VARCHAR(255),
        SLIPPICONNECTCODES VARCHAR(255)
    )
''')


paises_data = [(row['CountryCode'], row['SlippiConnectCodes']) for _, row in df_paises.iterrows()]
if paises_data:
    cursor.executemany("INSERT INTO melee_paises (COUNTRYCODE, SLIPPICONNECTCODES) VALUES (%s, %s)", paises_data)
    conexao.commit()
    print("Códigos dos jogadores inseridos no banco de dados")
else:
    print("Nenhum par CountryCode+SlippiConnectCode para inserir em melee_paises")


# processamento de tabelas geográficas
cursor.execute("DROP TABLE IF EXISTS paises_players")
cursor.execute('''
CREATE TABLE paises_players AS
SELECT slippiconnectcodes, player_name, rating_number, countrycode, rating_elo, most_used_character from melee
INNER JOIN melee_paises ON player_code = slippiconnectcodes
''')


# a tabela paises_players é criada unindo os dados de melee (jogadores, ratings) com melee_paises (códigos de país) usando o código do jogador como chave
#  essa junção permite associar cada jogador ao seu país e rating, o que é essencial para as análises geográficas e estatísticas posteriores
print("Junção entre nome dos jogadores e países dos jogadores executada")

# criando tabela de dados por país (média de rating, contagem de jogadores e rank mais comum)
# a subconsulta para most_common_rank conta quantas vezes cada rank aparece por país e ordena para pegar o mais frequente
cursor.execute("DROP TABLE IF EXISTS dados_pais")
cursor.execute('''
CREATE TABLE dados_pais AS
SELECT 
    pp1.countrycode, 
    AVG(pp1.rating_number) AS average_rating, 
    COUNT(pp1.countrycode) AS player_count,
    (
        SELECT pp2.rating_elo 
        FROM paises_players AS pp2
        WHERE pp2.countrycode = pp1.countrycode
        AND pp2.rating_elo != 'PENDING'
        GROUP BY pp2.rating_elo
        ORDER BY COUNT(*) DESC
        LIMIT 1
    ) AS most_common_rank,
    (
        SELECT pp3.most_used_character 
        FROM paises_players AS pp3
        WHERE pp3.countrycode = pp1.countrycode
        AND pp3.most_used_character IS NOT NULL
        GROUP BY pp3.most_used_character
        ORDER BY COUNT(*) DESC
        LIMIT 1
    ) AS most_used_character
FROM 
    paises_players AS pp1
GROUP BY 
    pp1.countrycode
ORDER BY 
    player_count DESC;
''')


# update único em vez de múltiplos comandos manuais
cursor.execute("UPDATE dados_pais SET countrycode = UPPER(countrycode);")
cursor.execute("UPDATE dados_pais SET countrycode = NULL WHERE countrycode = 'NULL';")
cursor.execute("UPDATE dados_pais SET most_common_rank = 'ALL PENDING' WHERE most_common_rank IS NULL;")


# criando tabela final de output (dados + geometria) e tabela de centroides
cursor.execute(''' DROP TABLE IF EXISTS public.output''')
cursor.execute('''
CREATE TABLE output AS 
SELECT
    b.country,
    ROW_NUMBER() OVER () AS id,
    CAST(a.average_rating AS DECIMAL (10,2)) as average_rating,
    a.player_count,
    a.most_common_rank,
    a.most_used_character,
    b.geom
FROM public.dados_pais AS a
JOIN public.countries AS b ON a.countrycode = b.countrycode;
''')


# adicionando chave primária para garantir integridade e facilitar operações futuras
cursor.execute("ALTER TABLE public.output ADD CONSTRAINT output_pk PRIMARY KEY (id);")


# a tabela output contém os dados agregados por país junto com a geometria do país (geom) para visualização geográfica
cursor.execute(''' DROP TABLE IF EXISTS public.output_centroids''')
cursor.execute('''
CREATE TABLE output_centroids AS
SELECT 
    country,
    id,
    most_common_rank,
    most_used_character,
    ST_Centroid(geom) AS centroid_geom
FROM output;''')


conexao.commit()
conexao.close()


# integração com o geoserver
# as URLs do WFS do GeoServer são construídas usando a variável de ambiente GEOSERVER_BASE, que deve conter a URL base do GeoServer (ex: http://localhost:8080)
geoserver_base = os.environ.get("GEOSERVER_BASE")
url_centroids = f"{geoserver_base}/geoserver/melee/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=melee%3Aoutput_centroids&maxFeatures=500&outputFormat=application%2Fjson"
url_polygons = f"{geoserver_base}/geoserver/melee/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=melee%3Aoutput&maxFeatures=500&outputFormat=application%2Fjson"


output_dir = "docs"
os.makedirs(output_dir, exist_ok=True)  


# os.path.join é usado para garantir compatibilidade entre sistemas operacionais (Windows, Linux, etc.) ao construir os caminhos dos arquivos
file_centroids = os.path.join(output_dir, "centroids.geojson")
file_polygons = os.path.join(output_dir, "polygons.geojson")
file_data = os.path.join(output_dir, "data.txt")


# função para baixar e salvar os arquivos GeoJSON usando requests,
# com tratamento de erros para garantir que falhas de rede ou problemas com o GeoServer sejam reportados sem quebrar o script
def download_geojson(url, filename):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  
        with open(filename, "w", encoding="utf-8") as file:
            file.write(response.text)
        print(f"Arquivo salvo: {filename}")
    except requests.RequestException as e:
        print(f"Erro ao baixar {filename}: {e}")

# baixa os arquivos geojson dos endpoints do GeoServer e os salva na pasta docs, que é a pasta de saída para o site estático
# o ideal é que o site leia direto do GeoServer, mas para que funcione no github como site estático, foi adotada essa solução
# a rotina faz upload desses geojson para a pasta do site.
download_geojson(url_centroids, file_centroids)
download_geojson(url_polygons, file_polygons)


# salva a data da última atualização em um arquivo de texto, que pode ser lido pelo site para exibir a data da última atualização dos dados
data_atual = datetime.now().strftime("%Y-%m-%d")
with open(file_data, "w") as arquivo: 
     arquivo.write(data_atual)
print("Data atualizada com sucesso")


print("Mapa (output) atualizado.")
