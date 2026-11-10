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
