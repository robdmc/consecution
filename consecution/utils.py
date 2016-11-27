from collections import Counter
from contextlib import contextmanager
import datetime


class Clock(object):
    def __init__(self):
        # see the reset method for instance attributes
        self.delta = Counter()
        self.active_start_times = dict()

    @contextmanager
    def running(self, *names):
        self.start(*names)
        yield
        self.stop(*names)

    @contextmanager
    def paused(self, *names):
        self.stop(*names)
        yield
        self.start(*names)

    def start(self, *names):
        if not names:
            raise ValueError('You must provide at least one name to start')

        for name in names:
            if name not in self.active_start_times:
                self.active_start_times[name] = datetime.datetime.now()

    def stop(self, *names):
        ending = datetime.datetime.now()
        if not names:
            names = list(self.active_start_times.keys())
        for name in names:
            if name in self.active_start_times:
                starting = self.active_start_times.pop(name)
                self.delta.update({name: (ending - starting).total_seconds()})

    def reset(self, *names):
        if not names:
            names = list(self.active_start_times.keys())
            names.extend(list(self.delta.keys()))
        for name in names:
            if name in self.delta:
                self.delta.pop(name)
            if name in self.active_start_times:
                self.active_start_times.pop(name)

    def get_time(self, *names):
        ending = datetime.datetime.now()
        if not names:
            names = list(self.delta.keys())
            names.extend(list(self.active_start_times.keys()))

        delta = Counter()
        for name in names:
            if name in self.delta:
                delta.update({name: self.delta[name]})
            elif name in self.active_start_times:
                delta.update(
                    {
                        name: (
                            ending - self.active_start_times[name]
                        ).total_seconds()
                    }
                )
        if len(delta) == 1:
            return delta[list(delta.keys())[0]]
        else:
            return dict(delta)

    def __str__(self):
        records = sorted(self.delta.items(), key=lambda t: t[1], reverse=True)
        records = [('%0.6f' % r[1], r[0]) for r in records]

        out_list = ['{: <15s}{}'.format('seconds', 'name')]

        for rec in records:
            out_list.append('{: <15s}{}'.format(*rec))

        return '\n'.join(out_list)

    def __repr__(self):
        return self.__str__()
