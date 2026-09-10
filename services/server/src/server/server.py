import os
import socket
import threading
import queue
import logger
import protocol
from lottery import Lottery, Bet


class Server:
    def __init__(
        self,
        server_host: str,
        server_port: int,
        agency_quorum_min: int = 1,
        storage_path: str = "bets.csv",
    ) -> None:
        self.server_host = server_host
        self.server_port = server_port
        self.agency_quorum_min = agency_quorum_min
        self.storage_path = storage_path
        if os.path.exists(self.storage_path):
            os.remove(self.storage_path)
        self.lottery = Lottery(self.storage_path)

        self.coordinator_queue = queue.Queue()
        self.is_running = True

    def _run_coordinator(self):
        """Hilo coordinador: dueño exclusivo del estado de agencias y de la lotería."""
        notified_agencies = set()
        pending_agencies = []
        quorum_reached = False
        winners_by_agency = {}

        while self.is_running:
            try:
                msg = self.coordinator_queue.get(timeout=1)
            except queue.Empty:
                continue

            if msg is None or msg[0] == "STOP":
                for _, reply_q in pending_agencies:
                    reply_q.put(None)
                break

            msg_type = msg[0]

            if msg_type == "STORE_BETS":
                _, bets, reply_q = msg
                try:
                    self.lottery.store_bets(bets)
                    reply_q.put(True)
                except Exception as e:
                    reply_q.put(e)

            elif msg_type == "END_BETS":
                _, agency_id, reply_q = msg
                notified_agencies.add(agency_id)

                if not quorum_reached and len(notified_agencies) >= self.agency_quorum_min:
                    quorum_reached = True
                    pending_agencies.append((agency_id, reply_q))
                    winners_map = {}
                    for bet in self.lottery.load_bets():
                        if self.lottery.has_won(bet):
                            winners_map.setdefault(bet.agency_id, []).append(
                                f"{bet.first_name},{bet.last_name},{bet.document},{bet.birthdate},{bet.number}"
                            )
                    winners_by_agency = {}
                    for aid, lines in winners_map.items():
                        winners_by_agency[aid] = "\n".join(lines).encode("utf-8") + b"\n"

                    for aid, q in pending_agencies:
                        q.put(winners_by_agency.get(aid, b""))
                    pending_agencies.clear()

                elif not quorum_reached:
                    pending_agencies.append((agency_id, reply_q))

                else:
                    reply_q.put(winners_by_agency.get(agency_id, b""))

            elif msg_type == "DISCONNECT":
                _, reply_q = msg
                pending_agencies = [
                    (aid, q) for aid, q in pending_agencies if q != reply_q
                ]

    def _handle_client(self, client_socket):
        action = "handle-client"
        message_amount = 0
        reply_queue = queue.Queue(maxsize=1)
        try:
            logger.info(action, logger.LogResult.in_progress)
            while self.is_running:
                msg_type, payload = protocol.recv_msg(client_socket)
                if msg_type is None:
                    logger.info(
                        action,
                        logger.LogResult.success,
                        "messages-amount",
                        message_amount,
                    )
                    return

                if msg_type == protocol.MSG_BET:
                    text = payload.decode("utf-8")
                    bets = []
                    for line in text.splitlines():
                        line = line.strip()
                        if not line:
                            continue
                        parts = line.split(",")
                        agency_id = int(parts[0])
                        first_name = parts[1]
                        last_name = parts[2]
                        document = int(parts[3])
                        birthdate = parts[4]
                        number = int(parts[5])
                        bets.append(
                            Bet(
                                agency_id,
                                first_name,
                                last_name,
                                document,
                                birthdate,
                                number,
                            )
                        )
                    if bets:
                        self.coordinator_queue.put(("STORE_BETS", bets, reply_queue))
                        res = reply_queue.get()
                        if isinstance(res, Exception):
                            raise res
                        message_amount += len(bets)
                    protocol.send_msg(client_socket, protocol.MSG_ACK)

                elif msg_type == protocol.MSG_END_BETS:
                    agency_id = int(payload.decode("utf-8").strip())
                    self.coordinator_queue.put(("END_BETS", agency_id, reply_queue))
                    winners_payload = reply_queue.get()
                    if winners_payload is not None:
                        protocol.send_msg(
                            client_socket, protocol.MSG_WINNERS, winners_payload
                        )
                    return

                else:
                    logger.warn("unknown-msg-type", logger.LogResult.fail, "type", msg_type)

        except Exception as e:
            logger.error(
                action, logger.LogResult.fail, "messages-amount", message_amount, "err", e
            )
        finally:
            self.coordinator_queue.put(("DISCONNECT", reply_queue))
            try:
                client_socket.close()
            except Exception:
                pass

    def run(self):
        action = "accept-connection"
        coordinator_thread = threading.Thread(target=self._run_coordinator, daemon=True)
        coordinator_thread.start()

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((self.server_host, self.server_port))
            server_socket.listen()
            while self.is_running:
                try:
                    logger.info(action, logger.LogResult.in_progress)
                    client_socket, _ = server_socket.accept()
                except Exception as e:
                    if not self.is_running:
                        break
                    logger.error(action, logger.LogResult.fail)
                    raise e
                logger.info(action, logger.LogResult.success)

                client_thread = threading.Thread(
                    target=self._handle_client, args=(client_socket,), daemon=True
                )
                client_thread.start()
