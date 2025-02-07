# -*- coding: utf-8 -*-

import pynini
from pynini import Fst, Arc, Weight
from . import config


class Wfst():
    """
    Pynini Fst wrapper with automatic handling of labels for inputs / 
    outputs / states and output strings. State labels must be hashable 
    (strings, tuples, etc.). Pynini constructive and destructive operations 
    generally lose track of state ids and symbol labels, so some operations 
    are reimplemented here (e.g., connect, compose).
    Fst() arguments: arc_type ("standard", "log", or "log64")
    """

    def __init__(self,
                 input_symtable=None,
                 output_symtable=None,
                 arc_type='standard'):
        # Symbol tables
        if input_symtable is None:
            input_symtable = pynini.SymbolTable()
            input_symtable.add_symbol(config.epsilon)
            input_symtable.add_symbol(config.bos)
            input_symtable.add_symbol(config.eos)
        if output_symtable is None:
            output_symtable = input_symtable
        # Empty Fst
        fst = Fst(arc_type)
        fst.set_input_symbols(input_symtable)
        fst.set_output_symbols(output_symtable)
        # Empty Wfst
        self.fst = fst  # Wrapped Fst
        self._state2label = {}  # State id -> state label
        self._label2state = {}  # State label -> state id
        self.sigma = {}  # State id -> output string

    # Input/output labels (delegate to Fst).

    def input_symbols(self):
        """ Get input symbol table. """
        return self.fst.input_symbols()

    def output_symbols(self):
        """ Get output symbol table. """
        return self.fst.output_symbols()

    def mutable_input_symbols(self):
        """ Get mutable input symbol table. """
        return self.fst.mutable_input_symbols()

    def mutable_output_symbols(self):
        """ Get mutable output symbol table. """
        return self.fst.mutable_output_symbols()

    def set_input_symbols(self, symbols):
        """ Set input symbol table. """
        self.fst.set_input_symbols(symbols)
        return self

    def set_output_symbols(self, symbols):
        """ Set output symbol table. """
        self.fst.set_output_symbols(symbols)
        return self

    def input_label(self, sym):
        """ Get input label for symbol id. """
        return self.fst.input_symbols().find(sym)

    def input_index(self, sym):
        """ Get input id for symbol label. """
        return self.fst.input_symbols().find(sym)

    def output_label(self, sym):
        """ Get output label for symbol id. """
        return self.fst.output_symbols().find(sym)

    def output_index(self, sym):
        """ Get output id for symbol label. """
        return self.fst.output_symbols().find(sym)

    # States.

    def add_state(self, label=None):
        """ Add new state, optionally specifying its label. """
        # Enforce unique labels
        if label is not None:
            if label in self._label2state:
                return self._label2state[label]
        # Create new state
        q = self.fst.add_state()
        # Self-labeling by string as default
        if label is None:
            label = str(q)
        # State <-> label
        self._state2label[q] = label
        self._label2state[label] = q
        return q

    def states(self, labels=True):
        """ Iterator over state labels (or ids). """
        fst = self.fst
        if not labels:
            return fst.states()
        return map(lambda q: self.state_label(q), fst.states())

    def num_states(self):
        return self.fst.num_states()

    def set_start(self, q):
        """ Set start state by id or label. """
        if not isinstance(q, int):
            q = self.state_id(q)
        return self.fst.set_start(q)

    def start(self, label=True):
        """ Start state label (or id). """
        if not label:
            return self.fst.start()
        return self.state_label(self.fst.start())

    def is_start(self, q):
        """ Check start status by id or label. """
        if not isinstance(q, int):
            q = self.state_id(q)
        return q == self.fst.start()

    def set_final(self, q, weight=None):
        """ Set final weight of state by id or label. """
        if not isinstance(q, int):
            q = self.state_id(q)
        if weight is None:
            weight = Weight.one(self.weight_type())
        return self.fst.set_final(q, weight)

    def is_final(self, q):
        """ Check final status by id or label. """
        if not isinstance(q, int):
            q = self.state_id(state)
        zero = Weight.zero(self.weight_type())
        return self.final(q) != zero

    def final(self, q):
        """ Final weight of state by id or label. """
        if not isinstance(q, int):
            q = self.state_id(q)
        return self.fst.final(q)

    def finals(self, labels=True):
        """
        Iterator over states with non-zero final weights.
        """
        fst = self.fst
        zero = pynini.Weight.zero(fst.weight_type())
        state_iter = fst.states()
        state_iter = filter(lambda q: fst.final(q) != zero, state_iter)
        if labels:
            state_iter = map(lambda q: self.state_label(q), state_iter)
        return state_iter

    def state_label(self, q):
        """ State label from id. """
        return self._state2label[q]

    def state_id(self, q):
        """ State id from label. """
        return self._label2state[q]

    # Arcs.

    def add_arc(self,
                src=None,
                ilabel=None,
                olabel=None,
                weight=None,
                dest=None):
        """ Add arc (accepts id or label for src/ilabel/olabel/dest). """
        fst = self.fst
        if not isinstance(src, int):
            src = self.state_id(src)
        if olabel is None:
            olabel = ilabel
        if not isinstance(ilabel, int):
            ilabel = fst.mutable_input_symbols().add_symbol(ilabel)
        if not isinstance(olabel, int):
            olabel = fst.mutable_output_symbols().add_symbol(olabel)
        if weight is None:
            weight = Weight.one(self.weight_type())
        if not isinstance(dest, int):
            dest = self.state_id(dest)
        arc = Arc(ilabel, olabel, weight, dest)
        fst.add_arc(src, arc)
        return self

    def arcs(self, src):
        """ Iterator over arcs from a state. """
        # todo: decorate arcs with input/output labels if requested.
        if not isinstance(src, int):
            src = self.state_id(src)
        return self.fst.arcs(src)

    def mutable_arcs(self, src):
        """ Mutable iterator over arcs from a state. """
        if not isinstance(src, int):
            src = self.state_id(src)
        return self.fst.mutable_arcs(src)

    def arcsort(self, sort_type='ilabel'):
        """ Sort arcs from each state. """
        self.fst.arcsort(sort_type)
        return self

    def num_arcs(self, src):
        """ Number of arcs from state. """
        if not isinstance(src, int):
            src = self.state_id(src)
        return self.fst.num_arcs(src)

    def num_arcs(self):
        """ Total count of arcs. """
        fst = self.fst
        n = 0
        for q in fst.states():
            n += fst.num_arcs(q)
        return n

    def num_input_epsilons(self, src):
        """ Number of arcs with input epsilon from state. """
        if not isinstance(src, int):
            src = self.state_id(src)
        return self.fst.num_input_epsilons(src)

    def num_output_epsilons(self, src):
        """ Number of arcs with output epsilon from state. """
        if not isinstance(src, int):
            src = self.state_id(src)
        return self.fst.num_output_epsilons(src)

    def arc_type(self):
        """ Arc type (standard, log, log64). """
        return self.fst.arc_type()

    def weight_type(self):
        """ Weight type (tropical, log, log64). """
        return self.fst.weight_type()

    def map_weights(self, map_type='identity', **kwargs):
        """
        Map weights (see pynini.arcmap).
        map_type is "identity", "invert", "quantize", "plus", "power", 
        "rmweight", "times", "to_log", or "to_log64"
        """
        # assumption: pynini.arcmap() does not reindex states.
        if map_type == 'identity':
            return self
        fst = self.fst
        isymbols = fst.input_symbols()
        osymbols = fst.output_symbols()
        fst_out = pynini.arcmap(fst, map_type=map_type, **kwargs)
        fst_out.set_input_symbols(isymbols)
        fst_out.set_output_symbols(osymbols)
        self.fst = fst_out
        return self

    def project(self, project_type):
        """ Project input or output labels. """
        # assumption: Fst.project() does not reindex states.
        fst = self.fst
        if project_type == 'input':
            isymbols = fst.input_symbols()
            fst.set_output_symbols(isymbols)
        if project_type == 'output':
            osymbols = fst.output_symbols()
            fst.set_input_symbols(osymbols)
        fst.project(project_type)
        return self

    # Algorithms.

    def paths(self):
        """
        Iterator over paths through this machine (assumed to be acyclic). 
        Path iterator has methods: ilabels(), istring(), labels(), 
        ostring(), weights(), items(); istrings(), ostrings().
        """
        fst = self.fst
        isymbols = fst.input_symbols()
        osymbols = fst.output_symbols()
        strpath_iter = fst.paths(
            input_token_type=isymbols, output_token_type=osymbols)
        return strpath_iter

    def istrings(self):
        """
        Iterator over input strings of paths through this machine 
        (assumed to be acyclic).
        """
        return self.paths().istrings()

    def ostrings(self):
        """
        Iterator over output strings of paths through this machine 
        (assumed to be acyclic).
        """
        return self.paths().ostrings()

    def accepted_strings(self, side='input', max_len=10):
        """
        Strings accepted on input (default) or output, up to max_len 
        (not including bos/eos); cf. paths() for acyclic machines. 
        todo: epsilon handling
        """
        fst = self.fst
        q0 = fst.start()
        Zero = Weight.zero(fst.weight_type())

        accepted = set()
        prefixes = {(q0, None)}
        prefixes_new = set()
        for _ in range(max_len + 2):
            for (src, prefix) in prefixes:
                for t in fst.arcs(src):
                    dest = t.nextstate
                    if side == 'input':
                        tlabel = self.input_label(t.ilabel)
                    else:
                        tlabel = self.output_label(t.olabel)
                    if prefix is None:
                        prefix_new = tlabel
                    else:
                        prefix_new = prefix + ' ' + tlabel
                    prefixes_new.add((dest, prefix_new))
                    if fst.final(dest) != Zero:
                        accepted.add(prefix_new)
                        #print(prefix_new)
            prefixes, prefixes_new = prefixes_new, prefixes
            prefixes_new.clear()

        return accepted

    def connect(self):
        """
        Remove states and arcs not on successful paths. [nondestructive]
        """
        accessible = self.accessible(forward=True)
        coaccessible = self.accessible(forward=False)
        live_states = accessible & coaccessible
        dead_states = set(self.fst.states()) - live_states
        wfst = self.delete_states(dead_states, connect=False)
        return wfst

    def accessible(self, forward=True):
        """
        Ids of states accessible from initial state (forward) 
        -or- coaccessible from final states (backward).
        """
        fst = self.fst

        if forward:
            # Initial state id; forward transitions
            Q = set([fst.start()])
            T = {}
            for src in fst.states():
                T[src] = set()
                for t in fst.arcs(src):
                    dest = t.nextstate
                    T[src].add(dest)
        else:
            # Final state ids; backward transitions
            Q = set([q for q in fst.states() if self.is_final(q)])
            T = {}
            for src in fst.states():
                for t in fst.arcs(src):
                    dest = t.nextstate
                    if dest not in T:
                        T[dest] = set()
                    T[dest].add(src)

        # (Co)accessible state ids
        Q_old = set()
        Q_new = set(Q)
        while len(Q_new) != 0:
            Q_old, Q_new = Q_new, Q_old
            Q_new.clear()
            for src in filter(lambda q1: q1 in T, Q_old):
                for dest in filter(lambda q2: q2 not in Q, T[src]):
                    Q.add(dest)
                    Q_new.add(dest)
        return Q

    def delete_states(self, states, connect=True):
        """
        Remove states by id while preserving labels. [nondestructive]
        """
        fst = self.fst
        live_states = set(fst.states()) - states

        # Preserve input/output symbols and weight type
        wfst = Wfst(fst.input_symbols(), fst.output_symbols(), fst.arc_type())

        # Reindex live states, copying labels
        state_map = {}
        q0 = fst.start()
        for q in live_states:
            q_label = self.state_label(q)
            q_id = wfst.add_state(q_label)
            state_map[q] = q_id
            if q == q0:
                wfst.set_start(q_id)
            wfst.set_final(q_id, self.final(q))

        # Copy transitions between live states
        for q in live_states:
            src = state_map[q]
            for t in filter(lambda t: t.nextstate in live_states, fst.arcs(q)):
                dest = state_map[t.nextstate]
                wfst.add_arc(src, t.ilabel, t.olabel, t.weight, dest)

        if connect:
            wfst.connect()
        return wfst

    def delete_arcs(self, dead_arcs):
        """
        Remove arcs. [destructive]
        Implemented by deleting all arcs from relevant states then adding 
        back all non-dead arcs, as suggested in the OpenFst forum: 
        https://www.openfst.org/twiki/bin/view/Forum/FstForumArchive2014
        """
        fst = self.fst

        # Group dead arcs by source state
        dead_arcs_ = {}
        for (src, t) in dead_arcs:
            if src not in dead_arcs_:
                dead_arcs_[src] = []
            dead_arcs_[src].append(t)

        # Process states with some dead arcs
        for q in dead_arcs_:
            # Remove all arcs from state
            arcs = fst.arcs(q)
            fst.delete_arcs(q)
            # Add back live arcs
            for t1 in arcs:
                live = True
                for t2 in dead_arcs_[q]:
                    if arc_equal(t1, t2):
                        live = False
                        break
                if live:
                    self.add_arc(q, t1.ilabel, t1.olabel, t1.weight,
                                 t1.nextstate)
        return self

    def transduce(self, x, add_delim=True, output_strings=True):
        """
        Transduce space-separated sequence x with this machine, 
        returning iterator over output strings (default) or resulting 
        machine that preserves input/output labels but not state labels. 
        Alternative: create acceptor for string with accep(), then 
        compose() with this machine to preserve input/output/state labels.
        """
        fst = self.fst
        isymbols = fst.input_symbols()
        osymbols = fst.output_symbols()

        if not isinstance(x, str):
            x = ' '.join(x)
        if add_delim:
            x = config.bos + ' ' + x + ' ' + config.eos
        fst_in = pynini.accep(x, token_type=isymbols)

        fst_out = fst_in @ fst
        fst_out.set_input_symbols(isymbols)
        fst_out.set_output_symbols(osymbols)
        if output_strings:
            strpath_iter = fst_out.paths(output_token_type=osymbols)
            return strpath_iter.ostrings()
        wfst = Wfst.from_fst(fst_out)
        return wfst

    def push_weights(self, reweight_type='to_initial', **kwargs):
        """
        Push weights (see Fst.push, pynini.push). [destructive]
        Fst.push() arguments: delta (1e-6), remove_total_weight(False), 
        reweight_type ("to_initial" or "to_final")
        """
        # assumption: Fst.push() does not reindex states.
        return self

    def push_labels(self, reweight_type='to_initial', **kwargs):
        """
        Push labels (see pynini.push). [destructive]
        pynini.push() arguments: remove_common_affix (False), 
        reweight_type ("to_initial" or "to_final")
        """
        # assumption: pynini.push() does not reindex states.
        # todo: test
        self.fst = pynini.push(
            self.fst, push_labels=True, reweight_type=reweight_type, **kwargs)
        return self

    def randgen(self, npath=1, select=None, output_strings=True, **kwargs):
        """
        Randomly generate paths through this machine, returning iterator 
        over output strings (default) or machine accepting the paths. 
        pynini.randgen() arguments: npath, seed, select ("uniform", 
        "log_prob", or "fast_log_prob"), max_length, weighted, 
        remove_total_weight
        """
        fst = self.fst
        if select is None:
            if fst.weight_type() == 'log' or fst.weight_type() == 'log64':
                select = 'log_prob'
            else:
                select = 'uniform'

        fst_samp = pynini.randgen(fst, npath=npath, select=select, **kwargs)

        if output_strings:
            osymbols = fst.output_symbols()
            strpath_iter = fst_samp.paths(output_token_type=osymbols)
            return strpath_iter.ostrings()
        wfst_samp = Wfst.from_fst(fst_samp)
        return wfst_samp

    def invert(self):
        """ Invert mapping (exchange input and output labels). """
        # assumption: Fst.invert() does not reindex states.
        fst = self.fst
        isymbols = fst.input_symbols()
        osymbols = fst.output_symbols()
        fst.invert()
        fst.set_input_symbols(isymbols)
        fst.set_output_symbols(osymbols)
        return self

    # Copying/creating

    def copy(self):
        """
        Deep copy preserving input/output/state symbols and string outputs.
        """
        fst = self.fst
        wfst = Wfst(fst.input_symbols(), fst.output_symbols(), fst.arc_type())
        wfst.fst = fst.copy()
        wfst._state2label = dict(self._state2label)
        wfst._label2state = dict(self._label2state)
        wfst.sigma = dict(self.sigma)
        return wfst

    @classmethod
    def from_fst(cls, fst):
        """ Wrap pynini Fst. """
        wfst = Wfst(fst.input_symbols(), fst.output_symbols(), fst.arc_type())
        state2label = {q: str(q) for q in fst.states()}
        label2state = {v: k for k, v in state2label.items()}
        wfst.fst = fst
        wfst._state2label = state2label
        wfst._label2state = label2state
        return wfst

    def to_fst(self):
        """ Copy and return wrapped pynini Fst. """
        # note: access fst member if do not need copy
        return self.fst.copy()

    # Printing/drawing

    def print(self, **kwargs):
        fst = self.fst
        # State symbol table
        state_symbols = pynini.SymbolTable()
        for q, label in self._state2label.items():
            state_symbols.add_symbol(str(label), q)
        return fst.print(
            isymbols=fst.input_symbols(),
            osymbols=fst.output_symbols(),
            ssymbols=state_symbols,
            **kwargs)

    def draw(self, source, acceptor=True, portrait=True, **kwargs):
        fst = self.fst
        # State symbol table
        state_symbols = pynini.SymbolTable()
        for q, label in self._state2label.items():
            state_symbols.add_symbol(str(label), q)
        return fst.draw(
            source,
            isymbols=fst.input_symbols(),
            osymbols=fst.output_symbols(),
            ssymbols=state_symbols,
            acceptor=acceptor,
            portrait=portrait,
            **kwargs)

    # todo:
    # read()/write() from/to file
    # encode()/decode() labels
    # minimize(), prune(), rmepsilon()


def acceptor(x, add_delim=True, weight=None, arc_type='standard'):
    """
    Acceptor for space-delimited sequence (see pynini.accep).
    pynini.accep() arguments: weight (final weight) and 
    arc_type ("standard", "log", or "log64")
    """
    if not isinstance(x, str):
        x = ' '.join(x)
    if add_delim:
        x = config.bos + ' ' + x + ' ' + config.eos

    isymbols = config.symtable
    fst = pynini.accep(x, weight, arc_type, token_type=isymbols)
    fst.set_input_symbols(isymbols)
    fst.set_output_symbols(isymbols)
    wfst = Wfst.from_fst(fst)
    return wfst


def trellis_acceptor(max_len=1, sigma_tier=None):
    """
    Acceptor for strings up to length max_len (+2 for delimiters). 
    If sigma_tier is specified as a subset of the alphabet, makes 
    acceptor for tier/projection for that subset with other symbols 
    labeling self-loops on interior states.
    """
    bos = config.bos
    eos = config.eos
    if sigma_tier is None:
        sigma_tier = set(config.sigma)
        sigma_skip = set()
    else:
        sigma_skip = set(config.sigma) - sigma_tier
    wfst = Wfst(config.symtable)

    # Initial and peninitial states
    q0 = wfst.add_state()  # id 0
    q1 = wfst.add_state()  # id 1
    wfst.set_start(q0)
    wfst.add_arc(src=q0, ilabel=bos, dest=q1)

    # Interior states
    for l in range(max_len):
        wfst.add_state()  # ids 2, ...

    # Final state
    qf = wfst.add_state()  # id (max_len+2)
    wfst.set_final(qf)

    # Zero-length form
    wfst.add_arc(src=q1, ilabel=eos, dest=qf)

    # Interior states
    q = q1
    for l in range(1, max_len + 1):
        r = (l + 1)
        # Advance
        for x in sigma_tier:
            wfst.add_arc(src=q, ilabel=x, dest=r)
        # Loop
        for x in sigma_skip:
            wfst.add_arc(src=q, ilabel=x, dest=q)
        # End
        wfst.add_arc(src=r, ilabel=eos, dest=qf)
        q = r

    # Loop
    for x in sigma_skip:
        wfst.add_arc(src=q, ilabel=x, dest=q)

    return wfst


def ngram_acceptor(context='left', context_length=1, sigma_tier=None):
    """
    Acceptor (identity transducer) for segments in immediately preceding 
    (left) / following (right) / both-side contexts of specified length.
    """
    if context == 'left':
        return ngram_acceptor_left(context_length, sigma_tier)
    if context == 'right':
        return ngram_acceptor_right(context_length, sigma_tier)
    if context == 'both':
        L = ngram_acceptor_left(context_length, sigma_tier)
        R = ngram_acceptor_right(context_length, sigma_tier)
        #R.project('input')
        LR = compose(L, R)
        return LR
    print(f'Bad side argument to ngram_acceptor {side}')
    return None


def ngram_acceptor_left(context_length=1, sigma_tier=None):
    """
    Acceptor (identity transducer) for segments in immediately preceding 
    contexts (histories) of specified length. If sigma_tier is specified as a 
    subset of sigma, only contexts over sigma_tier are tracked (other members  of sigma are skipped with self-loops on each interior state).
    """
    epsilon = config.epsilon
    bos = config.bos
    eos = config.eos
    if sigma_tier is None:
        sigma_tier = set(config.sigma)
        sigma_skip = set()
    else:
        sigma_skip = set(config.sigma) - sigma_tier
    wfst = Wfst(config.symtable)

    # Initial and peninitial states
    q0 = ('λ',)
    q1 = (epsilon,) * (context_length - 1) + (bos,)
    wfst.add_state(q0)
    wfst.set_start(q0)
    wfst.add_state(q1)
    wfst.add_arc(src=q0, ilabel=bos, dest=q1)

    # Interior arcs
    # xα -- y --> αy for each y
    Q = {q0, q1}
    Qnew = set(Q)
    for l in range(context_length + 1):
        Qold = set(Qnew)
        Qnew = set()
        for q1 in Qold:
            if q1 == q0:
                continue
            for x in sigma_tier:
                q2 = _suffix(q1, context_length - 1) + (x,)
                wfst.add_state(q2)
                wfst.add_arc(src=q1, ilabel=x, dest=q2)
                Qnew.add(q2)
        Q |= Qnew

    # Final state and incoming arcs
    qf = (eos,)
    wfst.add_state(qf)
    wfst.set_final(qf)
    for q1 in Q:
        if q1 == q0:
            continue
        wfst.add_arc(src=q1, ilabel=eos, dest=qf)
    Q.add(qf)

    # Self-transitions labeled by skipped symbols
    # on interior states
    for q in Q:
        if (q == q0) or (q == qf):
            continue
        for x in sigma_skip:
            wfst.add_arc(src=q, ilabel=x, dest=q)

    return wfst


def ngram_acceptor_right(context_length=1, sigma_tier=None):
    """
    Acceptor (identity transducer) for segments in immediately following 
    contexts (futures) of specified length. If sigma_tier is specified as a 
    subset of sigma, only contexts over sigma_tier are tracked (other members 
    of sigma are skipped with self-loops on each interior state)
    """
    epsilon = config.epsilon
    bos = config.bos
    eos = config.eos
    if sigma_tier is None:
        sigma_tier = set(config.sigma)
        sigma_skip = set()
    else:
        sigma_skip = set(config.sigma) - sigma_tier
    wfst = Wfst(config.symtable)

    # Final and penultimate state
    qf = ('λ',)
    qp = (eos,) + (epsilon,) * (context_length - 1)
    wfst.add_state(qf)
    wfst.set_final(qf)
    wfst.add_state(qp)
    wfst.add_arc(src=qp, ilabel=eos, dest=qf)

    # Interior transitions
    # xα -- x --> αy for each y
    Q = {qf, qp}
    Qnew = set(Q)
    for l in range(context_length + 1):
        Qold = set(Qnew)
        Qnew = set()
        for q2 in Qold:
            if q2 == qf:
                continue
            for x in sigma_tier:
                q1 = (x,) + _prefix(q2, context_length - 1)
                wfst.add_state(q1)
                wfst.add_arc(src=q1, ilabel=x, dest=q2)
                Qnew.add(q1)
        Q |= Qnew

    # Initial state and outgoing transitions
    q0 = (bos,)
    wfst.add_state(q0)
    wfst.set_start(q0)
    for q in Q:
        if q == qf:
            continue
        wfst.add_arc(src=q0, ilabel=bos, dest=q)
    Q.add(q0)

    # Self-transitions labeled by skipped symbols
    # on interior states
    for q in Q:
        if (q == q0) or (q == qf):
            continue
        for x in sigma_skip:
            wfst.add_arc(src=q, ilabel=x, dest=q)

    return wfst


def compose(wfst1, wfst2):
    """
    Composition/intersection, retaining contextual info from original 
    machines by labeling each state q = (q1, q2) as (label(q1), label(q2)).
    todo: multiply weights; matcher/filter options for compose; 
    flatten state labels created by repeated composition
    """
    wfst = Wfst(config.symtable)
    Zero = Weight.zero(wfst.weight_type())

    q0 = (wfst1.start(), wfst2.start())
    wfst.add_state(q0)
    wfst.set_start(q0)

    # Lazy state and transition construction
    Q = set([q0])
    Q_old, Q_new = set(), set([q0])
    while len(Q_new) != 0:
        Q_old, Q_new = Q_new, Q_old
        Q_new.clear()
        for src in Q_old:
            # State labels in M1, M2
            src1, src2 = src
            for t1 in wfst1.arcs(src1):
                # todo: sort arcs wfst2
                for t2 in wfst2.arcs(src2):
                    if t1.olabel != t2.ilabel:
                        continue
                    dest1 = t1.nextstate
                    dest2 = t2.nextstate
                    dest = (wfst1.state_label(dest1), wfst2.state_label(dest2))
                    wfst.add_state(dest)
                    # note: no change if dest already exists
                    wfst.add_arc(
                        src=src, ilabel=t1.ilabel, olabel=t2.olabel, dest=dest)
                    # dest is final if both dest1 and dest2 aere final
                    if wfst1.final(dest1) != Zero and wfst2.final(
                            dest2) != Zero:
                        wfst.set_final(dest)
                    if dest not in Q:
                        Q.add(dest)
                        Q_new.add(dest)

    return wfst.connect()


def arc_equal(arc1, arc2):
    """
    Arc equality (missing from pynini?).
    """
    val = (arc1.ilabel == arc2.ilabel) and \
            (arc1.olabel == arc2.olabel) and \
            (arc1.nextstate == arc2.nextstate) and \
            (arc1.weight == arc2.weight)
    return val


def _prefix(x, l):
    """ Length-l prefix of tuple x """
    if l < 1:
        return ()
    if len(x) < l:
        return x
    return x[:l]


def _suffix(x, l):
    """ Length-l suffix of tuple x """
    if l < 1:
        return ()
    if len(x) < l:
        return x
    return x[-l:]
