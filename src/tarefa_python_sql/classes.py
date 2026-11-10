from datetime import datetime

class Idoso:  
    def __init(self, id_idoso : int, nome: str, idade : int, quarto : int ):
        self.id = id
        self.nome = nome
        self.idade = idade
        self.num_quarto = quarto

class Quarto:
    def __init(self, quarto : int, numero_de_camas : int, largura : float, comprimento:float ):
        self.num_quarto = quarto
        self.numero_de_camas = numero_de_camas
        self.largura = largura
        self.comprimento = comprimento
        
class HistoricoQuedas:
    def __init(self, id_idoso : int, data: datetime):
        self.id_idoso = id_idoso
        self.data = data
           
class HistoricoSensor:
    def __init(self, temperatura : float, status_da_porta : bool, presenca : bool, quarto : int, data : datetime):
        self.temperatura = f"{temperatura:.1f}"
        self.status_da_porta= status_da_porta
        self.presenca = presenca
        self.num_quarto = quarto
        self.data = data