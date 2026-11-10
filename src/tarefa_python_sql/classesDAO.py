
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