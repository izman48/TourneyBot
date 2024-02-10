import pytest
from unittest.mock import patch
from src.tournament import tournamentCreator, InvalidTournamentException


@patch("src.tournament.random.shuffle", lambda x: x)
def testTwoVTwoTournamentCreator():
    # Test case 1: TwoVTwo tournament with 8 players
    players = [
        "Player1",
        "Player2",
        "Player3",
        "Player4",
        "Player5",
        "Player6",
        "Player7",
        "Player8",
    ]
    expected_result = [
        ["Player1", "Player2"],
        ["Player3", "Player4"],
        ["Player5", "Player6"],
        ["Player7", "Player8"],
    ]
    assert tournamentCreator(players) == expected_result


@patch("src.tournament.random.shuffle", lambda x: x)
def testThreeVTwoTournamentCreator():
    # Test case 2: ThreeVTwo tournament with 10 players
    players = [
        "Player1",
        "Player2",
        "Player3",
        "Player4",
        "Player5",
        "Player6",
        "Player7",
        "Player8",
        "Player9",
        "Player10",
    ]
    expected_result = [
        ["Player1", "Player2", "Player3"],
        ["Player4", "Player5", "Player6"],
        ["Player7", "Player8"],
        ["Player9", "Player10"],
    ]
    assert tournamentCreator(players) == expected_result


@patch("src.tournament.random.shuffle", lambda x: x)
def testThreeVThreeTournamentCreator():
    # Test case 3: ThreeVThree tournament with 12 players
    players = [
        "Player1",
        "Player2",
        "Player3",
        "Player4",
        "Player5",
        "Player6",
        "Player7",
        "Player8",
        "Player9",
        "Player10",
        "Player11",
        "Player12",
    ]
    expected_result = [
        ["Player1", "Player2", "Player3"],
        ["Player4", "Player5", "Player6"],
        ["Player7", "Player8", "Player9"],
        ["Player10", "Player11", "Player12"],
    ]
    assert tournamentCreator(players) == expected_result


@patch("src.tournament.random.shuffle", lambda x: x)
def testLessThanEightPlayersTournamentCreatorFails():
    # Test case 4: InvalidTournamentException - less than 8 players
    players = ["Player1", "Player2", "Player3", "Player4", "Player5"]
    try:
        tournamentCreator(players)
        assert False, "Expected InvalidTournamentException"
    except InvalidTournamentException as e:
        assert str(e) == "Need at least 8 players for a tournament"


@pytest.mark.parametrize(
    "players",
    [
        (["Player" + str(i) for i in range(1, 10)]),  # 9 players
        (["Player" + str(i) for i in range(1, 12)]),  # 11 players
        (["Player" + str(i) for i in range(1, 16)]),  # 15 players
    ],
)
@patch("src.tournament.random.shuffle", lambda x: x)
def testOtherComboTournamentCreatorFails(players):
    try:
        tournamentCreator(players)
        assert False, "Expected InvalidTournamentException"
    except InvalidTournamentException as e:
        assert str(e) == "Tournament size not supported"