from .Singleton import conexao
from .classes import *  

class ILPDAO:
    def __init__(self):
        self.conexao = conexao

    def inserir(self, ilp: ILP):
        sql = """
        INSERT INTO ilp (id_ilp, nome, endereco)
        VALUES (?, ?, ?)
        """
        valores = (ilp.id_ilp, ilp.nome, ilp.endereco)
        self.conexao.execute(sql, valores)
        self.conexao.commit()

    def buscar_por_id(self, id_ilp: int):
        sql = "SELECT * FROM ilp WHERE id_ilp = ?"
        linha = self.conexao.execute(sql, (id_ilp,)).fetchone()
        if linha is None:
            return None
        return ILP(linha["id_ilp"], linha["nome"], linha["endereco"])

    def buscar_por_nome(self, nome: str):
        sql = "SELECT * FROM ilp WHERE nome = ?"
        linha = self.conexao.execute(sql, (nome,)).fetchone()
        if linha is None:
            return None
        return ILP(linha["id_ilp"], linha["nome"], linha["endereco"])

    def atualizar(self, ilp: ILP):
        sql = """
        UPDATE ilp
        SET nome = ?, endereco = ?
        WHERE id_ilp = ?
        """
        valores = (ilp.id_ilp, ilp.nome, ilp.endereco)
        cursor = self.conexao.execute(sql, valores)
        self.conexao.commit()
        return cursor.rowcount

    def excluir(self, id_ilp: int):
        sql = "DELETE FROM ilp WHERE id_ilp = ?"
        cursor = self.conexao.execute(sql, (id_ilp,))
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
    
    def aniversario(self, id: int):
        sql = "SELECT idade FROM idosos WHERE id = ?"
        linha = self.conexao.execute(sql, (id,)).fetchone()
        if linha is None:
            return None
        idade_atualizada = linha["idade"] + 1
        sql_update = "UPDATE idosos SET idade = ? WHERE id = ?"
        self.conexao.execute(sql_update, (idade_atualizada, id))
        self.conexao.commit()
        return idade_atualizada
    
    def excluir(self, id: int):
        sql = "DELETE FROM idosos WHERE id = ?"
        cursor = self.conexao.execute(sql, (id,))
        self.conexao.commit()
        return cursor.rowcount
