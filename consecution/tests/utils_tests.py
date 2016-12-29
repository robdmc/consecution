from __future__ import print_function

from unittest import TestCase
from consecution.utils import Clock
import time
from consecution.tests.testing_helpers import print_catcher


class ClockTests(TestCase):
    def test_bad_start(self):
        clock = Clock()
        with self.assertRaises(ValueError):
            clock.start()

    def test_printing(self):
        clock = Clock()
        with clock.running('a', 'b', 'c'):
            with clock.paused('a'):
                time.sleep(.1)
                with clock.paused('b'):
                    time.sleep(.1)

        with print_catcher() as printer:
            print(repr(clock))

        names = []
        for ind, line in enumerate(printer.txt.split('\n')):
            if line:
                if ind > 0:
                    names.append(line.split()[-1])

        self.assertEqual(names, ['c', 'b', 'a'])

    def test_get_time_of_running(self):
        clock = Clock()
        with clock.running('a'):
            time.sleep(.1)
            delta1 = int(10 * clock.get_time())
            time.sleep(.1)
        delta2 = int(10 * clock.get_time())
        self.assertEqual(delta1, 1)
        self.assertEqual(delta2, 2)

    def test_pausing(self):
        clock = Clock()

        with clock.running('a', 'b', 'c'):
            time.sleep(.1)
            with clock.paused('b', 'c'):
                time.sleep(.1)

        self.assertEqual(int(10 * clock.get_time('a')), 2)
        self.assertEqual(int(10 * clock.get_time('b')), 1)
        self.assertEqual(int(10 * clock.get_time('c')), 1)
        self.assertEqual(
            {int(10 * v) for v in clock.get_time().values()},
            {1, 2}
        )

    def test_stop_all(self):
        clock = Clock()
        clock.start('a', 'b')
        time.sleep(.1)
        clock.stop()
        self.assertEqual(int(10 * clock.get_time('a')), 1)
        self.assertEqual(int(10 * clock.get_time('b')), 1)

    def test_reset_all(self):
        clock = Clock()
        clock.start('a', 'b')
        time.sleep(.1)
        clock.stop('b')
        self.assertEqual(len(clock.delta), 1)
        clock.reset()
        self.assertEqual(len(clock.get_time()), 0)

    def test_double_calls(self):
        clock = Clock()
        clock.start('a')
        clock.start('a')
        time.sleep(.1)
        clock.stop('a')
        clock.stop('a')
        self.assertEqual(int(round(10 * clock.get_time())), 1)
        clock.reset('a')
        clock.reset('a')
        clock.reset('b')
        clock.reset('b')
        self.assertEqual(clock.get_time(), {})

    def test_get_time_delta_only(self):
        clock = Clock()
        clock.start('a')
        clock.stop('a')
        self.assertEqual(clock.get_time('f'), {})
