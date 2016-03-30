# Full Stack Nanodegree Project 4 - Straight Gin
# Built by jennifer lyden on provided Tic-Tac-Toe template
#
# utility functions for Straight_Gin_API

import logging
import constants
import endpoints
import random
from itertools import groupby
from google.appengine.ext import ndb


def get_by_urlsafe(urlsafe, model):
    """
    Returns an ndb.Model entity that the urlsafe key points to. Checks
        that the type of entity returned is of the correct kind. Raises an
        error if the key String is malformed or the entity is of the incorrect
        kind
    Args:
        urlsafe: A urlsafe key string
        model: The expected entity kind
    Returns:
        The entity that the urlsafe Key string points to or None if no entity
        exists.
    Raises:
        ValueError
    This function is used verbatim from Tic-Tac-Toe Template
    """
    try:
        key = ndb.Key(urlsafe=urlsafe)
    except TypeError:
        raise endpoints.BadRequestException('Invalid Key')
    except Exception, e:
        if e.__class__.__name__ == 'ProtocolBufferDecodeError':
            raise endpoints.BadRequestException('Invalid Key')
        else:
            raise

    entity = key.get()
    if not entity:
        return None
    if not isinstance(entity, model):
        raise ValueError('Incorrect Kind')
    return entity


def deal_hand(deal, deck):
    """
    Return list of strings of quantity "deal"
        and list of remaining strings in "deck"
    deal: positive integer
    deck: list of strings
    """
    hand = []
    try:
        for i in range(deal):
            card = random.choice(deck)
            hand.append(card)
            deck.remove(card)
        return hand, deck
    except IndexError:
        return None, [0]


def test_hand(hand):
    """
    Calculate deadwood penalty of Straight_Gin hand
    hand: list of strings
    Return integer penalty of unplayable ("deadwood") cards in hand

    Resources consulted:
    http://stackoverflow.com/questions/7352684/how-to-find-the-groups-of-consecutive-elements-from-an-array-in-numpy
    https://docs.python.org/2/library/itertools.html#itertools.groupby
    http://stackoverflow.com/questions/1450111/delete-many-elements-of-list-python
    http://stackoverflow.com/questions/7025581/how-can-i-group-equivalent-items-together-in-a-python-list
    """
    suits = clean_hand(hand)

    # set up variables
    long_runs = []
    leftovers = []

    # look for runs within each suit
    for suit in suits:
        suit.sort()
        # if at least 3 cards in suit, test for a run
        if len(suit) > 2:
            groups = group_consecutives(suit)
            for group in groups:
                # if group is run of at least 3 different numbers
                if len(group) > 2 and group[0] != group[-1]:
                    # store long_runs to help with sets later
                    if len(group) > 3:
                        long_runs.append(group)
                    # remove cards used in run from suit
                    suit[:] = [item for i, item in enumerate(suit)
                               if item not in group]
            # after removing from suit all cards in run-groups,
            # dump remaining cards in suit to leftovers
            leftovers += suit
        # if too few cards in suit for a run, add cards in suit to leftovers
        else:
            leftovers += suit

    # check leftovers for sets of duplicate numbers
    leftovers, long_runs = check_sets(leftovers, long_runs)
    # (twice in case of buried last cards)
    leftovers, long_runs = check_sets(leftovers, long_runs)

    # calculate penalty (face card pts != 10)
    penalty = sum(leftovers)
    return penalty


def clean_hand(hand):
    """
    Remove '-' & face-card letters from human-readable card representations
    Split hand by suit & strip suit-letters

    hand: list of strings
    Return list of lists, where each inner list includes cards of same suit
    """
    clean_hand = []
    for card in hand:
        # remove - from card representation
        strip_card = card.replace('-', '')
        # if face card, replace with numerical equivalent (i.e. J = Jack = 11)
        if ord(strip_card[1]) in xrange(ord('A'), ord('Z')+1):
            # Keep letter for suit
            number_card = strip_card[0]
            # But change letter for face card (i.e. J for Jack) to number
            number_card = number_card + constants.LIBRARY[strip_card[1]]
            clean_hand.append(number_card)
        # Just add non-face cards without transformation
        else:
            clean_hand.append(strip_card)

    # set up variables
    clubs = []
    diamonds = []
    hearts = []
    spades = []
    suits = [clubs, diamonds, hearts, spades]

    for card in clean_hand:
        if card[0] == 'C':
            # add to club set, but strip letter from card representation
            just_number = int(card[1:])
            clubs.append(just_number)
        elif card[0] == 'D':
            just_number = int(card[1:])
            diamonds.append(just_number)
        elif card[0] == 'H':
            just_number = int(card[1:])
            hearts.append(just_number)
        elif card[0] == 'S':
            just_number = int(card[1:])
            spades.append(just_number)
    return suits


def group_consecutives(vals, step=1):
    """
    Return list of consecutive lists of numbers from vals (number list).

    Source:
    http://stackoverflow.com/questions/7352684/how-to-find-the-groups-of-consecutive-elements-from-an-array-in-numpy
    """
    run = []
    result = [run]
    expect = None
    for v in vals:
        if (v == expect) or (expect is None):
            run.append(v)
        else:
            run = [v]
            result.append(run)
        expect = v + step
    return result


def check_sets(leftovers, long_runs):
    """
    Sort & group leftovers by number
    Remove sets of 3 or 4 cards of same value from leftovers
    Look in long_runs (where run > 3) for completion cards for 1 or 2 card sets

    Return transformed leftovers & long_runs
    """
    # group leftovers by number
    leftovers.sort()
    sets = [list(g) for k, g in groupby(leftovers)]
    for set in sets:
        # if set of 3 or 4, just remove cards from leftovers
        if len(set) == 3 or len(set) == 4:
            leftovers[:] = [item for i, item in enumerate(leftovers)
                            if item not in set]
        # if set of 2 or 1, look for help in long_runs
        elif len(set) == 2 or len(set) == 1:
            for run in long_runs:
                # if number in set is first or last value in a long_run,
                # we can finish the set with that card!
                # 1) remove set cards from leftovers
                # 2) remove run from long_run
                # 3) if run > 4 (long enough to remove one card and still
                #    BE a long_run), put new_run (without the used set card)
                #    back in long_run
                if set[0] == run[0]:
                    leftovers[:] = [item for i, item in enumerate(leftovers)
                                    if item not in set]
                    long_runs.remove(run)
                    if len(run) > 4:
                        new_run = run[1:]
                        long_runs.append(new_run)
                elif set[0] == run[-1]:
                    leftovers[:] = [item for i, item in enumerate(leftovers)
                                    if item not in set]
                    long_runs.remove(run)
                    if len(run) > 4:
                        new_run = run[:-1]
                        long_runs.append(new_run)
    return leftovers, long_runs


def pre_move_verification(game, user):
    """
    Return true if pass all verifications: is game over, is this correct user.
    """
    if game_exists(game):
        if game.game_over:
            raise endpoints.NotFoundException('Game already over')
        elif not user:
            raise endpoints.NotFoundException('User not found')
        elif user.key != game.active_player:
            raise endpoints.BadRequestException('Not your turn!')
        else:
            return True


def game_exists(game):
    """
    Verify that game exists
    """
    if not game:
        raise endpoints.NotFoundException('Game not found')
    else:
        return True


def limit_set(input):
    """
    Validate input for get_high_scores
    """
    if not input.isdigit():
        raise endpoints.BadRequestException('Number_of_results must '
                                            'be an integer.')
    if int(input) < 1:
        raise endpoints.BadRequestException('Number_of_results requested must '
                                            'be greater than zero.')
    return True
