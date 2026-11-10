"""
Dados fictícios com o Faker, coerentes com os relacionamentos:
- cada idoso ocupa um quarto sem passar da capacidade, e o histórico guarda os períodos em cada quarto;
- o alerta de queda vem da pulseira do idoso e cai no quarto em que ele estava naquele dia;
- quem resolve um alerta é um cuidador da mesma ILPI.

Tudo é gerado com semente fixa e numa janela de datas fixa (UTC), então o resultado é sempre o mesmo.
(Este arquivo se chamava faker.py: com esse nome, "from faker import Faker" pode importar ele mesmo.)
"""

from .classes import (TIPOS_ALERTA, Alerta, Cuidador, EventoSensor, Gadget, HistoricoQuarto, Idoso, ILPI, Quarto,
                      Sensor)

# %% gerador
import math
import random
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from faker import Faker

SEMENTE = 42
INICIO_DADOS = datetime(2026, 11, 1, tzinfo=timezone.utc)    # começo da janela de eventos e alertas
DIAS_DE_DADOS = 3
ILPIS = [("ILPI Butantã", "butanta"), ("Residencial Vila Sônia", "vila_sonia")]
QUARTOS_POR_ILPI = 6
CUIDADORES_POR_ILPI = 3
SENSORES_POR_QUARTO = [("porta", "quarto", "MC-38"), ("porta", "banheiro", "MC-38"),
                       ("presenca", "quarto", "HC-SR501"), ("temperatura", "quarto", "LM35DZ")]
PULSEIRAS_RESERVA = 2
N_ALERTAS = 40


@dataclass
class DadosFicticios:
    ilpis: list
    quartos: list
    sensores: list
    cuidadores: list
    idosos: list
    gadgets: list
    historicos: list
    eventos: list
    alertas: list
    quarto_quente: Quarto       # o quarto que passa de 28 °C (gera os alertas de temperatura)
    transferidos: list          # idosos que mudaram de quarto durante a janela


def gerar_dados() -> DadosFicticios:
    fake = Faker("pt_BR")
    fake.seed_instance(SEMENTE)
    rng = random.Random(SEMENTE)

    def nome_pessoa():
        return f"{fake.first_name()} {fake.last_name()}"

    # --- lugares: ILPIs, quartos e sensores --------------------------------------------------------------
    ilpis = [ILPI(nome, site, f"{fake.street_address()}, São Paulo - SP") for nome, site in ILPIS]
    quartos = [Quarto(ilpi, f"quarto{100 + n}", capacidade=rng.choice([1, 2, 2]))
               for ilpi in ilpis for n in range(1, QUARTOS_POR_ILPI + 1)]
    sensores = [Sensor(quarto, tipo, lugar, modelo)
                for quarto in quartos for tipo, lugar, modelo in SENSORES_POR_QUARTO]

    # --- pessoas ---------------------------------------------------------------------------------------
    cuidadores, telegrams = [], set()
    for ilpi in ilpis:
        for _ in range(CUIDADORES_POR_ILPI):
            telegram = str(rng.randint(10**8, 10**10))
            while telegram in telegrams:
                telegram = str(rng.randint(10**8, 10**10))
            telegrams.add(telegram)
            cuidadores.append(Cuidador(nome_pessoa(), ilpi, telegram))

    idosos, historicos = [], []
    for quarto in quartos:
        for _ in range(rng.randint(1, quarto.capacidade)):          # nunca passa da capacidade
            nascimento = date(rng.randint(1926, 1960), rng.randint(1, 12), rng.randint(1, 28))
            idoso = Idoso(nome_pessoa(), nascimento, quarto)
            entrada = date(2026, rng.randint(1, 9), rng.randint(1, 28))
            if rng.random() < 0.3:                                    # já morou em outro quarto da ILPI
                outros = [q for q in quartos if q.ilpi is quarto.ilpi and q is not quarto]
                antes = entrada - timedelta(days=rng.randint(60, 400))
                historicos.append(HistoricoQuarto(idoso, rng.choice(outros), antes, entrada))
            historicos.append(HistoricoQuarto(idoso, quarto, entrada))
            idosos.append(idoso)

    # Dois idosos mudam de quarto no 2.º dia da janela (para um quarto com vaga na mesma ILPI).
    dia_mudanca = (INICIO_DADOS + timedelta(days=1)).date()
    transferidos = []
    for idoso in rng.sample(idosos, 2):
        com_vaga = [q for q in quartos if q.ilpi is idoso.quarto.ilpi and q is not idoso.quarto
                    and sum(i.quarto is q for i in idosos) < q.capacidade]
        if not com_vaga:
            continue
        novo = rng.choice(com_vaga)
        atual = next(h for h in historicos if h.idoso is idoso and h.atual)
        atual.data_saida = dia_mudanca
        historicos.append(HistoricoQuarto(idoso, novo, dia_mudanca))
        idoso.quarto = novo
        transferidos.append(idoso)

    def quarto_em(idoso, dia):
        return next(h.quarto for h in historicos if h.idoso is idoso and h.contem(dia))

    def ocupantes_em(quarto, dia):
        return [h.idoso for h in historicos if h.quarto is quarto and h.contem(dia)]

    # --- pulseiras: uma por idoso, mais algumas reservas -----------------------------------------------
    macs = set()

    def novo_mac():
        while True:
            mac = f"{rng.getrandbits(24):06x}"
            if mac not in macs:
                macs.add(mac)
                return mac

    gadgets = [Gadget(novo_mac(), idoso) for idoso in idosos] + [Gadget(novo_mac()) for _ in range(PULSEIRAS_RESERVA)]
    pulseira_de = {g.idoso: g for g in gadgets if g.idoso is not None}

    # --- eventos dos sensores --------------------------------------------------------------------------
    quarto_quente = rng.choice(quartos)
    eventos = []
    for sensor in sensores:
        if sensor.tipo == "temperatura":
            base = 27.5 if sensor.quarto is quarto_quente else rng.uniform(21.0, 24.5)
            for k in range(DIAS_DE_DADOS * 48):                      # uma leitura a cada 30 min
                momento = INICIO_DADOS + timedelta(minutes=30 * k)
                hora = momento.hour + momento.minute / 60            # UTC; o pico é às 15 h de Brasília
                valor = base + 2.0 * math.sin(2 * math.pi * (hora - 12) / 24) + rng.gauss(0, 0.3)
                eventos.append(EventoSensor(sensor, momento, valor=round(valor, 1)))
            continue
        ligado, desligado = ("aberta", "fechada") if sensor.tipo == "porta" else ("detectada", "livre")
        vezes_por_dia = {"quarto": (6, 12), "banheiro": (4, 9)}.get(sensor.lugar, (6, 12))
        if sensor.tipo == "presenca":
            vezes_por_dia = (10, 20)
        for dia in range(DIAS_DE_DADOS):
            for _ in range(rng.randint(*vezes_por_dia)):
                comeco = INICIO_DADOS + timedelta(days=dia, seconds=rng.randint(0, 86400 - 3600))
                eventos.append(EventoSensor(sensor, comeco, estado=ligado))
                eventos.append(EventoSensor(sensor, comeco + timedelta(seconds=rng.randint(30, 1800)),
                                            estado=desligado))
    eventos.sort(key=lambda e: e.ocorrido_em)

    # --- alertas ---------------------------------------------------------------------------------------
    alertas, usados = [], set()
    pesos = {"queda": 30, "saida_noturna": 15, "banheiro_prolongado": 15, "inatividade": 10,
             "temperatura": 15, "vestivel_offline": 8, "bateria_baixa": 7}
    for seq, tipo in enumerate(rng.choices(TIPOS_ALERTA, weights=[pesos[t] for t in TIPOS_ALERTA], k=N_ALERTAS),
                               start=1):
        if tipo == "saida_noturna":                                 # à noite: 22 h às 6 h de Brasília
            dia = rng.randrange(DIAS_DE_DADOS)
            inicio = INICIO_DADOS + timedelta(days=dia, hours=rng.randint(1, 8), minutes=rng.randint(0, 59))
        else:
            inicio = INICIO_DADOS + timedelta(seconds=rng.randint(0, DIAS_DE_DADOS * 86400 - 3600))
        dia = inicio.date()
        if tipo in ("queda", "vestivel_offline", "bateria_baixa"):  # vêm da pulseira de um idoso
            idoso = rng.choice(idosos)
            gadget = pulseira_de[idoso]
            quarto = quarto_em(idoso, dia)
        else:                                                       # vêm do hub do quarto
            quarto = quarto_quente if tipo == "temperatura" else rng.choice(quartos)
            presentes = ocupantes_em(quarto, dia)
            idoso = presentes[0] if len(presentes) == 1 else None   # num quarto duplo, não dá para saber
            gadget = None
        # Formato do id no protocolo MQTT: <pulseira>-<seq> na queda; <tipo>-<início em s> nos demais.
        id_mqtt = f"{gadget.id_gadget}-{seq}" if tipo == "queda" else f"{tipo}-{int(inicio.timestamp())}"
        if (quarto, id_mqtt) in usados:
            continue
        usados.add((quarto, id_mqtt))
        alerta = Alerta(id_mqtt, tipo, quarto, inicio, idoso, gadget)
        sorte = rng.random()
        if tipo == "queda" and sorte < 0.15:                        # o idoso apertou "estou bem"
            alerta.estado, alerta.fim = "cancelado", inicio + timedelta(seconds=rng.randint(5, 15))
        elif sorte < 0.85:
            equipe = [c for c in cuidadores if c.ilpi is quarto.ilpi]
            alerta.resolver(rng.choice(equipe), inicio + timedelta(minutes=rng.randint(2, 40),
                                                                  seconds=rng.randint(0, 59)))
        alertas.append(alerta)
    alertas.sort(key=lambda a: a.inicio)

    return DadosFicticios(ilpis, quartos, sensores, cuidadores, idosos, gadgets, historicos, eventos, alertas,
                          quarto_quente, transferidos)
