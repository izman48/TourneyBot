import pytest
import pytest_asyncio
import discord
from unittest.mock import Mock, AsyncMock, patch
from src.tourneyBot import DudeBot


@pytest_asyncio.fixture
async def client():
    client = DudeBot()
    client.bot_id = "123"
    return client


@pytest.fixture
def mock_message():
    message = Mock(spec=discord.Message)
    message.mentions = [Mock(spec=discord.Member)]
    message.mentions[0].id = "123"
    message.content = "@TourneyBot create"
    message.author = Mock(spec=discord.Member)
    message.author.id = "456"
    message.author.voice = Mock()
    message.author.voice.channel = Mock()
    message.channel = AsyncMock()

    # Add 8 players to the voice channel
    message.author.voice.channel.members = []
    for letter in "ABCDEFGH":
        member = Mock(spec=discord.Member)
        member.name = letter
        message.author.voice.channel.members.append(member)

    return message


@pytest.fixture
def mock_reaction(mock_message):
    reaction = Mock(spec=discord.Reaction)
    reaction.message = Mock(spec=discord.Message)
    reaction.message.id = "789"
    reaction.message.channel = AsyncMock()
    return reaction


@pytest.fixture
def mock_user():
    user = Mock(spec=discord.Member)
    user.id = "456"  # Same as tournament creator
    return user


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "emoji,user_id,should_send",
    [
        ("🔁", "456", True),  # Tournament creator can reroll
        ("🔁", "789", False),  # Other user cannot reroll
        ("✅", "456", True),  # Tournament creator can confirm
        ("✅", "789", False),  # Other user cannot confirm
    ],
)
async def test_reaction_handling(client, mock_reaction, emoji, user_id, should_send):
    # Setup
    client.current_team_message = mock_reaction.message
    client.tournament_creator = "456"  # Original creator's ID
    client.players = [f"Player{i}" for i in range(1, 9)]

    mock_reaction.emoji = emoji
    test_user = Mock(spec=discord.Member)
    test_user.id = user_id

    # Test
    await client.on_reaction_add(mock_reaction, test_user)

    # Verify
    if should_send:
        mock_reaction.message.channel.send.assert_called_once()
    else:
        mock_reaction.message.channel.send.assert_not_called()


@pytest.mark.asyncio
async def test_end_to_end_workflow(client, mock_message, mock_user, subtests):
    with subtests.test(msg="Initial team creation"):
        # Test initial creation
        await client.on_message(mock_message)
        assert client.tournament_creator == "456"
        assert client.current_team_message is not None
        assert len(client.teams) == 4

    with subtests.test(msg="Tournament creator can reroll"):
        # Test reroll by creator
        reroll = Mock(spec=discord.Reaction)
        reroll.emoji = "🔁"
        reroll.message = client.current_team_message
        reroll.message.channel = AsyncMock()
        await client.on_reaction_add(reroll, mock_user)
        reroll.message.channel.send.assert_called_once()

    with subtests.test(msg="Other user cannot reroll"):
        # Test reroll by other user (should fail)
        other_user = Mock(spec=discord.Member)
        other_user.id = "789"
        other_reroll = Mock(spec=discord.Reaction)
        other_reroll.emoji = "🔁"
        other_reroll.message = client.current_team_message
        other_reroll.message.channel = AsyncMock()
        await client.on_reaction_add(other_reroll, other_user)
        other_reroll.message.channel.send.assert_not_called()

    with subtests.test(msg="Tournament creator can confirm"):
        # Test confirmation
        confirm = Mock(spec=discord.Reaction)
        confirm.emoji = "✅"
        confirm.message = client.current_team_message
        confirm.message.channel = AsyncMock()
        await client.on_reaction_add(confirm, mock_user)
        confirm.message.channel.send.assert_called_once()
        assert client.current_team_message is None
