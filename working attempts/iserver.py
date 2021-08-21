import socket
import sys
import tiles
from _thread import *
import threading
import time
from random import seed
from random import randint
from datetime import datetime

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
where_tile_placed = []
players_alive = []
numberPlayersAlive = 0
setup_array = []

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
  idnum += 1
  host, port = address
  name = '{}:{}'.format(host, port)
  names[idnum] = name
  playerNum += 1  
  connectNum = idnum
  connections[connectNum] = connection
  live_idnums.append(idnum)

  buffer.append(bytearray())

  while True:
    chunk = connection.recv(4096)

    if not chunk:
      print('client {} disconnected'.format(names[connectNum]))
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

    playerMaximum = 4
    send_to_all(tiles.MessageGameStart())

    setup_array.clear() 
    if len(live_idnums) > playerMaximum:
        seed(datetime.now())
        val = randint(0,len(live_idnums)-1)
        for i in range(playerMaximum):
            setup_array.append(val)
            val = (val + 1)%(len(live_idnums)-1)
    else:
        setup_array = live_idnums[:]
    
    # setup_array.append(live_idnums[0])
    # setup_array.append(live_idnums[1])
    print("setup Array is", setup_array)
    numberPlayersAlive = 0 #Reset number of players alive
    for i in setup_array:
        numberPlayersAlive += 1
        print("in connect i is ", i)
        connections[i].send(tiles.MessageWelcome(i).pack())
        # if not to i then send it
        for j in setup_array:
            if j != i:
                connections[i].send((tiles.MessagePlayerJoined(names[j], j)).pack())

    for i in setup_array:
        send_in_game(tiles.MessagePlayerTurn(i))
    send_in_game(tiles.MessagePlayerTurn(setup_array[0]))

    print("players alive ",numberPlayersAlive)

    players_alive = [False for i in range(playerNum)]  
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


    positionupdates = []
    eliminated = []

    
    if idnum == playerTurn and players_alive[idnum]:
        # print("162 Idum is ", idnum)
        msg, consumed = tiles.read_message_from_bytearray(buffer[idnum])
        if not consumed:
            return
        buffer[idnum] = buffer[idnum][consumed:]   

        print('received message {}'.format(msg))
        # sent by the player to put a tile onto the board (in all turns except
        # their second)
        if isinstance(msg, tiles.MessagePlaceTile):
            print("Past first place tile if")
            if board.set_tile(msg.x, msg.y, msg.tileid, msg.rotation, msg.idnum):
                send_to_all(msg)
                currentTile = msg.tileid
                where_tile_placed.append((msg.x, msg.y, msg.tileid, msg.rotation, msg.idnum))
 
                # check for token movement
                positionupdates, eliminated = board.do_player_movement(live_idnums)
                # board.do_player_movement(live_idnums)
                print("Got to line 166")

                for msg in positionupdates:
                    # connections[idnumm].send(msg.pack()) DIDNT work has to be send_to_all:)
                    send_to_all(msg)
                if idnum in eliminated:
                    players_alive[idnum] = False
                    send_to_all(tiles.MessagePlayerEliminated(idnum))
                    print("eliminated player:", idnum)
                    print(players_alive)
                    while True:
                        playerTurn = (playerTurn + 1)%playerNum
                        if players_alive[playerTurn] == True:
                            break
                    numberPlayersAlive = numberPlayersAlive - 1
                    print("181 Number Players Alive =",numberPlayersAlive)
                    send_in_game(tiles.MessagePlayerTurn(playerTurn))
                    #TODO remove eliminated players from live idnums list --> maybe write a function
  
                    return

                # Pick up new tile for the one you placed
                tileid = tiles.get_random_tileid()
                connections[idnum].send(tiles.MessageAddTileToHand(tileid).pack())
                print("This player just moved:", playerTurn)

                while True:
                    playerTurn = (playerTurn + 1)%playerNum
                    if players_alive[playerTurn] == True:
                        break

                send_in_game(tiles.MessagePlayerTurn(playerTurn))
                print( "This player will move next: ", playerTurn)
            # sent by the player in the second turn, to choose their token's
            # starting path

        elif isinstance(msg, tiles.MessageMoveToken):
            print(msg.idnum)
            print(idnum)
            if not board.have_player_position(idnum):
                print("past the not if")
                if board.set_player_start_position(idnum, msg.x, msg.y, msg.position):
                    print("Past the board conditions")
                    
 
                    print("Getting here 211")

                    send_to_all(msg)
                    positionupdates, eliminated = board.do_player_movement(live_idnums)
                    board.do_player_movement(live_idnums)

                    for msg in positionupdates:
                        send_to_all(msg)

                    if idnum in eliminated:
                        players_alive[idnum] = False
                        send_to_all(tiles.MessagePlayerEliminated(idnum))
                        while True:
                            playerTurn = (playerTurn + 1)%playerNum
                            if players_alive[playerTurn] == True:
                                break
                        numberPlayersAlive = numberPlayersAlive - 1
                        print("227 Number Players Alive =",numberPlayersAlive)
                        send_in_game(tiles.MessagePlayerTurn(playerTurn))
                        return
                    print( "This player just moved ", playerTurn)
                   
                    print("This player will move next:", playerTurn)

                    while True:
                        playerTurn = (playerTurn + 1)%playerNum
                        if players_alive[playerTurn] == True:
                            break
                    send_in_game(tiles.MessagePlayerTurn(playerTurn))
                    print("This player will move next:", playerTurn)
    else:
        buffer[idnum] = bytearray() #If it is not there turn clear the buffer
        return
    

def game_ready():
    global live_idnums
    return (len(live_idnums) > 4) #Means 3 players are connected

    return (playerNum > 2)
def game_over():
    global numberPlayersAlive
    return (numberPlayersAlive == 1)


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

    if game_ready() and done == 0:
        # TODO sent all a countdown or waiting message
        time.sleep(10)
        connect_all_players()
        print("line 305")
        playerTurn = setup_array[0]
        done += 1
    if game_ready() and done > 0:
        lock.acquire()
        try:
            players_turn()
            idnum = (idnum + 1)%playerNum
        finally:
            lock.release()
    
    if game_ready() == False:
        board.reset()
    
    if game_over() and done == 1: #called to start a new game
        time.sleep(3)
        send_to_all(tiles.MessageGameStart())
        print("Line 299")
        for i in live_idnums: #Clears all the buffers
            buffer[i] = bytearray()
        
        board.reset()
        where_tile_placed.clear()            
        playerTurn = 0
        done = 0      


  sock.close()

if __name__ == "__main__":
    main()