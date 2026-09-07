import queue
import signal
import socket
import threading
import logger
import safe_socket
from protocol import read_expected, encode_ack, encode_winner, encode_end, WinnerMessage, BATCH, ACK
from lottery import Bet, Lottery
from coordinator import Coordinator,SHUTDOWN

class Server:
    def __init__(self, server_host: str, server_port: int, agency_quorum_min: int) -> None:
        self.server_host = server_host
        self.server_port = server_port
        self.lottery = Lottery("bets.csv")
        self.lottery_lock = threading.Lock()
        self.coordinator = Coordinator(agency_quorum_min, self.lottery, self.lottery_lock)
        self.shutdown_event = threading.Event()
        self.server_socket = None
        self._active_sockets = set()
        self._client_threads = []


    def _handle_client(self, client_socket):
        action = "handle-client"
        message_ammount = 0
        agency = None
        try:
            logger.info(action, logger.LogResult.in_progress)
            message_count, agency,  = self._receive_bets(client_socket)
            message_ammount += message_count

            winners = self._wait_for_winners(agency)

            if winners is None:
                return

            self._send_winners(client_socket, winners)
        except Exception as e:
            if self.shutdown_event.is_set():
                logger.info(action, logger.LogResult.in_progress,  "shutdown", True, "agency", agency)
            else:
                logger.error(action, logger.LogResult.fail, "agency", agency, "messages-amount", message_ammount)
                raise e
        finally:
            self._active_sockets.discard(client_socket)
            client_socket.close()

    def _send_winners(self, client_socket, winners):
        for winner in winners: 
            safe_socket.send_all(
                    client_socket,
                    encode_winner(WinnerMessage(
                        nombre=winner.first_name,
                        apellido=winner.last_name,
                        documento=winner.document,
                        cumpleanos=winner.birthdate,
                        number=winner.number,
                    )),
                )

            is_end, _ = read_expected(client_socket, ACK)
            if is_end:
                break

        safe_socket.send_all(client_socket, encode_end())


    def _wait_for_winners(self, agency):
        action = "wait-for-winners"
        client_channel = queue.Queue() 
        self.coordinator.get_channel().put((agency, client_channel))

        winners = client_channel.get()

        if winners == SHUTDOWN:
            logger.info(action, logger.LogResult.in_progress, "shutdown",True, "agency", agency)   
            return 

        return winners 
            
    def _receive_bets(self, client_socket):
        message_amount = 0
        while True:
            is_end, data = read_expected(client_socket, BATCH)
            if is_end:
                break
            agency, bet_msgs = data
            bets = [] 
            for bet in bet_msgs: 
                bets.append( Bet(agency, bet.nombre, bet.apellido, bet.documento, bet.cumpleanos, bet.number))

            with self.lottery_lock:
                self.lottery.store_bets(bets)

            message_amount += len(bets)
            safe_socket.send_all(client_socket, encode_ack())
        return message_amount,agency


    def run(self):
        action = "accept-connection"
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            self.server_socket = server_socket
            server_socket.bind((self.server_host, self.server_port))
            server_socket.listen()
            coordinator_thread = threading.Thread(target=self.coordinator.start, daemon=True)
            coordinator_thread.start()
            signal.signal(signal.SIGTERM, self._handle_sigterm)
            while True:
                try:
                    logger.info(action, logger.LogResult.in_progress)
                    client_socket, _ = server_socket.accept()
                except Exception as e:
                    if self.shutdown_event.is_set():
                        logger.info(action,logger.LogResult.in_progress,"shutdown",True)
                        break
                    logger.error(action, logger.LogResult.fail)
                    raise e
                logger.info(action, logger.LogResult.success)

                self._active_sockets.add(client_socket)
                client_thread = threading.Thread(target=self._handle_client, args=(client_socket,), daemon=True)
                self._client_threads.append(client_thread)
                client_thread.start()

            threads_to_join = list(self._client_threads)

            for client_thread in threads_to_join:
                client_thread.join()

            coordinator_thread.join()



    def _handle_sigterm(self, signum, frame): 
        self.shutdown_event.set()
        self.server_socket.close()

        sockets = list(self._active_sockets)
        for sock in sockets:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError: pass  
            except Exception as e:
                logger.error("shutdown", logger.LogResult.fail, "socket", sock, "error", e)

        self.coordinator.get_channel().put(SHUTDOWN)
