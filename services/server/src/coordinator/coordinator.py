
import queue
import logger
from lottery.lottery import Lottery


class Coordinator:
    def __init__(self, agency_quorum_min: int, storage_dir: str,queue: queue.Queue) -> None:
        self.agency_quorum_min = agency_quorum_min
        self.queue = queue
        self.lottery = Lottery(storage_dir)

    def start(self):
        logger.info("coordinator", logger.LogResult.in_progress, "start", "Starting coordinator")
        ready_agencies = {}
        while True:
            try:
                action, payload = self.queue.get()
                if action == "STORE_BETS":
                    logger.info("coordinator", logger.LogResult.in_progress, "store-bets", f"Storing {len(payload)} bets")
                    self.lottery.store_bets(payload)
                    logger.info("coordinator", logger.LogResult.success, "store-bets", f"Stored {len(payload)} bets")
                elif action == "AGENCY_SENT_ALL_BETS":
                    agency_id, reading_queue = payload
                    logger.info("coordinator", logger.LogResult.in_progress, "agency-sent-all-bets", f"Agency {agency_id} sent all bets")
                    ready_agencies[agency_id] = reading_queue

                    if len(ready_agencies) >= self.agency_quorum_min:
                        logger.info("coordinator", logger.LogResult.in_progress, "quorum-reached", f"Quorum reached with {len(ready_agencies)} agencies")
                
                        bets = list(self.lottery.load_bets())
                    
        
                        agency_winners = {aid: [] for aid in ready_agencies}
                        for bet in bets:
                            if bet.agency_id in agency_winners and self.lottery.has_won(bet):
                                agency_winners[bet.agency_id].append(bet)
                    
                      
                        for aid, client_ch in ready_agencies.items():
                            client_ch.put(agency_winners[aid])

            except Exception as e:
                logger.error("coordinator", logger.LogResult.failure, "error", f"Error in coordinator: {e}")



def start_coordinator(agency_quorum_min: int, storage_dir: str, queue: queue.Queue):
    coordinator = Coordinator(agency_quorum_min, storage_dir, queue)
    coordinator.start()