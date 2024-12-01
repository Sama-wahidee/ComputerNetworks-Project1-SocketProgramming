import socket
import threading
import time
import random
import select

# Server configs (Host => Local IP Address) && (Port => The Port Number That Server listen To..)
HOST = '127.0.0.1'
PORT = 5689

game_players = {}  # list to store players info..

questions = [
    {"question": "Who are the Networks Heroes?",
        "correct_answer": "Dr. Ahmad Shawahneh, Dr. Mohammed Jubran & The Teaching Assistant who will grade this project 😉"},
    {"question": "Will we get the full mark in this project?",
        "correct_answer": "Yes, of course! (Inshallah)"},
    {"question": "What is your favorite course this semester?",
        "correct_answer": "Networks"},
    {"question": "What are you excited for the most?",
        "correct_answer": "The Networks Lab"},
    {"question":
        "DNS is used to convert domain names into IP addresses. (True OR False)", "correct_answer": "True"},
    {"question": "What protocol is used for transferring web pages?",
        "correct_answer": "HTTP"},
    {"question":
        "An IP address is a unique identifier for a device on a network. (True OR False)", "correct_answer": "True"},
    {"question": "What device connects different networks?", "correct_answer": "Router"},
    {"question": "Which network device forwards data based on MAC addresses?",
        "correct_answer": "Switch"}
]

# ===========================================================================


def broadcast_message(message):  # msg to all connected active players
    for player in game_players.values():
        try:
            # send the msg to each players
            player['connection'].send(message.encode())
        except (BrokenPipeError, ConnectionResetError) as e:
            print(
                f"**ERROR** -> Error sending message to {player['name']}: {e}")
            player['connection'].close()

            # Remove player from the game after disconnection
            del game_players[player['connection']]


# ===========================================================================
# this method checks the joined clients number (active players) to start the game when there is enough players (at least 2)

def waiting_for_players():
    while len(game_players) < 2:
        print("Waiting for at least 2 clients to join the game!")
        time.sleep(25)
    print("Enough players connected! Starting the game Within 90 Seconds...")

# ===========================================================================


game_started = False  # flag to check if the game started or not

# to track all asked questions to make sure no questions are repeated..
asked_questions_set = set()


def start_game():
    global game_started, asked_questions_set
    if game_started:
        return  # do not restart the game if it has already begun

    game_started = True
    print("Enough players connected! Game will Start After 90 Seconds...\n")

    # delay 90 seconds before starting the game
    time.sleep(12)

    print("Game starting with players:")
    for player in game_players.values():
        print(
            f"- {player['name']} from {player['connection'].getpeername()}\n\n")

    totalRounds = 3

    for currRound in range(totalRounds):
        initialize_game_round(currRound)

        for question_number in range(3):  # 3 questions per round
            ask_question(question_number, currRound)

        # evaluate the current round winner
        evaluate_round_winner(currRound)

        # announce the final winner in the final round
        if currRound == totalRounds - 1:
            end_game(currRound)
# ===========================================================================


def initialize_game_round(currRound):
    # making sure there are at least 2 active clients (players) to start the round
    while len(game_players) < 2:
        print("Not enough players to start the round. Waiting for more players...")
        broadcast_message(
            f"Not enough players to start Round {
                currRound + 1}. Waiting for more players to join...\n"
        )
        time.sleep(3)  # check new connected players every 10 seconds
    print("________________________________________________________________________\n")
    print(f"\nStarting Round {currRound + 1}\n")
    broadcast_message(
        f"\n{'*'*53}🎲 Round {currRound + 1} 🎲{'*'*53}\n"
    )

# ===========================================================================


def ask_question(question_number, currRound):
    global asked_questions_set
    available_questions = [
        q for q in questions if q['question'] not in asked_questions_set
    ]
    if not available_questions:
        return  # No more questions left to ask..

    # randomly choose an unasked question
    questionInfo = random.choice(available_questions)
    # assign the question as asked
    asked_questions_set.add(questionInfo['question'])
    question = questionInfo['question']
    correct_answer = questionInfo['correct_answer']

    broadcast_message(f"{'===='*30}\n")
    send_to_all_players(f"-> Question {question_number + 1}: {question}\n")
    print(f"Question {question_number + 1}: {question}")
    broadcast_message(f"{'===='*30}\n")

    player_answers = {}
    question_start_time1 = time.time()

    # Wait for player to submit their answersa within 60 seconds
    while time.time() - question_start_time1 < 15:
        readable_sockets, _, _ = select.select(
            [player['connection']
                for player in game_players.values()], [], [], 0.1
        )

        for client_socket in readable_sockets:
            try:
                response = client_socket.recv(1024).decode().strip()
                playerAddress = next(
                    pl_addr for pl_addr, player in game_players.items()
                    if player['connection'] == client_socket
                )
                if playerAddress not in player_answers:
                    player_answers[playerAddress] = {
                        "response": response,
                        "time": time.time() - question_start_time1,
                    }
            except Exception as e:
                print(f" receiving data error: {e}")
                continue

    # notify active players who didn't answer in specified time ..
    for playerAddress, player_data in game_players.items():

        if playerAddress not in player_answers or player_answers[playerAddress]["response"] is None:
            print(f"Player ({game_players[playerAddress]
                             ['name']}) did not answer in time.")

            player_data["connection"].send(
                f"⏰ Time's up! ⏰ The correct answer was: {
                    correct_answer}\n".encode()
            )

    #  update scores..
    checkAnswers_UpdateScores(player_answers, correct_answer)
    # delay (pausing) for 5 seconds before sending the next question
    time.sleep(5)

    player_answers = {}  # reset players answers list to the next qustion

# ===========================================================================
# this method to announce the curr round winner


def evaluate_round_winner(currRound):
    round_winner = max(game_players.items(), key=lambda x: x[1]['score'])
    round_winner_name = round_winner[1]['name']
    round_winner_score = round_winner[1]['score']

    if currRound + 1 < 3:  # If it's not the last round (1st and 2nd rounds)
        round_scores = [player['score']
                        # all player scores in one round
                        for player in game_players.values()]
        roundMaxScore = max(round_scores)

        # find players (one or more) with the max score in the round
        roundTop_Players = [
            roundplayer for roundplayer in game_players if game_players[roundplayer]['score'] == roundMaxScore]

        winnersNames_Round = []

        if len(roundTop_Players) > 1:  # tie case

            winnersNames_Round = ", ".join(
                game_players[roundplayer]['name'] for roundplayer in roundTop_Players)
            round_winner_message = f"\n🎉 End of Round {currRound + 1}! 🎉\nRound {
                currRound + 1} ends with a thrilling tie! The top scorers are: {winnersNames_Round}, each with {round_winner_score} points\n"

            print(f"Round {
                  currRound + 1} ends with a tie between: {winnersNames_Round} , each with {round_winner_score} points")

        else:
            print(f"Round {
                  currRound + 1} winner: {round_winner_name} with {round_winner_score} points")

            round_winner_message = f"\n🎉 End of Round {currRound + 1}! 🎉\nThe winner of Round {
                currRound + 1} is '{round_winner_name}' with {round_winner_score} points!\n"
        broadcast_message(round_winner_message)
        broadcast_message("The Next Round Will Start Within 20 Seconds..🔥")
        time.sleep(20)
    else:  # final winner
        broadcast_message(f"\n🎉 End of The Final Round! 🎉\nThe winner of the final round is '{
                          round_winner_name}' with {round_winner_score} points!\n")

# ===========================================================================

# this method to end game & close server after rounds end and announce the final winner..


def end_game(currRound):
    RevealFinalWinner()  # Reveal the final winner after all rounds end

    # Notify players the server will close soon
    closing_message = (
        "\n🎉 Thank you for playing the Trivia Game! 🎉\n"
        "The server will close in 20 seconds. Have a great day! 😊\n"
    )
    broadcast_message(closing_message)

    # Delay for 20 seconds before shutting down the server
    time.sleep(20)

    # Close all player connections
    for player in game_players.values():
        try:
            player['connection'].close()
        except Exception as e:
            print(f"Error closing connection for {player['name']}: {e}")

    print("Server is shutting down. Goodbye!")
    exit(0)  # Exit the server


# ===========================================================================
# this method to handle players connections

def handle_client(client_socket, client_address):
    print(f"New client connected: {client_address}")
    client_socket.setblocking(False)

    # asking for the joined player name
    client_socket.send("Please enter your name: ".encode())

    ready_to_read, _, _ = select.select([client_socket], [], [], 5)
    if ready_to_read:
        name = client_socket.recv(1024).decode().strip()
        game_players[client_address] = {"name": name,
                                        "score": 0, "connection": client_socket}
        client_socket.send(
            f"\nWelcome, {name}! Waiting for enough players to start the game...\n".encode())

        print(f"Received name from {client_address}: ({name})\n")
        print(f"Total connected players: {len(game_players)}\n")

        rules_message = """
        ******************** Trivia Game Rules ********************
        1. The game consists of 3 rounds, with 3 questions in each round.
        2. You will have only 60 seconds to answer each question.
        3. The faster you answer correctly, the higher your score 😉.
        4. Players who fail to answer within the time limit will be marked as "Timeout".
        5. The player with the highest total score at the end of all rounds wins!
        ************************************************************
        Are you ready?🔥
        The game will start once we have at least 2 players. Please wait...

        """

        client_socket.send(rules_message.encode())

        # Check if at least 2 players -clients-  joined to start the game
        if len(game_players) >= 2 and not game_started:
            start_game()
        elif len(game_players) < 2:
            client_socket.send(
                "Waiting for at least 2 clients to join the game...\n".encode())
    else:
        client_socket.send(
            "Timeout: Could not receive name in time.\n".encode())
        client_socket.close()

# ===========================================================================


# this method used to send the same question to all active players in the game at same time..
def send_to_all_players(message):
    for player in game_players.values():
        player['connection'].send(message.encode())

# ===========================================================================

# => This method checks player answers (game participants), sorts them by response time (fastest first),
# => updates scores based on correctness and speed & sends results to players.
# => Faster correct answers get higher scores, and players who answered wrong or didn't respond in time get ZERO
# => For correct answers, the score is calculated based on how quickly the player responded.
# => (score reduces as time increases) -> reducing by 10% per second after the fastest time..


def checkAnswers_UpdateScores(SubmittedAnswers, CorrectAnswer):

    # ffirst, sort players by response time - only correct answers included
    sorted_playerAnswers = sorted(
        SubmittedAnswers.items(),
        key=lambda x: x[1]['time'] if x[1]['response'] == CorrectAnswer else float(
            'inf')
    )

    # Track the time of the fastest player
    fastest_time = None
    if sorted_playerAnswers:
        fastest_time = sorted_playerAnswers[0][1]['time']

    # check each player's sybmitted answer
    for index, (playerAddress, response_data) in enumerate(sorted_playerAnswers):
        response = response_data['response']
        playerName = game_players[playerAddress]['name']

       # Log player answers and response times.
        print(f"Player ({game_players[playerAddress]['name']}) answered: ({
              response}) in ({response_data['time']:.2f}) seconds")

        if response is None:  # If there is no answer submitted ->  show the "Time's up!" message
            result = ""
            game_players[playerAddress]['connection'].send(
                f"{result}\n".encode())
            game_players[playerAddress]['connection'].send(
                f"Your current score: {game_players[playerAddress]['score']}\n".encode())
            print(f"Updated score for {game_players[playerAddress]['name']}: {
                  game_players[playerAddress]['score']}")
            continue

        # If the answer is correct -> i calculated the score based on answer submitted speed
        if response.lower() == CorrectAnswer.lower():
            time_taken = response_data['time']

            # the first player answers correctly gets full point (1 point)
            if time_taken == fastest_time:
                score = 1
                result = "\n✅ Correct! You were the fastest! 🏃"
            else:  # the 2nd player answers correctly

                # calculate the score based on time difference..
                time_diff = max(0, time_taken - fastest_time)

                # decrement by 10% per second after fastest time
                score = max(0, 1 - time_diff * 0.1)
                result = f"\n✅ Correct! You were not the fastest, but you still got {
                    score:.2f} points! "
        else:  # wrong answer

            score = 0
            result = f"\n❌ Incorrect. The correct answer was: {CorrectAnswer}"

        # update player's score
        game_players[playerAddress]['score'] += score

        # send result message to clients
        game_players[playerAddress]['connection'].send(result.encode())
        game_players[playerAddress]['connection'].send(
            f"Your current score: {game_players[playerAddress]['score']}\n".encode())

    showClientsCurrScore()     # show the current scores to all game players (clients)

# ===========================================================================

# this method sends to the active client the current scores after each question


def showClientsCurrScore():
    score_message = "\n\n--------- Current Scores ---------\n"
    for player in game_players.values():
        score_message += f"{player['name']}: {player['score']}\n"
    broadcast_message(score_message)
    print(score_message)
    print("=========================================================\n")
# ===========================================================================


def RevealFinalWinner():  # announcing the final winner in the game

    max_score = max(game_players[p]['score']
                    for p in game_players)     # Find the highest score

    # find all game players winners
    winners = [p for p in game_players if game_players[p]
               ['score'] == max_score]

    if len(winners) == 1:  # if only one winner
        winner_name = game_players[winners[0]]['name']
        winner_score = game_players[winners[0]]['score']
        print(f"\nThe winner is {winner_name} with {winner_score} points!")
        broadcast_message(
            f"\n{'='*50}\n"
            f" The winner is... 🥁🥁🥁🥁\n"
            f" ✨ {winner_name} ✨ with {winner_score} points! 🏆\n"
            f" Congratulations {winner_name}!! 🥳\n"
            f"{'='*50}\n"
        )
    elif len(winners) > 1:  # more than one winnner case
        tiedPlayers = ", ".join(game_players[p]['name'] for p in winners)
        winner_score = game_players[winners[0]]['score']

        print(f"\nIt's a tie! The players with the highest score are: {
              tiedPlayers} with {winner_score} points!")

        broadcast_message(
            f"\n{'='*50}\n"
            f" It's a tie! 🎉 \n"
            f" Congratulations to {tiedPlayers} with {
                winner_score} points!! 🥳\n"
            f"{'='*50}\n"
        )
    else:  # No winner case ( all players timed out OR answered wrong)
        print("\nNo winner! Everyone timed out or answered incorrectly.")
        broadcast_message(
            f"\n{'='*50}\n"
            f" No winner! 🥲 \nEveryone timed out or answered incorrectly.\n"
            f"{'='*50}\n"
        )
# ===========================================================================

# this is the main methods that runs the server and accpets the players (clients) connections


def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    print(f"\nServer started on {HOST}:{PORT} Waiting for connections...\n")

    while True:
        try:
            client_socket, client_address = server_socket.accept()
            threading.Thread(target=handle_client, args=(
                client_socket, client_address)).start()
        except Exception as e:
            print(f"ERROR: {e}")


if __name__ == "__main__":
    main()
