import logging
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
    Determine if this is winning hand in StraightGin

    hand: list of strings

    Returns bool
    """
    # sort hand
    # first split by suit

    # test if there are at least 3 cards of each suit
    # if not, FALSE
    # test if the cards in each suit are sequential (a run)
    # if x-1 is in string, if x+1 is in string
    # if not, test if multiples found in other suits
    # if not, FALSE
    # if so, TRUE
