import datetime



class TimeSpan(object):
    def empty(self):
        return self._from2 == self._to2

    def __init__(self, _from, _to):
        self.set_from(_from)
        self.set_to(_to)

    def set_from(self, value):
        self._from = value
        self._from2 = self._from if self._from else datetime.datetime.min

    def set_to(self, value):
        self._to = value
        self._to2 = self._to if self._to else datetime.datetime.max

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "("+str(self._from)+", "+str(self._to)+")"

    def __sub__(self, other):
        if other._from2 <= other._to2 <= self._from2:
            #print "1"
            return [self]
        elif self._to2 <= other._from2 <= other._to2 :
            #print self._to2, other._from2, other._to2
            #print "2"
            return [self]
        elif other._from2 <= self._from2 <= other._to2 <= self._to2:
            #print "3"
            return [TimeSpan(other._to, self._to)]
        elif self._from2 <= other._from2 <= self._to2 <= other._to2:
            #print "4"
            return [TimeSpan(self._from, other._from)]
        elif other._from2 <= self._from2 <= self._to2 <= other._to2:
            #print "5"
            return []
        elif self._from2 <= other._from2 <=  other._to2 <= self._to2:
            #print "6"
            return [TimeSpan(self._from, other._from), TimeSpan(other._to, self._to)]
        else:
            raise AssertionError("Strange TimeSpan")

class TimeSpanSet(object):
    def lapse(self):
        raise NotImplemented()

    def __init__(self, timespan = None, timespans = None, _from = None, _to=None, empty = False):
        self._spans = []
        if empty:
            return
        if timespan or timespans is not None:
            if timespan:
                self._spans.append(timespan)
            else:
                self._spans = timespans
        else:
            self._spans.append(TimeSpan(_from, _to))

    def converge(self):
        self._spans.sort(key = lambda span : span._from)
        result = []
        current_span = None
        for span in self._spans:
            if current_span is None:
                current_span = TimeSpan(span._from, span._to)
            else:
                if current_span._to is None:
                    break
                if current_span._to < span._from:
                    result.append(current_span)
                    current_span = span
                elif not span._to or current_span._to < span._to:
                    current_span.set_to(span._to)
        if current_span:
            result.append(current_span)
        #filter out spans with from = to
        result = [r for r in result if not r.empty()]
        return TimeSpanSet(timespans = result)


    def __sub__(self, other):
        current_spans = self._spans
        for span in other._spans:
            next_spans = []
            for current_span in current_spans:
                diff = current_span - span
                #print current_span, "-", span, "=",  diff
                next_spans += diff
            current_spans = next_spans

        return TimeSpanSet(timespans = current_spans, empty = not current_spans)

    def __str__(self):
        return "["+", ".join([str(s) for s in self._spans])+"]"

    def __add__(self, other):
        return TimeSpanSet(timespans=self._spans + other._spans).converge()

if __name__=="__main__":
    span_set = TimeSpanSet(timespans = [TimeSpan(datetime.datetime(2015, 5, 1, 0), datetime.datetime(2015, 5, 1, 4)),
                                        TimeSpan(datetime.datetime(2015, 5, 1, 0), datetime.datetime(2015, 5, 1, 5)),
                                        TimeSpan(datetime.datetime(2015, 5, 1, 5,30), datetime.datetime(2015, 5, 1, 6)),
                                        ])
    span_set2 = TimeSpanSet(_from = datetime.datetime(2015,5,1,5), _to = datetime.datetime(2015,5,1,7))
    span_set = span_set.converge()
    print span_set
    print span_set + span_set2
    print span_set - span_set2
    #print TimeSpan(datetime.datetime(2015, 5, 1, 0), datetime.datetime(2015, 5, 1, 4)) - \
    #      TimeSpan(datetime.datetime(2015, 5, 1, 2), datetime.datetime(2015, 5, 1, 3))