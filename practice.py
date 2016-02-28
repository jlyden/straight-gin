import random

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
    Determine if this is winning hand in StraightGin

    hand: list of strings

    Returns bool
    """
    cleanHand = []
    for card in hand:                        
        newCard = card.replace('-','')
        # if face card
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
    melds = 0  
    
    # split by suit
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

    for suit in suits:
        suit.sort()
            
    return suits

userAHand, deck = dealHand(10, FULL_DECK)
userBHand, deck = dealHand(10, deck)

suitsA = testHand(userAHand)
suitsB = testHand(userBHand)
