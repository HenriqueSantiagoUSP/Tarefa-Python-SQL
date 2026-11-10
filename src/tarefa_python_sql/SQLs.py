from .Singleton import conexao

for sql in ("ilp", "cuidador", "quarto", "idoso", "gadget",
            "sensor", "evento_sensor", "historico_quarto", "alerta"):
    conexao.execute(f"DROP TABLE IF EXISTS {sql}")

sql_ilp = """
CREATE TABLE IF NOT EXISTS ilp (
    id_ilp INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    endereco TEXT NOT NULL
)
"""

sql_cuidador = """
CREATE TABLE IF NOT EXISTS cuidador (
    id_cuidador INTEGER PRIMARY KEY AUTOINCREMENT,
    id_ilp INTEGER NOT NULL,
    nome TEXT NOT NULL,
    telegram_id TEXT,
    FOREIGN KEY (id_ilp) REFERENCES ilp(id_ilp)
)
"""

sql_quarto = """
CREATE TABLE IF NOT EXISTS quarto (
    id_quarto INTEGER PRIMARY KEY,
    id_ilp INTEGER NOT NULL,
    FOREIGN KEY (id_ilp) REFERENCES ilp(id_ilp)
)
"""

# data_nascimento: YYYY-MM-DD
sql_idoso = """
CREATE TABLE IF NOT EXISTS idoso (
    id_idoso INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    data_nascimento TEXT NOT NULL,
    id_quarto INTEGER,
    FOREIGN KEY (id_quarto) REFERENCES quarto(id_quarto)
)
"""

sql_gadget = """
CREATE TABLE IF NOT EXISTS gadget (
    id_gadget TEXT PRIMARY KEY,
    id_idoso INTEGER,
    FOREIGN KEY (id_idoso) REFERENCES idoso(id_idoso)
)
"""

sql_sensor = """
CREATE TABLE IF NOT EXISTS sensor (
    id_sensor INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo TEXT NOT NULL,
    id_quarto INTEGER NOT NULL,
    lugar TEXT NOT NULL,
    FOREIGN KEY (id_quarto) REFERENCES quarto(id_quarto)
)
"""

sql_evento_sensor = """
CREATE TABLE IF NOT EXISTS evento_sensor (
    id_evento INTEGER PRIMARY KEY AUTOINCREMENT,
    id_sensor INTEGER NOT NULL,
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
    estado TEXT,
    valor REAL,
    FOREIGN KEY (id_sensor) REFERENCES sensor(id_sensor)
)
"""

sql_historico_quarto = """
CREATE TABLE IF NOT EXISTS historico_quarto (
    id_registro INTEGER PRIMARY KEY AUTOINCREMENT,
    id_idoso INTEGER NOT NULL,
    id_quarto INTEGER NOT NULL,
    tipo TEXT NOT NULL,
    data TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_quarto) REFERENCES quarto(id_quarto),
    FOREIGN KEY (id_idoso) REFERENCES idoso(id_idoso)
)
"""

sql_alerta = """
CREATE TABLE IF NOT EXISTS alerta (
    id_alerta INTEGER PRIMARY KEY AUTOINCREMENT,
    id_mqtt TEXT NOT NULL,
    tipo TEXT NOT NULL,
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
    id_quarto INTEGER,
    id_idoso INTEGER,
    id_gadget TEXT,
    FOREIGN KEY (id_quarto) REFERENCES quarto(id_quarto),
    FOREIGN KEY (id_idoso) REFERENCES idoso(id_idoso),
    FOREIGN KEY (id_gadget) REFERENCES gadget(id_gadget)
)
"""

for sql in (sql_ilp, sql_cuidador, sql_quarto, sql_idoso, sql_gadget,
            sql_sensor, sql_evento_sensor, sql_historico_quarto, sql_alerta):
    conexao.execute(sql)

conexao.commit()
