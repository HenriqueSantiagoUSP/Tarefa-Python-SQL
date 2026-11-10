"""
Monta o notebook de entrega a partir dos módulos de src/tarefa_python_sql/.

O código de cada célula é um trecho "# %% <nome>" de um módulo (as importações relativas, antes do primeiro
marcador, ficam de fora), então o notebook e os .py nunca divergem. Os textos explicativos ficam aqui.

    uv run python gerar_notebook.py
    uv run jupyter nbconvert --to notebook --execute --inplace Python_SQL_1682224_16872729_5797753.ipynb
"""

import base64
import re
from pathlib import Path

import nbformat

RAIZ = Path(__file__).resolve().parent
PACOTE = RAIZ / "src" / "tarefa_python_sql"
SAIDA = RAIZ / "Python_SQL_1682224_16872729_5797753.ipynb"
MARCADOR = re.compile(r"^# %% (\w+)\s*$", re.MULTILINE)


def trechos(modulo: str) -> dict[str, str]:
    texto = (PACOTE / f"{modulo}.py").read_text(encoding="utf-8")
    partes = MARCADOR.split(texto)            # [antes, nome1, corpo1, nome2, corpo2, ...]
    return {nome: corpo.strip("\n") for nome, corpo in zip(partes[1::2], partes[2::2])}


CODIGO = {}
for modulo in ("Singleton", "SQLs", "classes", "classesDAO", "gerador_dados", "demonstracao"):
    for nome, corpo in trechos(modulo).items():
        assert nome not in CODIGO, f"trecho repetido: {nome}"
        CODIGO[nome] = corpo

# Imagens embutidas no próprio .ipynb (anexo da célula de texto, em base64): o notebook não depende do arquivo.
# A sintaxe ![](attachment:...) funciona no Jupyter, no VS Code, no Colab e no nbconvert; um <img width=...> com
# anexo, não em todos. Por isso o tamanho na tela se ajusta reduzindo a própria imagem (LARGURA_DIAGRAMA_PX).
ANEXOS = {"diagrama_er.png": RAIZ / "diagrama_entidades-Entidade Relacional.drawio.png"}
LARGURA_DIAGRAMA_PX = 700
# Centralizada: as linhas em branco em volta fazem o Markdown de dentro do <div> ser interpretado.
DIAGRAMA = '<div align="center">\n\n![Diagrama entidade-relacionamento](attachment:diagrama_er.png)\n\n</div>'


def png_reduzido(caminho: Path, largura: int) -> bytes:
    """O PNG com no máximo `largura` pixels de largura (Lanczos), sem mexer no arquivo original."""
    from io import BytesIO

    from PIL import Image                    # grupo dev do pyproject (uv add --dev pillow)

    imagem = Image.open(caminho)
    if imagem.width > largura:
        altura = round(imagem.height * largura / imagem.width)
        imagem = imagem.resize((largura, altura), Image.Resampling.LANCZOS)
    saida = BytesIO()
    imagem.save(saida, format="PNG", optimize=True)
    return saida.getvalue()

CELULAS = [
    ("md", """# Python orientado a objetos e SQL com SQLite: banco do monitoramento de idosos

**Grupo:** Dimitri Garcia (1682224), Henrique Santiago (16872729) e Henrique Guimarães Margarido (5797753).

**Contexto.** O projeto integrativo do grupo é uma rede de sensores para monitorar idosos em ILPIs (Instituições
de Longa Permanência para Idosos):
- **em cada quarto**, um hub com ESP32 lê as portas (quarto e banheiro), a presença (PIR) e a temperatura;
- **cada idoso** usa uma pulseira que detecta quedas;
- **os alertas** (queda, saída noturna, banheiro prolongado...) chegam por MQTT e avisam os cuidadores.

Este notebook modela esse banco em SQLite: tabelas com chaves primárias e estrangeiras, classes Python para as
entidades, DAOs com CRUD em SQL parametrizado, dados fictícios com o Faker e consultas com `JOIN`. Ele segue o
exemplo da aula (Singleton, DAOs, SQL explícito, sem Pandas nem SQLAlchemy), com duas diferenças:
- **os ids são gerados pelo banco** e devolvidos com `INSERT ... RETURNING`, como no PostgreSQL que o projeto
  vai usar no fim;
- **as tabelas são `STRICT`**: o SQLite passa a recusar um texto numa coluna `INTEGER`.

O notebook roda do início ao fim sem nenhum arquivo externo: ele mesmo cria o `projeto.db`."""),
    ("md", "## Modelo entidade-relacionamento\n\n" + DIAGRAMA + """

| Tabela | Chave primária | Chaves estrangeiras | Observação |
|---|---|---|---|
| `ilpi` | `id_ilpi` | — | `site` é o `<site>` dos tópicos MQTT `idoso/<site>/<quarto>/...` |
| `cuidador` | `id_cuidador` | `id_ilpi` | `telegram_id` é texto: é identificador, não número |
| `quarto` | `id_quarto` | `id_ilpi` | `codigo` é o `<quarto>` do tópico; `UNIQUE(id_ilpi, codigo)` |
| `idoso` | `id_idoso` | `id_quarto` (quarto atual) | a idade não é gravada: é calculada da `data_nascimento` |
| `gadget` | `id_gadget` (MAC) | `id_idoso` (`UNIQUE`) | sem idoso = pulseira reserva |
| `sensor` | `id_sensor` | `id_quarto` | `tipo`: porta, presença ou temperatura |
| `evento_sensor` | `id_evento` | `id_sensor` | estado (porta, presença) ou valor (°C) |
| `historico_quarto` | `id_registro` | `id_idoso`, `id_quarto` | períodos `[data_entrada, data_saida)`; sem saída = quarto atual |
| `alerta` | `id_alerta` | `id_quarto`, `id_idoso`, `id_gadget`, `id_cuidador` | `estado`: ativo, resolvido ou cancelado |

**Datas.** O SQLite não tem tipo de data, então as datas ficam em `TEXT`, sempre no padrão ISO 8601:
- datas, como `'1940-05-17'`;
- instantes em UTC, como `'2026-11-01 03:00:00'`, o mesmo formato do `CURRENT_TIMESTAMP`.

Esse formato ordena certo como texto e funciona com `date()` e `julianday()`. No Python, viram `date` e
`datetime` com fuso UTC; o DAO faz a conversão."""),
    ("md", """## 1. Importações e conexão com o SQLite (Singleton)

`BancoSQLite()` sempre devolve a mesma instância enquanto a conexão está aberta. Assim, todos os DAOs
compartilham uma única conexão. No SQLite, as chaves estrangeiras vêm **desligadas**: o
`PRAGMA foreign_keys = ON` precisa ser executado em toda conexão nova."""),
    ("py", "singleton"),
    ("py", "conexao"),
    ("md", """## 2. Criação das tabelas

Cada `CREATE TABLE` define a chave primária, as chaves estrangeiras e as regras do domínio:
- `CHECK` para os valores possíveis e para o formato das datas;
- `UNIQUE` para o que não pode se repetir;
- um índice parcial `UNIQUE ... WHERE data_saida IS NULL`, que garante no máximo um quarto atual por idoso.

`ON DELETE` diz o que acontece com quem referencia uma linha apagada:
- **`SET NULL`:** o alerta continua no histórico se o idoso for excluído;
- **`CASCADE`:** as leituras de um sensor vão junto com ele;
- **o padrão** bloqueia a exclusão, por exemplo de um quarto ocupado.

**Para repetir a atividade:** `criar_tabelas` apaga e recria as tabelas. Numa aplicação real, os dados não
seriam apagados assim."""),
    ("py", "sql_tabelas"),
    ("py", "criar"),
    ("md", "**Diagnóstico:** as chaves estrangeiras de cada tabela, lidas do catálogo do próprio SQLite."),
    ("py", "chaves"),
    ("md", """## 3. Classes orientadas a objetos

As classes representam as entidades. As relações são **objetos**: um `Quarto` guarda a sua `ILPI`, e um
`Alerta` guarda o seu `Quarto`, o `Idoso` e a `Gadget`. No banco elas viram chaves estrangeiras, e quem faz a
tradução são os DAOs.

O id começa como `None` e só o DAO o define, com o valor gerado pelo banco. Depois ele não muda: é uma
propriedade somente leitura.

Primeiro, as funções de conversão de datas e horários usadas pelos DAOs."""),
    ("py", "datas"),
    ("md", "`Entidade` é a base de todas as classes. `Pessoa` (abstrata) é a base de `Idoso` e `Cuidador`."),
    ("py", "classes_base"),
    ("py", "classes_local"),
    ("py", "classes_pessoas"),
    ("py", "classes_vinculos"),
    ("md", """### Teste dos objetos, ainda sem banco

Os objetos funcionam na memória. A idade do idoso e a duração do alerta são calculadas, não gravadas.
`resolver()` muda o estado do alerta, e as classes validam os valores antes de chegar ao banco."""),
    ("py", "objetos"),
    ("md", """## 4. Classes DAO (Data Access Object)

Cada DAO grava e lê uma entidade com SQL escrito explicitamente:
- `inserir` (`INSERT ... RETURNING`), `buscar`, `listar`, `atualizar` (`UPDATE`) e `excluir` (`DELETE`);
- `_da_linha`, que monta o objeto a partir de uma linha do banco, buscando os objetos relacionados.

Todo valor externo entra por **parâmetro** (`?` ou `:nome`): os valores vão separados do SQL e nunca são
interpretados como comando. As consultas com `JOIN` devolvem dicionários, prontos para mostrar."""),
    ("py", "dao_base"),
    ("py", "dao_local"),
    ("py", "dao_pessoas"),
    ("md", """`GadgetDAO` usa o MAC como chave, sem `RETURNING`. `HistoricoQuartoDAO` grava os períodos em cada
quarto, e `AlertaDAO` usa parâmetros nomeados (`:tipo`, `:inicio`...), com o próprio `to_dict()` do alerta como
valores."""),
    ("py", "dao_vinculos"),
    ("md", """## 5. Dados fictícios com o Faker

O Faker gera nomes e endereços; o restante sai de um `random.Random` com semente fixa, numa janela de datas
fixa (01 a 03/11/2026, em UTC), então o resultado é sempre o mesmo. Os dados respeitam os relacionamentos:
- nenhum quarto passa da capacidade;
- cada pulseira é de um idoso (mais duas reservas);
- a queda cai no quarto em que o idoso estava **naquele dia**: um idoso muda de quarto no meio da janela;
- quem resolve um alerta é um cuidador da mesma ILPI."""),
    ("py", "try:\n    import faker\nexcept ImportError:      # no Colab é preciso instalar\n    %pip -q install Faker"),
    ("py", "gerador"),
    ("py", "gerar"),
    ("md", """### Gravando os objetos

A ordem respeita as chaves estrangeiras: primeiro o que é referenciado, depois quem referencia. Como os objetos
guardam os objetos relacionados, o DAO já encontra o id do pai, gerado pelo banco no `INSERT` anterior. Os
milhares de eventos dos sensores vão com `executemany` e um só `commit`."""),
    ("py", "gravar"),
    ("py", "contar"),
    ("md", """## 6. Operações de CRUD

### Idoso: Create, Read e Update

Uma idosa de teste entra num quarto com vaga. O `DELETE` dela fica para o fim desta seção, depois de ela ganhar
uma pulseira, mudar de quarto e ter um alerta."""),
    ("py", "crud_idoso"),
    ("md", "### Pulseira: Update (entregar a pulseira reserva)"),
    ("py", "crud_gadget"),
    ("md", """### Transação: mudar de quarto

A mudança tem três comandos que só fazem sentido juntos:
1. fechar o período atual no histórico;
2. abrir um período novo;
3. atualizar o quarto do idoso.

Dentro de `with conexao:` eles viram uma transação: ou valem os três (`COMMIT`), ou nenhum (`ROLLBACK`). A
regra de capacidade fica no Python, que recusa a mudança para um quarto cheio antes de gravar qualquer coisa."""),
    ("py", "transferir"),
    ("md", "### Alerta: CRUD completo"),
    ("py", "crud_alerta"),
    ("md", """### Quarto, sensor e evento: CRUD completo

Apagar o sensor apaga as leituras dele (`ON DELETE CASCADE`)."""),
    ("py", "crud_quarto"),
    ("md", """### Idoso: Delete

Excluir a idosa de teste afeta quem a referencia:
- **o histórico dela vai junto** (`CASCADE`);
- **a pulseira volta a ser reserva** (`SET NULL`)."""),
    ("py", "excluir_idoso"),
    ("md", """### SQL injection e consultas parametrizadas

Concatenar a entrada de um usuário no SQL pode mudar o sentido da consulta. Com parâmetro, a mesma entrada é só
um valor: nenhum idoso se chama `' OR 1=1 --`."""),
    ("py", "injection"),
    ("md", "### Integridade referencial\n\nUm quarto com idosos não pode ser excluído enquanto as chaves estrangeiras estiverem ativas."),
    ("py", "integridade"),
    ("md", """### Outras regras garantidas pelo banco

Cada tentativa abaixo viola uma regra do esquema e é recusada pelo SQLite com `IntegrityError`. Os comandos são
executados direto na conexão, sem passar pelas classes, que já recusariam alguns desses valores antes."""),
    ("py", "restricoes"),
    ("md", """## 7. Consultas com JOIN

As consultas estão nos DAOs. Cada uma é executada, mostrada e conferida contra os objetos em memória.

### 1. Idosos de uma ILPI, com quarto e pulseira

`idoso ⨝ quarto ⨝ ilpi`, com `LEFT JOIN gadget`: o idoso aparece mesmo sem pulseira."""),
    ("py", "join_idosos"),
    ("md", """### 2. Alertas ativos, com ILPI, quarto e idoso

`alerta ⨝ quarto ⨝ ilpi`, com `LEFT JOIN idoso`: num quarto duplo, o alerta do hub não diz qual idoso."""),
    ("py", "join_alertas"),
    ("md", "### 3. Últimos eventos dos sensores de um quarto\n\n`evento_sensor ⨝ sensor ⨝ quarto`, do mais recente para o mais antigo."),
    ("py", "join_eventos"),
    ("md", """### 4. Alertas resolvidos por cuidador e o tempo médio de atendimento

`alerta ⨝ cuidador ⨝ ilpi` com `GROUP BY`. O tempo sai de `julianday(fim) - julianday(inicio)`, que funciona
porque as datas estão no padrão ISO."""),
    ("py", "join_cuidadores"),
    ("md", """### 5. Quem estava no quarto quando o alerta aconteceu

`alerta ⨝ historico_quarto ⨝ idoso`, juntando pelo quarto **e** pelo período
(`data_entrada <= dia < data_saida`). É por isso que o histórico guarda períodos: o quarto atual do idoso não
diz onde ele estava antes da mudança."""),
    ("py", "join_historico"),
    ("md", "### 6. Temperatura média e máxima por quarto\n\n`evento_sensor ⨝ sensor ⨝ quarto ⨝ ilpi` com `GROUP BY`."),
    ("py", "join_temperatura"),
    ("md", """## 8. Persistência: fechar e reabrir

O Singleton é fechado e recriado, e a nova conexão lê o mesmo arquivo `projeto.db`: os registros continuam lá.
No fim, o SQLite confere que nenhuma chave estrangeira ficou quebrada e que o arquivo está íntegro."""),
    ("py", "persistencia"),
    ("py", "fechar"),
]


def main():
    nb = nbformat.v4.new_notebook()
    nb.metadata["kernelspec"] = {"display_name": "Python 3", "language": "python", "name": "python3"}
    nb.metadata["language_info"] = {"name": "python"}
    usados = set()
    for tipo, conteudo in CELULAS:
        if tipo == "md":
            anexos = {nome: {"image/png": base64.b64encode(png_reduzido(caminho, LARGURA_DIAGRAMA_PX)).decode("ascii")}
                      for nome, caminho in ANEXOS.items() if f"attachment:{nome}" in conteudo}
            celula = nbformat.v4.new_markdown_cell(conteudo)
            if anexos:
                celula["attachments"] = anexos
            nb.cells.append(celula)
        elif conteudo in CODIGO:
            nb.cells.append(nbformat.v4.new_code_cell(CODIGO[conteudo]))
            usados.add(conteudo)
        else:
            nb.cells.append(nbformat.v4.new_code_cell(conteudo))
    faltando = set(CODIGO) - usados
    assert not faltando, f"trechos dos módulos fora do notebook: {sorted(faltando)}"
    nbformat.validate(nb)
    with open(SAIDA, "w", encoding="utf-8", newline="\n") as arquivo:
        nbformat.write(nb, arquivo)
    print(f"{SAIDA.name}: {len(nb.cells)} células")


if __name__ == "__main__":
    main()
