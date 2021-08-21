import socket
import sys
import tiles
from _thread import *
import threading
import time
from random import seed
from random import randint
from datetime import datetime
import random

PLAYERMAX = 4
TIMEOUT = 10
idnum = -1 # Starts at 0 so we can see when no one is connected --> idnum starts at 0
isReady = 0
playerNum = 0
playerTurn = 0
live_idnums =[]
allIdNums = []
connections = {}
board = tiles.Board()
board.reset()
buffer = []
names = {}
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tiles_in_hand = {}
players_alive = []
numberPlayersAlive = 0
setup_array = []
connIdnum = -1 # Starts at 0 so we can see when no one is connected --> idnum starts at 0
where_client_start = []
inGameFlag = False
client_catch_up = []
all_messages = []
timeout_bool = False
player_moved = False
started_thread = False
turn_players_up_to = []


def send_to_all(msg):
  global live_idnums
  global connections
  for i in live_idnums:
    connections[i].sendall((msg).pack())
    # print("i is ", i)
    # print("connection is", connections[i])

def send_in_game(msg):
    global connections
    global setup_array

    for i in setup_array:
        connections[i].sendall(msg.pack())



def client_connect():
  global idnum
  global connections

  while True:
    connection, client_address = sock.accept()
    print('received connection from {}'.format(client_address))
    print('connection number {}'.format(idnum+1))
    start_new_thread(client_new_handler, (connection,client_address, ))  
    



def client_new_handler(connection,address):

  global idnum
  global buffer
  global connections
  global live_idnums
  global playerNum
  global names
  global numberPlayersAlive
  global setup_array
  global playerTurn
  global connIdnum
  global inGameFlag
  global client_catch_up
  global players_alive
  
  connIdnum += 1
  host, port = address
  name = '{}:{}'.format(host, port)
  names[connIdnum] = name
  playerNum += 1  
  connectNum = connIdnum
  connections[connectNum] = connection
  live_idnums.append(connIdnum)
  players_alive.append(False)

  buffer.append(bytearray())

  if in_game():
      client_catch_up.append(connIdnum)

  while True:
    chunk = connection.recv(4096)

    if not chunk:
      print('client {} disconnected'.format(names[connectNum]))
      live_idnums.remove(connectNum)
      if connectNum in setup_array:
        numberPlayersAlive -= 1
        setup_array.remove(connectNum)
        players_alive[connectNum] = False

      send_to_all(tiles.MessagePlayerEliminated(connectNum))
      if playerTurn == connectNum:
        for i in range(len(players_alive)):
            playerTurn = (playerTurn + 1)%playerNum
            if players_alive[playerTurn] == True:
                break
            print("227 Number Players Alive =",numberPlayersAlive)
        send_in_game(tiles.MessagePlayerTurn(playerTurn)) 

      return
      # global buffer dictionary 

    buffer[connectNum].extend(chunk)
    

def connect_all_players():
    global idnum
    global buffer
    global connections
    global live_idnums
    global names
    global board
    global playerNum
    global players_alive
    global numberPlayersAlive
    global setup_array
    global all_messages
    global PLAYERMAX
    global turn_players_up_to

    send_to_all(tiles.MessageGameStart())
    all_messages.append(tiles.MessageGameStart())

    setup_array.clear() 
    if len(live_idnums) > PLAYERMAX:
        seed(datetime.now())
        setup_array = random.sample(range(0,(len(live_idnums))), PLAYERMAX)[:] 
    else:
        setup_array = live_idnums[:]
    
    # setup_array.append(live_idnums[0])
    # setup_array.append(live_idnums[1])
    print("setup Array is", setup_array)
    numberPlayersAlive = 0 #Reset number of players alive
    for i in live_idnums:
        
        print("in connect i is ", i)
        connections[i].send(tiles.MessageWelcome(i).pack())
        # if not to i then send it
        for j in setup_array:
            if j != i:
                connections[i].send((tiles.MessagePlayerJoined(names[j], j)).pack())
    
    for i in live_idnums:
        for j in setup_array:
            all_messages.append((tiles.MessagePlayerJoined(names[j], j)))


    for i in setup_array:
        numberPlayersAlive += 1
        send_to_all(tiles.MessagePlayerTurn(i))
        all_messages.append(tiles.MessagePlayerTurn(i))
        
    send_to_all(tiles.MessagePlayerTurn(setup_array[0]))
    all_messages.append(tiles.MessagePlayerTurn(setup_array[0]))

    print("players alive ",numberPlayersAlive)

    players_alive = [False for i in range(playerNum + 1)]  
    turn_players_up_to = [0 for i in range(playerNum + 1)]
    for i in setup_array:
        players_alive[i] = True
    print(players_alive)
    for i in setup_array:
        tiles_in_hand[i] = []
        for _ in range(tiles.HAND_SIZE):
                tileid = tiles.get_random_tileid()
                connections[i].send((tiles.MessageAddTileToHand(tileid)).pack())
                tiles_in_hand[i].append(tileid)


def players_turn():
    global idnum
    global buffer
    global connections
    global live_idnums
    global playerNum
    global names
    global playerTurn
    global board
    global where_tile_placed
    global players_alive
    global numberPlayersAlive
    global all_messages
    global player_moved
    global started_thread
    global timeout_bool
    global TIMEOUT
    global turn_players_up_to

    # global turn_timer
    timeout_bool = True

    positionupdates = []
    eliminated = []

    
    if idnum == playerTurn and players_alive[idnum]:
    
        if timeout_bool:
            print("Timed out")

            if turn_players_up_to[idnum] != 1:
                print("Hand is",tiles_in_hand[idnum])
                for x in range(4):
                    for y in range(4):
                        for tile in tiles_in_hand[idnum]:
                            msg = tiles.MessagePlaceTile(idnum,tile, 1, x, y)
                            print("x:",msg.x)
                            print("y:",msg.y)
                            print("Tile:",msg.tileid)
                            if board.set_tile(msg.x, msg.y, msg.tileid, msg.rotation, msg.idnum):
                                print("tile is",tiles_in_hand[idnum][0])
                                time.sleep(1)
                                # timeout_bool = False
                                # board.set_tile(x, y,tiles_in_hand[idnum][0], rot, idnum)
                                send_to_all(msg)
                                
                                all_messages.append(msg)
                
                                # check for token movement
                                positionupdates, eliminated = board.do_player_movement(live_idnums)
                                # board.do_player_movement(live_idnums)
                                print("Got to line 166")

                                for msg in positionupdates:
                                    # connections[idnumm].send(msg.pack()) DIDNT work has to be send_to_all:)
                                    send_to_all(msg)
                                    all_messages.append(msg)
                                if idnum in eliminated:                    
                                    players_alive[idnum] = False
                                    send_to_all(tiles.MessagePlayerEliminated(idnum))
                                    all_messages.append((tiles.MessagePlayerEliminated(idnum)))
                                    print("eliminated player:", idnum)
                                    print(players_alive)
                                    while True:
                                        playerTurn = (playerTurn + 1)%playerNum
                                        if players_alive[playerTurn] == True:
                                            break
                                    numberPlayersAlive = numberPlayersAlive - 1
                                    print("181 Number Players Alive =",numberPlayersAlive)
                                    send_to_all(tiles.MessagePlayerTurn(playerTurn))
                                #     #TODO remove eliminated players from live idnums list --> maybe write a function                    
                                #     return

                                # Pick up new tile for the one you placed
                                tiles_in_hand[idnum].remove(tiles_in_hand[idnum][0])
                                tileid = tiles.get_random_tileid()
                                tiles_in_hand[idnum].append(tileid)
                                connections[idnum].send(tiles.MessageAddTileToHand(tileid).pack())
                                print("This player just moved:", playerTurn)

                                while True:
                                    playerTurn = (playerTurn + 1)%playerNum
                                    if players_alive[playerTurn] == True:
                                        break

                                send_to_all(tiles.MessagePlayerTurn(playerTurn))
                                all_messages.append(tiles.MessagePlayerTurn(playerTurn))
                                print( "This player will move next: ", playerTurn)
                                player_moved = False
                                started_thread = False
                                turn_players_up_to[idnum] += 1
                                time.sleep(1)
                                return

            elif turn_players_up_to[idnum] == 1:
                if not board.have_player_position(idnum):
                    for x in range(tiles.BOARD_WIDTH):
                        for y in range(tiles.BOARD_HEIGHT):
                            for pos in range(7):
                                msg = tiles.MessageMoveToken(idnum,x, y, pos)
                                if board.set_player_start_position(msg.idnum, msg.x, msg.y,msg.position):
                                    #code for sending
                                    send_to_all(msg)
                                    positionupdates, eliminated = board.do_player_movement(live_idnums)
                                    board.do_player_movement(live_idnums)
                                    all_messages.append(msg)
                                    for msg in positionupdates:
                                        send_to_all(msg)
                                        all_messages.append(msg)
                                    if idnum in eliminated:
                                        players_alive[idnum] = False
                                        send_to_all(tiles.MessagePlayerEliminated(idnum))
                                        all_messages.append(tiles.MessagePlayerEliminated(idnum))
                                        while True:
                                            playerTurn = (playerTurn + 1)%playerNum
                                            if players_alive[playerTurn] == True:
                                                break
                                        numberPlayersAlive = numberPlayersAlive - 1
                                        print("227 Number Players Alive =",numberPlayersAlive)
                                        send_to_all(tiles.MessagePlayerTurn(playerTurn))
                                        all_messages.append(tiles.MessagePlayerTurn(playerTurn))
                                        return
                                    print( "This player just moved ", playerTurn)
                                
                                    print("This player will move next:", playerTurn)

                                    while True:
                                        playerTurn = (playerTurn + 1)%playerNum
                                        if players_alive[playerTurn] == True:
                                            break
                                    send_to_all(tiles.MessagePlayerTurn(playerTurn))
                                    all_messages.append(tiles.MessagePlayerTurn(playerTurn))
                                    print("This player will move next:", playerTurn)
                                    player_moved = False
                                    started_thread = False
                                    turn_players_up_to[idnum] += 1
                                    return
    else:
        buffer[idnum] = bytearray() #If it is not there turn clear the buffer
        return

def timeout_function():
    global timeout_bool
    print("inside timeout_Function")
    timeout_bool = True


def timeout_thread():
    global timeout_bool
    global player_moved   
    global started_thread
    started_thread = True
    print("Inside timeoutThread")

    for i in range(1000):
        time.sleep(1)
        if player_moved:
            started_thread = False
            return
    timeout_bool = True
    
#My helper functions
def game_ready():
    global live_idnums

    return (len(live_idnums) > 1) #Means n players are connected
def game_over():
    global numberPlayersAlive
    return (numberPlayersAlive == 1)
def in_game():
    global inGameFlag
    return inGameFlag


def main():
  # create a TCP/IP socket
  global sock
  global playNum
  global live_idnums
  global connections
  global board
  global lock
  global idnum
  global playerTurn 
  global where_tile_placed
  global players_alive
  global setup_array
  global inGameFlag
  global all_messages
  playerTurn = 0
  done = 0

  lock = threading.Lock()

  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  # listen on all network interfaces
  server_address = ('', 30020)
  sock.bind(server_address)


  print('listening on {}'.format(sock.getsockname()))

  sock.listen(5)
  
  start_new_thread(client_connect, ())
  print("line 167")
  while True:

    if game_ready() and not in_game():
        # TODO sent all a countdown or waiting message
        time.sleep(2)
        connect_all_players()
        print("line 305")
        playerTurn = setup_array[0]
        inGameFlag = True
    if game_ready() and in_game():
        lock.acquire()
        try:
            players_turn()
            idnum = (idnum + 1)%playerNum
            if client_catch_up:
                for i in client_catch_up:
                    connections[i].send(tiles.MessageWelcome(i).pack())
                    for j in all_messages:                        
                        connections[i].send(j.pack())
                    client_catch_up.remove(i)
        finally:
            lock.release()
    
    if game_ready() == False:
        board.reset()
    
    if game_over() and in_game(): #called to start a new game
        time.sleep(3)
        send_to_all(tiles.MessageGameStart())
        print("Line 299")
        for i in live_idnums: #Clears all the buffers
            buffer[i] = bytearray()
        
        board.reset()
        all_messages.clear()
        playerTurn = 0
        inGameFlag = False   
    


  sock.close()

if __name__ == "__main__":
    main()