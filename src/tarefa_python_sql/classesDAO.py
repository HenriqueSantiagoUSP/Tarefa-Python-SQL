"""
DAOs (Data Access Objects): cada classe grava e lê uma entidade com SQL escrito explicitamente.

- Todo valor que vem de fora entra por parâmetro (? ou :nome), nunca concatenado no SQL: evita SQL injection.
- inserir() usa INSERT ... RETURNING para receber o id gerado pelo banco e guardá-lo no objeto.
- _da_linha() monta o objeto a partir de uma linha do banco, buscando os objetos relacionados.
- As consultas com JOIN devolvem dicionários, prontos para mostrar.
"""

from .Singleton import BancoSQLite
from .classes import (ILPI, Alerta, Cuidador, EventoSensor, Gadget, HistoricoQuarto, Idoso, Quarto, Sensor,
                      data_para_texto, instante_para_texto, texto_para_data, texto_para_instante)

# %% dao_base
class DAO:
    """Base dos DAOs: todos usam a mesma conexão, a do Singleton."""

    def __init__(self):
        self.conexao = BancoSQLite().conexao

    def _inserir_e_obter_id(self, sql, valores):
        """Executa um INSERT ... RETURNING, confirma e devolve o id gerado pelo banco."""
        linhas = self.conexao.execute(sql, valores).fetchall()   # termina o comando antes do commit
        self.conexao.commit()
        return linhas[0][0]

    def _alterar(self, sql, valores):
        """Executa um UPDATE ou DELETE, confirma e devolve quantas linhas mudaram."""
        cursor = self.conexao.execute(sql, valores)
        self.conexao.commit()
        return cursor.rowcount


# %% dao_local
class ILPIDAO(DAO):
    @staticmethod
    def _da_linha(linha):
        return ILPI(linha["nome"], linha["site"], linha["endereco"], id_ilpi=linha["id_ilpi"])

    def inserir(self, ilpi: ILPI) -> int:
        sql = """
        INSERT INTO ilpi (nome, site, endereco)
        VALUES (?, ?, ?)
        RETURNING id_ilpi
        """
        ilpi._definir_id(self._inserir_e_obter_id(sql, (ilpi.nome, ilpi.site, ilpi.endereco)))
        return ilpi.id_ilpi

    def buscar(self, id_ilpi: int):
        sql = "SELECT * FROM ilpi WHERE id_ilpi = ?"
        linha = self.conexao.execute(sql, (id_ilpi,)).fetchone()
        return None if linha is None else self._da_linha(linha)

    def buscar_por_site(self, site: str):
        sql = "SELECT * FROM ilpi WHERE site = ?"
        linha = self.conexao.execute(sql, (site,)).fetchone()
        return None if linha is None else self._da_linha(linha)

    def listar(self):
        sql = "SELECT * FROM ilpi ORDER BY nome"
        return [self._da_linha(linha) for linha in self.conexao.execute(sql).fetchall()]

    def atualizar(self, ilpi: ILPI) -> int:
        sql = """
        UPDATE ilpi
        SET nome = ?, site = ?, endereco = ?
        WHERE id_ilpi = ?
        """
        return self._alterar(sql, (ilpi.nome, ilpi.site, ilpi.endereco, ilpi.id_ilpi))

    def excluir(self, id_ilpi: int) -> int:
        return self._alterar("DELETE FROM ilpi WHERE id_ilpi = ?", (id_ilpi,))


class QuartoDAO(DAO):
    @staticmethod
    def _da_linha(linha):
        ilpi = ILPIDAO().buscar(linha["id_ilpi"])
        return Quarto(ilpi, linha["codigo"], linha["capacidade"], id_quarto=linha["id_quarto"])

    def inserir(self, quarto: Quarto) -> int:
        sql = """
        INSERT INTO quarto (id_ilpi, codigo, capacidade)
        VALUES (?, ?, ?)
        RETURNING id_quarto
        """
        valores = (quarto.ilpi.id_ilpi, quarto.codigo, quarto.capacidade)
        quarto._definir_id(self._inserir_e_obter_id(sql, valores))
        return quarto.id_quarto

    def buscar(self, id_quarto: int):
        sql = "SELECT * FROM quarto WHERE id_quarto = ?"
        linha = self.conexao.execute(sql, (id_quarto,)).fetchone()
        return None if linha is None else self._da_linha(linha)

    def buscar_por_topico(self, site: str, codigo: str):
        """JOIN: acha o quarto pelo tópico MQTT idoso/<site>/<codigo>, como faria o gravador da central."""
        sql = """
        SELECT q.*
        FROM quarto AS q
        JOIN ilpi AS il ON il.id_ilpi = q.id_ilpi
        WHERE il.site = ? AND q.codigo = ?
        """
        linha = self.conexao.execute(sql, (site, codigo)).fetchone()
        return None if linha is None else self._da_linha(linha)

    def listar(self):
        sql = "SELECT * FROM quarto ORDER BY id_ilpi, codigo"
        return [self._da_linha(linha) for linha in self.conexao.execute(sql).fetchall()]

    def atualizar(self, quarto: Quarto) -> int:
        sql = """
        UPDATE quarto
        SET id_ilpi = ?, codigo = ?, capacidade = ?
        WHERE id_quarto = ?
        """
        valores = (quarto.ilpi.id_ilpi, quarto.codigo, quarto.capacidade, quarto.id_quarto)
        return self._alterar(sql, valores)

    def excluir(self, id_quarto: int) -> int:
        return self._alterar("DELETE FROM quarto WHERE id_quarto = ?", (id_quarto,))


class SensorDAO(DAO):
    @staticmethod
    def _da_linha(linha):
        quarto = QuartoDAO().buscar(linha["id_quarto"])
        return Sensor(quarto, linha["tipo"], linha["lugar"], linha["modelo"], id_sensor=linha["id_sensor"])

    def inserir(self, sensor: Sensor) -> int:
        sql = """
        INSERT INTO sensor (id_quarto, tipo, lugar, modelo)
        VALUES (?, ?, ?, ?)
        RETURNING id_sensor
        """
        valores = (sensor.quarto.id_quarto, sensor.tipo, sensor.lugar, sensor.modelo)
        sensor._definir_id(self._inserir_e_obter_id(sql, valores))
        return sensor.id_sensor

    def buscar(self, id_sensor: int):
        sql = "SELECT * FROM sensor WHERE id_sensor = ?"
        linha = self.conexao.execute(sql, (id_sensor,)).fetchone()
        return None if linha is None else self._da_linha(linha)

    def listar_por_quarto(self, id_quarto: int):
        sql = "SELECT * FROM sensor WHERE id_quarto = ? ORDER BY tipo, lugar"
        return [self._da_linha(linha) for linha in self.conexao.execute(sql, (id_quarto,)).fetchall()]

    def atualizar(self, sensor: Sensor) -> int:
        sql = """
        UPDATE sensor
        SET id_quarto = ?, tipo = ?, lugar = ?, modelo = ?
        WHERE id_sensor = ?
        """
        valores = (sensor.quarto.id_quarto, sensor.tipo, sensor.lugar, sensor.modelo, sensor.id_sensor)
        return self._alterar(sql, valores)

    def excluir(self, id_sensor: int) -> int:
        return self._alterar("DELETE FROM sensor WHERE id_sensor = ?", (id_sensor,))


class EventoSensorDAO(DAO):
    @staticmethod
    def _da_linha(linha):
        sensor = SensorDAO().buscar(linha["id_sensor"])
        return EventoSensor(sensor, texto_para_instante(linha["ocorrido_em"]), linha["estado"], linha["valor"],
                            id_evento=linha["id_evento"])

    def inserir(self, evento: EventoSensor) -> int:
        sql = """
        INSERT INTO evento_sensor (id_sensor, ocorrido_em, estado, valor)
        VALUES (?, ?, ?, ?)
        RETURNING id_evento
        """
        valores = (evento.sensor.id_sensor, instante_para_texto(evento.ocorrido_em), evento.estado, evento.valor)
        evento._definir_id(self._inserir_e_obter_id(sql, valores))
        return evento.id_evento

    def inserir_varios(self, eventos) -> int:
        """
        Grava muitos eventos de uma vez (executemany) com um só commit: bem mais rápido que um commit por linha.
        Sem RETURNING, os objetos ficam sem id; quem precisar do id usa inserir().
        """
        sql = """
        INSERT INTO evento_sensor (id_sensor, ocorrido_em, estado, valor)
        VALUES (?, ?, ?, ?)
        """
        valores = [(e.sensor.id_sensor, instante_para_texto(e.ocorrido_em), e.estado, e.valor) for e in eventos]
        with self.conexao:                 # uma transação: grava tudo ou nada
            self.conexao.executemany(sql, valores)
        return len(valores)

    def buscar(self, id_evento: int):
        sql = "SELECT * FROM evento_sensor WHERE id_evento = ?"
        linha = self.conexao.execute(sql, (id_evento,)).fetchone()
        return None if linha is None else self._da_linha(linha)

    def atualizar(self, evento: EventoSensor) -> int:
        sql = """
        UPDATE evento_sensor
        SET id_sensor = ?, ocorrido_em = ?, estado = ?, valor = ?
        WHERE id_evento = ?
        """
        valores = (evento.sensor.id_sensor, instante_para_texto(evento.ocorrido_em), evento.estado, evento.valor,
                   evento.id_evento)
        return self._alterar(sql, valores)

    def excluir(self, id_evento: int) -> int:
        return self._alterar("DELETE FROM evento_sensor WHERE id_evento = ?", (id_evento,))

    def ultimos_do_quarto(self, id_quarto: int, limite: int = 10):
        """JOIN: os últimos eventos de todos os sensores de um quarto."""
        sql = """
        SELECT e.ocorrido_em, q.codigo AS quarto, s.tipo, s.lugar, e.estado, e.valor
        FROM evento_sensor AS e
        JOIN sensor AS s ON s.id_sensor = e.id_sensor
        JOIN quarto AS q ON q.id_quarto = s.id_quarto
        WHERE q.id_quarto = ?
        ORDER BY e.ocorrido_em DESC, e.id_evento DESC
        LIMIT ?
        """
        return [dict(linha) for linha in self.conexao.execute(sql, (id_quarto, limite)).fetchall()]

    def temperatura_por_quarto(self):
        """JOIN + GROUP BY: média e máxima da temperatura de cada quarto."""
        sql = """
        SELECT il.site, q.codigo AS quarto, COUNT(*) AS leituras,
               ROUND(AVG(e.valor), 1) AS media, MAX(e.valor) AS maxima
        FROM evento_sensor AS e
        JOIN sensor AS s ON s.id_sensor = e.id_sensor
        JOIN quarto AS q ON q.id_quarto = s.id_quarto
        JOIN ilpi AS il ON il.id_ilpi = q.id_ilpi
        WHERE s.tipo = 'temperatura'
        GROUP BY il.site, q.id_quarto, q.codigo
        ORDER BY maxima DESC, il.site, q.codigo
        """
        return [dict(linha) for linha in self.conexao.execute(sql).fetchall()]


# %% dao_pessoas
class IdosoDAO(DAO):
    @staticmethod
    def _da_linha(linha):
        quarto = None if linha["id_quarto"] is None else QuartoDAO().buscar(linha["id_quarto"])
        return Idoso(linha["nome"], texto_para_data(linha["data_nascimento"]), quarto, id_idoso=linha["id_idoso"])

    def inserir(self, idoso: Idoso) -> int:
        sql = """
        INSERT INTO idoso (nome, data_nascimento, id_quarto)
        VALUES (?, ?, ?)
        RETURNING id_idoso
        """
        valores = (idoso.nome, data_para_texto(idoso.data_nascimento),
                   idoso.quarto.id_quarto if idoso.quarto else None)
        idoso._definir_id(self._inserir_e_obter_id(sql, valores))
        return idoso.id_idoso

    def buscar(self, id_idoso: int):
        sql = "SELECT * FROM idoso WHERE id_idoso = ?"
        linha = self.conexao.execute(sql, (id_idoso,)).fetchone()
        return None if linha is None else self._da_linha(linha)

    def buscar_por_nome(self, nome: str):
        sql = "SELECT * FROM idoso WHERE nome = ?"
        return [self._da_linha(linha) for linha in self.conexao.execute(sql, (nome,)).fetchall()]

    def listar(self):
        sql = "SELECT * FROM idoso ORDER BY nome"
        return [self._da_linha(linha) for linha in self.conexao.execute(sql).fetchall()]

    def atualizar(self, idoso: Idoso) -> int:
        sql = """
        UPDATE idoso
        SET nome = ?, data_nascimento = ?, id_quarto = ?
        WHERE id_idoso = ?
        """
        valores = (idoso.nome, data_para_texto(idoso.data_nascimento),
                   idoso.quarto.id_quarto if idoso.quarto else None, idoso.id_idoso)
        return self._alterar(sql, valores)

    def excluir(self, id_idoso: int) -> int:
        return self._alterar("DELETE FROM idoso WHERE id_idoso = ?", (id_idoso,))

    def transferir(self, idoso: Idoso, quarto_novo: Quarto, dia):
        """
        Muda o idoso de quarto. São três comandos que só fazem sentido juntos, então rodam numa transação:
        se um falhar, nenhum vale (ROLLBACK).
        """
        sql_ocupantes = "SELECT COUNT(*) FROM idoso WHERE id_quarto = ?"
        ocupantes = self.conexao.execute(sql_ocupantes, (quarto_novo.id_quarto,)).fetchone()[0]
        if ocupantes >= quarto_novo.capacidade:
            raise ValueError(f"{quarto_novo.codigo} está cheio ({ocupantes} de {quarto_novo.capacidade})")
        sql_fecha = """
        UPDATE historico_quarto
        SET data_saida = ?
        WHERE id_idoso = ? AND data_saida IS NULL
        """
        sql_abre = """
        INSERT INTO historico_quarto (id_idoso, id_quarto, data_entrada)
        VALUES (?, ?, ?)
        """
        sql_idoso = "UPDATE idoso SET id_quarto = ? WHERE id_idoso = ?"
        with self.conexao:                 # BEGIN ... COMMIT (ou ROLLBACK se der erro)
            self.conexao.execute(sql_fecha, (data_para_texto(dia), idoso.id_idoso))
            self.conexao.execute(sql_abre, (idoso.id_idoso, quarto_novo.id_quarto, data_para_texto(dia)))
            self.conexao.execute(sql_idoso, (quarto_novo.id_quarto, idoso.id_idoso))
        idoso.quarto = quarto_novo

    def listar_por_ilpi(self, site: str):
        """JOIN: os idosos de uma ILPI, com o quarto e a pulseira (se tiver)."""
        sql = """
        SELECT q.codigo AS quarto, i.id_idoso, i.nome, i.data_nascimento, g.id_gadget AS pulseira
        FROM idoso AS i
        JOIN quarto AS q ON q.id_quarto = i.id_quarto
        JOIN ilpi AS il ON il.id_ilpi = q.id_ilpi
        LEFT JOIN gadget AS g ON g.id_idoso = i.id_idoso
        WHERE il.site = ?
        ORDER BY q.codigo, i.nome
        """
        return [dict(linha) for linha in self.conexao.execute(sql, (site,)).fetchall()]


class CuidadorDAO(DAO):
    @staticmethod
    def _da_linha(linha):
        ilpi = ILPIDAO().buscar(linha["id_ilpi"])
        return Cuidador(linha["nome"], ilpi, linha["telegram_id"], id_cuidador=linha["id_cuidador"])

    def inserir(self, cuidador: Cuidador) -> int:
        sql = """
        INSERT INTO cuidador (id_ilpi, nome, telegram_id)
        VALUES (?, ?, ?)
        RETURNING id_cuidador
        """
        valores = (cuidador.ilpi.id_ilpi, cuidador.nome, cuidador.telegram_id)
        cuidador._definir_id(self._inserir_e_obter_id(sql, valores))
        return cuidador.id_cuidador

    def buscar(self, id_cuidador: int):
        sql = "SELECT * FROM cuidador WHERE id_cuidador = ?"
        linha = self.conexao.execute(sql, (id_cuidador,)).fetchone()
        return None if linha is None else self._da_linha(linha)

    def listar_por_ilpi(self, id_ilpi: int):
        sql = "SELECT * FROM cuidador WHERE id_ilpi = ? ORDER BY nome"
        return [self._da_linha(linha) for linha in self.conexao.execute(sql, (id_ilpi,)).fetchall()]

    def atualizar(self, cuidador: Cuidador) -> int:
        sql = """
        UPDATE cuidador
        SET id_ilpi = ?, nome = ?, telegram_id = ?
        WHERE id_cuidador = ?
        """
        valores = (cuidador.ilpi.id_ilpi, cuidador.nome, cuidador.telegram_id, cuidador.id_cuidador)
        return self._alterar(sql, valores)

    def excluir(self, id_cuidador: int) -> int:
        return self._alterar("DELETE FROM cuidador WHERE id_cuidador = ?", (id_cuidador,))


# %% dao_vinculos
class GadgetDAO(DAO):
    @staticmethod
    def _da_linha(linha):
        idoso = None if linha["id_idoso"] is None else IdosoDAO().buscar(linha["id_idoso"])
        return Gadget(linha["id_gadget"], idoso)

    def inserir(self, gadget: Gadget) -> str:
        """O id da pulseira vem do MAC, não do banco: aqui não precisa de RETURNING."""
        sql = """
        INSERT INTO gadget (id_gadget, id_idoso)
        VALUES (?, ?)
        """
        self._alterar(sql, (gadget.id_gadget, gadget.idoso.id_idoso if gadget.idoso else None))
        return gadget.id_gadget

    def buscar(self, id_gadget: str):
        sql = "SELECT * FROM gadget WHERE id_gadget = ?"
        linha = self.conexao.execute(sql, (id_gadget,)).fetchone()
        return None if linha is None else self._da_linha(linha)

    def buscar_do_idoso(self, id_idoso: int):
        sql = "SELECT * FROM gadget WHERE id_idoso = ?"
        linha = self.conexao.execute(sql, (id_idoso,)).fetchone()
        return None if linha is None else self._da_linha(linha)

    def listar_reservas(self):
        sql = "SELECT * FROM gadget WHERE id_idoso IS NULL ORDER BY id_gadget"
        return [self._da_linha(linha) for linha in self.conexao.execute(sql).fetchall()]

    def atualizar(self, gadget: Gadget) -> int:
        """Entrega a pulseira a outro idoso (ou a devolve, com idoso = None)."""
        sql = """
        UPDATE gadget
        SET id_idoso = ?
        WHERE id_gadget = ?
        """
        return self._alterar(sql, (gadget.idoso.id_idoso if gadget.idoso else None, gadget.id_gadget))

    def excluir(self, id_gadget: str) -> int:
        return self._alterar("DELETE FROM gadget WHERE id_gadget = ?", (id_gadget,))


class HistoricoQuartoDAO(DAO):
    @staticmethod
    def _da_linha(linha):
        idoso = IdosoDAO().buscar(linha["id_idoso"])
        quarto = QuartoDAO().buscar(linha["id_quarto"])
        return HistoricoQuarto(idoso, quarto, texto_para_data(linha["data_entrada"]),
                               texto_para_data(linha["data_saida"]), id_registro=linha["id_registro"])

    def inserir(self, registro: HistoricoQuarto) -> int:
        sql = """
        INSERT INTO historico_quarto (id_idoso, id_quarto, data_entrada, data_saida)
        VALUES (?, ?, ?, ?)
        RETURNING id_registro
        """
        valores = (registro.idoso.id_idoso, registro.quarto.id_quarto, data_para_texto(registro.data_entrada),
                   data_para_texto(registro.data_saida))
        registro._definir_id(self._inserir_e_obter_id(sql, valores))
        return registro.id_registro

    def buscar(self, id_registro: int):
        sql = "SELECT * FROM historico_quarto WHERE id_registro = ?"
        linha = self.conexao.execute(sql, (id_registro,)).fetchone()
        return None if linha is None else self._da_linha(linha)

    def listar_por_idoso(self, id_idoso: int):
        sql = "SELECT * FROM historico_quarto WHERE id_idoso = ? ORDER BY data_entrada"
        return [self._da_linha(linha) for linha in self.conexao.execute(sql, (id_idoso,)).fetchall()]

    def atualizar(self, registro: HistoricoQuarto) -> int:
        sql = """
        UPDATE historico_quarto
        SET id_idoso = ?, id_quarto = ?, data_entrada = ?, data_saida = ?
        WHERE id_registro = ?
        """
        valores = (registro.idoso.id_idoso, registro.quarto.id_quarto, data_para_texto(registro.data_entrada),
                   data_para_texto(registro.data_saida), registro.id_registro)
        return self._alterar(sql, valores)

    def excluir(self, id_registro: int) -> int:
        return self._alterar("DELETE FROM historico_quarto WHERE id_registro = ?", (id_registro,))


class AlertaDAO(DAO):
    @staticmethod
    def _da_linha(linha):
        quarto = QuartoDAO().buscar(linha["id_quarto"])
        idoso = None if linha["id_idoso"] is None else IdosoDAO().buscar(linha["id_idoso"])
        gadget = None if linha["id_gadget"] is None else GadgetDAO().buscar(linha["id_gadget"])
        cuidador = None if linha["id_cuidador"] is None else CuidadorDAO().buscar(linha["id_cuidador"])
        return Alerta(linha["id_mqtt"], linha["tipo"], quarto, texto_para_instante(linha["inicio"]), idoso, gadget,
                      linha["estado"], texto_para_instante(linha["fim"]), cuidador, id_alerta=linha["id_alerta"])

    def inserir(self, alerta: Alerta) -> int:
        sql = """
        INSERT INTO alerta (id_mqtt, tipo, estado, inicio, fim, id_quarto, id_idoso, id_gadget, id_cuidador)
        VALUES (:id_mqtt, :tipo, :estado, :inicio, :fim, :id_quarto, :id_idoso, :id_gadget, :id_cuidador)
        RETURNING id_alerta
        """
        valores = alerta.to_dict()         # parâmetros nomeados: as chaves do dicionário
        alerta._definir_id(self._inserir_e_obter_id(sql, valores))
        return alerta.id_alerta

    def buscar(self, id_alerta: int):
        sql = "SELECT * FROM alerta WHERE id_alerta = ?"
        linha = self.conexao.execute(sql, (id_alerta,)).fetchone()
        return None if linha is None else self._da_linha(linha)

    def atualizar(self, alerta: Alerta) -> int:
        sql = """
        UPDATE alerta
        SET id_mqtt = :id_mqtt, tipo = :tipo, estado = :estado, inicio = :inicio, fim = :fim,
            id_quarto = :id_quarto, id_idoso = :id_idoso, id_gadget = :id_gadget, id_cuidador = :id_cuidador
        WHERE id_alerta = :id_alerta
        """
        return self._alterar(sql, alerta.to_dict())

    def excluir(self, id_alerta: int) -> int:
        return self._alterar("DELETE FROM alerta WHERE id_alerta = ?", (id_alerta,))

    def listar_ativos(self):
        """JOIN: alertas ainda abertos, com a ILPI, o quarto, o idoso e a pulseira."""
        sql = """
        SELECT a.id_alerta, a.tipo, a.inicio, il.nome AS ilpi, q.codigo AS quarto,
               i.nome AS idoso, a.id_gadget AS pulseira
        FROM alerta AS a
        JOIN quarto AS q ON q.id_quarto = a.id_quarto
        JOIN ilpi AS il ON il.id_ilpi = q.id_ilpi
        LEFT JOIN idoso AS i ON i.id_idoso = a.id_idoso
        WHERE a.estado = 'ativo'
        ORDER BY a.inicio, a.id_alerta
        """
        return [dict(linha) for linha in self.conexao.execute(sql).fetchall()]

    def atendimentos_por_cuidador(self):
        """JOIN + GROUP BY: alertas resolvidos por cuidador e o tempo médio até a resolução."""
        sql = """
        SELECT c.nome AS cuidador, il.nome AS ilpi, COUNT(*) AS alertas,
               ROUND(AVG((julianday(a.fim) - julianday(a.inicio)) * 24 * 60), 1) AS minutos_em_media
        FROM alerta AS a
        JOIN cuidador AS c ON c.id_cuidador = a.id_cuidador
        JOIN ilpi AS il ON il.id_ilpi = c.id_ilpi
        WHERE a.estado = 'resolvido'
        GROUP BY c.id_cuidador, c.nome, il.nome
        ORDER BY alertas DESC, c.nome
        """
        return [dict(linha) for linha in self.conexao.execute(sql).fetchall()]

    def ocupantes_no_alerta(self, id_alerta: int):
        """
        JOIN com o histórico: quem estava no quarto no dia do alerta. É por isso que o histórico guarda
        períodos [data_entrada, data_saida): o quarto atual do idoso não diz onde ele estava antes.
        """
        sql = """
        SELECT a.id_alerta, a.tipo, a.inicio, q.codigo AS quarto, i.id_idoso, i.nome AS idoso
        FROM alerta AS a
        JOIN quarto AS q ON q.id_quarto = a.id_quarto
        JOIN historico_quarto AS h
             ON h.id_quarto = a.id_quarto
            AND h.data_entrada <= date(a.inicio)
            AND (h.data_saida IS NULL OR date(a.inicio) < h.data_saida)
        JOIN idoso AS i ON i.id_idoso = h.id_idoso
        WHERE a.id_alerta = ?
        ORDER BY i.nome
        """
        return [dict(linha) for linha in self.conexao.execute(sql, (id_alerta,)).fetchall()]
