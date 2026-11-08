"""Specification-based safety net, written before application changes."""
import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from supplydesk.service import OrderService
from supplydesk.menu import run_menu


def items(product='notebook', quantity=2):
    return [{'product_id': product, 'quantity': quantity}]


class RegressionTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / 'state.json'
        self.service = OrderService(self.path)

    def test_normal_placement_and_history(self):
        order = self.service.place_order('regular', items())
        self.assertEqual((order['order_id'], order['status'], order['total_cents']),
                         ('ORD-0001', 'placed', 1000))
        self.assertEqual(self.service.catalog()[0]['stock'], 18)
        self.assertEqual(OrderService(self.path).list_orders(), [order])

    def test_quote_has_no_side_effects(self):
        before = self.service.store.load()
        self.service.quote('regular', items())
        self.assertFalse(self.path.exists())
        self.assertEqual(self.service.store.load(), before)
        self.service.place_order('regular', items())
        saved = self.path.read_bytes()
        self.service.quote('regular', items())
        self.assertEqual(self.path.read_bytes(), saved)

    def test_standard_delivery_boundary(self):
        for quantity, fee, total in [(3, 600, 10100), (4, 0, 10000)]:
            with self.subTest(quantity=quantity):
                quote = self.service.quote('regular', items('hoodie', 2) + items('notebook', quantity), 'delivery')
                self.assertEqual((quote['delivery_cents'], quote['total_cents']), (fee, total))
        quote = self.service.quote('student', items('hoodie', 2) + items('notebook', 4), 'delivery')
        self.assertEqual((quote['discount_cents'], quote['delivery_cents'], quote['total_cents']), (1000, 600, 9600))

    def test_student_discount_at_threshold(self):
        for operation in (self.service.quote, self.service.place_order):
            with self.subTest(operation=operation.__name__):
                result = operation('student', items('bag', 2))
                self.assertEqual((result['discount_cents'], result['total_cents']), (500, 4500))

    def test_student_discount_below_and_above_threshold(self):
        for request, discount in [(items('hoodie', 1), 0), (items('hoodie', 2), 800)]:
            self.assertEqual(self.service.quote('student', request)['discount_cents'], discount)

    def test_half_cent_rounding(self):
        # A controlled catalog fixture isolates rounding; no new catalog-editing feature.
        state = self.service.store.load()
        state['catalog'][0]['unit_price_cents'] = 5005
        self.service.store.save(state)
        quote = self.service.quote('student', items(quantity=1))
        self.assertEqual((quote['discount_cents'], quote['total_cents']), (501, 4504))

    def test_last_stock_and_quantity_limits(self):
        order = self.service.place_order('regular', items(quantity=20))
        self.assertEqual(order['total_cents'], 10000)
        self.assertEqual(self.service.catalog()[0]['stock'], 0)
        with self.assertRaises(ValueError):
            self.service.place_order('regular', items(quantity=1))
        state = self.service.store.load()
        state['catalog'][0]['stock'] = 100
        self.service.store.save(state)
        self.assertEqual(self.service.quote('regular', items(quantity=99))['subtotal_cents'], 49500)
        with self.assertRaises(ValueError):
            self.service.quote('regular', items(quantity=100))

    def test_invalid_requests_preserve_existing_state(self):
        self.service.place_order('regular', items(quantity=1))
        saved = self.path.read_bytes()
        requests = [('vip', items(), 'pickup'), ('regular', items(), 'drone'),
                    ('regular', [], 'pickup'), ('regular', None, 'pickup'),
                    ('regular', [None], 'pickup'), ('regular', [{}], 'pickup'),
                    ('regular', items('missing'), 'pickup')]
        requests += [('regular', items(quantity=q), 'pickup') for q in (0, -1, 100, True, 1.5, '2', 21)]
        for request in requests:
            for operation in (self.service.quote, self.service.place_order):
                with self.subTest(request=request, operation=operation.__name__):
                    with self.assertRaises(ValueError):
                        operation(*request)
                    self.assertEqual(self.path.read_bytes(), saved)
        self.assertEqual(self.service.place_order('regular', items(quantity=1))['order_id'], 'ORD-0002')

    def test_invalid_first_order_does_not_consume_id(self):
        with self.assertRaises(ValueError):
            self.service.place_order('regular', items(quantity=0))
        self.assertFalse(self.path.exists())
        self.assertEqual(self.service.catalog()[0]['stock'], 20)
        self.assertEqual(self.service.list_orders(), [])
        order = self.service.place_order('regular', items(quantity=1))
        self.assertEqual(order['order_id'], 'ORD-0001')
        self.assertEqual(OrderService(self.path).list_orders(), [order])
        self.assertEqual(OrderService(self.path).catalog()[0]['stock'], 19)

    def test_duplicate_lines_cannot_exceed_combined_stock(self):
        for operation in (self.service.quote, self.service.place_order):
            with self.subTest(operation=operation.__name__):
                with self.assertRaises(ValueError):
                    operation('regular', items(quantity=11) + items(quantity=10))
                self.assertFalse(self.path.exists())
                self.assertEqual(self.service.catalog()[0]['stock'], 20)

    def test_valid_duplicate_lines(self):
        order = self.service.place_order('regular', items(quantity=10) + items(quantity=10))
        self.assertEqual(len(order['items']), 2)
        self.assertEqual(self.service.catalog()[0]['stock'], 0)
        self.service.cancel_order(order['order_id'])
        self.assertEqual(self.service.catalog()[0]['stock'], 20)

    def test_quote_and_order_agree(self):
        quote = self.service.quote('student', items('hoodie', 2), 'delivery')
        order = self.service.place_order('student', items('hoodie', 2), 'delivery')
        self.assertEqual({key: order[key] for key in quote}, quote)
        self.assertEqual([quote[key] for key in ('subtotal_cents', 'discount_cents', 'delivery_cents', 'total_cents')],
                         [8000, 800, 600, 7800])

    def test_placement_rechecks_stock_after_quote(self):
        self.service.quote('regular', items(quantity=20))
        self.service.place_order('regular', items(quantity=1))
        with self.assertRaises(ValueError):
            self.service.place_order('regular', items(quantity=20))
        self.assertEqual(self.service.catalog()[0]['stock'], 19)
        self.assertEqual(len(self.service.list_orders()), 1)

    def test_repeated_cancellation_is_idempotent(self):
        order = self.service.place_order('regular', items())
        cancelled = self.service.cancel_order(order['order_id'])
        saved = self.path.read_bytes()
        self.assertEqual(self.service.cancel_order(order['order_id']), cancelled)
        self.assertEqual(self.service.catalog()[0]['stock'], 20)
        self.assertEqual(self.path.read_bytes(), saved)

    def test_history_and_prices_survive_catalog_changes_and_cancel(self):
        first = self.service.place_order('student', items('hoodie', 2), 'delivery')
        second = self.service.place_order('regular', items())
        state = self.service.store.load()
        state['catalog'][2]['unit_price_cents'] = 1
        self.service.store.save(state)
        reopened = OrderService(self.path)
        self.assertEqual(reopened.get_order(first['order_id']), first)
        cancelled = reopened.cancel_order(first['order_id'])
        self.assertEqual(cancelled, dict(first, status='cancelled'))
        self.assertEqual(reopened.list_orders(), [cancelled, second])
        self.assertEqual(reopened.place_order('regular', items())['order_id'], 'ORD-0003')

    def test_unknown_order_and_malformed_save(self):
        for operation in (self.service.get_order, self.service.cancel_order):
            with self.assertRaises(ValueError):
                operation('ORD-9999')
            self.assertFalse(self.path.exists())
        self.service.place_order('regular', items())
        saved = self.path.read_bytes()
        with self.assertRaises(ValueError):
            self.service.cancel_order('ORD-9999')
        self.assertEqual(self.path.read_bytes(), saved)
        self.path.write_text('{broken')
        with self.assertRaises(ValueError):
            self.service.catalog()
        self.assertEqual(self.path.read_text(), '{broken')

    def menu(self, answers):
        output = io.StringIO()
        with patch('builtins.input', side_effect=answers), contextlib.redirect_stdout(output):
            self.assertEqual(run_menu(self.service), 0)
        return output.getvalue()

    def test_menu_defaults_decline_and_confirmation(self):
        output = self.menu(['3', '', 'notebook', '2', '', '', 'n', '0'])
        self.assertIn('Order not placed.', output)
        self.assertFalse(self.path.exists())
        output = self.menu(['3', '', 'notebook', '2', '', '', 'y', '6', 'ORD-0001', 'n', '0'])
        self.assertIn('Cancellation abandoned.', output)
        order = self.service.get_order('ORD-0001')
        self.assertEqual((order['customer_type'], order['fulfillment'], order['status']), ('regular', 'pickup', 'placed'))
        self.menu(['6', 'ORD-0001', 'y', '0'])
        self.assertEqual(self.service.catalog()[0]['stock'], 20)

    def test_menu_errors_and_exit(self):
        output = self.menu(['2', '', 'notebook', 'oops', 'notebook', '0', '', '', '9', '0'])
        self.assertIn('Please enter a whole number.', output)
        self.assertIn('Returning to the menu.', output)
        self.assertIn('Choose a number from 0 to 6.', output)
        self.assertFalse(self.path.exists())
        for exception in (EOFError, KeyboardInterrupt):
            self.assertIn('Goodbye.', self.menu([exception]))

    def test_cli_defaults_and_invalid_exit(self):
        command = [sys.executable, '-m', 'supplydesk', '--data', str(self.path)]
        result = subprocess.run(command + ['quote', '--item', 'notebook:2'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        quote = json.loads(result.stdout)
        self.assertEqual((quote['customer_type'], quote['fulfillment'], quote['total_cents']), ('regular', 'pickup', 1000))
        for args in (['place', '--item', 'notebook:0'], ['quote', '--item', 'bad'], ['quote', '--item', 'notebook:2', '--fulfillment', 'drone']):
            rejected = subprocess.run(command + args, capture_output=True, text=True)
            self.assertEqual(rejected.returncode, 2)
            self.assertTrue(rejected.stderr)
        self.assertFalse(self.path.exists())
