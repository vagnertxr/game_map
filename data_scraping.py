# importando todas as bibliotecas necessárias
import pandas as pd
import psycopg2
import re
import os
import requests
from io import StringIO
from bs4 import BeautifulSoup
from datetime import datetime

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

# convertendo a tabela do html do site em um dataframe e tratando os dados
# StringIO evita "File name too long" no Linux: pandas não interpreta o HTML como caminho de arquivo
tabela = soup.find('table')
df = pd.read_html(StringIO(str(tabela)), flavor='html5lib')[0]

# tratamento dos dados
df['RANK'] = df['RANK'].astype(str).str.replace('NEW!', '', regex=False).str.extract(r'(\d+)')
rating_parts = df['RATING'].str.extract(r'(\d+)\s+(\w+\s*\w*)')
df['RATING_NUMBER'] = rating_parts[0]
df['RATING_ELO'] = rating_parts[1]
df.drop(columns=['CHARACTERS'], inplace=True)

# conexão com o banco (variáveis de ambiente no servidor)
db_config = {
    "database": os.environ.get("DB_NAME", "melee"),
    "host": os.environ.get("DB_HOST", "192.168.15.20"),
    "user": os.environ.get("DB_USER", "postgres"),
    "password": os.environ.get("DB_PASSWORD", "postgres"),
    "port": os.environ.get("DB_PORT", "5432"),
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
        SETS VARCHAR(255)
    )
''')

# inserção dos dados
query_insert_melee = "INSERT INTO melee (RANK, PLAYER, RATING_NUMBER, RATING_ELO, SETS) VALUES (%s, %s, %s, %s, %s)"
melee_data = [(row['RANK'], row['PLAYER'], row['RATING_NUMBER'], row['RATING_ELO'], row['W / L']) for _, row in df.iterrows()]
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
SELECT slippiconnectcodes, player_name, rating_number, countrycode, rating_elo from melee
INNER JOIN melee_paises ON player_code = slippiconnectcodes
''')

print("Junção entre nome dos jogadores e países dos jogadores executada")

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
    ) AS most_common_rank
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

cursor.execute(''' DROP TABLE IF EXISTS public.output''')
cursor.execute('''
CREATE TABLE output AS 
SELECT
    b.country,
    ROW_NUMBER() OVER () AS id,
    a.average_rating,
    a.player_count,
    a.most_common_rank,
    b.geom
FROM public.dados_pais AS a
JOIN public.countries AS b ON a.countrycode = b.countrycode;
''')

cursor.execute("ALTER TABLE public.output ADD CONSTRAINT output_pk PRIMARY KEY (id);")

cursor.execute(''' DROP TABLE IF EXISTS public.output_centroids''')
cursor.execute('''
CREATE TABLE output_centroids AS
SELECT 
    country,
    id,
    most_common_rank,
    ST_Centroid(geom) AS centroid_geom
FROM output;''')

conexao.commit()
conexao.close()

# integração geoserver (no servidor: GEOSERVER_BASE=http://127.0.0.1:8082 se GeoServer estiver local)
geoserver_base = os.environ.get("GEOSERVER_BASE", "http://192.168.15.20:8082")
url_centroids = f"{geoserver_base}/geoserver/melee/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=melee%3Aoutput_centroids&maxFeatures=500&outputFormat=application%2Fjson"
url_polygons = f"{geoserver_base}/geoserver/melee/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=melee%3Aoutput&maxFeatures=500&outputFormat=application%2Fjson"

output_dir = "docs"
os.makedirs(output_dir, exist_ok=True)  

file_centroids = os.path.join(output_dir, "centroids.geojson")
file_polygons = os.path.join(output_dir, "polygons.geojson")
file_data = os.path.join(output_dir, "data.txt")
                         
def download_geojson(url, filename):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  
        with open(filename, "w", encoding="utf-8") as file:
            file.write(response.text)
        print(f"Arquivo salvo: {filename}")
    except requests.RequestException as e:
        print(f"Erro ao baixar {filename}: {e}")

download_geojson(url_centroids, file_centroids)
download_geojson(url_polygons, file_polygons)

data_atual = datetime.now().strftime("%Y-%m-%d")
with open(file_data, "w") as arquivo: 
     arquivo.write(data_atual)
print("Data atualizada com sucesso")

print("Mapa (output) atualizado.")
