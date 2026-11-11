"""
Roteiro da atividade, na ordem do notebook: conexão, tabelas, objetos, dados do Faker, CRUD, consultas com
JOIN e persistência. Rode com `python -m tarefa_python_sql`; cada trecho "# %%" vira uma célula do notebook.
"""

from datetime import date, datetime, timezone

from .Singleton import ARQUIVO_BANCO, BancoSQLite
from .SQLs import TABELAS, criar_tabelas
from .classes import ILPI, Alerta, Cuidador, EventoSensor, Gadget, HistoricoQuarto, Idoso, Quarto, Sensor
from .classesDAO import (AlertaDAO, CuidadorDAO, EventoSensorDAO, GadgetDAO, HistoricoQuartoDAO, IdosoDAO, ILPIDAO,
                         QuartoDAO, SensorDAO)
from .gerador_dados import gerar_dados

# %% conexao
existia_antes = ARQUIVO_BANCO.exists()
banco = BancoSQLite()
conexao = banco.conexao

versao = conexao.execute("SELECT sqlite_version() AS versao").fetchone()["versao"]
print("Arquivo já existia?", existia_antes)
print("Arquivo existe agora?", ARQUIVO_BANCO.exists())
print("SQLite:", versao)
print("Mesma conexão?", conexao is BancoSQLite().conexao)
print("Chaves estrangeiras ligadas?", conexao.execute("PRAGMA foreign_keys").fetchone()[0] == 1)

assert banco is BancoSQLite()
assert conexao is BancoSQLite().conexao

# %% criar
criar_tabelas(conexao, recriar=True)
sql = """
SELECT type, name
FROM sqlite_master
WHERE name NOT LIKE 'sqlite_%'
ORDER BY type DESC, name
"""
for linha in conexao.execute(sql).fetchall():
    print(f"{linha['type']:6} {linha['name']}")

# %% chaves
for tabela in TABELAS:
    for fk in conexao.execute(f"PRAGMA foreign_key_list({tabela})").fetchall():
        origem, destino = f"{tabela}.{fk['from']}", f"{fk['table']}.{fk['to']}"
        print(f"{origem:28} → {destino:22} ON DELETE {fk['on_delete']}")

# %% objetos
ilpi_exemplo = ILPI("ILPI Exemplo", "exemplo", "Rua A, 1")
quarto_exemplo = Quarto(ilpi_exemplo, "quarto101", capacidade=2)
idoso_exemplo = Idoso("Ana Souza", date(1940, 5, 17), quarto_exemplo)
pulseira_exemplo = Gadget("a1b2c3", idoso_exemplo)
sensor_exemplo = Sensor(quarto_exemplo, "porta", "banheiro", "MC-38")
cuidador_exemplo = Cuidador("Beatriz Lima", ilpi_exemplo, "123456789")
alerta_exemplo = Alerta("a1b2c3-1", "queda", quarto_exemplo, datetime(2026, 11, 1, 3, 0, tzinfo=timezone.utc),
                        idoso_exemplo, pulseira_exemplo)

print(idoso_exemplo, "| idade em 01/11/2026:", idoso_exemplo.idade_em(date(2026, 11, 1)))
print(pulseira_exemplo)
print("Tópico MQTT do sensor:", sensor_exemplo.topico)
print(alerta_exemplo, alerta_exemplo.to_dict())

alerta_exemplo.resolver(cuidador_exemplo, datetime(2026, 11, 1, 3, 12, tzinfo=timezone.utc))
print("Depois de resolver:", alerta_exemplo, "| duração:", alerta_exemplo.duracao)

assert idoso_exemplo.id_idoso is None          # ainda não foi gravado
assert idoso_exemplo.idade_em(date(2026, 11, 1)) == 86
assert alerta_exemplo.estado == "resolvido" and not alerta_exemplo.ativo

# %% gerar
dados = gerar_dados()

for nome in ("ilpis", "quartos", "sensores", "cuidadores", "idosos", "gadgets", "historicos", "eventos", "alertas"):
    print(f"{nome:11} {len(getattr(dados, nome)):5}")
print("Três idosos:", dados.idosos[:3])
print("Três alertas:", dados.alertas[:3])
print("Mudaram de quarto em 02/11:", dados.transferidos)

# %% gravar
ilpi_dao, quarto_dao, sensor_dao, evento_dao = ILPIDAO(), QuartoDAO(), SensorDAO(), EventoSensorDAO()
idoso_dao, cuidador_dao = IdosoDAO(), CuidadorDAO()
gadget_dao, historico_dao, alerta_dao = GadgetDAO(), HistoricoQuartoDAO(), AlertaDAO()
assert ilpi_dao.conexao is idoso_dao.conexao is alerta_dao.conexao

for ilpi in dados.ilpis:
    ilpi_dao.inserir(ilpi)
for quarto in dados.quartos:
    quarto_dao.inserir(quarto)
for sensor in dados.sensores:
    sensor_dao.inserir(sensor)
for cuidador in dados.cuidadores:
    cuidador_dao.inserir(cuidador)
for idoso in dados.idosos:
    idoso_dao.inserir(idoso)
for gadget in dados.gadgets:
    gadget_dao.inserir(gadget)
for registro in dados.historicos:
    historico_dao.inserir(registro)
evento_dao.inserir_varios(dados.eventos)       # executemany, um só commit
for alerta in dados.alertas:
    alerta_dao.inserir(alerta)

print("Ids gerados pelo banco (idosos):", [i.id_idoso for i in dados.idosos[:8]], "...")
print("Ids gerados pelo banco (alertas):", [a.id_alerta for a in dados.alertas[:8]], "...")

# %% contar
listas = {"ilpi": dados.ilpis, "cuidador": dados.cuidadores, "quarto": dados.quartos, "idoso": dados.idosos,
          "gadget": dados.gadgets, "sensor": dados.sensores, "evento_sensor": dados.eventos,
          "historico_quarto": dados.historicos, "alerta": dados.alertas}
for tabela in TABELAS:
    quantidade = conexao.execute(f"SELECT COUNT(*) FROM {tabela}").fetchone()[0]
    print(f"{tabela:16} {quantidade:5}")
    assert quantidade == len(listas[tabela])

# %% crud_idoso
def ocupantes(quarto):
    sql = "SELECT COUNT(*) FROM idoso WHERE id_quarto = ?"
    return conexao.execute(sql, (quarto.id_quarto,)).fetchone()[0]


quarto_com_vaga = next(q for q in dados.quartos if ocupantes(q) < q.capacidade)

# C — CREATE
nova = Idoso("Maria Teste", date(1945, 3, 8), quarto_com_vaga)
print("Antes do INSERT:", nova)
idoso_dao.inserir(nova)
historico_dao.inserir(HistoricoQuarto(nova, quarto_com_vaga, date(2026, 11, 8)))
print("Depois do INSERT:", nova)

# R — READ
lida = idoso_dao.buscar(nova.id_idoso)
print("Lida do banco:", lida.to_dict(), "| quarto:", lida.quarto.topico)

# U — UPDATE
lida.nome = "Maria Teste da Silva"
print("Linhas atualizadas:", idoso_dao.atualizar(lida))
print("Nome após UPDATE:", idoso_dao.buscar(nova.id_idoso).nome)
assert idoso_dao.buscar(nova.id_idoso).nome == "Maria Teste da Silva"

# %% crud_gadget
reserva = gadget_dao.listar_reservas()[0]
print("Pulseira reserva:", reserva)

# U — UPDATE: a pulseira reserva passa a ser da Maria
reserva.idoso = lida
print("Linhas atualizadas:", gadget_dao.atualizar(reserva))
print("Pulseira da Maria:", gadget_dao.buscar_do_idoso(lida.id_idoso))
assert gadget_dao.buscar(reserva.id_gadget).idoso.id_idoso == lida.id_idoso

# %% transferir
mesma_ilpi = [q for q in dados.quartos if q.ilpi.id_ilpi == lida.quarto.ilpi.id_ilpi]
destino = next(q for q in mesma_ilpi if q.id_quarto != lida.quarto.id_quarto and ocupantes(q) < q.capacidade)
cheio = next(q for q in mesma_ilpi if q.id_quarto != lida.quarto.id_quarto and ocupantes(q) >= q.capacidade)

idoso_dao.transferir(lida, destino, date(2026, 11, 9))   # 3 comandos numa transação (with conexao)
for registro in historico_dao.listar_por_idoso(lida.id_idoso):
    print(registro)
print("Quarto atual:", idoso_dao.buscar(lida.id_idoso).quarto.codigo)

try:                                           # quarto cheio: recusado antes de gravar
    idoso_dao.transferir(lida, cheio, date(2026, 11, 10))
except ValueError as erro:
    print("Transferência recusada:", erro)

assert idoso_dao.buscar(lida.id_idoso).quarto.id_quarto == destino.id_quarto
assert len(historico_dao.listar_por_idoso(lida.id_idoso)) == 2

# %% crud_alerta
# C — CREATE
queda = Alerta(f"{reserva.id_gadget}-900", "queda", lida.quarto,
               datetime(2026, 11, 9, 2, 40, tzinfo=timezone.utc), lida, reserva)
alerta_dao.inserir(queda)
print("Inserido:", alerta_dao.buscar(queda.id_alerta).to_dict())

# U — UPDATE: um cuidador resolve o alerta
cuidador = cuidador_dao.listar_por_ilpi(lida.quarto.ilpi.id_ilpi)[0]
queda.resolver(cuidador, datetime(2026, 11, 9, 2, 52, tzinfo=timezone.utc))
print("Linhas atualizadas:", alerta_dao.atualizar(queda))
relido = alerta_dao.buscar(queda.id_alerta)
print("Após UPDATE:", relido, "| atendido por", relido.cuidador.nome, "em", relido.duracao)
assert relido.estado == "resolvido" and relido.cuidador.id_cuidador == cuidador.id_cuidador

# D — DELETE
print("Linhas excluídas:", alerta_dao.excluir(queda.id_alerta))
assert alerta_dao.buscar(queda.id_alerta) is None

# %% crud_quarto
ilpi = dados.ilpis[0]

# C — CREATE: quarto, sensor e duas leituras
quarto_novo = Quarto(ilpi, "quarto201", capacidade=2)
quarto_dao.inserir(quarto_novo)
termometro = Sensor(quarto_novo, "temperatura", "quarto", "LM35DZ")
sensor_dao.inserir(termometro)
leitura = EventoSensor(termometro, datetime(2026, 11, 9, 15, 0, tzinfo=timezone.utc), valor=23.4)
evento_dao.inserir(leitura)
evento_dao.inserir(EventoSensor(termometro, datetime(2026, 11, 9, 15, 30, tzinfo=timezone.utc), valor=23.9))

# R — READ
print("Pelo tópico:", quarto_dao.buscar_por_topico(ilpi.site, "quarto201"))
print("Leitura:", evento_dao.buscar(leitura.id_evento).to_dict())

# U — UPDATE
quarto_novo.capacidade = 1
leitura.valor = 23.6
print("Linhas atualizadas:", quarto_dao.atualizar(quarto_novo), evento_dao.atualizar(leitura))
assert quarto_dao.buscar(quarto_novo.id_quarto).capacidade == 1
assert evento_dao.buscar(leitura.id_evento).valor == 23.6

# D — DELETE (as leituras do sensor saem junto: ON DELETE CASCADE)
print("Sensores excluídos:", sensor_dao.excluir(termometro.id_sensor))
print("Leituras que sobraram:", len(evento_dao.ultimos_do_quarto(quarto_novo.id_quarto)))
print("Quartos excluídos:", quarto_dao.excluir(quarto_novo.id_quarto))
assert evento_dao.buscar(leitura.id_evento) is None
assert quarto_dao.buscar(quarto_novo.id_quarto) is None

# %% excluir_idoso
# D — DELETE: o histórico sai junto (CASCADE) e a pulseira volta a ser reserva (SET NULL)
print("Idosos excluídos:", idoso_dao.excluir(lida.id_idoso))
print("Histórico que sobrou:", historico_dao.listar_por_idoso(lida.id_idoso))
print("A pulseira voltou a ser reserva:", gadget_dao.buscar(reserva.id_gadget))

assert idoso_dao.buscar(lida.id_idoso) is None
assert historico_dao.listar_por_idoso(lida.id_idoso) == []
assert gadget_dao.buscar(reserva.id_gadget).idoso is None

# %% join_idosos
site = dados.ilpis[0].site
linhas = idoso_dao.listar_por_ilpi(site)
print(f"Idosos da ILPI '{site}':", len(linhas))
for linha in linhas:
    print(linha)

esperado = [i for i in dados.idosos if i.quarto.ilpi.site == site]
assert len(linhas) == len(esperado)
assert all(linha["pulseira"] is not None for linha in linhas)   # todo idoso gerado tem pulseira

# %% join_alertas
ativos = alerta_dao.listar_ativos()
print("Alertas ativos:", len(ativos))
for linha in ativos:
    print(linha)

assert len(ativos) == sum(a.ativo for a in dados.alertas)

# %% join_eventos
quarto = dados.quartos[0]
ultimos = evento_dao.ultimos_do_quarto(quarto.id_quarto, limite=8)
print("Últimos eventos de", quarto.topico)
for linha in ultimos:
    print(linha)

momentos = [linha["ocorrido_em"] for linha in ultimos]
assert momentos == sorted(momentos, reverse=True)
assert all(linha["quarto"] == quarto.codigo for linha in ultimos)

# %% join_cuidadores
atendimentos = alerta_dao.atendimentos_por_cuidador()
for linha in atendimentos:
    print(linha)

resolvidos = [a for a in dados.alertas if a.estado == "resolvido"]
assert sum(linha["alertas"] for linha in atendimentos) == len(resolvidos)

# %% join_historico
# Confere, para cada alerta com idoso, que ele estava no quarto naquele dia.
com_idoso = [a for a in dados.alertas if a.idoso is not None]
for alerta in com_idoso:
    presentes = {linha["id_idoso"] for linha in alerta_dao.ocupantes_no_alerta(alerta.id_alerta)}
    assert alerta.idoso.id_idoso in presentes, alerta
print("Alertas conferidos com o histórico:", len(com_idoso))

# Exemplo: alerta num quarto duplo.
sem_idoso = next(a for a in dados.alertas if a.idoso is None and a.tipo == "saida_noturna")
for linha in alerta_dao.ocupantes_no_alerta(sem_idoso.id_alerta):
    print(linha)

# %% join_temperatura
temperaturas = evento_dao.temperatura_por_quarto()
for linha in temperaturas[:5]:
    print(linha)

# Confere com os dados em memória.
assert temperaturas[0]["quarto"] == dados.quarto_quente.codigo
leituras = [e.valor for e in dados.eventos
            if e.sensor.tipo == "temperatura" and e.sensor.quarto is dados.quarto_quente]
assert temperaturas[0]["media"] == round(sum(leituras) / len(leituras), 1)

# %% persistencia
conexao_anterior = conexao
banco.fechar()

banco = BancoSQLite()
conexao = banco.conexao
assert conexao is not conexao_anterior

idoso_dao, alerta_dao = IdosoDAO(), AlertaDAO()
quantidade = conexao.execute("SELECT COUNT(*) AS quantidade FROM idoso").fetchone()["quantidade"]
print("Idosos recuperados após reabrir:", quantidade)
print("Idoso recuperado:", idoso_dao.buscar(dados.idosos[0].id_idoso))
print("Alerta recuperado:", alerta_dao.buscar(dados.alertas[0].id_alerta))
assert quantidade == len(dados.idosos)

# Nenhuma chave estrangeira quebrada e arquivo íntegro.
print("foreign_key_check:", conexao.execute("PRAGMA foreign_key_check").fetchall())
print("integrity_check:", conexao.execute("PRAGMA integrity_check").fetchone()[0])
assert conexao.execute("PRAGMA foreign_key_check").fetchall() == []
assert conexao.execute("PRAGMA integrity_check").fetchone()[0] == "ok"

# %% fechar
banco.fechar()
print("Conexão encerrada.")
