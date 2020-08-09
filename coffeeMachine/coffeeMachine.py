import logging
import queue
import threading
import time
from collections import Counter
from queue import Queue
from threading import Lock, Event, Thread
from typing import List, Union

from coffeeMachine.beverageFactory import BeverageFactory

logging.basicConfig(format='%(asctime)s %(threadName)s %(message)s',
                    level=logging.DEBUG)


class CoffeeMachine:
    servers: List[Thread]  # list of servers who prepare beverage
    shut_down_event: Event  # event that marks all servers to stop
    tasks_q: Queue  # queue of user requests
    items_counter: Counter  # Counter of items remaining in the machine
    items_counter_lock: Lock  # lock for making updates to item counter atomic
    beverage_factory: BeverageFactory  # Factory for creating beverage objects
    minimum_to_serve_everything: Counter  # Minimum quantity of items required to serve all the beverages

    def __init__(self, initial_items_quantity: dict, beverage_desc: dict, outlet_cnt: int) -> None:
        """
        Initializes a coffee machine
        :param initial_items_quantity: dict of item name and value 
        :param beverage_desc: dict of beverage name and ingredients(dict of items and quantity)
        :param outlet_cnt: number of outlets in the machine
        """
        logging.debug("Setting up the coffee machine")
        self.beverage_factory = BeverageFactory(beverage_desc)
        self._items_counter = Counter(initial_items_quantity)
        self.items_counter_lock = threading.Lock()

        self.tasks_q = queue.Queue()
        self.shut_down_event = threading.Event()

        self.running_low_event = threading.Event()

        self.minimum_to_serve_everything = self.beverage_factory.get_minimum_ingredients()
        self.servers = []
        self._observers_of_running_low_items = []
        for outlet_id in range(outlet_cnt):
            # we name the threads like Outlet - 0,1,2...
            server = threading.Thread(target=self.prepare, name='Outlet-' + str(outlet_id))
            self.servers.append(server)
            server.start()

    logging.debug("Set up complete")

    @property
    def items_counter(self):
        return self._items_counter

    @items_counter.setter
    def items_counter(self, value):
        self._items_counter = value
        running_low = self.minimum_to_serve_everything - self._items_counter
        if running_low:
            for callback in self._observers_of_running_low_items:
                callback(running_low)

    def get_notified_when_items_run_low(self, callback):
        self._observers_of_running_low_items.append(callback)

    def prepare(self):
        """
        worker function for server. Keeps waiting for an element in task queue and serves or notifies the request
        """
        while not self.shut_down_event.is_set():
            try:
                beverage = self.tasks_q.get(timeout=1)
                logging.debug("Preparing " + beverage.name)
                with self.items_counter_lock:
                    missing_items = beverage.ingredients - self.items_counter
                    if missing_items:
                        logging.info(
                            "{beverage_name} cannot be prepared because {missing_items} are not available".format(
                                **{"beverage_name": beverage.name,
                                   'missing_items': ','.join(list(missing_items))
                                   }))
                        self.tasks_q.task_done()
                        continue

                    self.items_counter = self.items_counter - beverage.ingredients
                time.sleep(.1)
                logging.info(beverage.name + " is prepared")
                self.tasks_q.task_done()
            except queue.Empty:
                pass

    def request_beverage(self, beverage_name):
        """
        adds the requested beverage to task queue
        :param beverage_name: Name of the requested beverage
        """
        beverage = self.beverage_factory.get_beverage(beverage_name)
        self.tasks_q.put_nowait(beverage)
        logging.debug("Added " + beverage.name + " to queue")

    def shut_down(self):
        """
        Waits for the queue to be empty and sends shut down event to kill the servers
        """
        self.tasks_q.join()  # wait for all task to be done
        self.shut_down_event.set()  # shut down all threads
        for server in self.servers:
            server.join()
        logging.debug("all tasks done")

    def refill(self, item_quantity: dict) -> None:
        """
        Refill items in the machine
        :param item_quantity: dct of items and their amount
        """
        with self.items_counter_lock:
            self.items_counter += Counter(item_quantity)


def log_running_low_items(running_low_items):
    """
    function warns when items run low
    """
    logging.warning('Some items running low. Please add at least ' + str(
        running_low_items.most_common()) + " for everything to be served.")


def coffee_machine_decoder(dct: dict) -> Union[CoffeeMachine, dict]:
    """
    Transforms the dict object retrieved from the given json to machine input
    :return: a coffee machine object or the given dict if not valid format
    :type dct: dct object as provided in the example
    """
    try:
        machine = dct["machine"]
        outlet_cnt = machine["outlets"]["count_n"]
        total_items_quantity = machine["total_items_quantity"]
        beverage_dsc = machine["beverages"]
        return CoffeeMachine(total_items_quantity, beverage_dsc, outlet_cnt)
    except KeyError:
        return dct
