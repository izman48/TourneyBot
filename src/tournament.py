import random


class InvalidTournamentException(Exception):
    pass


def teamCreator(players: list[str]) -> list[list[str]]:
    """
    Create teams for a tournament based on the number of players.

    Args:
        players (list[str]): A list of player names.

    Returns:
        list[list[str]]: A list of teams, where each team is represented as a list of player names.

    Raises:
        InvalidTournamentException: If the number of players is less than 8 or not supported.

    """
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


def tournamentGenerator(teams: list[list[str]]) -> str:
    """
    Generate a tournament based on the teams.

    Args:
        teams (list[list[str]]): A list of teams, where each team is represented as a list of player names.

    Returns:
        str: A string representation of the tournament.

    """
    random.shuffle(teams)
    # return team 1 vs team 2, team 3 vs team 4, etc.
    return "\n".join([f"{' '.join(teams[i])} vs {' '.join(teams[i+1])}" for i in range(0, len(teams), 2)])
