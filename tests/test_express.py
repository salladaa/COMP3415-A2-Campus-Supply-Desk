"""Official CR-01 acceptance tests across the service and both terminal interfaces."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from supplydesk.service import OrderService


def item(product, quantity):
    return {'product_id': product, 'quantity': quantity}


class ExpressTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / 'state.json'
        self.service = OrderService(self.path)

    def command(self, *args, input=None):
        return subprocess.run([sys.executable, '-m', 'supplydesk', '--data', str(self.path), *args],
                              input=input, capture_output=True, text=True, timeout=10)

    def test_official_examples_quote_and_place(self):
        for customer, product, quantity, subtotal, discount, total in [
            ('regular', 'notebook', 2, 1000, 0, 2200),
            ('student', 'hoodie', 2, 8000, 800, 8400),
            ('regular', 'hoodie', 3, 12000, 0, 13200),
        ]:
            with self.subTest(customer=customer, quantity=quantity):
                request = [item(product, quantity)]
                quote = self.service.quote(customer, request, 'express')
                order = self.service.place_order(customer, request, 'express')
                self.assertEqual({key: order[key] for key in quote}, quote)
                self.assertEqual([quote[key] for key in ('subtotal_cents', 'discount_cents', 'delivery_cents', 'total_cents')],
                                 [subtotal, discount, 1200, total])
                self.assertEqual(order['fulfillment'], 'express')

    def test_express_fee_never_waived(self):
        for customer, fulfillment, discount, fee, total in [
            ('regular', 'pickup', 0, 0, 12000),
            ('regular', 'delivery', 0, 0, 12000),
            ('regular', 'express', 0, 1200, 13200),
            ('student', 'delivery', 1200, 0, 10800),
            ('student', 'express', 1200, 1200, 12000),
        ]:
            quote = self.service.quote(customer, [item('hoodie', 3)], fulfillment)
            self.assertEqual((quote['discount_cents'], quote['delivery_cents'], quote['total_cents']),
                             (discount, fee, total))
        for customer, total in [('regular', 11200), ('student', 10200)]:
            quote = self.service.quote(customer, [item('bag', 4)], 'express')
            self.assertEqual((quote['delivery_cents'], quote['total_cents']), (1200, total))

    def test_discount_threshold_and_rounding_exclude_delivery(self):
        for quantity, discount, total in [(9, 0, 5700), (10, 500, 5700), (11, 550, 6150)]:
            quote = self.service.quote('student', [item('notebook', quantity)], 'express')
            self.assertEqual((quote['discount_cents'], quote['total_cents']), (discount, total))
        state = self.service.store.load()
        state['catalog'][0]['unit_price_cents'] = 5005
        self.service.store.save(state)
        quote = self.service.quote('student', [item('notebook', 1)], 'express')
        order = self.service.place_order('student', [item('notebook', 1)], 'express')
        self.assertEqual((quote['discount_cents'], quote['delivery_cents'], quote['total_cents']), (501, 1200, 5704))
        self.assertEqual({key: order[key] for key in quote}, quote)

    def test_lifecycle_snapshot_history_and_repeat_cancel(self):
        order = self.service.place_order('student', [item('hoodie', 2)], 'express')
        self.assertEqual(self.service.catalog()[2]['stock'], 3)
        state = self.service.store.load()
        state['catalog'][2]['name'] = 'Updated catalog name'
        state['catalog'][2]['unit_price_cents'] = 1
        self.service.store.save(state)
        reopened = OrderService(self.path)
        self.assertEqual(reopened.get_order(order['order_id']), order)
        self.assertEqual(reopened.list_orders(), [order])
        cancelled = reopened.cancel_order(order['order_id'])
        self.assertEqual(cancelled, dict(order, status='cancelled'))
        self.assertEqual(reopened.catalog()[2]['stock'], 5)
        saved = self.path.read_bytes()
        self.assertEqual(reopened.cancel_order(order['order_id']), cancelled)
        self.assertEqual(self.path.read_bytes(), saved)
        self.assertEqual(OrderService(self.path).get_order(order['order_id']), cancelled)
        second = reopened.place_order('regular', [item('notebook', 1)], 'express')
        self.assertEqual(second['order_id'], 'ORD-0002')
        self.assertEqual(reopened.list_orders(), [cancelled, second])

    def test_invalid_express_requests_preserve_state(self):
        self.service.place_order('regular', [item('notebook', 1)], 'express')
        saved = self.path.read_bytes()
        requests = [('vip', [item('notebook', 1)], 'express'),
                    ('regular', [], 'express'), ('regular', [None], 'express'),
                    ('regular', [item('missing', 1)], 'express'),
                    ('regular', [item('notebook', 10), item('notebook', 10)], 'express')]
        requests += [('regular', [item('notebook', q)], 'express') for q in (0, -1, True, '1', 1.5, 100, 20)]
        requests += [('regular', [item('notebook', 1)], f) for f in ('drone', 'Express', '', None)]
        for request in requests:
            for operation in (self.service.quote, self.service.place_order):
                with self.subTest(request=request, operation=operation.__name__):
                    with self.assertRaises(ValueError):
                        operation(*request)
                    self.assertEqual(self.path.read_bytes(), saved)
        for operation in (self.service.get_order, self.service.cancel_order):
            with self.assertRaises(ValueError):
                operation('missing')
            self.assertEqual(self.path.read_bytes(), saved)
        self.assertEqual(self.service.place_order('regular', [item('notebook', 1)], 'express')['order_id'], 'ORD-0002')

    def test_quote_does_not_reserve_and_place_revalidates(self):
        self.service.quote('regular', [item('notebook', 20)], 'express')
        self.assertFalse(self.path.exists())
        self.service.place_order('regular', [item('notebook', 1)])
        saved = self.path.read_bytes()
        with self.assertRaises(ValueError):
            self.service.place_order('regular', [item('notebook', 20)], 'express')
        self.assertEqual(self.path.read_bytes(), saved)

    def test_cli_express_lifecycle_and_help(self):
        request = ['--customer', 'student', '--fulfillment', 'express', '--item', 'hoodie:2']
        quoted = self.command('quote', *request)
        self.assertEqual(quoted.returncode, 0, quoted.stderr)
        quote = json.loads(quoted.stdout)
        self.assertEqual(quote['total_cents'], 8400)
        self.assertFalse(self.path.exists())
        placed = self.command('place', *request)
        self.assertEqual(placed.returncode, 0, placed.stderr)
        order = json.loads(placed.stdout)
        self.assertEqual({key: order[key] for key in quote}, quote)
        for args, expected in [(('show', order['order_id']), order), (('orders',), [order])]:
            result = self.command(*args)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout), expected)
        for _ in range(2):
            cancelled = self.command('cancel', order['order_id'])
            self.assertEqual(cancelled.returncode, 0, cancelled.stderr)
            self.assertEqual(json.loads(cancelled.stdout), dict(order, status='cancelled'))
        catalog = self.command('catalog')
        self.assertEqual(catalog.returncode, 0, catalog.stderr)
        self.assertEqual(json.loads(catalog.stdout)[2]['stock'], 5)
        for operation in ('quote', 'place'):
            help_result = self.command(operation, '--help')
            self.assertEqual(help_result.returncode, 0)
            self.assertIn('express', help_result.stdout)
            self.assertIn('1200', help_result.stdout)
            result = self.command(operation, '--fulfillment', 'drone', '--item', 'notebook:1')
            self.assertEqual(result.returncode, 2)
            self.assertIn('invalid choice', result.stderr)

    def test_menu_quote_place_retrieve_cancel(self):
        quoted = self.command(input='2\nstudent\nhoodie\n2\n\nexpress\n0\n')
        self.assertEqual(quoted.returncode, 0, quoted.stderr)
        self.assertIn('Fulfillment [pickup/delivery/express]', quoted.stdout)
        self.assertIn('Total: $84.00', quoted.stdout)
        self.assertIn('Quote only: no stock reserved', quoted.stdout)
        self.assertFalse(self.path.exists())
        placed = self.command(input='3\nstudent\nhoodie\n2\n\nexpress\ny\n4\n5\nORD-0001\n6\nORD-0001\ny\n0\n')
        self.assertEqual(placed.returncode, 0, placed.stderr)
        self.assertIn('Delivery: $12.00', placed.stdout)
        self.assertIn('ORD-0001 - placed', placed.stdout)
        self.assertIn('ORD-0001 - cancelled', placed.stdout)
        order = self.service.get_order('ORD-0001')
        self.assertEqual((order['fulfillment'], order['total_cents'], order['status']), ('express', 8400, 'cancelled'))
        self.assertEqual(self.service.catalog()[2]['stock'], 5)

    def test_menu_decline_invalid_and_defaults(self):
        declined = self.command(input='3\n\nnotebook\n2\n\nexpress\nn\n0\n')
        self.assertEqual(declined.returncode, 0, declined.stderr)
        self.assertIn('Order not placed.', declined.stdout)
        self.assertFalse(self.path.exists())
        rejected = self.command(input='2\n\nnotebook\n2\n\ndrone\n2\n\nnotebook\n2\n\n\n0\n')
        self.assertEqual(rejected.returncode, 0, rejected.stderr)
        self.assertIn('Returning to the menu.', rejected.stdout)
        self.assertIn('Customer: regular | Fulfillment: pickup', rejected.stdout)
        self.assertIn('Total: $10.00', rejected.stdout)
        self.assertFalse(self.path.exists())
