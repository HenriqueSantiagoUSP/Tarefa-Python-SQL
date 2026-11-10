from .Singleton import conexao
from .classes import *  

class ILPIDAO:
    def __init__(self):
        self.conexao = conexao

    def inserir(self, ilp: ILPI):
        sql = """
        INSERT INTO ilpi (id_ilpi, nome, endereco)
        VALUES (?, ?, ?)
        """
        valores = (ilp.id_ilpi, ilp.nome, ilp.endereco)
        self.conexao.execute(sql, valores)
        self.conexao.commit()

    def buscar_por_id(self, id_ilpi: int):
        sql = "SELECT * FROM ilpi WHERE id_ilpi = ?"
        linha = self.conexao.execute(sql, (id_ilpi,)).fetchone()
        if linha is None:
            return None
        return ILPI(linha["id_ilpi"], linha["nome"], linha["endereco"])

    def buscar_por_nome(self, nome: str):
        sql = "SELECT * FROM ilpi WHERE nome = ?"
        linha = self.conexao.execute(sql, (nome,)).fetchone()
        if linha is None:
            return None
        return ILPI(linha["id_ilpi"], linha["nome"], linha["endereco"])

    def atualizar(self, ilp: ILPI):
        sql = """
        UPDATE ilpi
        SET nome = ?, endereco = ?
        WHERE id_ilpi = ?
        """
        valores = (ilp.id_ilpi, ilp.nome, ilp.endereco)
        cursor = self.conexao.execute(sql, valores)
        self.conexao.commit()
        return cursor.rowcount

    def excluir(self, id_ilpi: int):
        sql = "DELETE FROM ilpi WHERE id_ilpi = ?"
        cursor = self.conexao.execute(sql, (id_ilpi,))
        self.conexao.commit()
        return cursor.rowcount

class IdosoDAO:
    def __init__(self):
        self.conexao = BancoSQLite().conexao

    def inserir(self, idoso: Idoso):
        sql = """
        INSERT INTO idosos (id, nome, idade, quarto)
        VALUES (?, ?, ?, ?)
        """
        valores = (idoso.id, idoso.nome, idoso.idade, idoso.quarto)
        self.conexao.execute(sql, valores)
        self.conexao.commit()

    def buscar(self, id: int):
        sql = "SELECT * FROM idosos WHERE id = ?"
        linha = self.conexao.execute(sql, (id,)).fetchone()
        if linha is None:
            return None
        return Idoso(linha["id"], linha["nome"], linha["idade"], linha["quarto"])


    def atualiazar_quarto(self, idoso: Idoso):
        sql = """
        UPDATE idosos
        SET quarto = ?
        WHERE id = ?
        """
        valores = (idoso.quarto, idoso.id)
        cursor = self.conexao.execute(sql, valores)
        self.conexao.commit()
        return cursor.rowcount
    
   
    
    def excluir(self, id: int):
        sql = "DELETE FROM idosos WHERE id = ?"
        cursor = self.conexao.execute(sql, (id,))
        self.conexao.commit()
        return cursor.rowcount

class CuidadorDAO:
    def __init__(self):
        self.conexao = BancoSQLite().conexao

    def inserir(self, cuidador: Cuidador):
        sql = """
        INSERT INTO cuidadores (id, nome, idade, quarto)
        VALUES (?, ?, ?, ?)
        """
        valores = (cuidador.id, cuidador.nome, cuidador.idade, cuidador.quarto)
        self.conexao.execute(sql, valores)
        self.conexao.commit()

    def atualizar_quarto(self, cuidador: Cuidador):
        sql = """
        UPDATE cuidadores
        SET quarto = ?
        WHERE id = ?
        """
        valores = (cuidador.quarto, cuidador.id)
        cursor = self.conexao.execute(sql, valores)
        self.conexao.commit()
        return cursor.rowcount

    def buscar(self, id: int):
        sql = "SELECT * FROM cuidadores WHERE id = ?"
        linha = self.conexao.execute(sql, (id,)).fetchone()
        if linha is None:
            return None
        return Cuidador(linha["id"], linha["nome"], linha["idade"], linha["quarto"])

    def excluir(self, id: int):
        sql = "DELETE FROM cuidadores WHERE id = ?"
        cursor = self.conexao.execute(sql, (id,))
        self.conexao.commit()
        return cursor.rowcount
class QuartoDAO:
    def __init__(self):
        self.conexao = BancoSQLite().conexao

    def inserir(self, quarto: Quarto):
        sql = """
        INSERT INTO quartos (id_quarto, id_ilpi)
        VALUES (?, ?)
        """
        valores = (quarto.id_quarto, quarto.id_ilpi)
        self.conexao.execute(sql, valores)
        self.conexao.commit()

    def buscar(self, id: int):
        sql = "SELECT * FROM quartos WHERE id_quarto = ?"
        linha = self.conexao.execute(sql, (id,)).fetchone()
        if linha is None:
            return None
        return Quarto(linha["id_quarto"], linha["id_ilpi"])

    def excluir(self, id: int):
        sql = "DELETE FROM quartos WHERE id_quarto = ?"
        cursor = self.conexao.execute(sql, (id,))
        self.conexao.commit()
        return cursor.rowcount
    
class GadgetDAO:
    def __init__(self):
        self.conexao = BancoSQLite().conexao

    def inserir(self, gadget: Gadget):
        sql = """
        INSERT INTO gadgets (id_gadget, id_idoso)
        VALUES (?, ?)
        """
        valores = (gadget.id_gadget, gadget.id_idoso)
        self.conexao.execute(sql, valores)
        self.conexao.commit()

    def buscar(self, id: str):
        sql = "SELECT * FROM gadgets WHERE id_gadget = ?"
        linha = self.conexao.execute(sql, (id,)).fetchone()
        if linha is None:
            return None
        return Gadget(linha["id_gadget"], linha["id_idoso"])

    def excluir(self, id: str):
        sql = "DELETE FROM gadgets WHERE id_gadget = ?"
        cursor = self.conexao.execute(sql, (id,))
        self.conexao.commit()
        return cursor.rowcount
    
class SensorDAO:
    def __init__(self):
        self.conexao = BancoSQLite().conexao

    def inserir(self, sensor: Sensor):
        sql = """
        INSERT INTO sensores (id, tipo, quarto, lugar)
        VALUES (?, ?, ?, ?)
        """
        valores = (sensor.id_sensor, sensor.tipo, sensor.id_quarto, sensor.lugar)
        self.conexao.execute(sql, valores)
        self.conexao.commit()

    def buscar(self, id: int):
        sql = "SELECT * FROM sensores WHERE id = ?"
        linha = self.conexao.execute(sql, (id,)).fetchone()
        if linha is None:
            return None
        return Sensor(linha["id_sensor"], linha["tipo"], linha["id_quarto"], linha["lugar"])

    def excluir(self, id: int):
        sql = "DELETE FROM sensores WHERE id = ?"
        cursor = self.conexao.execute(sql, (id,))
        self.conexao.commit()
        return cursor.rowcount
    
class HistoricoQuartoDAO:
    def __init__(self):
        self.conexao = BancoSQLite().conexao

    def inserir(self, historico: HistoricoQuarto):
        sql = """
        INSERT INTO historico_quartos (id_registro, id_idoso, id_quarto, tipo, data)
        VALUES (?, ?, ?, ?, ?)
        """
        valores = (historico.id, historico.idoso, historico.quarto, historico.tipo, historico.data)
        self.conexao.execute(sql, valores)
        self.conexao.commit()

    def buscar(self, id: int):
        sql = "SELECT * FROM historico_quartos WHERE id = ?"
        linha = self.conexao.execute(sql, (id,)).fetchone()
        if linha is None:
            return None
        return HistoricoQuarto(linha["id"], linha["idoso"], linha["quarto"], linha["data_entrada"], linha["data_saida"])

    def excluir(self, id: int):
        sql = "DELETE FROM historico_quartos WHERE id = ?"
        cursor = self.conexao.execute(sql, (id,))
        self.conexao.commit()

class EventoSensorDAO:
    def __init__(self):
        self.conexao = BancoSQLite().conexao

    def inserir(self, evento: EventoSensor):
        sql = """
        INSERT INTO eventos_sensores (id_evento, id_sensor, timestamp, estado, valor)
        VALUES (?, ?, ?, ?, ?)
        """
        valores = (evento.id_evento, evento.id_sensor, evento.timestamp, evento.estado, evento.valor)
        self.conexao.execute(sql, valores)
        self.conexao.commit()

    def buscar(self, id: int):
        sql = "SELECT * FROM eventos_sensores WHERE id_evento = ?"
        linha = self.conexao.execute(sql, (id,)).fetchone()
        if linha is None:
            return None
        return EventoSensor(linha["id_evento"], linha["id_sensor"], linha["timestamp"], linha["estado"], linha["valor"])

    def excluir(self, id: int):
        sql = "DELETE FROM eventos_sensores WHERE id_evento = ?"
        cursor = self.conexao.execute(sql, (id,))
        self.conexao.commit()
        return cursor.rowcount

class AlertaDAO:
    def __init__(self):
        self.conexao = BancoSQLite().conexao

    def inserir(self, alerta: Alerta):
        sql = """
        INSERT INTO alertas (id_alerta, id_mqtt, tipo, timestamp, id_quarto, id_idoso, id_gadget)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        valores = (alerta.id_alerta, alerta.id_mqtt, alerta.tipo, alerta.timestamp, alerta.id_quarto, alerta.id_idoso, alerta.id_gadget)
        self.conexao.execute(sql, valores)
        self.conexao.commit()

    def buscar(self, id: int):
        sql = "SELECT * FROM alertas WHERE id_alerta = ?"
        linha = self.conexao.execute(sql, (id,)).fetchone()
        if linha is None:
            return None
        return Alerta(linha["id_alerta"], linha["id_evento"], linha["mensagem"], linha["timestamp"])

    def excluir(self, id: int):
        sql = "DELETE FROM alertas WHERE id_alerta = ?"
        cursor = self.conexao.execute(sql, (id,))
        self.conexao.commit()
        return cursor.rowcount