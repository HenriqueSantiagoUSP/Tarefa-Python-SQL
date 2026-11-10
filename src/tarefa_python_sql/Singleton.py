import sqlite3
from pathlib import Path

ARQUIVO_BANCO = Path("projeto.db")
existia_antes = ARQUIVO_BANCO.exists()


class BancoSQLite:
    _instancia = None

    def __new__(cls, arquivo=ARQUIVO_BANCO):
        if cls._instancia is None:
            banco = super().__new__(cls)
            banco.arquivo = Path(arquivo)
            banco.conexao = sqlite3.connect(banco.arquivo)
            banco.conexao.row_factory = sqlite3.Row
            banco.conexao.execute("PRAGMA foreign_keys = ON")
            cls._instancia = banco
        return cls._instancia

    def fechar(self):
        self.conexao.close()
        type(self)._instancia = None

banco = BancoSQLite()
conexao = banco.conexao


if __name__ == "__main__":

    sql = "SELECT sqlite_version() AS versao, 2 + 2 AS resultado"
    resultado = conexao.execute(sql).fetchone()

    print("Arquivo já existia?", existia_antes)
    print("Arquivo existe agora?", ARQUIVO_BANCO.exists())
    print("SQLite:", resultado["versao"])
    print("Consulta de teste:", resultado["resultado"])
    print("Mesma conexão?", conexao is BancoSQLite().conexao)

    assert ARQUIVO_BANCO.exists()
    assert resultado["resultado"] == 4
    assert banco is BancoSQLite()
    assert conexao is BancoSQLite().conexao