import random
from itertools import groupby

FULL_DECK = ['H-A','H-2','H-3','H-4','H-5','H-6','H-7',
             'H-8','H-9','H-10','H-J','H-Q','H-K',
             'D-A','D-2','D-3','D-4','D-5','D-6','D-7',
             'D-8','D-9','D-10','D-J','D-Q','D-K',
             'C-A','C-2','C-3','C-4','C-5','C-6','C-7',
             'C-8','C-9','C-10','C-J','C-Q','C-K',
             'S-A','S-2','S-3','S-4','S-5','S-6','S-7',
             'S-8','S-9','S-10','S-J','S-Q','S-K']

LIBRARY = {'A': '1', 'J': '11', 'Q': '12', 'K': '13'}


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
            newerCard = newerCard + LIBRARY[newCard[1]]
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

# Test Suite
# 1 long run
A = ['C-2', 'C-3', 'C-4', 'C-5', 'C-6', 'C-7', 'C-8', 'C-9', 'C-10', 'C-11']
# 2 runs in 1 suit - fail
B = ['C-2', 'C-3', 'C-4', 'C-5', 'C-8', 'C-9', 'C-10', 'C-11', 'C-12', 'C-13']
# 2 runs in 2 suits
C = ['H-2', 'H-3', 'H-4', 'C-7', 'C-8', 'C-9', 'C-10', 'C-11', 'C-12', 'C-13']
# 3 runs in 2 suits - fail
D = ['H-2', 'H-3', 'H-4', 'C-7', 'C-8', 'C-9', 'C-10', 'H-11', 'H-12', 'H-13']
# 3 runs in 3 suits
E = ['H-2', 'H-3', 'H-4', 'C-7', 'C-8', 'C-9', 'C-10', 'D-11', 'D-12', 'D-13']
# 3 sets
F = ['C-2', 'D-2', 'H-2', 'S-2', 'D-6', 'H-6', 'C-6', 'D-10', 'C-10', 'H-10']
# 2 runs + 1 set
G = ['H-2', 'H-3', 'H-4', 'C-7', 'C-8', 'C-9', 'C-10', 'C-2', 'D-2', 'S-2']
# 1 run + 2 sets
F = ['H-2', 'H-3', 'H-4', 'S-6', 'D-6', 'H-6', 'C-6', 'D-10', 'C-10', 'H-10']
# 2 runs + 1 set of 2 cards
H = ['H-2', 'H-3', 'H-4', 'C-7', 'C-8', 'C-9', 'C-10', 'C-11', 'D-7', 'S-7']
# 2 runs + 1 set of 1 card - fail
I = ['H-2', 'H-3', 'H-4', 'H-5', 'C-5', 'C-6', 'C-7', 'C-8', 'C-9', 'S-5']
# 1 run + 2 sets of 2 cards, where two borrowed cards at at either end of run
J = ['H-2', 'H-3', 'H-4', 'H-5', 'H-6', 'H-7', 'C-7', 'S-7', 'C-2', 'S-2']
# 1 run + 2 sets of 2 cards, , where two borrowed cards are sequential at front of run
K = ['H-2', 'H-3', 'H-4', 'H-5', 'H-6', 'H-7', 'C-2', 'S-2', 'C-3', 'S-3']
# 1 run + 2 sets of 2 cards, , where two borrowed cards are sequential at end of run
L = ['H-2', 'H-3', 'H-4', 'H-5', 'H-6', 'H-7', 'C-7', 'S-7', 'C-6', 'S-6']

hands = [A,B,C,D,E,F,G,H,I,J,K,L]

def test():
    counter = 1
    for hand in hands:
        if len(hand) != 10:
            print 'Wrong number of cards: ', len(hand)
        else:
            penalty = testHand(hand)
            if penalty != 0:
                print 'Hand ', counter, ' fails.'
                print hand
            else:
                print 'Hand ', counter, ' passes.'
                print 'Penalty: ', penalty
        counter += 1

jenny, deck = dealHand(10, FULL_DECK)
faceUpCard, deck = dealHand(1, deck)
print jenny
print faceUpCard
jenny += faceUpCard
print jenny

def endMove(move, hand):
    move = move.split()
    print move[0]
    
    if move[0] in hand:
        hand.remove(move[0])
    faceUpCard = ''.join(move[0])

    return faceUpCard, hand