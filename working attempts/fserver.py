import socket
import sys
import tiles
from _thread import *
import threading
import time

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

def send_to_all(msg):
  global live_idnums
  global connections
  for i in live_idnums:
    connections[i].sendall((msg).pack())
    # print("i is ", i)
    # print("connection is", connections[i])


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

    for i in live_idnums:
        print("in connect i is ", i)
        connections[i].send(tiles.MessageWelcome(i).pack())
        # if not to i then send it
        for j in live_idnums:
            if j != i:
                connections[i].send((tiles.MessagePlayerJoined(names[j], j)).pack())

    for i in live_idnums:
        send_to_all(tiles.MessagePlayerTurn(i))
    send_to_all(tiles.MessagePlayerTurn(0))

    players_alive = [True for i in range(6)]


    
    for i in live_idnums:
        tiles_in_hand[i] = []
        for _ in range(tiles.HAND_SIZE):
                tileid = tiles.get_random_tileid()
                connections[i].send((tiles.MessageAddTileToHand(tileid)).pack())
                tiles_in_hand[i].append(tileid)

    # connections[0].sendall((tiles.MessagePlayerTurn(live_idnums[1]).pack()))
    # switcher = { 
    #     2: [1,0,0,1],
    #     3: [1,2,0,0,1,2,2,0,1]
    # }

    # send_list = switcher[playerNum]
    # sender = 0
    # for i in live_idnums:
    #     for j in range(playerNum):
    #         connections[i].sendall((tiles.MessagePlayerTurn(send_list[sender]).pack()))
    #         sender += 1  
    
    # for i in tiles_in_hand:
    #     print(tiles_in_hand[i])

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
            if board.set_tile(msg.x, msg.y, msg.tileid, msg.rotation, msg.idnum):
                send_to_all(msg)
                currentTile = msg.tileid
                where_tile_placed.append((msg.x, msg.y, msg.tileid, msg.rotation, msg.idnum))
 
                # check for token movement
                positionupdates, eliminated = board.do_player_movement(live_idnums)
                # board.do_player_movement(live_idnums)
                print("Got to line 116")

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
                    send_to_all(tiles.MessagePlayerTurn(playerTurn))
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
                send_to_all(tiles.MessagePlayerTurn(playerTurn))
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
                    
 
                    print("Getting here 202")

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
                        send_to_all(tiles.MessagePlayerTurn(playerTurn))
                        return
                    print( "This player just moved ", playerTurn)
                   
                    print("This player will move next:", playerTurn)

                    while True:
                        playerTurn = (playerTurn + 1)%playerNum
                        if players_alive[playerTurn] == True:
                            break
                    send_to_all(tiles.MessagePlayerTurn(playerTurn))
                    print("This player will move next:", playerTurn)
    else:
        buffer[idnum] = bytearray() #If it is not there turn clear the buffer
        return
    

def game_ready():
    global playerNum
    return (playerNum > 2)


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
        # time.sleep(5)
        connect_all_players()

        print("line 169")
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
        


  sock.close()

if __name__ == "__main__":
    main()