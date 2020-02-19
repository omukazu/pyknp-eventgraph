"""A wrapper class of pyknp.Tag."""
import collections
from typing import List, Tuple, Union

from pyknp import Tag

from pyknp_eventgraph.helper import (
    PAS_ORDER,
    convert_mrphs_to_midasi_list,
    convert_mrphs_to_repname_list
)
from pyknp_eventgraph.relation import Relation


class BasicPhrase:
    """A class to manage basic phrase information.

    Attributes:
        tag (Tag): A tag.
        ssid (int): A serial sentence ID.
        bid (int): A serial bunsetsu ID.
        tid (int): A serial tag ID.
        is_modifier (bool): Whether this basic phrase is a modifier or not.
        is_possessive (bool): Whether this basic phrase is a possessive or not.
        is_child (bool): Whether this basic phrase is a child of another one or not.
        omitted_case (str): An omitted case.
        adnominal_evids (List[int]): A list of adnominal event IDs.
        sentential_complement_evids (List[int]): A list of sentential complement event IDs.
        exophora (str): The type of exophora.

    """

    def __init__(self, tag_or_midasi, ssid=-1, bid=-1, is_child=False, omitted_case=''):
        """Initialize a BasicPhrase instance.

        Args:
            tag_or_midasi (Union[Tag, str]): A tag or the midasi (surface string).
            ssid (int): A serial sentence ID.
            bid (int): A serial bunsetsu ID.
            is_child (bool): Whether this basic phrase is a child of another one or not.
            omitted_case (str): An omitted case.

        """
        self.tag = None
        self.exophora = ''
        self.ssid = ssid
        self.bid = bid
        self.tid = -1
        self.is_modifier = False
        self.is_possessive = False
        self.is_child = is_child
        self.omitted_case = omitted_case
        self.adnominal_evids = []
        self.sentential_complement_evids = []

        if isinstance(tag_or_midasi, Tag):
            self.tag = tag_or_midasi
            self.tid = self.tag.tag_id
            self.is_modifier = '修飾' in self.tag.features
            self.is_possessive = self.tag.features.get('係', '') == 'ノ格'
        elif isinstance(tag_or_midasi, str):
            self.exophora = tag_or_midasi
        else:
            raise NotImplementedError

    def assign_modifier_evids(self, incoming_relations):
        """Assign modifier event IDs.

        Args:
            incoming_relations (List[Relation]): A list of relations, where the heads are in this event.

        """
        if not self.omitted_case:
            for r in incoming_relations:
                if r.label == '連体修飾' and r.head_tid == self.tid:
                    self.adnominal_evids.append(r.modifier_evid)
                if r.label == '補文' and r.head_tid == self.tid:
                    self.sentential_complement_evids.append(r.modifier_evid)

    def to_string(self, type_, normalize, truncate, normalizes_child_bp=False):
        """Convert this instance into a string based on given parameters.

        Args:
            type_ (str): A type of string, which can take either `midasi` or `repname`.
            normalize (str): A normalization target, which can take either `predicate`, `argument`, or `none`.
            truncate (bool): Whether to truncate adjunct strings or not.
            normalizes_child_bp (bool): Whether to normalize child basic phrases or not.

        Returns:
            Tuple[List[str], List[str], bool]: Content strings, adjunct strings, and a flag which indicates that
                a normalization process has been performed or not

        """
        assert type_ in {'midasi', 'repname'}, '`type_` must be either midasi or repname'
        assert normalize in {'predicate', 'argument', 'none'}, '`normalize` must be either predicate, argument, or none'

        def _normalize_none():
            _content_strings = []
            _adjunct_strings = []
            _is_after_normalization = False

            if type_ == 'midasi':
                _content_strings = convert_mrphs_to_midasi_list(self.tag.mrph_list())
            else:
                _content_strings = convert_mrphs_to_repname_list(self.tag.mrph_list())
            _adjunct_strings = []

            return _content_strings, _adjunct_strings, _is_after_normalization

        def _normalize_predicate(_truncate):
            _content_strings = []
            _adjunct_strings = []
            _is_after_normalization = False

            mrphs = self.tag.mrph_list()

            # find the position of the morpheme to be normalized
            slicer = -1
            normalization_type = 'genkei'
            for i, m in reversed(list(enumerate(mrphs))):
                # adjective + 'です' -> ignore 'です' (e.g., 美しいです -> 美しい)
                if m.hinsi == '助動詞' and m.genkei == 'です' and 0 < i and mrphs[i - 1].hinsi == '形容詞':
                    slicer = i
                    break
                # adjective or verb +'じゃん' -> ignore 'じゃん' (e.g., 使えないじゃん -> 使えない)
                if m.hinsi == '判定詞' and m.midasi == 'じゃ' and 0 < i and '<活用語>' in mrphs[i - 1].fstring:
                    slicer = i
                    break
                # check the last word with conjugation except some meaningless words
                if ('<活用語>' in m.fstring or '<用言意味表記末尾>' in m.fstring) \
                        and m.genkei not in {'のだ', 'んだ'}:
                    slicer = i + 1
                    # 'ぬ' -> midasi
                    if m.hinsi == '助動詞' and m.genkei == 'ぬ':
                        normalization_type = 'midasi'
                    break

            # if `truncate` is False, update the normalization type to 'midasi'
            if _truncate is False:
                normalization_type = 'midasi'

            # do a normalization process
            if slicer == -1:
                if type_ == 'midasi':
                    _content_strings = convert_mrphs_to_midasi_list(mrphs)
                else:
                    _content_strings = convert_mrphs_to_repname_list(mrphs)
                _adjunct_strings = []
            else:
                if type_ == 'midasi':
                    _content_strings = convert_mrphs_to_midasi_list(mrphs[:slicer - 1])
                    normalizer = getattr(mrphs[slicer - 1], normalization_type)
                    _content_strings.append(normalizer)
                    _adjunct_strings = convert_mrphs_to_midasi_list(mrphs[slicer:])
                elif type_ == 'repname':
                    _content_strings = convert_mrphs_to_repname_list(mrphs[:slicer])
                    _adjunct_strings = convert_mrphs_to_repname_list(mrphs[slicer:])
                _is_after_normalization = True

            return _content_strings, _adjunct_strings, _is_after_normalization

        def _normalize_argument(_truncate):
            _content_strings = []
            _adjunct_strings = []
            _is_after_normalization = False

            mrphs = self.tag.mrph_list()

            # find the position of the morpheme to be normalized
            slicer = -1
            normalization_type = 'genkei' if _truncate else 'midasi'

            def exists_content_words_before_index(index):
                return any(m.hinsi not in ('助詞', '特殊', '判定詞') for m in mrphs[:index])

            for i, m in enumerate(mrphs):
                if m.hinsi in ('助詞', '特殊', '判定詞') and exists_content_words_before_index(i):
                    slicer = i
                    break

            # do a normalization process
            if slicer == -1:
                if type_ == 'midasi':
                    _content_strings = convert_mrphs_to_midasi_list(mrphs[:-1])
                    normalizer = getattr(mrphs[-1], normalization_type)
                    _content_strings.append(normalizer)
                else:
                    _content_strings = convert_mrphs_to_repname_list(mrphs)
                _adjunct_strings = []
                _is_after_normalization = True
            else:
                if type_ == 'midasi':
                    _content_strings = convert_mrphs_to_midasi_list(mrphs[:slicer - 1])
                    normalizer = getattr(mrphs[slicer - 1], normalization_type)
                    _content_strings.append(normalizer)
                    _adjunct_strings = convert_mrphs_to_midasi_list(mrphs[slicer:])
                elif type_ == 'repname':
                    _content_strings = convert_mrphs_to_repname_list(mrphs[:slicer])
                    _adjunct_strings = convert_mrphs_to_repname_list(mrphs[slicer:])
                _is_after_normalization = True

            return _content_strings, _adjunct_strings, _is_after_normalization

        content_strings = []
        adjunct_strings = []
        is_after_normalization = False

        if self.omitted_case:
            if self.exophora:
                content_strings = [self.exophora]
            else:
                content_strings, _, _ = _normalize_argument(_truncate=True)

            omission = self.convert_katakana_to_hiragana(self.omitted_case)
            omission = omission if type_ == 'midasi' else '{}/{}'.format(omission, omission)

            if normalize == 'argument':
                adjunct_strings = [omission]
                is_after_normalization = True
            else:
                content_strings.append(omission)
                adjunct_strings = []
        else:
            if normalize == 'none' or (self.is_child is True and normalizes_child_bp is False):
                content_strings, adjunct_strings, is_after_normalization = _normalize_none()
            elif normalize == 'predicate':
                content_strings, adjunct_strings, is_after_normalization = _normalize_predicate(_truncate=truncate)
            elif normalize == 'argument':
                content_strings, adjunct_strings, is_after_normalization = _normalize_argument(_truncate=truncate)

        return content_strings, adjunct_strings, is_after_normalization

    def __repr__(self):
        """Print this instance.

        Returns:
            str: A string which represents this instance.

        """
        content_strings, _, _ = self.to_string('midasi', normalize='none', truncate=False)
        content_string = ' '.join(content_strings)
        omission = self.omitted_case if self.omitted_case else 'none'
        return 'BP({}, ssid={}, bid={}, omission={})'.format(content_string, self.ssid, self.bid, omission)

    def index(self):
        """Return the index.

        Returns:
            Tuple[int, int, str]: A tuple of ssid, tid, and omitted_case.

        """
        return self.ssid, self.tid, self.omitted_case

    @staticmethod
    def convert_katakana_to_hiragana(in_str):
        """Convert katakana characters in a given string to their corresponding hiragana characters.

        Args:
            in_str (str): A string.

        Returns:
            str: A string, where katakana characters have been converted into hiragana.

        """
        return "".join(chr(ord(ch) - 96) if ("ァ" <= ch <= "ン") else ch for ch in in_str)


def convert_basic_phrases_to_string(bps, type_='midasi', mark=False, space=True, normalize='predicate', truncate=False,
                                    needs_exophora=True, normalizes_child_bps=False):
    """Convert basic phrases into a string.

    Args:
        bps (List[BasicPhrase]): A list of basic phrases.
        type_ (str): A type of string, which can take either `midasi` or `repname`.
        mark (bool): Whether to include special marks or not.
        space (bool): Whether to include white spaces between morphemes or not.
        normalize (str): A normalization target, which can take either `predicate` or `argument`.
        truncate (bool): Whether to truncate the latter of the normalized token or not.
        needs_exophora (bool): Whether to include exophora or not.
        normalizes_child_bps (bool): Whether to normalize child basic phrases or not.

    Returns:
        str: A string converted from the given basic phrases.

    """
    omitted_string_fragments = []
    content_string_fragments = []
    adjunct_string_fragments = []

    joiner = ' ' if space else ''

    is_after_normalization = False
    prev_bp = None

    for bnst_bps in group_basic_phrases_by_sbid(bps):
        exophora = ''
        omitted_case = ''
        needs_adnominal = False
        needs_sentential_complement = False
        for bp in bnst_bps:
            exophora = exophora or bp.exophora
            omitted_case = omitted_case or bp.omitted_case
            if mark and bp.adnominal_evids:
                needs_adnominal = True
            if mark and bp.sentential_complement_evids:
                needs_sentential_complement = True

        if needs_exophora is False and exophora:
            continue

        content_bps = []
        adjunct_bps = []
        for bp in bnst_bps:
            if prev_bp:
                # add a separator mark (|) when the following conditions are satisfied
                # 0. the current base phrase skips some units
                cond0 = prev_bp.ssid == bp.ssid and prev_bp.tid + 1 < bp.tid
                # 1. the previous base phrase is not omitted (to avoid "[...] | ...")
                cond1 = not prev_bp.omitted_case
                # 2. there is no other marks (to avoid "▼ | ..." and "■ | ...")
                cond2 = not needs_adnominal and not needs_sentential_complement
                needs_separator = mark and all((cond0, cond1, cond2))
            else:
                needs_separator = False

            # convert bps into content strings and adjunct strings
            if is_after_normalization:
                content_mrphs = []
                adjunct_mrphs, _, _ = bp.to_string(
                    type_,
                    normalize='none',
                    truncate=truncate,
                    normalizes_child_bp=normalizes_child_bps
                )
            else:
                content_mrphs, adjunct_mrphs, is_after_normalization_ = bp.to_string(
                    type_,
                    normalize=normalize,
                    truncate=truncate,
                    normalizes_child_bp=normalizes_child_bps
                )

                # check the normalization process has been performed
                is_after_normalization = is_after_normalization or is_after_normalization_

                # add a separator mark
                if needs_separator:
                    content_mrphs.insert(0, '|' if space else ' | ')

            # overwrite the result in a special case
            if omitted_case and normalize == 'argument' and not truncate:
                content_mrphs.extend(adjunct_mrphs)
                adjunct_mrphs = []
                is_after_normalization = False

            if content_mrphs:
                content_bps.extend(content_mrphs)
            if adjunct_mrphs:
                adjunct_bps.extend(adjunct_mrphs)

            prev_bp = bp

        if content_bps:
            content_bnst_string = joiner.join(content_bps)
            if omitted_case:
                omitted_string_fragments.append('[{}]'.format(content_bnst_string))
            elif needs_adnominal:
                content_string_fragments.append('▼ {}'.format(content_bnst_string))
            elif needs_sentential_complement:
                content_string_fragments.append('■ {}'.format(content_bnst_string))
            else:
                content_string_fragments.append(content_bnst_string)

        if adjunct_bps:
            adjunct_bnst_string = joiner.join(adjunct_bps)
            adjunct_string_fragments.append(adjunct_bnst_string)

    omitted_string = ''.join(omitted_string_fragments)
    content_string = joiner.join(content_string_fragments)
    adjunct_string = joiner.join(adjunct_string_fragments)

    if omitted_string:
        content_string = '{} {}'.format(omitted_string, content_string) if content_string else omitted_string

    if truncate or not adjunct_string:
        return content_string
    else:
        if mark:
            return '{} ({})'.format(content_string, adjunct_string)
        else:
            return joiner.join((content_string, adjunct_string))


def convert_basic_phrases_to_content_rep_list(bps):
    """Convert basic phrases into a list of the representative strings of content words.

    Args:
        bps (List[BasicPhrase]): A list of basic phrases.

    Returns:
        List[str]: A list of the representative strings of content words.

    """
    content_reps = []
    for bnst_bps in group_basic_phrases_by_sbid(bps):
        for bp in filter(lambda x: x.tag, bnst_bps):
            for m in bp.tag.mrph_list():
                if any(feature in m.fstring for feature in ('<内容語>', '<準内容語>')):
                    content_reps.extend(convert_mrphs_to_repname_list([m]))
    return content_reps


def group_basic_phrases_by_sbid(bps):
    """Group basic phrases based on their ssid and bid.

    Args:
        bps (List[BasicPhrase]): A list of basic phrases.

    Returns:
        List[List[BasicPhrase]]: A list of lists of basic phrases.

    """
    sbid_bps_map = collections.defaultdict(list)
    for bp in bps:
        sbid_bps_map[(bp.ssid, bp.bid, bp.omitted_case)].append(bp)

    bunsetsu_bps_list = []
    for sbid in sorted(sbid_bps_map, key=lambda x: (PAS_ORDER.get(x[2], 99), x[0], x[1])):
        bunsetsu_bps_list.append(sorted(sbid_bps_map[sbid], key=lambda x: x.tid))
    return bunsetsu_bps_list
