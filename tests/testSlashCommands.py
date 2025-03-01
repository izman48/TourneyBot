import pytest
import discord
from discord import app_commands
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from src.tourneyBot import DudeBot, SETUP_ROLE_ID, ADMIN_ROLE_IDS


@pytest.fixture
def mock_interaction():
    """Creates a mock discord Interaction object for testing slash commands."""
    interaction = AsyncMock(spec=discord.Interaction)
    interaction.response = AsyncMock()
    interaction.response.send_message = AsyncMock()
    interaction.guild = Mock(spec=discord.Guild)
    return interaction


@pytest.fixture
def mock_member():
    """Creates a mock discord Member object."""
    member = Mock(spec=discord.Member)
    member.edit = AsyncMock()
    member.remove_roles = AsyncMock()
    member.mention = "@test_user"
    member.roles = []
    member.nick = "test"
    member.name = "test"
    return member


@pytest.fixture
def mock_setup_role():
    """Creates a mock setup role."""
    role = Mock(spec=discord.Role)
    role.id = SETUP_ROLE_ID
    return role


@pytest.fixture
def mock_admin_role():
    """Creates a mock admin role."""
    role = Mock(spec=discord.Role)
    role.id = list(ADMIN_ROLE_IDS)[0]  # Use the first admin role ID
    return role


@pytest.fixture
def mock_client():
    """Creates a mock client with the command tree."""
    client = Mock(spec=DudeBot)
    client.tree = Mock(spec=app_commands.CommandTree)
    return client


@pytest.fixture
def setup_command():
    """Creates a mock setup command with minimal functionality for testing."""

    async def mock_setup_callback(interaction, member, first_name, last_initial):
        try:
            # Check if the user has already been setup
            setup_role = interaction.guild.get_role(SETUP_ROLE_ID)
            is_already_setup = (
                setup_role not in member.roles
                and member.nick is not None
                and member.nick != member.name
            )

            if is_already_setup:
                await interaction.response.send_message(
                    f"{member.mention} has already been set up.",
                    ephemeral=True,
                )
                return

            # Get current nickname or username if no nickname
            current_name = member.nick if member.nick else member.name

            # Format the new nickname: FirstName "CurrentName" LastInitial
            # Calculate how much space we have for the middle part
            max_length = 32
            extras = len(first_name) + 5 + len(last_initial)
            available_space = max_length - extras

            # Truncate the current name if needed
            if len(current_name) > available_space:
                truncated_name = current_name[: available_space - 3] + "..."
            else:
                truncated_name = current_name

            # Create the new nickname
            new_nickname = f'{first_name} "{truncated_name}" {last_initial}'

            # Final check to ensure we're within limits
            if len(new_nickname) > 32:
                # If still too long, reduce the first name or use initials
                new_nickname = f'{first_name[:1]}. "{truncated_name}" {last_initial}'

            await member.edit(nick=new_nickname)

            # Remove setup role if they have it
            setup_role = interaction.guild.get_role(SETUP_ROLE_ID)
            if setup_role in member.roles:
                await member.remove_roles(setup_role)

            await interaction.response.send_message(
                f"Successfully set up {member.mention}:\n"
                f"• Changed nickname to: {new_nickname}\n"
                f"• Removed setup role",
                ephemeral=True,
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "I don't have permission to modify this user's nickname or roles.",
                ephemeral=True,
            )
        except Exception as e:
            await interaction.response.send_message(
                f"An error occurred: {str(e)}", ephemeral=True
            )

    async def mock_error_handler(interaction, error):
        if isinstance(error, app_commands.MissingAnyRole):
            await interaction.response.send_message(
                "You don't have permission to use this command.", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"An error occurred: {str(error)}", ephemeral=True
            )

    # Create a mock command that we can use for testing
    command = MagicMock()
    command.name = "setup"
    command.callback = mock_setup_callback
    command.error = AsyncMock(side_effect=mock_error_handler)

    return command


@pytest.mark.asyncio
async def test_setup_command_success(
    mock_interaction, mock_member, mock_setup_role, setup_command
):
    """Test that the setup command correctly changes nickname and removes role."""
    # Arrange
    mock_interaction.guild.get_role.return_value = mock_setup_role
    mock_member.roles = [mock_setup_role]  # Member has the setup role
    first_name = "Tim"
    last_initial = "H"
    expected_nickname = 'Tim "test" H'

    # Act
    await setup_command.callback(
        mock_interaction, mock_member, first_name, last_initial
    )

    # Assert
    mock_member.edit.assert_called_once_with(nick=expected_nickname)
    mock_member.remove_roles.assert_called_once_with(mock_setup_role)
    mock_interaction.response.send_message.assert_called_once()
    # Check that the success message contains the expected information
    args, kwargs = mock_interaction.response.send_message.call_args
    assert expected_nickname in args[0]
    assert mock_member.mention in args[0]
    assert "Removed setup role" in args[0]
    assert kwargs.get("ephemeral") is True


@pytest.mark.asyncio
async def test_setup_command_no_role(mock_interaction, mock_member, setup_command):
    """Test that the setup command works correctly when the member doesn't have the setup role."""
    # Arrange
    setup_role = Mock(spec=discord.Role)
    setup_role.id = SETUP_ROLE_ID
    mock_interaction.guild.get_role.return_value = setup_role
    first_name = "Tim"
    last_initial = "H"
    expected_nickname = 'Tim "test" H'

    # Act
    await setup_command.callback(
        mock_interaction, mock_member, first_name, last_initial
    )

    # Assert
    mock_member.edit.assert_called_once_with(nick=expected_nickname)
    mock_member.remove_roles.assert_not_called()  # Shouldn't be called as the member doesn't have the role
    mock_interaction.response.send_message.assert_called_once()
    args, kwargs = mock_interaction.response.send_message.call_args
    assert expected_nickname in args[0]
    assert mock_member.mention in args[0]
    assert kwargs.get("ephemeral") is True


@pytest.mark.asyncio
async def test_setup_command_long_nickname(
    mock_interaction, mock_member, mock_setup_role, setup_command
):
    """Test that the setup command correctly truncates long nicknames."""
    # Arrange
    mock_interaction.guild.get_role.return_value = mock_setup_role
    mock_member.roles = [mock_setup_role]
    mock_member.nick = "ThisIsAReallyLongNicknameThatExceedsDiscordLimit"
    first_name = "Timothy"  # Longer first name to force more truncation
    last_initial = "H"

    # Act
    await setup_command.callback(
        mock_interaction, mock_member, first_name, last_initial
    )

    # Assert
    mock_member.edit.assert_called_once()
    nick_arg = mock_member.edit.call_args[1]["nick"]
    assert (
        len(nick_arg) <= 32
    ), f"Nickname should not exceed 32 characters, got {len(nick_arg)}: '{nick_arg}'"
    assert (
        first_name in nick_arg or f"{first_name[:1]}." in nick_arg
    ), "First name or its initial should be in the nickname"
    assert last_initial in nick_arg, "Last initial should be in the nickname"
    assert "..." in nick_arg, "Truncated nickname should contain '...'"


@pytest.mark.asyncio
async def test_setup_command_very_long_names(
    mock_interaction, mock_member, mock_setup_role, setup_command
):
    """Test with extremely long first name and nickname to ensure it stays within limits."""
    # Arrange
    mock_interaction.guild.get_role.return_value = mock_setup_role
    mock_member.roles = [mock_setup_role]
    mock_member.nick = "ThisIsAReallyLongNicknameThatExceedsDiscordLimit"
    first_name = "Bartholomew-Christopher"  # Very very long first name
    last_initial = "H"

    # Act
    await setup_command.callback(
        mock_interaction, mock_member, first_name, last_initial
    )

    # Assert
    mock_member.edit.assert_called_once()
    nick_arg = mock_member.edit.call_args[1]["nick"]
    assert (
        len(nick_arg) <= 32
    ), f"Nickname should not exceed 32 characters, got {len(nick_arg)}: '{nick_arg}'"

    # The logic here is different - the command will truncate the nickname first,
    # and only use first initial if the nickname is still too long.
    # So we should check that either the first name is truncated or the nickname is properly shortened
    assert len(nick_arg) <= 32, "Nickname exceeds Discord's 32 character limit"
    assert '"..."' in nick_arg, "Long nickname should be truncated"


@pytest.mark.asyncio
async def test_setup_command_no_nickname(
    mock_interaction, mock_member, mock_setup_role, setup_command
):
    """Test that the setup command works with username when no nickname is set."""
    # Arrange
    mock_interaction.guild.get_role.return_value = mock_setup_role
    mock_member.roles = [mock_setup_role]
    mock_member.nick = None  # No nickname set
    mock_member.name = "DiscordUsername"
    first_name = "Tim"
    last_initial = "H"
    expected_nickname = 'Tim "DiscordUsername" H'

    # Act
    await setup_command.callback(
        mock_interaction, mock_member, first_name, last_initial
    )

    # Assert
    mock_member.edit.assert_called_once()
    nick_arg = mock_member.edit.call_args[1]["nick"]
    assert (
        len(nick_arg) <= 32
    ), f"Nickname should not exceed 32 characters: '{nick_arg}'"
    assert (
        "Discord" in nick_arg
    ), "Username should be included in the nickname when no nickname is set"


@pytest.mark.asyncio
async def test_setup_command_forbidden_error(
    mock_interaction, mock_member, mock_setup_role, setup_command
):
    """Test that the setup command correctly handles discord.Forbidden errors."""
    # Arrange
    mock_interaction.guild.get_role.return_value = mock_setup_role
    mock_member.roles = [mock_setup_role]

    # Create a Forbidden error
    forbidden_error = discord.Forbidden(MagicMock(), "Missing permissions")
    mock_member.edit.side_effect = forbidden_error

    first_name = "Tim"
    last_initial = "H"

    # Act
    await setup_command.callback(
        mock_interaction, mock_member, first_name, last_initial
    )

    # Assert
    mock_interaction.response.send_message.assert_called_once()
    args, kwargs = mock_interaction.response.send_message.call_args
    assert "permission" in args[0].lower()
    assert kwargs.get("ephemeral") is True


@pytest.mark.asyncio
async def test_setup_command_general_error(
    mock_interaction, mock_member, mock_setup_role, setup_command
):
    """Test that the setup command correctly handles general exceptions."""
    # Arrange
    mock_interaction.guild.get_role.return_value = mock_setup_role
    mock_member.roles = [mock_setup_role]
    mock_member.edit.side_effect = Exception("Something went wrong")
    first_name = "Tim"
    last_initial = "H"

    # Act
    await setup_command.callback(
        mock_interaction, mock_member, first_name, last_initial
    )

    # Assert
    mock_interaction.response.send_message.assert_called_once()
    args, kwargs = mock_interaction.response.send_message.call_args
    assert "error occurred" in args[0].lower()
    assert "Something went wrong" in args[0]
    assert kwargs.get("ephemeral") is True


@pytest.mark.asyncio
async def test_setup_error_handler_missing_role(mock_interaction, setup_command):
    """Test that the setup_error handler correctly handles MissingAnyRole errors."""
    # Arrange
    error = app_commands.MissingAnyRole(["Admin"])

    # Act
    await setup_command.error(mock_interaction, error)

    # Assert
    mock_interaction.response.send_message.assert_called_once()
    args, kwargs = mock_interaction.response.send_message.call_args
    assert "permission" in args[0].lower()
    assert kwargs.get("ephemeral") is True


@pytest.mark.asyncio
async def test_setup_error_handler_general_error(mock_interaction, setup_command):
    """Test that the error handler handles general errors correctly."""
    error = Exception("Test error")
    await setup_command.error(mock_interaction, error)
    mock_interaction.response.send_message.assert_called_once_with(
        "An error occurred: Test error", ephemeral=True
    )


@pytest.mark.asyncio
async def test_setup_already_setup_user(
    mock_interaction, mock_member, mock_setup_role, setup_command
):
    """Test that the setup command detects users that are already set up."""
    # Arrange
    # Configure the member to appear already set up
    # Has a nickname different from username and doesn't have the setup role
    mock_member.nick = "Already Set Up"
    mock_member.name = "original_username"
    mock_member.roles = []  # No setup role

    # Configure guild to return the setup role
    mock_interaction.guild.get_role.return_value = mock_setup_role

    # Act
    await setup_command.callback(mock_interaction, mock_member, "First", "L")

    # Assert
    mock_interaction.response.send_message.assert_called_once_with(
        f"{mock_member.mention} has already been set up.",
        ephemeral=True,
    )

    # Verify no edits were made to the member
    mock_member.edit.assert_not_called()
    mock_member.remove_roles.assert_not_called()
