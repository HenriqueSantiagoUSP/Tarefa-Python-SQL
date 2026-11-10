# Atividade: Python OO e SQLite

Banco SQLite do sistema de monitoramento de idosos em ILPIs, feito com classes, o padrão DAO, dados do Faker
e consultas com JOIN.

- **Entrega:** `Python_SQL_1682224_16872729_5797753.ipynb`. Roda do início ao fim e cria o próprio `projeto.db`.
- **Modelo:** `OO_SQLite_Exemplo_Atualizado.ipynb`, o exemplo da aula.

## Arquivos

O código fica em `src/tarefa_python_sql/`:

| Arquivo | Conteúdo |
|---|---|
| `Singleton.py` | `BancoSQLite`: uma conexão única para todos os DAOs, com `PRAGMA foreign_keys = ON` |
| `SQLs.py` | os `CREATE TABLE` (9 tabelas `STRICT`), os índices e `criar_tabelas()` |
| `classes.py` | as entidades e as conversões de data e hora |
| `classesDAO.py` | um DAO por tabela: CRUD em SQL parametrizado e as consultas com JOIN |
| `gerador_dados.py` | dados fictícios coerentes (Faker e `random` com semente fixa) |
| `demonstracao.py` | o roteiro inteiro: tabelas, dados, CRUD, injection, integridade, JOINs e persistência |

O notebook é **gerado** a partir desses módulos por `gerar_notebook.py`. Cada trecho `# %% <nome>` de um
módulo vira uma célula, e os textos ficam no gerador, então o notebook e os `.py` não divergem.

Para mudar o código, edite o `.py` e gere o notebook de novo. Com o `uv`, na raiz:

```bash
uv run python -m tarefa_python_sql
```

```bash
uv run python gerar_notebook.py
```

```bash
uv run jupyter nbconvert --to notebook --execute --inplace Python_SQL_1682224_16872729_5797753.ipynb
```

O primeiro comando roda o roteiro pelos módulos. Os outros dois geram o notebook e o executam, gravando as
saídas.

## Decisões do esquema

- **Ids artificiais:** `INTEGER PRIMARY KEY`, gerados pelo banco e devolvidos com `INSERT ... RETURNING`.
  O objeto nasce com id `None`, e o DAO preenche.
- **Ids que vêm de fora:** `TEXT`. São o MAC da pulseira, o id do alerta no MQTT, o `site` da ILPI, o `codigo`
  do quarto e o id do Telegram.
- **Datas:** `TEXT 'AAAA-MM-DD'`.
- **Instantes:** `TEXT 'AAAA-MM-DD HH:MM:SS'` em UTC, o formato do `CURRENT_TIMESTAMP`. O
  `CHECK (col IS date(col))` recusa formato errado e datas que não existem.
- **No Python:** `date` e `datetime` com fuso UTC. A conversão é explícita no DAO.
- **Tabelas `STRICT`:** o SQLite recusa um texto numa coluna `INTEGER`, como o PostgreSQL faria.
- **`historico_quarto`:** guarda períodos `[data_entrada, data_saida)`. Um índice parcial único garante no
  máximo um quarto atual por idoso, e a troca de quarto é uma transação.
- **`ON DELETE`:**
  - `SET NULL` onde o histórico deve sobreviver (alerta → idoso, pulseira e cuidador; pulseira → idoso);
  - `CASCADE` nas leituras de um sensor apagado;
  - o padrão, que bloqueia, no resto: um quarto ocupado não pode ser apagado.

No PostgreSQL, as mesmas ideias viram:
- ids: `GENERATED ALWAYS AS IDENTITY` + `RETURNING`;
- datas e instantes: `DATE` e `TIMESTAMPTZ`;
- `tipo` e `estado`: `ENUM` ou tabela de domínio.
