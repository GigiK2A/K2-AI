from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from interfaces.telegram.presentation import BOARD_MEMBERS, visible_agent_label


def board_menu_keyboard() -> InlineKeyboardMarkup:
    """Menu del board: un bottone per ogni membro + il roundtable.

    Selezionare un membro apre una chat 1:1 con lui (callback board:<agent>).
    Il roundtable (callback board:consiglio) fa convocare tutto il board da Giuseppina.
    """
    buttons: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for member in BOARD_MEMBERS:
        row.append(
            InlineKeyboardButton(
                f"{member['emoji']} {member['name']}",
                callback_data=f"board:{member['agent']}",
            )
        )
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("🧠 Convoca tutto il board", callback_data="board:consiglio")])
    return InlineKeyboardMarkup(buttons)


def approval_keyboard(approval_id: str) -> InlineKeyboardMarkup:
    """Keyboard per approvare/rifiutare un draft."""
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Approva", callback_data=f"approve:{approval_id}"),
                InlineKeyboardButton("Rifiuta", callback_data=f"reject:{approval_id}"),
            ],
            [
                InlineKeyboardButton("Vedi completo", callback_data=f"view:{approval_id}"),
                InlineKeyboardButton("Modifica nota", callback_data=f"note:{approval_id}"),
            ],
        ]
    )


def agent_selector_keyboard() -> InlineKeyboardMarkup:
    """Keyboard per selezionare un agente da eseguire."""
    from core.orchestrator import list_agents

    buttons = []
    row = []
    for agent_name in list_agents():
        row.append(
            InlineKeyboardButton(
                visible_agent_label(agent_name),
                callback_data=f"select_agent:{agent_name}",
            )
        )
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(buttons)


def confirm_keyboard(action: str, target_id: str) -> InlineKeyboardMarkup:
    """Keyboard generica di conferma si/no."""
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Si, procedi", callback_data=f"confirm:{action}:{target_id}"),
                InlineKeyboardButton("Annulla", callback_data="cancel"),
            ]
        ]
    )


def back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("Indietro", callback_data="back:main")]])
