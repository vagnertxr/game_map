# importando todas as bibliotecas necessárias
import pandas as pd
import psycopg2
import re
from urllib.request import urlopen, Request
from bs4 import BeautifulSoup
import os
import requests
from datetime import datetime

# conectando ao site
url = "https://caioicy.github.io/slsa/leaderboards/"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36"}
req = Request(url, headers=headers)
response = urlopen(req)
html = response.read()
soup = BeautifulSoup(html, 'html.parser')

#convertendo a tabela do html do site em um dataframe e tratando os dados
tabela = soup.find('table')
df = pd.read_html(str(tabela), flavor='html5lib')[0]
df['RANK'] = df['RANK'].astype(str)
df['RANK'] = df['RANK'].str.replace('NEW!', '')
df['RANK'] = df['RANK'].str.extract(r'(\d+)')
rating_parts = df['RATING'].str.extract(r'(\d+)\s+(\w+\s*\w*)')
df['RATING_NUMBER'] = rating_parts[0]
df['RATING_ELO'] = rating_parts[1]
df.drop(columns=['CHARACTERS'], inplace=True)

#conexão com o banco
conexao = psycopg2.connect(database="melee",
                           host="localhost",
                           user="postgres",
                           password="postgres",
                           port="5432")

cursor = conexao.cursor()

#criando tabela base
cursor.execute("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'melee')")
table_exists = cursor.fetchone()[0]
if table_exists:
    print("Tabela 'melee' encontrada no banco, recriando-a...")
    for index, row in df.iterrows():
        cursor.execute("DROP TABLE melee")
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

    for index, row in df.iterrows():
            cursor.execute("INSERT INTO melee (RANK, PLAYER, RATING_NUMBER, RATING_ELO, SETS) VALUES (%s, %s, %s, %s, %s)",
                       (row['RANK'], row['PLAYER'], row['RATING_NUMBER'], row['RATING_ELO'], row['W / L']))
else:
    print("Tabela 'melee' não foi encontrada no banco, criando-a...")
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

    for index, row in df.iterrows():
            cursor.execute("INSERT INTO melee (RANK, PLAYER, RATING_NUMBER, RATING_ELO, SETS) VALUES (%s, %s, %s, %s, %s)",
                       (row['RANK'], row['PLAYER'], row['RATING_NUMBER'], row['RATING_ELO'], row['W / L']))

conexao.commit()
conexao.close()


#criando tabela com os códigos de conexão
html_string = str(html)
html_string_sem_colchetes = html_string.replace('[', '!')
html_string_treated = html_string_sem_colchetes.replace(']', '!')
country_codes = re.findall(r'countryCode\\\\":(.*?),', html_string_treated)
slippi_connect_codes = re.findall(r'slippiConnectCodes\\\\":!(.*?),', html_string_treated)

# del slippi_connect_codes[-1] # aqui, eu apago o código do último player, já que ele não possui país (não entendo como, mas funciona)
country_codes = [code.replace('\\', '') for code in country_codes]
country_codes = [code.replace('"', '') for code in country_codes]
country_codes = [code.replace('}', '') for code in country_codes]
slippi_connect_codes = [code.replace('\\', '') for code in slippi_connect_codes]
slippi_connect_codes = [code.replace('!', '') for code in slippi_connect_codes]
slippi_connect_codes = [code.replace('}', '') for code in slippi_connect_codes]
slippi_connect_codes = [code.replace('"', '') for code in slippi_connect_codes]

# codigo para encontrar o texto que varia = (.*?)
# como estão os dados lá no html:
# \\\\"tr\\\\":{\\\\"slug\\\\":\\\\"tr\\\\",\\\\"tag\\\\":\\\\"TXR\\\\",
# \\\\"countryCode\\\\":\\\\"br\\\\",\\\\"slippiConnectCodes\\\\":c\\\\"TXR#205\\\\"u,\\\\"subregion\\\\":\\\\"br\\\\"}

countrysize = len(country_codes)
codesize = len(slippi_connect_codes)
print("Países Encontrados:")
print(countrysize)
print("Códigos Encontrados:")
print(codesize)
#isso serve para acompanhar o andamento do script

#apenas criando um csv com os códigos de todo mundo para ver se está batendo sem precisar acessar o banco
csvcodes = pd.DataFrame({'codes': slippi_connect_codes})
csvpaises = pd.DataFrame({'paises': country_codes})
csvcodes.to_csv('codigos_brutos.csv', index=False)
csvpaises.to_csv('paises_brutos.csv', index=False)


#subtituindo o dataframe original por um com códigos de país, para depois dar join na tabela melee
df = pd.DataFrame({'CountryCode': country_codes, 'SlippiConnectCodes': slippi_connect_codes})

conexao = psycopg2.connect(database="melee",
                           host="localhost",
                           user="postgres",
                           password="postgres",
                           port="5432")

cursor = conexao.cursor()
cursor.execute("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'melee_paises')")
table_exists = cursor.fetchone()[0]

cursor.execute('''
ALTER TABLE melee ADD COLUMN PLAYER_NAME VARCHAR(255);

ALTER TABLE melee ADD COLUMN PLAYER_CODE VARCHAR(255);

UPDATE melee SET PLAYER_NAME = REGEXP_REPLACE(PLAYER, ' [A-Za-z#0-9]+$', '');

UPDATE melee SET PLAYER_CODE = REGEXP_REPLACE(PLAYER, '^.+ ', '');
''')
cursor.execute("ALTER TABLE melee DROP COLUMN player")
if table_exists:
    for index, row in df.iterrows():
        cursor.execute("DROP TABLE melee_paises")
        cursor.execute('''
        CREATE TABLE melee_paises (
            ID SERIAL PRIMARY KEY,
            COUNTRYCODE VARCHAR(255),
            SLIPPICONNECTCODES VARCHAR(255)
        )
    ''')
    for index, row in df.iterrows():
        cursor.execute("INSERT INTO melee_paises (COUNTRYCODE, SLIPPICONNECTCODES) VALUES (%s, %s)",
                       (row['CountryCode'], row['SlippiConnectCodes']))

        
else:
    cursor.execute('''
        CREATE TABLE melee_paises (
            ID SERIAL PRIMARY KEY,
            COUNTRYCODE VARCHAR(255),
            SLIPPICONNECTCODES VARCHAR(255)
        );
    ''')

    for index, row in df.iterrows():
        cursor.execute("INSERT INTO melee_paises (COUNTRYCODE, SLIPPICONNECTCODES) VALUES (%s, %s)",
                       (row['CountryCode'], row['SlippiConnectCodes']))

conexao.commit()

df = pd.DataFrame({'CountryCode': country_codes, 'SlippiConnectCodes': slippi_connect_codes})
df.to_csv('paises_codes.csv', index=False)
#isso aqui exporta mais um csv para mostrar o procedimento pronto

cursor.execute("DROP TABLE IF EXISTS paises_players")
cursor.execute('''
CREATE TABLE paises_players AS
SELECT slippiconnectcodes, player_name, rating_number, countrycode, rating_elo from melee
INNER JOIN melee_paises
ON player_code = slippiconnectcodes
''')
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

cursor.execute('''
UPDATE dados_pais
SET countrycode = 'US'
WHERE countrycode = 'us';
UPDATE dados_pais
SET countrycode = 'CL'
WHERE countrycode = 'cl';
UPDATE dados_pais
SET countrycode = 'VE'
WHERE countrycode = 've';
UPDATE dados_pais
SET countrycode = 'UY'
WHERE countrycode = 'uy';
UPDATE dados_pais
SET countrycode = 'PE'
WHERE countrycode = 'pe';
UPDATE dados_pais
SET countrycode = 'CO'
WHERE countrycode = 'co';
UPDATE dados_pais
SET countrycode = 'EC'
WHERE countrycode = 'ec';
UPDATE dados_pais
SET countrycode = 'BR'
WHERE countrycode = 'br';
UPDATE dados_pais
SET countrycode = 'BO'
WHERE countrycode = 'bo';
UPDATE dados_pais
SET countrycode = 'AR'
WHERE countrycode = 'ar';
UPDATE dados_pais
SET countrycode = 'GT'
WHERE countrycode = 'gt';               
UPDATE dados_pais
SET countrycode = NULL
WHERE countrycode = 'null';
               ''')
query_dados = "SELECT * from dados_pais"

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
JOIN public.countries AS b
ON a.countrycode = b.iso;
''')

cursor.execute('''
ALTER TABLE public.output
ADD CONSTRAINT output_pk PRIMARY KEY (id);
''')

cursor.execute(''' DROP TABLE IF EXISTS public.output_centroids''')
cursor.execute('''
CREATE TABLE output_centroids AS
SELECT 
    country,
    id,
    most_common_rank,
    ST_Centroid(geom) AS centroid_geom
FROM output;''')

cursor.execute('''
DROP TABLE public.paises_players
''')
cursor.execute('''
DROP TABLE public.melee_paises
''')
cursor.execute('''
DROP TABLE public.dados_pais
''')
conexao.commit()
conexao.close()

url_centroids = "http://localhost:8081/geoserver/melee/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=melee%3Aoutput_centroids&outputFormat=application%2Fjson"

url_polygons = "http://localhost:8081/geoserver/melee/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=melee%3Aoutput&outputFormat=application%2Fjson"

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