
import sqlite3

conexao = sqlite3.connect("banco.db")
sql_quarto = """
CREATE TABLE IF NOT EXISTS quartos (
    num_quarto INTEGER NOT NULL PRIMARY KEY,
    numero_de_camas INTEGER NOT NULL,
    largura REAL NOT NULL,
    comprimento REAL NOT NULL
)
"""

sql_idoso = """
CREATE TABLE IF NOT EXISTS idosos (
    id INTEGER PRIMARY KEY,
    nome TEXT NOT NULL,
    idade INTEGER NOT NULL,
    quarto INTEGER NOT NULL REFERENCES quartos(num_quarto)
)
"""


sql_historico_queda = """
CREATE TABLE IF NOT EXISTS historico_quedas (
    id INTEGER NOT NULL REFERENCES idosos(id),
    data DATETIME NOT NULL
)
"""

sql_historico_sensor= """
CREATE TABLE IF NOT EXISTS historico_sensores (
    temperatura FLOAT NOT NULL,
    status_da_porta BOOLEAN NOT NULL,
    presenca BOOLEAN NOT NULL,
    data DATETIME NOT NULL,
    num_quarto INTEGER NOT NULL REFERENCES quartos(num_quarto)
)
"""
conexao.execute(sql_quarto)
conexao.execute(sql_idoso)
conexao.execute(sql_historico_queda)
conexao.execute(sql_historico_sensor)