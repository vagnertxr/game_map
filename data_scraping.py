# importando todas as bibliotecas necessárias
import pandas as pd
import psycopg2
import re
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# conectando ao site do caio e lendo o html
url = "https://caioicy.github.io/slsa/leaderboards/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36"
}
response = requests.get(url, headers=headers)
response.encoding = 'utf-8'
html = response.text
soup = BeautifulSoup(html, 'html.parser')

# convertendo a tabela do html do site em um dataframe e tratando os dados
tabela = soup.find('table')
df = pd.read_html(str(tabela), flavor='html5lib')[0]

# tratamento dos dados
df['RANK'] = df['RANK'].astype(str).str.replace('NEW!', '', regex=False).str.extract(r'(\d+)')
rating_parts = df['RATING'].str.extract(r'(\d+)\s+(\w+\s*\w*)')
df['RATING_NUMBER'] = rating_parts[0]
df['RATING_ELO'] = rating_parts[1]
df.drop(columns=['CHARACTERS'], inplace=True)

# conexão com o banco (definido como variável, aí é só chamar ela depois)
db_config = {
    "database": "melee",
    "host": "192.168.15.20",
    "user": "postgres",
    "password": "postgres",
    "port": "5432"
}

conexao = psycopg2.connect(**db_config)
cursor = conexao.cursor()

# criando tabela base
# checa se a tabela existe antes de qualquer modificação
cursor.execute("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'melee')")
table_exists = cursor.fetchone()[0]

if table_exists:
    print("Tabela 'melee' encontrada no banco, recriando-a...")
else:
    print("Tabela 'melee' não foi encontrada no banco, criando-a...")

# executa a limpeza e criação
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

#criando tabela com os códigos de conexão
html_string = str(html)
# regex aprimorado para capturar os códigos diretamente do JSON interno do site
country_codes = re.findall(r'countryCode[\\"]+: ?[\\"]+(.*?)[\\"]+', html)
# extraímos os códigos Slippi diretamente do DataFrame para garantir alinhamento total com os nomes
slippi_connect_codes = df['PLAYER'].str.split().str[-1].tolist()


# com essa linha aqui aqui, eu apago o código do último player, já que ele não possui país (não entendo como, mas funciona)
# del slippi_connect_codes[-1] 

#isso serve para acompanhar o andamento do script
print(f"Players com código de país encontrados na base: {len(country_codes)}")
print(f"Players ativos na temporada atual: {len(slippi_connect_codes)}")
print(f"Primeiros 3 códigos encontrados: {slippi_connect_codes[:3]}")

# codigo para encontrar o texto que varia = (.*?)
# aqui é um exemplo de como estão os dados lá no html:
# \\\\"tr\\\\":{\\\\"slug\\\\":\\\\"tr\\\\",\\\\"tag\\\\":\\\\"TXR\\\\",
# \\\\"countryCode\\\\":\\\\"br\\\\",\\\\"slippiConnectCodes\\\\":c\\\\"TXR#205\\\\"u,\\\\"subregion\\\\":\\\\"br\\\\"}

# alinhando as listas para evitar erro de comprimento no DataFrame
tamanho_minimo = min(len(country_codes), len(slippi_connect_codes))
country_codes = country_codes[:tamanho_minimo]
slippi_connect_codes = slippi_connect_codes[:tamanho_minimo]

#apenas criando um csv com os códigos de todo mundo para ver se está batendo sem precisar acessar o banco
csvcodes = pd.DataFrame({'codes': slippi_connect_codes})
csvpaises = pd.DataFrame({'paises': country_codes})
csvcodes.to_csv('codigos_brutos.csv', index=False)
csvpaises.to_csv('paises_brutos.csv', index=False)

#subtituindo o dataframe original por um com códigos de país, para depois dar join na tabela melee
df_paises = pd.DataFrame({'CountryCode': country_codes, 'SlippiConnectCodes': slippi_connect_codes})

# reabrindo cursor se necessário ou continuando a transação
cursor.execute("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'melee_paises')")
table_exists = cursor.fetchone()[0]

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
cursor.executemany("INSERT INTO melee_paises (COUNTRYCODE, SLIPPICONNECTCODES) VALUES (%s, %s)", paises_data)

conexao.commit()
print("Códigos dos jogadores inseridos no banco de dados")

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

# limpeza final das tabelas de processamento
cursor.execute("DROP TABLE IF EXISTS public.paises_players")
cursor.execute("DROP TABLE IF EXISTS public.melee_paises")
cursor.execute("DROP TABLE IF EXISTS public.dados_pais")

conexao.commit()
conexao.close()

# integração geoserver
url_centroids = "http://192.168.15.20:8082/geoserver/melee/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=melee%3Aoutput_centroids&maxFeatures=500&outputFormat=application%2Fjson"
url_polygons = "http://192.168.15.20:8082/geoserver/melee/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=melee%3Aoutput&maxFeatures=500&outputFormat=application%2Fjson"

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