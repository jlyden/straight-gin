# utility functions for StraightGinAPI

#import logging ?
import random
import constants
from itertools import groupby
from google.appengine.ext import ndb
import endpoints

def get_by_urlsafe(urlsafe, model):
    """Returns an ndb.Model entity that the urlsafe key points to. Checks
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
        ValueError:"""
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


def dealHand(deal, deck):
    """
    Return list of strings of quantity "deal" and remaining strings in "deck"

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


def testHand(hand):
    """
    Calculate deadwood penalty of StraightGin hand

    hand: list of strings

    Returns integer penalty of unplayable ("deadwood") cards in hand

    Resources consulted:
    http://stackoverflow.com/questions/7352684/how-to-find-the-groups-of-consecutive-elements-from-an-array-in-numpy
    https://docs.python.org/2/library/itertools.html#itertools.groupby
    http://stackoverflow.com/questions/1450111/delete-many-elements-of-list-python
    http://stackoverflow.com/questions/7025581/how-can-i-group-equivalent-items-together-in-a-python-list
    """

    suits = cleanHand(hand)

    # set up variables
    longRuns = []
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
                    # store longRuns to help with sets later
                    if len(group) > 3:
                        longRuns.append(group)
                    # remove cards used in run from suit
                    suit[:] = [item for i,item in enumerate(suit) if item not in group]

            # after removing from suit all cards in run-groups,
            # dump remaining cards in suit to leftovers
            leftovers += suit

        # if too few cards in suit for a run, add cards in suit to leftovers
        else:
            leftovers += suit

    # look for sets in leftovers

    # check leftovers for sets of duplicates
    # (twice in case of buried last-cards)
    leftovers, longRuns = checkSets(leftovers, longRuns)
    leftovers, longRuns = checkSets(leftovers, longRuns)

    # calculate penalty (face card pts != 10)
    penalty = sum(leftovers)
    return penalty


def cleanHand(hand):
    """
    Remove '-' & face-card letters from human-readable card representations
    Split hand by suit & strip suit-letters

    hand: list of strings

    Returns list of lists, where each inner list includes cards of same suit
    """

    cleanHand = []
    for card in hand:
        newCard = card.replace('-','')
        # if face card, replace with numerical equivalent
        if ord(newCard[1]) in xrange(ord('A'), ord('Z')+1):
            newerCard = newCard[0]
            newerCard = newerCard + constants.LIBRARY[newCard[1]]
            cleanHand.append(newerCard)
        else:
            cleanHand.append(newCard)

    # set up variables
    clubs = []
    spades = []
    hearts = []
    diamonds = []
    suits = [clubs, spades, hearts, diamonds]

    for card in cleanHand:
        if card[0] == 'C':
            newcard = int(card[1:])
            clubs.append(newcard)
        elif card[0] == 'S':
            newcard = int(card[1:])
            spades.append(newcard)
        elif card[0] == 'H':
            newcard = int(card[1:])
            hearts.append(newcard)
        elif card[0] == 'D':
            newcard = int(card[1:])
            diamonds.append(newcard)

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


def checkSets(leftovers, longRuns):
    """
    Sort & group leftovers by number
    Remove sets of 3 or 4 cards of same value from leftovers
    Look in longRuns (where run > 3) for completion cards for 1 or 2 card sets

    Return transformed leftovers & longRuns
    """
    # group leftovers by number
    leftovers.sort()
    sets = [list(g) for k,g in groupby(leftovers)]
    for set in sets:

        # if set of 3 or 4, remove cards from leftovers
        if len(set) == 3 or len(set) == 4:
            leftovers[:] = [item for i,item in enumerate(leftovers) if item not in set]

        # if set of 2 or 1, look for help in longRuns
        elif len(set) == 2 or len(set) == 1:
            for run in longRuns:
                # if number in set is first or last item in longRun
                # we can finish the set with that card!
                # 1) remove set cards from leftovers
                # 2) remove run from longRun
                # 3) if run > 4 (long enough to remove one card and still be a longRun),
                #    put newrun (without the set card) back in longRun
                if set[0] == run[0]:
                    leftovers[:] = [item for i,item in enumerate(leftovers) if item not in set]
                    longRuns.remove(run)
                    if len(run) > 4:
                        newrun = run[1:]
                        longRuns.append(newrun)
                elif set[0] == run[-1]:
                    leftovers[:] = [item for i,item in enumerate(leftovers) if item not in set]
                    longRuns.remove(run)
                    if len(run) > 4:
                        newrun = run[:-1]
                        longRuns.append(newrun)
    return leftovers, longRuns
