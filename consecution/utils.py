from collections import Counter
import datetime

class Clock(object):
    def __init__(self):
        # see the reset method for instance attributes
        self.reset()

    def start(self, name):
        if name not in self.active_start_times:
            self.active_start_times[name] = datetime.datetime.now()

    def stop(self, name):
        ending = datetime.datetime.now()
        if name in self.active_start_times:
            starting = self.active_start_times.pop(name)
            self.delta.update({name: (ending - starting).total_seconds()})

    def pause(self):
        for name in self.active_start_times.keys():
            self.stop(name)
            self.paused_set.add(name)

    def resume(self):
        for name in self.paused_set:
            self.start(name)
        self.paused_set = set()

    def reset(self):
        self.delta = Counter()
        self.active_start_times = dict()
        self.paused_set = set()

    def __str__(self):
        records = sorted(self.delta.items(), key=lambda t: t[1], reverse=True)
        name_length = max(len(key) for key in self.delta.keys())
        template = '{:>%d}  {}\n' % name_length

        row_list = []
        row_list.append(template.format('seconds', 'name'))

        for rec in records:
            row_list.append(template.format(*rec))
        return ''.join(row_list)

    def __repr__(self):
        return self.__str__()

