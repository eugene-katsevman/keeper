#my little accountant

class Account(object):
    def __init__(self, name):
        self.name = name
        self.inbound = []
        self.outbound = []
    def __str__(self):
        i = sum([i.amount for i in self.inbound])
        o = sum([o.amount for o in self.outbound])
        return "{} i: {}, o: {}, d: {}".format(self.name, i, o, i-o)

class AccountSet(object):
    def __init__(self, name, acc_names):
        self.name = name
        self.accounts = {name: Account(name) for name in acc_names}
        
    def __str__(self):
        return  "{}: ({})".format(self.name, ", ".join([str(acc) for acc in self.accounts.values()]))    
        
class Operation(object):
    def __init__(self, from_, to, amount):
        self._from = from_
        self.to = to
        self.amount = amount
        from_.outbound.append(self)
        to.inbound.append(self)



transactions = []
def transact(_from, _to, amount, ofwhat):
    transactions.append(Operation(_from.accounts[ofwhat], _to.accounts[ofwhat], amount)) 

