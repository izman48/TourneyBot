import random


class InvalidTournamentException(Exception):
    pass


def tournamentCreator(players: list[str]) -> list[list[str]]:

    if len(players) < 8:
        raise InvalidTournamentException("Need at least 8 players for a tournament")

    random.shuffle(players)

    if len(players) == 8:
        return [players[i : i + 2] for i in range(0, len(players), 2)]
    if len(players) == 10:
        threesTeams = [players[i : i + 3] for i in range(0, 6, 3)]
        twosTeams = [players[i : i + 2] for i in range(6, 10, 2)]
        return threesTeams + twosTeams
    if len(players) == 12:
        return [players[i : i + 3] for i in range(0, len(players), 3)]

    raise InvalidTournamentException("Tournament size not supported")
