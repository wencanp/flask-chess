"""
Basic funtctions for Chess Game

"""

from string import ascii_lowercase

from chess_support import *


def initial_state() -> Board:
    """(Board): Returns the initial board state."""
    return (
        ("".join(BLACK_PIECES[:-1]), BLACK_PAWN * 8)
        + (EMPTY * 8,) * 4
        + (WHITE_PAWN * 8, "".join(WHITE_PIECES[:-1]))
    )


def print_board(board: Board) -> None:
    """Prints the board in a user-friendly way.

    Parameters:
        board (Board): The current board state.
    """
    for i, row in enumerate(board):
        print(f"{row}  {BOARD_SIZE - i}")
    print("\n" + ascii_lowercase[:BOARD_SIZE])


def square_to_position(square: str) -> Position:
    """Converts chess notation to its row/column counterpart.

    Parameters:
        square (str): The position in chess notation e.g. "e4"

    Returns:
        (Position): The corresponding position in (row, column) format.
    """
    file, rank = square[0], square[1]

    row = BOARD_SIZE - int(rank)
    column = ascii_lowercase.index(file)

    return row, column


def process_move(user_input: str) -> Move:
    """Convert a move in traditional chess notation to a move based on row/col
    positions.

    Parameters:
        user_input (str): The input from the user describing two squares
                          in chess notation.

    Returns:
        (Move): The move which includes the position to move from and 
                the position to move to.
    """
    from_square, to_square = user_input.split()
    return square_to_position(from_square), square_to_position(to_square)


def change_position(board: Board, position: Position, character: str) -> Board:
    """Returns a copy of board with the character at position changed to the
        requested character.

    Parameters:
        board (Board): The board state before the change.
        position (Position): The (row, col) position at which to put character.
        character (str): The character to put at position.

    Returns:
        (Board): The updated board.
    """
    row, column = position
    changed_row = board[row]

    # replace the character at 'column' index within changed_row
    changed_row = changed_row[:column] + character + changed_row[column + 1 :]

    # replace the row at 'row' index within board
    return board[:row] + (changed_row,) + board[row + 1 :]


def clear_position(board: Board, position: Position) -> Board:
    """Delete the piece at the supplied position and return the resulting
    board. The board should remain unchanged if there exists no piece at
    this position.

    Parameters:
        board (Board): The board state before the change.
        position (Position): The (row, col) position at which to put character.

    Returns:
        (Board): The new board state with the move made.
    """
    return change_position(board, position, EMPTY)


def update_board(board: Board, move: Move) -> Board:
    """Returns and updated version of the board with the move made. Assumes
        the given move is valid.

    Parameters:
        board (Board): The board state before the change.
        move (Move): The move to enact

    Returns:
        (Board): The new board state with the move made.
    """
    from_position, to_position = move
    piece = piece_at_position(from_position, board)

    intermediate_state = change_position(board, to_position, piece)
    return clear_position(intermediate_state, from_position)


def is_current_players_piece(piece: str, whites_turn: bool) -> bool:
    """Checks that the piece is a piece owned by the player whose turn it is.

    Parameters:
        piece (str): The piece we are trying to move.
        whites_turn (bool): True iff white's turn.

    Returns:
        (bool): True iff this is a piece owned by the player whose turn it is.
    """
    if whites_turn:
        return piece in WHITE_PIECES
    return piece in BLACK_PIECES


def is_move_valid(move: Move, board: Board, whites_turn: bool) -> bool:
    """Determines whether a given move is valid.

    Parameters:
        move (Move): The move to check
        board (Board): The current board state.
        whites_turn (bool): True iff it's white's turn.

    Returns:
        (bool): True iff the move is valid.
    """
    from_position, to_position = move

    # Check if either component of the move is out of bounds.
    if out_of_bounds(from_position) or out_of_bounds(to_position):
        return False

    # Can't try to move to the same spot
    if from_position == to_position:
        return False

    # Check if the player owns the piece they're trying to move
    piece_moved = piece_at_position(from_position, board)
    if not is_current_players_piece(piece_moved, whites_turn):
        return False

    # Check that the square that they're trying to move to doesn't contain
    # another one of their own pieces.
    piece_at_destination = piece_at_position(to_position, board)
    if is_current_players_piece(piece_at_destination, whites_turn):
        return False

    # Check if the piece can move to that square based on the type of the piece
    if to_position not in get_possible_moves(from_position, board):
        return False

    # Perform move and check if our king is in check in the resulting state.
    next_state = update_board(board, move)
    return not is_in_check(next_state, whites_turn)


def can_move(board: Board, whites_turn: bool) -> bool:
    """Determines whether there is a possible move for the player whose turn
        it is out that will get them out of check (including blocking or taking
        attacking pieces).

    Parameters:
        board (Board): The current board state.
        whites_turn (bool): True iff it's white's turn.

    Returns:
        (bool): True iff the player can make a move such that in the resulting
        board state, they are not in check.
    """
    # Brute forced because there could be multiple attacking pieces,
    # so just check every state the game can move to in the next turn
    #  and see if any are not in check.

    pieces = WHITE_PIECES if whites_turn else BLACK_PIECES

    for i, row in enumerate(board):
        for j, piece in enumerate(row):
            position = (i, j)
            if piece in pieces:
                # Perform every possible move for all of our pieces and check
                # if the resulting position can escape check.
                for possible_position in get_possible_moves(position, board):
                    candidate_move = (position, possible_position)
                    next_state = update_board(board, candidate_move)
                    if not is_in_check(next_state, whites_turn):
                        return True
    return False


def is_stalemate(board: Board, whites_turn: bool) -> bool:
    """Determines whether a stalemate has been reached; this occurs when the
        player who is about to move isn't in check but can't make any moves
        without putting themselves in check.

    Parameters:
        board (Board): The current board state.
        whites_turn (bool): True iff it's white's turn.

    Returns:
        (bool): True iff a stalemate has been reached.
    """
    if is_in_check(board, whites_turn):
        return False
    
    return not can_move(board, whites_turn)


def check_game_over(board: Board, whites_turn: bool) -> bool:
    """Determines whether the game is over, and prints the result. Will also
        print if the player is in check.

    Parameters:
        board (Board): The current board state.
        whites_turn (bool): True iff it's white's turn.

    Returns:
        (bool): True iff the game is over.
    """
    if is_stalemate(board, whites_turn):
        print("\nStalemate")
        return True

    if not can_move(board, whites_turn):
        print("\nCheckmate")
        return True

    if is_in_check(board, whites_turn):
        turn = "White" if whites_turn else "Black"
        print(f"\n{turn} is in check")

    return False


def main():
    """Entry point to gameplay."""
    whites_turn = True
    board = initial_state()

    while True:
        print_board(board)
        if check_game_over(board, whites_turn):
            break

        turn = "White's" if whites_turn else "Black's"
        response = input(f"\n{turn} move: ")

        # Handle non-move options
        if response in ("h", "H"):
            print(HELP_MESSAGE)
            continue

        if response in ("q", "Q"):
            confirmation = input("Are you sure you want to quit? ")
            if confirmation in ("y", "Y"):
                break
            continue
        
        if not valid_move_format(response):
            print("Invalid move\n")
            continue

        # Process the move, and enact it if valid.
        move = process_move(response)
        if not is_move_valid(move, board, whites_turn):
            print("Invalid move\n")
            continue

        board = update_board(board, move)
        whites_turn = not whites_turn
