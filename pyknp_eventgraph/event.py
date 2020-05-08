"""A class to manage event information."""
import collections
from typing import List

from pyknp import Tag

from pyknp_eventgraph.base import Base
from pyknp_eventgraph.basic_phrase import (
    BasicPhrase,
    BasicPhraseList
)
from pyknp_eventgraph.features import Features
from pyknp_eventgraph.pas import PAS


class Event(Base):
    """A class to manage an event.

    Attributes:
        evid (int): A serial event ID.
        sid (str): An original sentence ID.
        ssid (int): A serial sentence ID.
        start (Tag): A clause-start tag.
        head (Tag): A clause-head tag.
        end (Tag): A clause-end tag.
        surf (str): A surface string.
        surf_with_mark (str): `surf` with special marks.
        mrphs (str): `surf` with white spaces between morphemes.
        mrphs_with_mark (str): `mrphs` with special marks.
        normalized_mrphs (str): A normalized version of `mrphs`.
        normalized_mrphs_with_mark (str): `normalized_mrphs` with special marks.
        normalized_mrphs_without_exophora (str): `normalized_mrphs` without exophora arguments.
        normalized_mrphs_with_mark_without_exophora (str): `normalized_mrphs_with_mark` without exophora arguments.
        reps (str): The representative string.
        reps_with_mark (str): `reps` with special marks.
        normalized_reps (str): A normalized version of `reps`.
        normalized_reps_with_mark (str): `normalized_reps` with special marks.
        content_rep_list (List[str]): A collection of repnames corresponding to content words.
        parent_evid (int): A parent event ID.
        outgoing_relations (List[Relation]): A list of relations, where the modifiers point this event.
        incoming_relations (List[EventRelation]): A list of relations, where the heads point this event.
        pas (PAS): A predicate argument structure.
        features (Features): Features.

    """

    __evid = 0

    def __init__(self):
        self.evid = -1
        self.sid = ''
        self.ssid = -1

        self.start = None
        self.head = None
        self.end = None

        self.surf = ''
        self.surf_with_mark = ''
        self.mrphs = ''
        self.mrphs_with_mark = ''
        self.normalized_mrphs = ''
        self.normalized_mrphs_with_mark = ''
        self.normalized_mrphs_without_exophora = ''
        self.normalized_mrphs_with_mark_without_exophora = ''
        self.reps = ''
        self.reps_with_mark = ''
        self.normalized_reps = ''
        self.normalized_reps_with_mark = ''
        self.content_rep_list = []

        self.parent_evid = -1
        self.outgoing_relations = []
        self.incoming_relations = []
        self.pas = None
        self.features = None

    @property
    def adnominal_relations(self):
        return list(filter(lambda r: r.label == '連体修飾', self.incoming_relations))

    @property
    def sentential_complement_relations(self):
        return list(filter(lambda r: r.label == '補文', self.incoming_relations))

    @property
    def adnominal_events(self):
        return list(map(lambda r: r.modifier, self.adnominal_relations))

    @property
    def sentential_complement_events(self):
        return list(map(lambda r: r.modifier, self.sentential_complement_relations))

    @classmethod
    def reset_serial_id(cls):
        """Reset the serial event ID."""
        cls.__evid = 0

    @classmethod
    def build(cls, sid, ssid, start, head, end):
        """Create an instance from language analysis.

        Args:
            sid (str): An original sentence ID.
            ssid (int): A serial sentence ID.
            start (Tag): A clause-start tag.
            head (Tag): A clause-head tag.
            end (Tag): A clause-end tag.

        Returns:
            Event: An event.

        """
        event = Event()
        event.evid = cls.__evid
        event.sid = sid
        event.ssid = ssid
        event.start = start
        event.head = head
        event.end = end
        event.pas = PAS.build(head)
        event.features = Features.build(head)
        Event.__evid += 1
        return event

    @classmethod
    def load(cls, dct):
        """Create an instance from a dictionary.

        Args:
            dct (dict): A dictionary storing an instance.

        Returns:
            Event: An event.

        """
        event = Event()
        event.evid = dct['event_id']
        event.sid = dct['sid']
        event.ssid = dct['ssid']
        event.surf = dct['surf']
        event.surf_with_mark = dct['surf_with_mark']
        event.mrphs = dct['mrphs']
        event.mrphs_with_mark = dct['mrphs_with_mark']
        event.normalized_mrphs = dct['normalized_mrphs']
        event.normalized_mrphs_with_mark = dct['normalized_mrphs_with_mark']
        event.normalized_mrphs_without_exophora = dct['normalized_mrphs_without_exophora']
        event.normalized_mrphs_with_mark_without_exophora = dct['normalized_mrphs_with_mark_without_exophora']
        event.reps = dct['reps']
        event.reps_with_mark = dct['reps_with_mark']
        event.normalized_reps = dct['normalized_reps']
        event.normalized_reps_with_mark = dct['normalized_reps_with_mark']
        event.content_rep_list = dct['content_rep_list']
        event.pas = PAS.load(dct['pas'])
        event.features = Features.load(dct['features'])
        Event.__evid = event.evid
        return event

    def push_bp(self, bp):
        """Push a basic phrase.

        Args:
            bp (BasicPhrase): A basic phrase.

        """
        if not bp.is_omitted:
            bp.set_adnominal_evids(list(map(
                lambda r: r.modifier_evid,
                filter(lambda r: r.head_tid == bp.tid, self.adnominal_relations)
            )))
            bp.set_sentential_complement_evids(list(map(
                lambda r: r.modifier_evid,
                filter(lambda r: r.head_tid == bp.tid, self.sentential_complement_relations)
            )))
        if bp.case:  # argument
            self.pas.arguments[bp.case].push_bp(bp)
        else:  # predicate
            if all(bp not in argument.bpl for argument in self.pas.arguments.values()):
                self.pas.predicate.push_bp(bp)

    def finalize(self):
        """Finalize this instance."""
        self.pas.finalize()
        self.features.finalize()
        for relation in self.outgoing_relations:
            relation.finalize()

        bpl = self.to_basic_phrase_list()
        self.surf = bpl.to_string(space=False)
        self.surf_with_mark = bpl.to_string(mark=True, space=False)
        self.mrphs = bpl.to_string()
        self.mrphs_with_mark = bpl.to_string(mark=True)
        self.normalized_mrphs = bpl.to_string(truncate=True)
        self.normalized_mrphs_with_mark = bpl.to_string(mark=True, truncate=True)
        self.normalized_mrphs_without_exophora = bpl.to_string(truncate=True, needs_exophora=False)
        self.normalized_mrphs_with_mark_without_exophora = bpl.to_string(mark=True, truncate=True, needs_exophora=False)
        self.reps = bpl.to_string('repname', mark=False, truncate=False)
        self.reps_with_mark = bpl.to_string('repname', mark=True, truncate=False)
        self.normalized_reps = bpl.to_string('repname', mark=False, truncate=True)
        self.normalized_reps_with_mark = bpl.to_string('repname', mark=True, truncate=True)
        self.content_rep_list = bpl.to_content_rep_list()

    def to_dict(self):
        """Convert this instance into a dictionary.

        Returns:
            dict: A dictionary storing this instance information.

        """
        return collections.OrderedDict([
            ('event_id', self.evid),
            ('sid', self.sid),
            ('ssid', self.ssid),
            ('rel', [r.to_dict() for r in self.outgoing_relations]),
            ('surf', self.surf),
            ('surf_with_mark', self.surf_with_mark),
            ('mrphs', self.mrphs),
            ('mrphs_with_mark', self.mrphs_with_mark),
            ('normalized_mrphs', self.normalized_mrphs),
            ('normalized_mrphs_with_mark', self.normalized_mrphs_with_mark),
            ('normalized_mrphs_without_exophora', self.normalized_mrphs_without_exophora),
            ('normalized_mrphs_with_mark_without_exophora', self.normalized_mrphs_with_mark_without_exophora),
            ('reps', self.reps),
            ('reps_with_mark', self.reps_with_mark),
            ('normalized_reps', self.normalized_reps),
            ('normalized_reps_with_mark', self.normalized_reps_with_mark),
            ('content_rep_list', self.content_rep_list),
            ('pas', self.pas.to_dict()),
            ('features', self.features.to_dict())
        ])

    def to_basic_phrase_list(self):
        """Convert this instance into a basic phrase list.

        Returns:
            BasicPhraseList: A basic phrase list.

        """
        predicate_bpl = self.pas.predicate.bpl
        argument_bps = []
        last_tid = max(bp.tid for bp in predicate_bpl)
        for argument in filter(lambda x: not x.event_head, self.pas.arguments.values()):
            for bp in filter(lambda x: x.is_omitted or x.tid < last_tid, argument.bpl):
                bp.is_child = True  # treated as a child of the predicate
                argument_bps.append(bp)
        argument_bpl = BasicPhraseList(argument_bps)
        return predicate_bpl + argument_bpl


class Relation(Base):
    """A class to manage relation information.

    Attributes:
        modifier (Event): A modifier event.
        head (Event): A head event.
        modifier_evid (int): The serial event ID of a modifier event.
        head_evid (int): The serial event ID of a head event.
        head_tid (int): The serial tag ID of a head event's head tag.
            A negative value implies that the modifier event does not modify a specific token.
        label (str): A label.
        surf (str): An explicit marker.
        reliable (bool): Whether a syntactic dependency is ambiguous.

    """

    def __init__(self):
        self.modifier = None
        self.head = None
        self.modifier_evid = -1
        self.head_evid = -1
        self.head_tid = -1
        self.label = ''
        self.surf = ''
        self.reliable = False

    @classmethod
    def build(cls, modifier, head, head_tid, label, surf, reliable):
        """Create an instance from language analysis.

        Args:
            modifier (Event): A modifier event.
            head (Event): A head event.
            head_tid (int): The serial tag ID of a head event's head tag.
                A negative value implies that the modifier event does not modify a specific token.
            label (str): A label.
            surf (str): An explicit marker.
            reliable (bool): Whether a syntactic dependency is ambiguous.

        Returns:
            Relation: A relation.

        """
        relation = Relation()
        relation.modifier = modifier
        relation.head = head
        relation.modifier_evid = modifier.evid
        relation.head_evid = head.evid
        relation.head_tid = head_tid
        relation.label = label
        relation.surf = surf
        relation.reliable = reliable
        return relation

    @classmethod
    def load(cls, modifier, head, dct):
        """Create an instance from a dictionary.

        Args:
            modifier (Event): A modifier event.
            head (Event): A head event.
            dct (dict): A dictionary storing relation information.

        Returns:
            Relation: A relation.

        """
        relation = Relation()
        relation.modifier = modifier
        relation.head = head
        relation.modifier_evid = modifier.evid
        relation.head_evid = dct['event_id']
        relation.label = dct['label']
        relation.surf = dct['surf']
        relation.reliable = dct['reliable']
        relation.head_tid = dct['head_tid']
        return relation

    def finalize(self):
        """Finalize this instance."""
        pass

    def to_dict(self):
        """Convert this instance into a dictionary.

        Returns:
            dict: A dictionary storing this relation information.

        """
        return collections.OrderedDict([
            ('event_id', self.head_evid),
            ('label', self.label),
            ('surf', self.surf),
            ('reliable', self.reliable),
            ('head_tid', self.head_tid)
        ])
