from aiogram import Dispatcher, types
from aiogram.filters import Command
from storage import create_game, join_game, get_game, get_board, switch_turn, get_turn, delete_game
from game_logic import print_board, process_shot, check_victory
from keyboards import main_menu, connect_menu, playing_menu, current_game_menu

# Создаём глобальный словарь для хранения ID игры
user_game_requests = {}

# Список с координатами
coordinates = ['A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9', 'A10',
               'B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B9', 'B10',
               'C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9', 'C10',
               'D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'D8', 'D9', 'D10',
               'E1', 'E2', 'E3', 'E4', 'E5', 'E6', 'E7', 'E8', 'E9', 'E10',
               'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'F10',
               'G1', 'G2', 'G3', 'G4', 'G5', 'G6', 'G7', 'G8', 'G9', 'G10',
               'H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'H7', 'H8', 'H9', 'H10',
               'I1', 'I2', 'I3', 'I4', 'I5', 'I6', 'I7', 'I8', 'I9', 'I10',
               'J1', 'J2', 'J3', 'J4', 'J5', 'J6', 'J7', 'J8', 'J9', 'J10']

# Создаём глобальный словарь для хранения ID игроков и матчей, в которых они участвуют
current_games = {}


# Функция для обработки команды /start
async def start_command(message: types.Message):
    await message.answer(
        f'👋 Привет! Добро пожаловать в Морской бой!\n\nСоздай новую игру и приглашай друга или присоединяйся к уже созданной игре, удачи! 🚢\n\nРазработчик: @vladelo',
        reply_markup=main_menu())


# Функция для создания игры
async def create_game_command(message: types.Message):
    if message.from_user.id not in current_games:
        game_id = create_game(message.from_user.id)
        print(f'🚀 Игрок @{message.from_user.username} запустил игру, ID игры: {game_id}')
        current_games[message.from_user.id] = game_id
        await message.answer(f"🛠 Игра создана! ID игры: {game_id}\n Ожидаем второго игрока.",
                             reply_markup=connect_menu())
    else:
        print(f'🚀 Игрок @{message.from_user.username} пытался запустить ещё игру, не закончив предыдущую.')
        await message.answer(f"❗ Прежде чем создать новую игру, доиграйте текущую или сдайтесь.")


# Функция для подключения к игре
async def process_game_id(message: types.Message):
    user_game_requests[message.from_user.id] = None
    await message.answer("💬 Выберите и отправьте ID игры, к которой хотите присоединиться.",
                         reply_markup=current_game_menu())


# Функция для подключения к игре
async def join_game_command(message: types.Message):
    try:
        game_id = message.text
        user_id = message.from_user.id
        if user_id in current_games and current_games[user_id] == game_id:
            print(f'❗ Пользователь @{message.from_user.username} пытался подключиться к своей же игре с ID: {game_id}')
            await message.answer(f"❗ Нельзя подключаться к своей же игре.", reply_markup=current_game_menu())
        else:
            if user_id in user_game_requests and user_game_requests[user_id] is None:
                game = get_game(game_id)
                if game:
                    if join_game(game_id, user_id):
                        game = get_game(game_id)
                        player1 = game["player1"]
                        player2 = game["player2"]
                        print(f'➕ Игрок @{message.from_user.username} присоединился к игре, ID игры: {game_id}')
                        current_games[message.from_user.id] = game_id
                        await message.answer(f"✅ Вы успешно присоединились к игре с ID: {game_id}!")
                        await message.bot.send_message(player1, f"🎮 Игра началась!\n1️⃣ Вы ходите первым!",
                                                       reply_markup=types.ReplyKeyboardRemove())
                        await message.bot.send_message(player2, f"🎮 Игра началась!\n2️⃣ Вы ходите вторым!",
                                                       reply_markup=types.ReplyKeyboardRemove())
                        await message.bot.send_message(player1,
                                                       "Ваше поле:\n" + print_board(get_board(game_id, player1)),
                                                       parse_mode="html", reply_markup=playing_menu(game_id, player2))
                        await message.bot.send_message(player2,
                                                       "Ваше поле:\n" + print_board(get_board(game_id, player2)),
                                                       parse_mode="html")
                    else:
                        await message.answer(f"❗ Игра с ID: {game_id} не найдена или уже заполнена.")
                else:
                    await message.answer(f"❗ Игра с ID: {game_id} не найдена или уже заполнена.")
                # Убираем пользователя из ожидания
                del user_game_requests[user_id]
    except IndexError:
        await message.answer(f"❗ Вы ввели некорректные данные.")


# Функция для хода (выстрела) по координатам с кнопок
async def shot_command_coord(message: types.Message):
    game_id = str(current_games[message.from_user.id])
    game = get_game(game_id)

    if message.text == "🏳️ Сдаться":
        print(f'🏳️ Игрок @{message.from_user.username} сдался, ID игры: {game_id}')
        opponent_id = game["player1"] if game["turn"] == game["player2"] else game["player2"]
        del current_games[message.from_user.id]
        del current_games[opponent_id]

        await message.answer(f"🏳️ Поражение! Вы сдались в игре!", reply_markup=main_menu())
        await message.bot.send_message(opponent_id, f"🎉 Победа! Противник сдался!", reply_markup=main_menu())
    else:
        coord = message.text.upper()
        x = ord(coord[0]) - ord('A')
        y = int(coord[1:]) - 1

        if game and message.from_user.id == get_turn(game_id):
            opponent_id = game["player1"] if game["turn"] == game["player2"] else game["player2"]
            board = get_board(game_id, opponent_id)

            if 0 <= x < 10 and 0 <= y < 10:
                hit = process_shot(board, x, y)

                # Проверка на победу после выстрела
                if check_victory(board):
                    del current_games[message.from_user.id]
                    del current_games[opponent_id]
                    winner = message.from_user.username
                    loser = await message.bot.get_chat(opponent_id)
                    await message.answer(f"🎉 Победа! Вы уничтожили все корабли противника!", reply_markup=main_menu())
                    await message.bot.send_message(opponent_id,
                                                   f"💥 Поражение! Все ваши корабли уничтожены.\nПобедил @{winner}!",
                                                   reply_markup=main_menu())
                    delete_game(game_id)
                    return

                switch_turn(game_id)

                result = "💥 Попадание!" if hit else "❌ Мимо!"
                board_view = print_board(board, hide_ships=True)
                await message.answer(
                    f"{result}\nОбновлённое поле противника:\n{board_view}\n Ожидайте ход другого игрока!",
                    parse_mode="html", reply_markup=types.ReplyKeyboardRemove())
                await message.bot.send_message(
                    opponent_id,
                    f"Ход противника завершён.\n"
                    f"Обновлённое поле после выстрела:\n{board_view}\n Ваш ход!", parse_mode="html",
                    reply_markup=playing_menu(game_id, message.from_user.id))
            else:
                await message.answer("❗ Неверные координаты. Используйте формат A1.")
        else:
            await message.answer("❗ Сейчас не ваш ход или игра не найдена.")


def register_handlers(dp: Dispatcher):
    # Вызываем функцию приветствия по команде /start
    dp.message.register(start_command, Command("start"))

    # Вызываем функцию создания новой игры по фразе '🚀 Новая игра'
    dp.message.register(create_game_command, lambda message: message.text == "🚀 Новая игра")

    # Вызываем функцию хода (выстрела) по фразе введенным координатам или сдаемся
    dp.message.register(shot_command_coord, lambda message: message.text == "🏳️ Сдаться")
    dp.message.register(shot_command_coord, lambda message: message.text in coordinates)

    # Вызываем функцию подключения к игре по фразе '📎 Присоединиться к игре'
    dp.message.register(process_game_id, lambda message: message.text == "📎 Присоединиться к игре")
    dp.message.register(join_game_command)
