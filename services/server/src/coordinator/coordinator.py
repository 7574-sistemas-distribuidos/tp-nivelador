
import queue
import logger
from lottery.lottery import Lottery


class Coordinator:
    def __init__(self, agency_quorum_min: int, storage_dir: str,queue: queue.Queue) -> None:
        self.agency_quorum_min = agency_quorum_min
        self.queue = queue
        self.lottery = Lottery(storage_dir)
        self.ready_agencies = {}

    def stop(self):
        logger.info("coordinator", logger.LogResult.in_progress, "stop", "Stopping coordinator")
        self.queue.put(("SHUTDOWN", None))
        for ready_queue in self.ready_agencies.values():
            ready_queue.put(("SHUTDOWN", None))

    def start(self):
        logger.info("coordinator", logger.LogResult.in_progress, "start", "Starting coordinator")
        while True:
            try:
                action, payload = self.queue.get()
                if action == "SHUTDOWN":
                    logger.info("coordinator", logger.LogResult.in_progress, "shutdown", "Received shutdown signal")
                    break
                if action == "STORE_BETS":
                    self.lottery.store_bets(payload)

                if action == "AGENCY_SENT_ALL_BETS":
                    agency_id, reading_queue = payload
                    logger.info("coordinator", logger.LogResult.in_progress, "agency-sent-all-bets", f"Agency {agency_id} sent all bets")
                    self.ready_agencies[agency_id] = reading_queue

                    if len(self.ready_agencies) >= self.agency_quorum_min:
                        logger.info("coordinator", logger.LogResult.in_progress, "quorum-reached", f"Quorum reached with {len(self.ready_agencies)} agencies")
                
                        bets = list(self.lottery.load_bets())
                    
        
                        agency_winners = {aid: [] for aid in self.ready_agencies}
                        for bet in bets:
                            if bet.agency_id in agency_winners and self.lottery.has_won(bet):
                                agency_winners[bet.agency_id].append(bet)
                    
                      
                        for aid, client_ch in self.ready_agencies.items():
                            client_ch.put(("WINNERS",agency_winners[aid]))

            except Exception as e:
                logger.error("coordinator", logger.LogResult.failure, "error", f"Error in coordinator: {e}")
