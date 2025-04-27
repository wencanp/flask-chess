# app.py

from flask import Flask, request, jsonify, redirect, url_for
from chess_base import initial_state, update_board, is_move_valid, process_move, check_game_over, square_to_position
from chess_rules import attempt_promotion, is_valid_castle_attempt, perform_castling, is_valid_en_passant, perform_en_passant, update_castling_info, update_en_passant_position
from chess_support import get_possible_moves, BOARD_SIZE

app = Flask(__name__)

# Game initialization
board = initial_state()
whites_turn = True

white_pieces_moved = (False, False, False)  # Left rook, king, right rook
black_pieces_moved = (False, False, False)  # Left rook, king, right rook

en_passant_position = None


@app.route('/')
def index():
    return redirect('/static/index.html')


@app.route('/api/board', methods=['GET'])
def get_board():
    """Current board"""
    return jsonify({
        'board': board,
        'whites_turn': whites_turn,
        'game_over': False
    })


@app.route('/api/move', methods=['POST'])
def move():
    global board, whites_turn, white_pieces_moved, black_pieces_moved, en_passant_position

    data = request.get_json()
    move_str = data.get('move')  # format like "e2 e4"

    if not move_str:
        return jsonify({'error': 'No move provided.'}), 400

    try:
        move = process_move(move_str)
    except Exception as e:
        return jsonify({'error': f'Invalid move format: {str(e)}'}), 400

    castling_info = (
        white_pieces_moved if whites_turn else black_pieces_moved
    )

    if is_move_valid(move, board, whites_turn):
        board = attempt_promotion(update_board(board, move), whites_turn)
    elif is_valid_castle_attempt(move, board, whites_turn, castling_info):
        board = perform_castling(move, board)
    elif is_valid_en_passant(move, board, whites_turn, en_passant_position):
        board = perform_en_passant(move, board, whites_turn)
    else:
        return jsonify({'error': 'Invalid move.'}), 400

    castling_info = update_castling_info(move, whites_turn, castling_info)
    if whites_turn:
        white_pieces_moved = castling_info
    else:
        black_pieces_moved = castling_info

    en_passant_position = update_en_passant_position(
        move, board, whites_turn
    )
    whites_turn = not whites_turn

    game_over = check_game_over(board, whites_turn)

    return jsonify({
        'board': board,
        'whites_turn': whites_turn,
        'game_over': game_over
    })


@app.route('/api/reset', methods=['POST'])
def reset_board():
    """Reset the board to initial state"""
    global board, whites_turn
    board = initial_state()  # initialize board
    whites_turn = True  # reset to whites turn
    return jsonify({
        'board': board,
        'whites_turn': whites_turn,
        'game_over': False
    })


@app.route('/api/moves')
def get_possible_moves_api():
    global board, whites_turn

    from_square = request.args.get('from')
    if not from_square:
        return jsonify({'moves': []})

    position = square_to_position(from_square)
    possible_positions = get_possible_moves(position, board)

    moves = []
    for pos in possible_positions:
        file = chr(ord('a') + pos[1])
        rank = str(BOARD_SIZE - pos[0])
        moves.append(file + rank)

    return jsonify({'moves': moves})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
