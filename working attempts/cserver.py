import socket
import sys
import tiles
from _thread import *
import threading
import time

idnum = -1 # Starts at 0 so we can see when no one is connected --> idnum starts at 1
isReady = 0
playerNum = 0
playerTurn = 0
live_idnums =[]
allIdNums = []
connections = {}
board = tiles.Board()
board.reset()
buffer = {}
names = {}
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def send_to_all(msg):
  global live_idnums
  global connections
  for i in live_idnums:
    connections[i].send((msg).pack())
    # print("i is ", i)
    # print("connection is", connections[i])

def remove_element(array,element):
    return

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
  connections[idnum] = connection
  live_idnums.append(idnum)

 
  # for _ in range(tiles.HAND_SIZE):
  #   tileid = tiles.get_random_tileid()
  #   connection.send(tiles.MessageAddTileToHand(tileid).pack())
  

  
#   for _ in range(tiles.HAND_SIZE):
#             tileid = tiles.get_random_tileid()
#             connections[idnum].send(tiles.MessageAddTileToHand(tileid).pack())

  for i in live_idnums:
      print("id {} is alive".format(i))
#   playerTurn = 1

  buffer[connectNum] = bytearray()

  while True:
    chunk = connection.recv(4096)

    if not chunk:
      print('client {} disconnected'.format(names[connectNum]))
      allIdNums.remove(connectNum)
      live_idnums.remove(connectNum)
      playerNum -= 1
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

    
    # connections[0].send(tiles.MessageWelcome(live_idnums[0]).pack())
    # connections[1].send(tiles.MessageWelcome(live_idnums[1]).pack())
    # connections[1].send(tiles.MessageWelcome(live_idnums[0]).pack())    
    # connections[0].send(tiles.MessageWelcome(live_idnums[1]).pack())
    # connections[0].send(tiles.MessagePlayerJoined(names[0], live_idnums[0]).pack())
    # connections[1].send(tiles.MessagePlayerJoined(names[0], live_idnums[0]).pack())
    # connections[0].send(tiles.MessagePlayerJoined(names[1], live_idnums[1]).pack())
    # connections[1].send(tiles.MessagePlayerJoined(names[1], live_idnums[1]).pack())
    

    # connections[0].send(tiles.MessageGameStart().pack())
    # connections[1].send(tiles.MessageGameStart().pack())


    # connections[0].send((tiles.MessagePlayerTurn(live_idnums[1]).pack()))
    # connections[1].send((tiles.MessagePlayerTurn(live_idnums[1]).pack()))
    # connections[0].send((tiles.MessagePlayerTurn(live_idnums[0]).pack()))
    # connections[1].send((tiles.MessagePlayerTurn(live_idnums[0]).pack()))
 
    for i in live_idnums:
        print("in connect i is ", i)
        send_to_all(tiles.MessageWelcome(i))
        send_to_all(tiles.MessagePlayerJoined(names[i], i))

    # for _ in range(tiles.HAND_SIZE):
    #         tileid = tiles.get_random_tileid()
    #         connections[0].send((tiles.MessageAddTileToHand(tileid)).pack())
    # for _ in range(tiles.HAND_SIZE):
    #         tileid = tiles.get_random_tileid()
    #         connections[1].send((tiles.MessageAddTileToHand(tileid)).pack())
    # send_to_all((tiles.MessageGameStart()))
    connections[0].send(tiles.MessagePlayerTurn(1).pack()) #needed to make it work for some reason 
    # connections[1].send(tiles.MessagePlayerTurn(0).pack())
    for i in live_idnums:
        # connections[i].send(tiles.MessagePlayerTurn(i).pack())
        send_to_all(tiles.MessagePlayerTurn(i))
        for _ in range(tiles.HAND_SIZE):
                tileid = tiles.get_random_tileid()
                connections[i].send((tiles.MessageAddTileToHand(tileid)).pack())
        

def players_turn():
    global idnum
    global buffer
    global connections
    global live_idnums
    global playerNum
    global names
    global playerTurn
    global board
    idnum = playerTurn
    positionupdates = []
    eliminated = []

    msg, consumed = tiles.read_message_from_bytearray(buffer[idnum])
    if not consumed:
        return

    buffer[idnum] = buffer[idnum][consumed:]   

    print('received message {}'.format(msg))
    # sent by the player to put a tile onto the board (in all turns except
    # their second)
    if isinstance(msg, tiles.MessagePlaceTile):
        if board.set_tile(msg.x, msg.y, msg.tileid, msg.rotation, msg.idnum):
            # notify client that placement was successful
            board.set_tile(msg.x, msg.y, msg.tileid, msg.rotation, msg.idnum)
            send_to_all(msg)
            # for i in live_idnums:
            #     if i == idnum:
            #         connections[idnum].send(msg.pack())
            #     else:
            #         connections[i].send(msg.pack()) # To everyone else i just want to say a tile has been placed not that they placed it 

            # is there a message for displaying a tile without having it placed by that client
            # When I put a piece down that the other client has for turn 1, client2 automatically places piece in same position
            # as where client1 placed it

            # check for token movement
            positionupdates, eliminated = board.do_player_movement(live_idnums)
            board.do_player_movement(live_idnums)
            print("Got to line 116")

            for msg in positionupdates:
                # connections[idnumm].send(msg.pack()) DIDNT work has to be send_to_all:)
                send_to_all(msg)
            if idnum in eliminated:
                send_to_all(tiles.MessagePlayerEliminated(idnum))
                #TODO remove eliminated players from live idnums list --> maybe write a function
                # allIdNums.remove(idnum)
                # live_idnums.remove(idnum)
                playerNum -= 1
                return

            # pickup a new tile
            tileid = tiles.get_random_tileid()
            connections[idnum].send(tiles.MessageAddTileToHand(tileid).pack())
            print("This player just moved:", playerTurn)
            playerTurn = (playerTurn + 1)%playerNum
            print( "This player will move next: ", playerTurn)

            # start next turn, IDEA have it go to (idnum+1)%2
            # connection.send(tiles.MessagePlayerTurn((idnum+1)%2).pack())
            # send_to_all(tiles.MessagePlayerTurn(playerTurn))
            # connection.send(board.set_player_turn((idnum+1)%2).pack())
            send_to_all(tiles.MessagePlayerTurn(playerTurn))
        # sent by the player in the second turn, to choose their token's
        # starting path

    elif isinstance(msg, tiles.MessageMoveToken):
        print(idnum)
        if not board.have_player_position(idnum):
            print("past the not if")
            if board.set_player_start_position(msg.idnum, msg.x, msg.y, msg.position):
                print("Past the board conditions")
                
                board.set_player_start_position(msg.idnum, msg.x, msg.y, msg.position)
                print("Getting here 202")
                # check for token movement
                positionupdates, eliminated = board.do_player_movement(live_idnums)
                board.do_player_movement(live_idnums)

                for msg in positionupdates:
                    # connections[idnum].send(msg.pack())
                    send_to_all(msg)

                if idnum in eliminated:
                    send_to_all(tiles.MessagePlayerEliminated(idnum))
                    playerNum -= 1
                    return
                print( "This player just moved ", playerTurn)
                playerTurn = (playerTurn + 1)%playerNum
                print("This player will move next:", playerTurn)

                #should be %PlayerNum at some point ^^
                    # start next turn
                    # connection.send(tiles.MessagePlayerTurn(idnum).pack())
                send_to_all(tiles.MessagePlayerTurn(playerTurn))
        elif  board.have_player_position(idnum):
            print("Has player_position for idnum", idnum)
    

def game_ready():
    global playerNum
    return (playerNum > 1)


def main():
  # create a TCP/IP socket
  global sock
  global playNum
  global live_idnums
  global connections
  global board
  global lock
  playerTurn = 0
  done = 0

  lock = threading.Lock()

  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  # listen on all network interfaces
  server_address = ('', 30020)
  sock.bind(server_address)


  print('listening on {}'.format(sock.getsockname()))

  sock.listen(5)
  #inside my client_listener, ()) let my connections all update connection, client_address = sock.accept ::connect them all
  #then call the handler which takes information from everyone and my main function listens for when they're in game 

  # Put my while True inside client listener
  start_new_thread(client_connect, ())
  print("line 167")
  while True:

    if game_ready() and done == 0:
        # time.sleep(10)
        connect_all_players()
        print("line 169")
        done += 1
    if game_ready() and done > 0:
        # lock.acquire()
        # try:
            players_turn()
        # finally:
        #     lock.release()
    
    if game_ready() == False:
        board.reset()
        


  sock.close()

if __name__ == "__main__":
    main()