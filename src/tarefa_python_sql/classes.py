"""
Classes do domínio: cada uma representa uma tabela. As relações são objetos (um Quarto guarda a sua ILPI);
no banco elas viram chaves estrangeiras, e quem faz essa tradução são os DAOs.

O id de cada objeto é None até ele ser gravado: quem o define é o DAO, com o valor que o banco gerou.
"""

# %% datas
from datetime import date, datetime, timezone

# Formato dos instantes no banco: o mesmo do CURRENT_TIMESTAMP do SQLite, sempre em UTC.
FORMATO_INSTANTE = "%Y-%m-%d %H:%M:%S"


def instante_para_texto(momento: datetime | None) -> str | None:
    """datetime com fuso → 'AAAA-MM-DD HH:MM:SS' em UTC (o que vai para o banco)."""
    if momento is None:
        return None
    if momento.tzinfo is None:
        raise ValueError("use datetime com fuso horário, por exemplo timezone.utc")
    return momento.astimezone(timezone.utc).strftime(FORMATO_INSTANTE)


def texto_para_instante(texto: str | None) -> datetime | None:
    """'AAAA-MM-DD HH:MM:SS' (UTC) → datetime com fuso UTC (o que volta do banco)."""
    if texto is None:
        return None
    return datetime.strptime(texto, FORMATO_INSTANTE).replace(tzinfo=timezone.utc)


def data_para_texto(dia: date | None) -> str | None:
    return None if dia is None else dia.isoformat()


def texto_para_data(texto: str | None) -> date | None:
    return None if texto is None else date.fromisoformat(texto)


# %% classes_base
from abc import ABC, abstractmethod


class Entidade(ABC):
    """Base de todas as entidades: guarda o id, que só o DAO define, uma única vez."""

    def __init__(self, id_entidade=None):
        self._id = id_entidade

    def _definir_id(self, valor):
        if self._id is not None:
            raise ValueError(f"{type(self).__name__} já tem id ({self._id})")
        self._id = valor

    @abstractmethod
    def to_dict(self) -> dict:
        pass


class Pessoa(Entidade):
    """Idosos e cuidadores são pessoas: têm um nome."""

    def __init__(self, nome: str, id_pessoa: int | None = None):
        super().__init__(id_pessoa)
        self.nome = nome

    def __repr__(self):
        return f"{type(self).__name__}(id={self._id}, nome={self.nome!r})"


# %% classes_local
class ILPI(Entidade):
    def __init__(self, nome: str, site: str, endereco: str, id_ilpi: int | None = None):
        super().__init__(id_ilpi)
        self.nome = nome
        self.site = site
        self.endereco = endereco

    @property
    def id_ilpi(self) -> int | None:
        return self._id

    def to_dict(self) -> dict:
        return {"id_ilpi": self.id_ilpi, "nome": self.nome, "site": self.site, "endereco": self.endereco}

    def __repr__(self):
        return f"ILPI(id={self.id_ilpi}, site={self.site!r})"


class Quarto(Entidade):
    def __init__(self, ilpi: ILPI, codigo: str, capacidade: int = 1, id_quarto: int | None = None):
        super().__init__(id_quarto)
        if capacidade < 1:
            raise ValueError("a capacidade do quarto deve ser de pelo menos 1")
        self.ilpi = ilpi
        self.codigo = codigo
        self.capacidade = capacidade

    @property
    def id_quarto(self) -> int | None:
        return self._id

    @property
    def topico(self) -> str:
        """Prefixo dos tópicos MQTT que o hub deste quarto publica."""
        return f"idoso/{self.ilpi.site}/{self.codigo}"

    def to_dict(self) -> dict:
        return {"id_quarto": self.id_quarto, "id_ilpi": self.ilpi.id_ilpi, "codigo": self.codigo,
                "capacidade": self.capacidade}

    def __repr__(self):
        return f"Quarto(id={self.id_quarto}, topico={self.topico!r})"


TIPOS_SENSOR = ("porta", "presenca", "temperatura")   # os mesmos do CHECK da tabela sensor


class Sensor(Entidade):
    def __init__(self, quarto: Quarto, tipo: str, lugar: str, modelo: str, id_sensor: int | None = None):
        super().__init__(id_sensor)
        if tipo not in TIPOS_SENSOR:
            raise ValueError(f"tipo de sensor desconhecido: {tipo!r}")
        self.quarto = quarto
        self.tipo = tipo
        self.lugar = lugar
        self.modelo = modelo

    @property
    def id_sensor(self) -> int | None:
        return self._id

    @property
    def topico(self) -> str:
        """Tópico MQTT do sensor, como em docs/protocolo.md do projeto."""
        if self.tipo == "porta":
            return f"{self.quarto.topico}/porta/{self.lugar}"
        return f"{self.quarto.topico}/{self.tipo}"

    def to_dict(self) -> dict:
        return {"id_sensor": self.id_sensor, "id_quarto": self.quarto.id_quarto, "tipo": self.tipo,
                "lugar": self.lugar, "modelo": self.modelo}

    def __repr__(self):
        return f"Sensor(id={self.id_sensor}, topico={self.topico!r})"


class EventoSensor(Entidade):
    """Uma leitura (temperatura) ou mudança de estado (porta, presença) de um sensor."""

    def __init__(self, sensor: Sensor, ocorrido_em: datetime, estado: str | None = None,
                 valor: float | None = None, id_evento: int | None = None):
        super().__init__(id_evento)
        if estado is None and valor is None:
            raise ValueError("o evento precisa de um estado ou de um valor")
        self.sensor = sensor
        self.ocorrido_em = ocorrido_em
        self.estado = estado
        self.valor = valor

    @property
    def id_evento(self) -> int | None:
        return self._id

    def to_dict(self) -> dict:
        return {"id_evento": self.id_evento, "id_sensor": self.sensor.id_sensor,
                "ocorrido_em": instante_para_texto(self.ocorrido_em), "estado": self.estado,
                "valor": self.valor}

    def __repr__(self):
        leitura = self.estado if self.estado is not None else f"{self.valor} °C"
        return f"EventoSensor(id={self.id_evento}, sensor={self.sensor.id_sensor}, {leitura})"


# %% classes_pessoas
class Idoso(Pessoa):
    def __init__(self, nome: str, data_nascimento: date, quarto: Quarto | None = None,
                 id_idoso: int | None = None):
        super().__init__(nome, id_idoso)
        self.data_nascimento = data_nascimento
        self.quarto = quarto

    @property
    def id_idoso(self) -> int | None:
        return self._id

    def idade_em(self, dia: date) -> int:
        """Idade calculada a partir da data de nascimento (não é gravada no banco)."""
        aniversario_ja_passou = (dia.month, dia.day) >= (self.data_nascimento.month, self.data_nascimento.day)
        return dia.year - self.data_nascimento.year - (0 if aniversario_ja_passou else 1)

    @property
    def idade(self) -> int:
        return self.idade_em(date.today())

    def to_dict(self) -> dict:
        return {"id_idoso": self.id_idoso, "nome": self.nome,
                "data_nascimento": data_para_texto(self.data_nascimento),
                "id_quarto": self.quarto.id_quarto if self.quarto else None}


class Cuidador(Pessoa):
    def __init__(self, nome: str, ilpi: ILPI, telegram_id: str | None = None, id_cuidador: int | None = None):
        super().__init__(nome, id_cuidador)
        self.ilpi = ilpi
        self.telegram_id = telegram_id

    @property
    def id_cuidador(self) -> int | None:
        return self._id

    def to_dict(self) -> dict:
        return {"id_cuidador": self.id_cuidador, "id_ilpi": self.ilpi.id_ilpi, "nome": self.nome,
                "telegram_id": self.telegram_id}


# %% classes_vinculos
class Gadget(Entidade):
    """A pulseira. O id é o MAC (3 últimos bytes), então já nasce definido."""

    def __init__(self, id_gadget: str, idoso: Idoso | None = None):
        if len(id_gadget) != 6 or any(c not in "0123456789abcdef" for c in id_gadget):
            raise ValueError(f"id de pulseira inválido: {id_gadget!r} (6 dígitos hexadecimais minúsculos)")
        super().__init__(id_gadget)
        self.idoso = idoso

    @property
    def id_gadget(self) -> str:
        return self._id

    def to_dict(self) -> dict:
        return {"id_gadget": self.id_gadget, "id_idoso": self.idoso.id_idoso if self.idoso else None}

    def __repr__(self):
        dono = self.idoso.nome if self.idoso else "reserva"
        return f"Gadget(id={self.id_gadget!r}, {dono})"


class HistoricoQuarto(Entidade):
    """Período em que um idoso ocupou um quarto: [data_entrada, data_saida). Sem saída = quarto atual."""

    def __init__(self, idoso: Idoso, quarto: Quarto, data_entrada: date, data_saida: date | None = None,
                 id_registro: int | None = None):
        super().__init__(id_registro)
        if data_saida is not None and data_saida < data_entrada:
            raise ValueError("a saída não pode ser antes da entrada")
        self.idoso = idoso
        self.quarto = quarto
        self.data_entrada = data_entrada
        self.data_saida = data_saida

    @property
    def id_registro(self) -> int | None:
        return self._id

    @property
    def atual(self) -> bool:
        return self.data_saida is None

    def contem(self, dia: date) -> bool:
        return self.data_entrada <= dia and (self.data_saida is None or dia < self.data_saida)

    def to_dict(self) -> dict:
        return {"id_registro": self.id_registro, "id_idoso": self.idoso.id_idoso,
                "id_quarto": self.quarto.id_quarto, "data_entrada": data_para_texto(self.data_entrada),
                "data_saida": data_para_texto(self.data_saida)}

    def __repr__(self):
        fim = self.data_saida or "hoje"
        return f"HistoricoQuarto({self.idoso.nome!r} em {self.quarto.codigo}, {self.data_entrada} a {fim})"


TIPOS_ALERTA = ("queda", "saida_noturna", "banheiro_prolongado", "inatividade", "temperatura",
                "vestivel_offline", "bateria_baixa")            # os mesmos do CHECK da tabela alerta
ESTADOS_ALERTA = ("ativo", "resolvido", "cancelado")


class Alerta(Entidade):
    def __init__(self, id_mqtt: str, tipo: str, quarto: Quarto, inicio: datetime,
                 idoso: Idoso | None = None, gadget: Gadget | None = None, estado: str = "ativo",
                 fim: datetime | None = None, cuidador: Cuidador | None = None, id_alerta: int | None = None):
        super().__init__(id_alerta)
        if tipo not in TIPOS_ALERTA:
            raise ValueError(f"tipo de alerta desconhecido: {tipo!r}")
        if estado not in ESTADOS_ALERTA:
            raise ValueError(f"estado de alerta desconhecido: {estado!r}")
        self.id_mqtt = id_mqtt
        self.tipo = tipo
        self.quarto = quarto
        self.inicio = inicio
        self.idoso = idoso
        self.gadget = gadget
        self.estado = estado
        self.fim = fim
        self.cuidador = cuidador

    @property
    def id_alerta(self) -> int | None:
        return self._id

    @property
    def ativo(self) -> bool:
        return self.estado == "ativo"

    @property
    def duracao(self):
        """Do início ao fim (timedelta), ou None enquanto estiver ativo."""
        return None if self.fim is None else self.fim - self.inicio

    def resolver(self, cuidador: Cuidador, fim: datetime):
        """O cuidador atendeu: o alerta deixa de estar ativo."""
        if not self.ativo:
            raise ValueError(f"o alerta já está {self.estado}")
        if fim < self.inicio:
            raise ValueError("o fim não pode ser antes do início")
        self.estado, self.fim, self.cuidador = "resolvido", fim, cuidador

    def to_dict(self) -> dict:
        return {"id_alerta": self.id_alerta, "id_mqtt": self.id_mqtt, "tipo": self.tipo, "estado": self.estado,
                "inicio": instante_para_texto(self.inicio), "fim": instante_para_texto(self.fim),
                "id_quarto": self.quarto.id_quarto, "id_idoso": self.idoso.id_idoso if self.idoso else None,
                "id_gadget": self.gadget.id_gadget if self.gadget else None,
                "id_cuidador": self.cuidador.id_cuidador if self.cuidador else None}

    def __repr__(self):
        return f"Alerta(id={self.id_alerta}, {self.tipo}, {self.estado}, {self.quarto.codigo})"
