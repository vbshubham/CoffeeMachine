import json
import logging
import unittest
from unittest import TestCase

from coffeeMachine.coffeeMachine import coffee_machine_decoder


class TestCoffeeMachine(TestCase):

    def setUp(self) -> None:
        logging.basicConfig(format='%(asctime)s %(threadName)s %(message)s', level=logging.DEBUG)
        with open("../resources/machine.json") as file_obj:
            self.machine = json.load(file_obj, object_hook=coffee_machine_decoder)

    def test_coffee_machine_decoder(self):
        self.assertEqual(len(self.machine.servers), 3)
        assert self.machine.beverage_factory is not None

    def test_runs_correctly(self):
        beverages = ["green_tea", "hot_tea", "black_tea", "hot_coffee"]
        for beverage in beverages:
            self.machine.request_beverage(beverage)
        self.machine.shut_down()
        self.assertTrue(True, "Coffee Machine should correctly")

    def test_serve(self):
        with self.assertLogs(level='INFO') as log:
            beverages = ["green_tea", "hot_tea", "black_tea", "hot_coffee"]
            for beverage in beverages:
                self.machine.request_beverage(beverage)
            self.machine.shut_down()
            self.assertEqual(len(log.output), len(beverages), "Each beverage should have a log")
            log_messages = map(lambda x: x.message, log.records)
            self.assertIn('green_tea cannot be prepared because green_mixture are not available', log_messages)

    def test_unknown_beverage(self):
        unsupported_beverage = '_'
        with self.assertRaises(ValueError) as context:
            self.machine.request_beverage(unsupported_beverage)
        self.machine.shut_down()
        self.assertTrue(unsupported_beverage in str(context.exception),
                        "Unsupported Beverage should throw exception")

    def tearDown(self) -> None:
        self.machine.shut_down()


if __name__ == "__main__":
    unittest.main(failfast=True)
