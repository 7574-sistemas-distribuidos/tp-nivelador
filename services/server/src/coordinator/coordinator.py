import queue

import logger

#objeto que usamos para propagar el cierre de recursos 
SHUTDOWN = object()


class Coordinator:
    def __init__(self, agency_quorum_min: int, lottery, lottery_lock) -> None:
        self.agency_quorum_min = agency_quorum_min
        self.response_channel = queue.Queue()
        self.clients_channels = {} 
        self.lottery = lottery
        self.lottery_lock = lottery_lock

    def get_channel(self):
        """canal por el que los hilos de los clientes se registran 
        con agency-id y su propio channel, y por el que llega el aviso de shutdown"""
        return self.response_channel

    def start(self):
        """loop del coordinador: registra agencias hasta cumplir con el quorum minimo 
        y comienza el sorteo. si recibe shutdown, lo reenvia las agencias"""
        while True:
            msg = self.response_channel.get()

            if msg == SHUTDOWN:
                clients = self.clients_channels.values() 
                for client_channel in clients:
                    client_channel.put(SHUTDOWN)
                break

            agency_id, client_channel = msg
            logger.info("coordinator", logger.LogResult.in_progress, "new agency registered", agency_id)
            self.clients_channels[agency_id] = client_channel

            if len(self.clients_channels) >= self.agency_quorum_min:
                self._run_lottery()

    def _run_lottery(self):
        """ejecuta el sorteo sobre las apuestas de las agencias que 
        cubrieron el minimo, calcula los ganadores sobre estas agencias, 
        se les envia por su channel correspondiente y se limpia el 
        registro para la proxima ronda"""
        logger.info("coordinator", logger.LogResult.success, "quorum reached")
        with self.lottery_lock:
            bets = list(self.lottery.load_bets())

        winners_by_agency = {
                    agency_id: []
                    for agency_id in self.clients_channels
                }

        for bet in bets: 
            if bet.agency_id in self.clients_channels and self.lottery.has_won(bet):
                winners_by_agency[bet.agency_id].append(bet)

        for agency_id, client_channel in self.clients_channels.items(): 
            client_channel.put(winners_by_agency[agency_id])

        self.clients_channels.clear()