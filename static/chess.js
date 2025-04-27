// static/chess.js

let selectedSquare = null;
let gameOver = false;
let possibleMoves = [];

function toPos(row, col) {
    const file = String.fromCharCode('a'.charCodeAt(0) + parseInt(col));
    const rank = 8 - parseInt(row);
    return file + rank;
}

async function fetchBoard() {
    const response = await fetch('/api/board');
    const data = await response.json();
    drawBoard(data.board, data.whites_turn);

    const message = document.getElementById('message');
    if (data.game_over) {
        gameOver = true;
        message.style.color = 'blue';
        message.textContent = 'Game Ends';
    }
}

function drawBoard(board, whitesTurn) {
    const chessboard = document.getElementById('chessboard');
    chessboard.innerHTML = ''; // 清空之前的棋盘

    // 更新当前回合提示
    const message = document.getElementById('message');
    message.textContent = whitesTurn ? "White's Turn" : "Black's Turn";

    for (let i = 0; i < 8; i++) {
        for (let j = 0; j < 8; j++) {
            const square = document.createElement('div');
            square.classList.add('square');

            if ((i + j) % 2 === 0) {
                square.classList.add('white');
            } else {
                square.classList.add('black');
            }

            const piece = board[i][j];
            if (piece !== '.') {
                const img = document.createElement('img');
                img.src = `/static/images/${pieceToFilename(piece)}`;
                square.appendChild(img);
            }

            square.dataset.row = i;
            square.dataset.col = j;

            square.addEventListener('click', onSquareClick);

            const pos = toPos(i, j);
            if (possibleMoves.includes(pos)) {
                square.style.boxShadow = 'inset 0 0 10px green';
            }

            chessboard.appendChild(square);
        }
    }

    // 如果之前有选中格子，重新加上高亮
    if (selectedSquare) {
        highlightSelectedSquare();
    }
}

function pieceToFilename(piece) {
    const map = {
        'P': 'white_pawn.png',
        'R': 'white_rook.png',
        'N': 'white_knight.png',
        'B': 'white_bishop.png',
        'Q': 'white_queen.png',
        'K': 'white_king.png',
        'p': 'black_pawn.png',
        'r': 'black_rook.png',
        'n': 'black_knight.png',
        'b': 'black_bishop.png',
        'q': 'black_queen.png',
        'k': 'black_king.png',
    };
    return map[piece] || '';
}

function highlightSelectedSquare() {
    const squares = document.querySelectorAll('.square');
    squares.forEach(square => {
        const pos = toPos(square.dataset.row, square.dataset.col);

        if (pos === selectedSquare) {
            square.style.backgroundColor = '#add8e6'; // 浅蓝色
        }
    });
}

async function onSquareClick(event) {
    if (gameOver) return;

    const row = event.currentTarget.dataset.row;
    const col = event.currentTarget.dataset.col;
    const pos = toPos(row, col);

    if (!selectedSquare) {
        selectedSquare = pos;
        await fetchPossibleMoves(selectedSquare);
        highlightSelectedSquare();
    } else if (selectedSquare === pos) {
        // 如果点了自己，再次点击取消选择
        selectedSquare = null;
        possibleMoves = [];
        fetchBoard();
    } else {
        const move = `${selectedSquare} ${pos}`;
        await makeMove(move);
        selectedSquare = null;
        possibleMoves = [];
        fetchBoard();
    }
}

async function fetchPossibleMoves(fromPos) {
    const response = await fetch(`/api/moves?from=${fromPos}`);
    const data = await response.json();
    possibleMoves = data.moves;
    fetchBoard();
}

async function makeMove(move) {
    const message = document.getElementById('message');

    const response = await fetch('/api/move', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({move: move})
    });

    const data = await response.json();

    if (data.error) {
        message.textContent = "Error：" + data.error;
        message.style.color = 'red';
        setTimeout(() => {
            message.style.color = '';
            fetchBoard();
        }, 1500);
    } else {
        fetchBoard();
    }

}

async function resetBoard() {
    selectedSquare = null;
    possibleMoves = [];
    gameOver = false;

    const message = document.getElementById('message');

    const response = await fetch('/api/reset', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'}
    });

    const data = await response.json();

    // 如果重置成功，更新棋盘
    if (data.board) {
        message.textContent = "Reset Complete";
        fetchBoard();
    } else {
        message.textContent = "Failed to reset";
        message.style.color = 'red';
    }
}

// 页面加载时自动拉棋盘
window.onload = function() {
    fetchBoard();
    const restartButton = document.querySelector('button');
    restartButton.addEventListener('click', resetBoard);
}
