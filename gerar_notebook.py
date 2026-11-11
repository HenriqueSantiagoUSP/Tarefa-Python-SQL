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
    ("md", """# Banco de dados do monitoramento de idosos: Python OO e SQLite

**Grupo:** Dimitri Garcia (1682224), Henrique Santiago (16872729) e Henrique Guimarães Margarido (5797753).

Banco do projeto integrativo do grupo, que monitora idosos em ILPIs:
- cada quarto tem um hub com sensores de porta, presença e temperatura;
- cada idoso usa uma pulseira que detecta quedas;
- os alertas avisam os cuidadores.

| Requisito da atividade | Onde |
|---|---|
| SQLite com o módulo `sqlite3` | seção 1 |
| `CREATE TABLE` com chaves primárias e estrangeiras (9 tabelas relacionadas) | seção 2 |
| Classes que representam as entidades | seção 3 |
| Classes DAO com CRUD em SQL explícito e parametrizado | seção 4 |
| Dados fictícios com Faker, respeitando os relacionamentos | seção 5 |
| Demonstração do CRUD | seção 6 |
| Consultas com JOIN (6 consultas) | seção 7 |

O notebook roda do início ao fim sem arquivos externos e cria o próprio `projeto.db`.

> **Google Colab (nuvem):** o Faker não vem instalado. A primeira célula da seção 5 o instala com
> `%pip install Faker`, o que exige internet. Localmente, instale antes com `pip install Faker`."""),
    ("md", "## Modelo entidade-relacionamento\n\n" + DIAGRAMA + """

| Tabela | Chave primária | Chaves estrangeiras |
|---|---|---|
| `ilpi` | `id_ilpi` | — |
| `cuidador` | `id_cuidador` | `id_ilpi` |
| `quarto` | `id_quarto` | `id_ilpi` |
| `idoso` | `id_idoso` | `id_quarto` |
| `gadget` (pulseira) | `id_gadget` (MAC) | `id_idoso` |
| `sensor` | `id_sensor` | `id_quarto` |
| `evento_sensor` | `id_evento` | `id_sensor` |
| `historico_quarto` | `id_registro` | `id_idoso`, `id_quarto` |
| `alerta` | `id_alerta` | `id_quarto`, `id_idoso`, `id_gadget`, `id_cuidador` |

- **Ids:** gerados pelo banco e devolvidos com `INSERT ... RETURNING`.
- **Datas:** `TEXT` no padrão ISO 8601 (`AAAA-MM-DD`).
- **Instantes:** `TEXT` em UTC (`AAAA-MM-DD HH:MM:SS`)."""),
    ("md", """## 1. Conexão com o SQLite

A conexão é única (Singleton) e compartilhada por todos os DAOs, com as chaves estrangeiras ativadas."""),
    ("py", "singleton"),
    ("py", "conexao"),
    ("md", """## 2. Criação das tabelas

São 9 tabelas, com chaves primárias, chaves estrangeiras e restrições (`CHECK`, `UNIQUE`). `criar_tabelas`
recria tudo a cada execução."""),
    ("py", "sql_tabelas"),
    ("py", "criar"),
    ("md", "Chaves estrangeiras criadas:"),
    ("py", "chaves"),
    ("md", """## 3. Classes

Há uma classe por entidade, e as relações são objetos: um `Alerta` guarda o `Quarto`, o `Idoso` e a `Gadget`.
O id começa como `None` e é preenchido pelo DAO com o valor gerado pelo banco. Antes das classes vêm as
conversões de data usadas pelos DAOs."""),
    ("py", "datas"),
    ("py", "classes_base"),
    ("py", "classes_local"),
    ("py", "classes_pessoas"),
    ("py", "classes_vinculos"),
    ("md", "Teste das classes em memória:"),
    ("py", "objetos"),
    ("md", """## 4. Classes DAO

Há um DAO por tabela, com `inserir`, `buscar`, `listar`, `atualizar` e `excluir`. O SQL é escrito
explicitamente e é parametrizado (`?` ou `:nome`). As consultas com JOIN também estão nos DAOs."""),
    ("py", "dao_base"),
    ("py", "dao_local"),
    ("py", "dao_pessoas"),
    ("py", "dao_vinculos"),
    ("md", """## 5. Dados fictícios com Faker

Os dados são gerados com semente fixa e respeitam os relacionamentos:
- capacidade dos quartos;
- uma pulseira por idoso;
- cada alerta no quarto do idoso;
- o cuidador da mesma ILPI.

> **Google Colab:** rode a célula abaixo antes das demais. Ela instala o Faker (`%pip install Faker`) se ele
> ainda não estiver instalado, e precisa de internet."""),
    ("py", "try:\n    import faker\nexcept ImportError:      # no Colab é preciso instalar\n    %pip -q install Faker"),
    ("py", "gerador"),
    ("py", "gerar"),
    ("md", "Inserção no banco, na ordem das chaves estrangeiras, e contagem de cada tabela:"),
    ("py", "gravar"),
    ("py", "contar"),
    ("md", "## 6. CRUD\n\n### Idoso: Create, Read, Update"),
    ("py", "crud_idoso"),
    ("md", "### Pulseira: Update"),
    ("py", "crud_gadget"),
    ("md", "### Transferência de quarto (transação)"),
    ("py", "transferir"),
    ("md", "### Alerta: Create, Read, Update, Delete"),
    ("py", "crud_alerta"),
    ("md", "### Quarto, sensor e evento: Create, Read, Update, Delete"),
    ("py", "crud_quarto"),
    ("md", "### Idoso: Delete"),
    ("py", "excluir_idoso"),
    ("md", "## 7. Consultas com JOIN\n\n### 1. Idosos de uma ILPI, com quarto e pulseira"),
    ("py", "join_idosos"),
    ("md", "### 2. Alertas ativos, com ILPI, quarto e idoso"),
    ("py", "join_alertas"),
    ("md", "### 3. Últimos eventos dos sensores de um quarto"),
    ("py", "join_eventos"),
    ("md", "### 4. Alertas resolvidos por cuidador e tempo médio de atendimento"),
    ("py", "join_cuidadores"),
    ("md", "### 5. Quem estava no quarto quando o alerta aconteceu"),
    ("py", "join_historico"),
    ("md", "### 6. Temperatura média e máxima por quarto"),
    ("py", "join_temperatura"),
    ("md", "## 8. Persistência\n\nA conexão é fechada e reaberta, e os dados continuam no arquivo."),
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
