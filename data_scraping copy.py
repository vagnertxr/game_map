import pandas as pd
import psycopg2
from urllib.request import urlopen, Request
from bs4 import BeautifulSoup

url = "https://caioicy.github.io/slsa/leaderboards/"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36"}
req = Request(url, headers=headers)
response = urlopen(req)
html = response.read()
soup = BeautifulSoup(html, 'html.parser')

tabela = soup.find('table')
df = pd.read_html(str(tabela), flavor='html5lib')[0]

df['RANK'] = df['RANK'].str.replace('NEW!', '')
df['RANK'] = df['RANK'].str.extract(r'(\d+)')
rating_parts = df['RATING'].str.extract(r'(\d+)\s+(\w+\s*\w*)')
df['RATING_NUMBER'] = rating_parts[0]
df['RATING_ELO'] = rating_parts[1]
df[['PLAYER_NAME', 'PLAYER_CODE']] = df['PLAYER'].str.split(expand=True)
df.drop(columns=['PLAYER'], inplace=True)
df.drop(columns=['CHARACTERS'], inplace=True)

print(df)

conexao = psycopg2.connect(database="melee",
                           host="localhost",
                           user="postgres",
                           password="postgres",
                           port="5432")

cursor = conexao.cursor()
cursor.execute("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'melee')")
table_exists = cursor.fetchone()[0]

if table_exists:
    for index, row in df.iterrows():
        cursor.execute("DROP TABLE melee")
        cursor.execute('''
        CREATE TABLE melee (
            ID SERIAL PRIMARY KEY,
            RANK INT,
            PLAYER_NAME VARCHAR(255),
            PLAYER_CODE VARCHAR(255),
            RATING_NUMBER INT,
            RATING_ELO VARCHAR(255),
            SETS VARCHAR(255)
        )
    ''')

        for index, row in df.iterrows():
            cursor.execute("INSERT INTO melee (RANK, PLAYER_NAME, PLAYER_CODE, RATING_NUMBER, RATING_ELO, SETS) VALUES (%s, %s, %s, %s, %s, %s)",
                   (row['RANK'], row['PLAYER_NAME'], row['PLAYER_CODE'], row['RATING_NUMBER'], row['RATING_ELO'], row['SETS']))
else:
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
                       (row['RANK'], row['PLAYER'], row['RATING_NUMBER'], row['RATING_ELO'], row['SETS']))

conexao.commit()
conexao.close()