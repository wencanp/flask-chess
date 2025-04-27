"""
Special rules for Chess Game including promotion, castling, en passant
"""
from typing import Optional, Tuple

from chess_support import *
from chess_base import *


QUEEN = "q"
KNIGHT = "n"
ROOK = "r"
BISHOP = "b"
VALID_PROMOTION_INPUTS = (QUEEN, KNIGHT, ROOK, BISHOP)
PROMOTION_MESSAGE = "What piece would you like (q, n, r, b)? "
INVALID_PROMOTION_MESSAGE = "Not a valid piece. "

KING_CASTLING_COL_DELTA = 2
KING_CASTLING_DELTAS = (
    (0, -KING_CASTLING_COL_DELTA),
    (0, KING_CASTLING_COL_DELTA),
)


def attempt_promotion(board: Board, whites_turn: bool) -> Board:
    """Checks whether there is a pawn on the board that needs to be promoted.
        If there is, we prompt the user for the piece to upgrade to, replace
        the pawn with this piece, and return the updated board. Otherwise,
        just return the original board.

    Parameters:
        board (Board): The board state.
        whites_turn (bool): True iff white's turn.

    Returns:
        (Board): The updated board state, with either the promoted piece
                    in place or no changes.
    """
    if whites_turn:
        row = 0
        pawn, rook, bishop = WHITE_PAWN, WHITE_ROOK, WHITE_BISHOP
        knight, queen = WHITE_KNIGHT, WHITE_QUEEN
    else:
        row = BOARD_SIZE - 1
        pawn, rook, bishop = BLACK_PAWN, BLACK_ROOK, BLACK_BISHOP
        knight, queen = BLACK_KNIGHT, BLACK_QUEEN

    for col, piece in enumerate(board[row]):
        if piece == pawn:
            substitute = input(PROMOTION_MESSAGE)
            # prompt until a valid promotion is given
            while substitute not in VALID_PROMOTION_INPUTS:
                substitute = input(
                    INVALID_PROMOTION_MESSAGE + PROMOTION_MESSAGE
                )

            if substitute == QUEEN:
                piece = queen
            elif substitute == KNIGHT:
                piece = knight
            elif substitute == ROOK:
                piece = rook
            else:
                piece = bishop

            return change_position(board, (row, col), piece)

    return board


def is_valid_castle_attempt(
    move: Move,
    board: Board,
    whites_turn: bool,
    castling_info: Tuple[bool, bool, bool],
) -> bool:
    """Determines if the given move is a valid attempt at castling for the 
    current game state.

    Parameters:
        move (Move): The move to check.
        board (Board): The current board.
        whites_turn (bool): True iff it's white's turn.
        castling_info (tuple<bool, bool, bool>): A tuple of booleans which are
                true iff the respective left rook, king and right rook have moved
                this game.

    Returns:
        (bool): True iff the supplied move is a valid castling attempt.
    """
    left_rook_moved, king_moved, right_rook_moved = castling_info

    # If the king has already moved we can't castle.
    if king_moved:
        return False

    # Check that the move could even be a valid castling move
    (start_row, start_col), (end_row, end_col) = move
    row_delta = end_row - start_row
    col_delta = end_col - start_col

    if (row_delta, col_delta) not in KING_CASTLING_DELTAS:
        return False

    # If the king attempts to castle to the left, it's called long castling.
    is_long_castle = col_delta < 0

    # Check that the appropriate rook has not moved
    if (is_long_castle and left_rook_moved) \
        or (not is_long_castle and right_rook_moved):
        return False

    direction = int(col_delta / KING_CASTLING_COL_DELTA)
    number_of_between_squares = 3 if is_long_castle else 2

    # Check that the appropriate rook has not been taken
    rook_position = start_row, start_col + (
        direction * (number_of_between_squares + 1)
    )
    rook = WHITE_ROOK if whites_turn else BLACK_ROOK
    if piece_at_position(rook_position, board) != rook:
        return False

    # Check that nothing obstructs the king's sight of the respective rook
    for i in range(number_of_between_squares):
        position = start_row, start_col + ((i + 1) * direction)
        if piece_at_position(position, board) != EMPTY:
            return False

    if is_in_check(board, whites_turn):
        return False

    # Check that the king wouldn't be in check in any of the squares between
    # his starting and ending positions
    for i in range(KING_CASTLING_COL_DELTA):
        position = start_row, start_col + ((i + 1) * direction)
        # move the king to that square and check if it would be in check
        move = ((start_row, start_col), position)
        next_state = update_board(board, move)
        if is_in_check(next_state, whites_turn):
            return False

    return True


def perform_castling(move: Move, board: Board) -> Board:
    """Given a valid castling move, returns the resulting board state.

    Parameters:
        move (Move): The move to make.
        board (Board): The current board.

    Returns:
        (Board): The board representing the game state after castling.
    """
    (row, start_col), (_, end_col) = move
    col_delta = end_col - start_col

    # Get the rook's position
    if col_delta < 0:
        rook_position = (row, 0)
    else:
        rook_position = (row, BOARD_SIZE - 1)

    # Move the king
    intermediate_state = update_board(board, move)

    # Move the rook
    relative_rook_col_delta = int(-col_delta / 2)
    rook_move = rook_position, (row, end_col + relative_rook_col_delta)
    return update_board(intermediate_state, rook_move)


def perform_en_passant(move: Move, board: Board, whites_turn: bool) -> Board:
    """Assuming the supplied move is a valid en-passant, return the resulting
    board state.

    Parameters:
        move (Move): The move to make.
        board (Board): The current board.
        whites_turn (bool): True iff it's white's turn.

    Returns:
        (Board): The board representing the game state after the move.
    """
    # Take the en-passant square with our pawn.
    intermediate_state = update_board(board, move)

    # Determine the direction of the pawn we took, relative to the end move.
    relative_pawn_row_delta = 1 if whites_turn else -1

    # Find and remove the taken pawn.
    _, (end_row, end_col) = move
    taken_pawn_position = end_row + relative_pawn_row_delta, end_col
    return clear_position(intermediate_state, taken_pawn_position)


def is_valid_en_passant(
    move: Move,
    board: Board,
    whites_turn: bool,
    en_passant_square: Optional[Position],
) -> bool:
    """Determine if the supplied move constitutes a valid en passant move.

    Parameters:
        move (Move): The move to check.
        board (Board): The current board.
        whites_turn (bool): True iff it's white's turn.
        en_passant_square (Position or None): The position representing the
                en passant square, or null, if a pawn did not move forward
                twice on the last turn.

    Returns:
        (bool): True iff the suplied move is a valid en passant move.
    """
    if en_passant_square is None:
        return False

    pawn = WHITE_PAWN if whites_turn else BLACK_PAWN
    start_position, end_position = move

    # If the piece we're moving isn't our pawn, can't be a valid en passant move.
    if piece_at_position(start_position, board) != pawn:
        return False

    # Check that the position we're moving to is the en passant square.
    if end_position != en_passant_square:
        return False

    # Check that the move is a valid pawn attacking move.
    start_row, start_col = start_position
    end_row, end_col = end_position
    delta = end_row - start_row, end_col - start_col

    if delta not in pawn_attacking_deltas(whites_turn):
        return False

    # Finally, check that the move wouldn't put us in check
    next_state = perform_en_passant(move, board, whites_turn)
    return not is_in_check(next_state, whites_turn)


def update_castling_info(
    move: Move, whites_turn: bool, castling_info: Tuple[bool, bool, bool]
) -> Tuple[bool, bool, bool]:
    """Returns the updated castling info for the respective player, after
    performing the given, valid move.

    Parameters:
        move (Move): The move just performed
        whites_turn (bool): True iff it's white's turn.
        castling_info (tuple<bool, bool, bool>): A tuple of booleans which are
                true iff the respective left rook, king and right rook have moved
                this game.
    Returns:
        (tuple<bool, bool, bool>): The castling info after the move has been
                performed.
    """
    original_major_piece_row = BOARD_SIZE - 1 if whites_turn else 0
    # Corresponding to the original columns for the left rook, king and right
    # rook respectively.
    original_castling_piece_cols = [0, 4, BOARD_SIZE - 1]
    move_start_position, _ = move

    # If the player is moving a rook or king that hasnt moved yet, update the
    # appropriate column in the castling info.
    for i, col in enumerate(original_castling_piece_cols):
        original_position = original_major_piece_row, col
        piece_already_moved = castling_info[i]
        if move_start_position == original_position and not piece_already_moved:
            castling_info = castling_info[:i] + (True,) + castling_info[i + 1 :]

    return castling_info


def update_en_passant_position(
    move: Move, board: Board, whites_turn: bool
) -> Optional[Position]:
    """If the current player's pawn just moved forward two squares, returns
        the position that an enemy pawn could take to perform a valid en passant
        move. If no en passant square should be active, returns None.

    Parameters:
        move (Move): The move just performed
        board (Board): The board after the move.
        whites_turn (bool): True iff it's white's turn just passed.

    Returns:
        (Position or None): The position of the active en passant sqaure if one
                            exists, otherwise None.
    """
    pawn = WHITE_PAWN if whites_turn else BLACK_PAWN
    (start_row, col), (end_row, _) = move

    if piece_at_position((end_row, col), board) != pawn:
        return None

    row_delta = end_row - start_row
    if abs(row_delta) != 2:
        return None

    return (start_row + int(row_delta / 2), col)


# def main():
#     """ Entry point to gameplay. """
#     whites_turn = True
#     board = initial_state()
#
#     white_pieces_moved = (False, False, False)  # Left rook, king, right rook
#     black_pieces_moved = (False, False, False)  # Left rook, king, right rook
#
#     en_passant_position = None
#
#     while True:
#         print_board(board)
#         if check_game_over(board, whites_turn):
#             break
#
#         turn = "White's" if whites_turn else "Black's"
#         response = input(f"\n{turn} move: ")
#
#         # Handle non-move options
#         if response in ("h", "H"):
#             print(HELP_MESSAGE)
#             continue
#         if response in ("q", "Q"):
#             confirmation = input("Are you sure you want to quit? ")
#             if confirmation in ("y", "Y"):
#                 break
#             continue
#         if not valid_move_format(response):
#             print("Invalid move\n")
#             continue
#
#         # Process the move, and enact it if valid.
#         move = process_move(response)
#         castling_info = (
#             white_pieces_moved if whites_turn else black_pieces_moved
#         )
#
#         if is_move_valid(move, board, whites_turn):
#             board = attempt_promotion(update_board(board, move), whites_turn)
#         elif is_valid_castle_attempt(move, board, whites_turn, castling_info):
#             board = perform_castling(move, board)
#         elif is_valid_en_passant(move, board, whites_turn, en_passant_position):
#             board = perform_en_passant(move, board, whites_turn)
#         else:
#             print("Invalid move\n")
#             continue
#
#         # Update the rest of the game state.
#         castling_info = update_castling_info(move, whites_turn, castling_info)
#         if whites_turn:
#             white_pieces_moved = castling_info
#         else:
#             black_pieces_moved = castling_info
#
#         en_passant_position = update_en_passant_position(
#             move, board, whites_turn
#         )
#         whites_turn = not whites_turn
