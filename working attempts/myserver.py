# CITS3002 2021 Assignment
#
# This file implements a basic server that allows a single client to play a
# single game with no other participants, and very little error checking.
#
# Any other clients that connect during this time will need to wait for the
# first client's game to complete.
#
# Your task will be to write a new server that adds all connected clients into
# a pool of players. When enough players are available (two or more), the server
# will create a game with a random sample of those players (no more than
# tiles.PLAYER_LIMIT players will be in any one game). Players will take turns
# in an order determined by the server, continuing until the game is finished
# (there are less than two players remaining). When the game is finished, if
# there are enough players available the server will start a new game with a
# new selection of clients.

import socket
import sys
import tiles
from _thread import *
import threading

idnum = -1 # Starts at -1 so we can see when no one is connected
isReady = 0
playerNum = 0
live_idnums =[]
allIdNums = []
connections = {}
board = tiles.Board()
board.reset()
buffer = {}
#global dictionaries for all things 

def client_connect(connection, address):
    host, port = address
    global playerNum
    name = '{}:{}'.format(host, port)
    playerNum = 1 + playerNum
    print("player numer is:", playerNum)
    # live_idnums = [idnum]
    connection.send(tiles.MessageWelcome(idnum).pack())
    connection.send(tiles.MessagePlayerJoined(name, idnum).pack())

    connection.send(tiles.MessageGameStart().pack())
    

    for _ in range(tiles.HAND_SIZE):
      tileid = tiles.get_random_tileid()
      connection.send(tiles.MessageAddTileToHand(tileid).pack())

    connection.send(tiles.MessagePlayerTurn(idnum).pack())
    print("Got to line 49")

    while True:
      doing = 1
    



def client_handler(connection, address, idnum):

  host, port = address
  name = '{}:{}'.format(host, port)
  global live_idnums
  global playerNum
  global allIdNums
  allIdNums.append(idnum)
  playerNum += 1
  print("player number is ", playerNum)
  live_idnums = [idnum]
  for i in live_idnums:
    print(i)

  connection.send(tiles.MessageWelcome(idnum).pack())
  connection.send(tiles.MessagePlayerJoined(name, idnum).pack())

  # connection.send(tiles.MessageGameStart().pack())
  

  for _ in range(tiles.HAND_SIZE):
    tileid = tiles.get_random_tileid()
    connection.send(tiles.MessageAddTileToHand(tileid).pack())
  
  connection.send(tiles.MessagePlayerTurn(idnum).pack())
  started = 0
  buffer = bytearray()
 
  global board
  # global live_idnums 
  live_idnums.append(idnum)
  


  while True:
    if playerNum > 1 and started == 0:
      connection.send(tiles.MessageGameStart().pack())
      for i in allIdNums:
        connection.send(tiles.MessagePlayerTurn(i).pack())
      # connection.send(tiles.MessageCountdown().pack())
      started += 1

    chunk = connection.recv(4096)

    if not chunk:
      print('client disconnected')
      allIdNums.remove(idnum)
      live_idnums.remove(idnum)
      playerNum -= 1
      return
      # global buffer dictionary 

    buffer.extend(chunk)

  while True:
    msg, consumed = tiles.read_message_from_bytearray(buffer)
    if not consumed:
      break

    buffer = buffer[consumed:]
    # TODO read the message and construct the board from it before sending all updates

    print('received message {}'.format(msg))

    # sent by the player to put a tile onto the board (in all turns except
    # their second)
    if isinstance(msg, tiles.MessagePlaceTile):
      if board.set_tile(msg.x, msg.y, msg.tileid, msg.rotation, msg.idnum):
        # notify client that placement was successful
        if 1 == 1: #playernum > 1
          board.set_tile(msg.x, msg.y, msg.tileid, msg.rotation, msg.idnum)
          connection.send(msg.pack())

        # check for token movement
          positionupdates, eliminated = board.do_player_movement(live_idnums)
          board.do_player_movement(live_idnums)
          print("Got to line 116")

          for msg in positionupdates:
            connection.send(msg.pack())
          print("Got to line 120")
          if idnum in eliminated:
            connection.send(tiles.MessagePlayerEliminated(idnum).pack())
            allIdNums.remove(idnum)
            live_idnums.remove(idnum)
            playerNum -= 1
            return

        # pickup a new tile
          tileid = tiles.get_random_tileid()
          connection.send(tiles.MessageAddTileToHand(tileid).pack())

          # start next turn, IDEA have it go to (idnum+1)%2
          # connection.send(tiles.MessagePlayerTurn((idnum+1)%2).pack())
          connection.send(tiles.MessagePlayerTurn(idnum).pack())
          # connection.send(board.set_player_turn((idnum+1)%2).pack())
          print("Got to line 134")

    # sent by the player in the second turn, to choose their token's
    # starting path
    elif isinstance(msg, tiles.MessageMoveToken):
      if not board.have_player_position(msg.idnum):
        if board.set_player_start_position(msg.idnum, msg.x, msg.y, msg.position):
          board.set_player_start_position(msg.idnum, msg.x, msg.y, msg.position)
          # check for token movement
          positionupdates, eliminated = board.do_player_movement(live_idnums)
          board.do_player_movement(live_idnums)

          for msg in positionupdates:
            connection.send(msg.pack())
          
          if idnum in eliminated:
            connection.send(tiles.MessagePlayerEliminated(idnum).pack())
            playerNum -= 1
            return
          
          # start next turn
          connection.send(tiles.MessagePlayerTurn(idnum).pack())

def client_listener(connection, address):
  buffer = bytearray()
  while True:
    chunk = connection.recv(4096)

    if not chunk:
        print('client message corrupted')
        return

    buffer.extend(chunk)

    while True:
      msg, consumed = tiles.read_message_from_bytearray(buffer)
      if not consumed:  #Means data size = 0
        break

      if isinstance(msg, tiles.MessagePlaceTile):
        for i in allIdNums:
          if board.set_tile(msg.x, msg.y, msg.tileid, msg.rotation, msg.i):
            board.set_tile(msg.x, msg.y, msg.tileid, msg.rotation, msg.i)
            break
      
      elif isinstance(msg, tiles.MessageMoveToken):
        for i in allIdNums:
          if not board.have_player_position(msg.i):
              if board.set_player_start_position(msg.i, msg.x, msg.y, msg.position):
                board.set_player_start_position(msg.i, msg.x, msg.y, msg.position)
                break

def send_to_all(msg):
  for i in live_idnums:
    connections[i].send(msg.pack())

def client_connect():
  global idnum
  global connections

  while True:
    connection, client_address = sock.accept()
    print('received connection from {}'.format(client_address))
    print('connection number {}'.format(idnum))
    start_new_thread(client_connect, (connection,client_address ))  


def client_new_handler(connection,address):
  global idnum
  global buffer
  global connections
  global live_idnums
  idnum += 1
  connections.append(connection)
  live_idnums.append(idnum)

  buffer[idnum] = bytearray()

  while True:
    chunk = connection.recv(4096)

    if not chunk:
      print('client disconnected')
      allIdNums.remove(idnum)
      live_idnums.remove(idnum)
      playerNum -= 1
      return
      # global buffer dictionary 

    buffer[idnum].extend(chunk)



   
# make a main that looks thriough each clients buffer and if it is there turn then it reads buffer sends an update to each client about new 
# placement 
# The client handler ONLY updates all the info then lets them add to the buffer, reading what is in the buffer should happen in main
# Read the buffer if it is there turn (check also if it is valid) then send this update to everyone
# connection[i].send() sends specifically a message to i
# client handler takes it and fills up the buffer

def main():
  # create a TCP/IP socket
  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  # listen on all network interfaces
  server_address = ('', 30020)
  sock.bind(server_address)


  print('listening on {}'.format(sock.getsockname()))

  sock.listen(5)
  #inside my client_listener, ()) let my connections all update  connection, client_address = sock.accept ::connect them all
  #then call the handler which takes information from everyone and my main function listens for when they're in game 

  # Put my while True inside client listener
  start_new_thread(client_listener, ())
  while True:
    # handle each new connection independently 
      connection, client_address = sock.accept()
      # board.reset()
      print('received connection from {}'.format(client_address))
      print('connection number {}'.format(idnum))
      # start_new_thread(client_connect, (connection,client_address,))  
      
      start_new_thread(client_handler, (connection,client_address, idnum,))
      idnum += 1
      # if idnum  > 0:
      # if idnum == 1:  
      #  client_handler(connection, client_address, idnum)
      #  client_handler(connection, client_address, idnum -1)'
    # except KeyboardInterrupt as e:
    #   print("shutting down")

  sock.close()