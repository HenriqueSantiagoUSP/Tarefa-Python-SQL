"""
Esquema do banco: CREATE TABLE de cada entidade, índices e a função que (re)cria tudo.

Decisões de tipo (o SQLite tem só INTEGER, REAL, TEXT e BLOB):
- ids gerados pelo banco: INTEGER PRIMARY KEY (é o próprio rowid). O DAO recebe o valor com RETURNING.
- ids que vêm de fora (MAC da pulseira, id do alerta no MQTT, site, código do quarto): TEXT.
- datas: TEXT 'AAAA-MM-DD'; instantes: TEXT 'AAAA-MM-DD HH:MM:SS' em UTC, o formato do CURRENT_TIMESTAMP.
  O CHECK "col IS date(col)" recusa outro formato e datas inválidas (date() devolve NULL para elas, e
  "col = NULL" não reprovaria o CHECK; "IS" reprova).
- STRICT: o SQLite passa a recusar, por exemplo, texto numa coluna INTEGER (como o PostgreSQL).
"""

# %% sql_tabelas
SQL_ILPI = """
CREATE TABLE IF NOT EXISTS ilpi (
    id_ilpi  INTEGER PRIMARY KEY,
    nome     TEXT NOT NULL,
    site     TEXT NOT NULL UNIQUE,          -- o <site> do tópico MQTT idoso/<site>/<quarto>/...
    endereco TEXT NOT NULL
) STRICT
"""

SQL_CUIDADOR = """
CREATE TABLE IF NOT EXISTS cuidador (
    id_cuidador INTEGER PRIMARY KEY,
    id_ilpi     INTEGER NOT NULL,
    nome        TEXT NOT NULL,
    telegram_id TEXT UNIQUE,                -- identificador, não número: fica TEXT
    FOREIGN KEY (id_ilpi) REFERENCES ilpi (id_ilpi)
) STRICT
"""

SQL_QUARTO = """
CREATE TABLE IF NOT EXISTS quarto (
    id_quarto  INTEGER PRIMARY KEY,
    id_ilpi    INTEGER NOT NULL,
    codigo     TEXT NOT NULL,               -- o <quarto> do tópico MQTT, ex.: 'quarto101'
    capacidade INTEGER NOT NULL DEFAULT 1 CHECK (capacidade > 0),
    UNIQUE (id_ilpi, codigo),               -- duas ILPIs podem ter um 'quarto101'
    FOREIGN KEY (id_ilpi) REFERENCES ilpi (id_ilpi)
) STRICT
"""

SQL_IDOSO = """
CREATE TABLE IF NOT EXISTS idoso (
    id_idoso        INTEGER PRIMARY KEY,
    nome            TEXT NOT NULL,
    data_nascimento TEXT NOT NULL CHECK (data_nascimento IS date(data_nascimento)),
    id_quarto       INTEGER,                -- quarto atual (NULL: sem quarto)
    FOREIGN KEY (id_quarto) REFERENCES quarto (id_quarto)
) STRICT
"""

SQL_GADGET = """
CREATE TABLE IF NOT EXISTS gadget (
    id_gadget TEXT NOT NULL PRIMARY KEY     -- 3 últimos bytes do MAC em hexadecimal, ex.: 'a1b2c3'
              CHECK (length(id_gadget) = 6 AND id_gadget NOT GLOB '*[^0-9a-f]*'),
    id_idoso  INTEGER UNIQUE,               -- uma pulseira por idoso; NULL = pulseira reserva
    FOREIGN KEY (id_idoso) REFERENCES idoso (id_idoso) ON DELETE SET NULL
) STRICT
"""

SQL_SENSOR = """
CREATE TABLE IF NOT EXISTS sensor (
    id_sensor INTEGER PRIMARY KEY,
    id_quarto INTEGER NOT NULL,
    tipo      TEXT NOT NULL CHECK (tipo IN ('porta', 'presenca', 'temperatura')),
    lugar     TEXT NOT NULL,                -- ex.: porta do 'quarto' ou do 'banheiro'
    modelo    TEXT NOT NULL,                -- MC-38, HC-SR501, LM35DZ
    UNIQUE (id_quarto, tipo, lugar),
    FOREIGN KEY (id_quarto) REFERENCES quarto (id_quarto)
) STRICT
"""

SQL_EVENTO_SENSOR = """
CREATE TABLE IF NOT EXISTS evento_sensor (
    id_evento   INTEGER PRIMARY KEY,
    id_sensor   INTEGER NOT NULL,
    ocorrido_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                CHECK (ocorrido_em IS datetime(ocorrido_em)),
    estado      TEXT,                       -- 'aberta'/'fechada', 'detectada'/'livre'
    valor       REAL,                       -- temperatura em °C
    CHECK (estado IS NOT NULL OR valor IS NOT NULL),
    FOREIGN KEY (id_sensor) REFERENCES sensor (id_sensor) ON DELETE CASCADE
) STRICT
"""

SQL_HISTORICO_QUARTO = """
CREATE TABLE IF NOT EXISTS historico_quarto (
    id_registro  INTEGER PRIMARY KEY,
    id_idoso     INTEGER NOT NULL,
    id_quarto    INTEGER NOT NULL,
    data_entrada TEXT NOT NULL CHECK (data_entrada IS date(data_entrada)),
    data_saida   TEXT CHECK (data_saida IS date(data_saida)),   -- NULL: ainda está no quarto
    CHECK (data_saida IS NULL OR data_saida >= data_entrada),
    FOREIGN KEY (id_idoso) REFERENCES idoso (id_idoso) ON DELETE CASCADE,
    FOREIGN KEY (id_quarto) REFERENCES quarto (id_quarto)
) STRICT
"""

SQL_ALERTA = """
CREATE TABLE IF NOT EXISTS alerta (
    id_alerta   INTEGER PRIMARY KEY,
    id_mqtt     TEXT NOT NULL,              -- o "id" do payload MQTT do alerta
    tipo        TEXT NOT NULL CHECK (tipo IN ('queda', 'saida_noturna', 'banheiro_prolongado',
                    'inatividade', 'temperatura', 'vestivel_offline', 'bateria_baixa')),
    estado      TEXT NOT NULL DEFAULT 'ativo' CHECK (estado IN ('ativo', 'resolvido', 'cancelado')),
    inicio      TEXT NOT NULL CHECK (inicio IS datetime(inicio)),
    fim         TEXT CHECK (fim IS datetime(fim)),
    id_quarto   INTEGER NOT NULL,
    id_idoso    INTEGER,
    id_gadget   TEXT,
    id_cuidador INTEGER,                    -- quem atendeu
    UNIQUE (id_quarto, id_mqtt),            -- 'temperatura-<ts>' pode se repetir em outro quarto
    CHECK ((estado = 'ativo') = (fim IS NULL)),
    CHECK (fim IS NULL OR fim >= inicio),
    FOREIGN KEY (id_quarto) REFERENCES quarto (id_quarto),
    FOREIGN KEY (id_idoso) REFERENCES idoso (id_idoso) ON DELETE SET NULL,
    FOREIGN KEY (id_gadget) REFERENCES gadget (id_gadget) ON DELETE SET NULL,
    FOREIGN KEY (id_cuidador) REFERENCES cuidador (id_cuidador) ON DELETE SET NULL
) STRICT
"""

SQL_INDICES = [
    # Consultas por sensor ou quarto em ordem de tempo.
    "CREATE INDEX IF NOT EXISTS idx_evento_sensor_tempo ON evento_sensor (id_sensor, ocorrido_em)",
    "CREATE INDEX IF NOT EXISTS idx_alerta_quarto_inicio ON alerta (id_quarto, inicio)",
    # Índice parcial: no máximo um período em aberto (quarto atual) por idoso.
    """CREATE UNIQUE INDEX IF NOT EXISTS idx_historico_quarto_atual
       ON historico_quarto (id_idoso) WHERE data_saida IS NULL""",
]

# Ordem em que as tabelas dependem umas das outras (as referenciadas antes).
TABELAS = ["ilpi", "cuidador", "quarto", "idoso", "gadget", "sensor", "evento_sensor",
           "historico_quarto", "alerta"]
SQL_TABELAS = [SQL_ILPI, SQL_CUIDADOR, SQL_QUARTO, SQL_IDOSO, SQL_GADGET, SQL_SENSOR, SQL_EVENTO_SENSOR,
               SQL_HISTORICO_QUARTO, SQL_ALERTA]


def criar_tabelas(conexao, recriar=True):
    """Cria as tabelas e os índices. Com recriar=True, apaga antes (só para a atividade poder rodar de novo)."""
    if recriar:
        for tabela in reversed(TABELAS):   # as que referenciam primeiro; os nomes vêm da lista fixa acima
            conexao.execute(f"DROP TABLE IF EXISTS {tabela}")
    for sql in SQL_TABELAS + SQL_INDICES:
        conexao.execute(sql)
    conexao.commit()
