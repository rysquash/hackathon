import network
from network import *

import helper
from helper import *

import scoreboard
from scoreboard import *

from Tkinter import *
from random import *


root=Tk()

root.title("SphereShoot v.0.1")

frame=Frame()
frame.grid(row=1,column=0)

canvas=Canvas(frame,width=500,height=500)
canvas.grid(row=1,column=0)

upperFrame=Frame(width=root.winfo_screenwidth())
upperFrame.grid(row=0,column=0)

lowerFrame=Frame(width=root.winfo_screenwidth())
lowerFrame.grid(row=2,column=0)

objects=[]

class OpponentBullet:
	def __init__(self):
		self.id=canvas.create_oval(0,0,10,10, fill="blue")

		#this will be changed
		self.uuid=0

#these functions run with the update()
#copy the coordinates from network.newPlayerCoords to the Opponent data
def updateOpponent():
	canvas.coords(helper.opponent.id, *network.newPlayerCoords)

#updates opponent bullets
def updateBullets():

	# delete extra bullets
	while len(helper.opponentBullets)>len(network.newBulletCoords):
		canvas.delete(helper.opponentBullets[-1].id)
		del helper.opponentBullets[-1]

	# make new bullets if we dont have enough
	while len(helper.opponentBullets)<len(network.newBulletCoords):
		helper.opponentBullets.append(OpponentBullet())


	# change coordinates of all bullets to recieved packet
	for count,bulletCoords in enumerate(network.newBulletCoords):
		helper.opponentBullets[count].uuid=bulletCoords[0]

		# remove the hex# from the array
		# del bulletCoords[0]

		# try:
		canvas.coords(helper.opponentBullets[count].id,(bulletCoords[1+0],bulletCoords[1+1],10+bulletCoords[1+0],10+bulletCoords[1+1]))
		# except Exception as e:
		# 	print 'caught crash!!!'
		# 	print e
		# 	print count
		# 	print helper.opponentBullets
		# 	print bulletCoords
		# 	print network.newBulletCoords
		# 	exit()

def restartfn():
	print 'you killed the opponent!'
	gfxInit()
	scoreboardInit()


#send importiant stuff to network
network.lowerFrame=lowerFrame
network.root=root
network.updateOpponent=updateOpponent
network.updateBullets=updateBullets
network.restartfn=restartfn


helper.objects=objects
helper.canvas=canvas
helper.root=root
helper.setLives=scoreboard.setLives



scoreboard.upperFrame=upperFrame
scoreboard.root=root



def update():
	# print 'updating',network.doRestart
	if network.doRestart:
		restartfn()
		network.doRestart=False

		#schedule this function again
		root.after(10,update)
		return


	for obj in objects:
		obj.update()

	bulletCoords=[]

	#make array of coords from bullets
	for count,bullet in enumerate(helper.bullets):

		# use the hex address of the bullet - id returns hex address
		bulletCoords.append([id(helper.bullets[count])]+canvas.coords(bullet.id))
		# if len(bulletCoords[-1])!=3:
		# 	print bulletCoords[-1],bullet,bullet.id

	#make all coords ints
	for count,item in enumerate(bulletCoords):
		bulletCoords[count][1]=int(bulletCoords[count][1])
		bulletCoords[count][2]=int(bulletCoords[count][2])

	# if len(bulletCoords)!=3:
		

	#send coords of everything
	#dont change the order of this
	network.addToSend([int(i) for i in canvas.coords(helper.player.id)])
	network.addToSend(bulletCoords)
	network.addToSend(helper.bulletsToStopSending)
	network.send()


	for localBulletUuid in network.recievedBulletsToStopSending:
		for localbullet in helper.bullets:
			if localBulletUuid==id(localbullet):
				canvas.delete(localbullet.id)

				helper.objects.remove(localbullet)
				helper.bullets.remove(localbullet)

	helper.bulletsToStopSending=[]

	#if there is no opponent, don't update Opponent and Opponent bullets
	if network.destIp:
		updateBullets()
		updateOpponent()
	
	if helper.player.lives<0:
		print "Out of lives!"
		sendRestartMsg()
		gfxInit()
		scoreboardInit()

	#schedule this function again
	root.after(10,update)


# ===== Keybinding ===== #
# w,a,s,d -> move
# r -> restart
# ESC,q -> quit
# b -> debug
root.bind("<Key>", onKey)
canvas.bind("<Button-1>", onClick)

Button(lowerFrame, text="Restart",command=gfxInit).grid(row=1,column=0)

#start update loop
root.after(10,update)

# ===== Init functions ===== #
gfxInit()
networkInit()
scoreboardInit()

root.mainloop()


