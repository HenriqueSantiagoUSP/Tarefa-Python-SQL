"""
Conexão única com o SQLite (padrão Singleton): todos os DAOs compartilham a mesma conexão.

As células do notebook são os trechos entre os marcadores "# %%" (veja gerar_notebook.py).
"""

# %% singleton
import sqlite3
from pathlib import Path

ARQUIVO_BANCO = Path("projeto.db")


class BancoSQLite:
    """`BancoSQLite()` devolve sempre a mesma instância enquanto a conexão estiver aberta."""

    _instancia = None

    def __new__(cls, arquivo=ARQUIVO_BANCO):
        if cls._instancia is None:
            banco = super().__new__(cls)
            banco.arquivo = Path(arquivo)
            banco.conexao = sqlite3.connect(banco.arquivo)
            banco.conexao.row_factory = sqlite3.Row
            # No SQLite as chaves estrangeiras vêm desligadas: é preciso ligar em toda conexão.
            banco.conexao.execute("PRAGMA foreign_keys = ON")
            cls._instancia = banco
        return cls._instancia

    def fechar(self):
        self.conexao.close()
        type(self)._instancia = None
