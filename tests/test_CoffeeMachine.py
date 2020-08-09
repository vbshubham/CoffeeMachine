import json
import unittest
from unittest import TestCase
from unittest.mock import create_autospec

from coffeeMachine.coffeeMachine import coffee_machine_decoder, log_running_low_items


class TestCoffeeMachine(TestCase):

    def setUp(self) -> None:
        with open("../resources/machine.json") as file_obj:
            self.machine = json.load(file_obj, object_hook=coffee_machine_decoder)

    def test_coffee_machine_decoder(self):
        self.assertEqual(len(self.machine.servers), 3)
        assert self.machine.beverage_factory is not None

    def test_machine_runs_correctly(self):
        beverages = ["green_tea", "hot_tea", "black_tea", "hot_coffee"]
        self.machine.get_notified_when_items_run_low(log_running_low_items)
        for beverage in beverages:
            self.machine.request_beverage(beverage)
        self.machine.shut_down()
        self.assertTrue(True, "Coffee Machine should correctly")

    def test_running_low_notification(self):
        def f(running_low_items):
            pass

        mock_f = create_autospec(f)
        self.machine.get_notified_when_items_run_low(mock_f)
        self.machine.request_beverage("black_tea")
        self.machine.request_beverage("black_tea")
        self.machine.shut_down()
        mock_f.assert_called()

    def test_request_beverage(self):
        with self.assertLogs(level='INFO') as log:
            beverages = ["green_tea", "hot_tea", "black_tea", "hot_coffee"]
            for beverage in beverages:
                self.machine.request_beverage(beverage)
            self.machine.shut_down()
            self.assertEqual(len(log.output), len(beverages), "Each beverage should have a log")
            log_messages = map(lambda x: x.message, log.records)
            self.assertIn('green_tea cannot be prepared because green_mixture are not available', log_messages)

    def test_refill(self):
        with self.assertLogs(level='INFO') as log:
            self.machine.refill({"green_mixture": 30})
            self.machine.request_beverage('green_tea')
            self.machine.shut_down()
            log_messages = map(lambda x: x.message, log.records)
            self.assertIn('green_tea is prepared', log_messages)

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
