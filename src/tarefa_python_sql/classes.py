from datetime import datetime
#ja tem DAo
class ILPI:
    def __init__(self, id_ilpi : int, nome : str, endereco : str):
        self.__id_ilpi = id_ilpi
        self.nome = nome
        self.endereco = endereco

    @property
    def id_ilpi(self) -> int:
        return self.__id_ilpi
#ja tem DAO
class Cuidador:
    def __init__(self, id_cuidador : int, id_ilpi : int, nome : str, telegram_id : str):
        self.__id_cuidador = id_cuidador
        self.id_ilpi = id_ilpi
        self.nome = nome
        self.telegram_id = telegram_id

    @property
    def id_cuidador(self) -> int:
        return self.__id_cuidador
#ja tem DAO
class Quarto:
    def __init__(self, id_quarto : int, id_ilpi : int):
        self.__id_quarto = id_quarto
        self.id_ilpi = id_ilpi

    @property
    def id_quarto(self) -> int:
        return self.__id_quarto
#ja tem DAO
class Idoso:  
    def __init__(self, id_idoso : int, nome: str, data_nascimento : datetime.date, id_quarto : int ):
        self.__id_idoso = id_idoso
        self.nome = nome
        self.data_nascimento = data_nascimento
        self.id_quarto = id_quarto

    @property
    def id_idoso(self) -> int:
        return self.__id_idoso
#ja tem DAO
class Gadget:
    def __init__(self, id_gadget : str, id_idoso : int):
        self.__id_gadget = id_gadget
        self.id_idoso = id_idoso

    @property
    def id_gadget(self) -> str:
        return self.__id_gadget
#ja tem DAO
class Sensor:
    def __init__(self, id_sensor : int, tipo : str, id_quarto : int, lugar : str):
        self.__id_sensor = id_sensor
        self.tipo = tipo
        self.id_quarto = id_quarto
        self.lugar = lugar

    @property
    def id_sensor(self) -> int:
        return self.__id_sensor

class EventoSensor:
    def __init__(self, id_evento : int, id_sensor : int, timestamp : datetime.date, estado = "NULL", valor = "NULL"):
        self.__id_evento = id_evento
        self.id_sensor = id_sensor
        self.timestamp = timestamp
        self.estado = estado
        self.valor = valor

    @property
    def id_evento(self) -> int:
        return self.id_evento
# ja tem DAO
class HistoricoQuarto:
    def __init__(self, id_registro : int, id_idoso : int, id_quarto : int, tipo : str, data : datetime.date):
        self.__id_registro = id_registro
        self.id_idoso = id_idoso
        self.id_quarto = id_quarto
        self.tipo = tipo
        self.data = data

    @property
    def id_registro(self) -> int:
        return self.__id_registro

class Alerta:
    def __init__(self, id_alerta : int, id_mqtt : str, tipo : str, timestamp : datetime.date, id_quarto : int, id_idoso : int, id_gadget : str):
        self.__id_alerta = id_alerta
        self.id_mqtt = id_mqtt
        self.tipo = tipo
        self.timestamp = timestamp
        self.id_quarto = id_quarto
        self.id_idoso = id_idoso
        self.id_gadget = id_gadget

    @property
    def id_alerta(self) -> int:
        return self.__id_alerta
    