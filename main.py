import network
from network import *

import helper
from helper import *

import scoreboard
from scoreboard import *

from Tkinter import *
from random import *
from sys import exit
import tkMessageBox
import time

# ===== Create the window ===== #
root=Tk()
root.title("SphereShooter v.1.0")

#top frame for scores
upperFrame=Frame(width=root.winfo_screenwidth())
upperFrame.grid(row=0,column=0)

#middle frame for the canvas
middleframe=Frame()
middleframe.grid(row=1,column=0)

canvas=Canvas(middleframe,width=helper.CANVASWIDTH,height=helper.CANVASHEIGHT,background="GRAY")
canvas.grid(row=1,column=0)

#lower frame for text box and restart buttom
lowerFrame=Frame(width=root.winfo_screenwidth())
lowerFrame.grid(row=2,column=0)

objects=[]

#these functions run with the update()
#copy the coordinates from network.newPlayerCoords to the Opponent data
def updateOpponent():
	canvas.coords(helper.opponent.id, *network.newPlayerCoords)

#updates opponent bullets from received data
def updateBullets():

	# delete extra bullets
	while len(helper.opponentBullets)>len(network.newBulletCoords):
		canvas.delete(helper.opponentBullets[-1].id)
		del helper.opponentBullets[-1]

	# make new bullets if we don't have enough
	while len(helper.opponentBullets)<len(network.newBulletCoords):
		helper.opponentBullets.append(OpponentBullet())


	# change coordinates of all bullets to received packet
	for count,bulletCoords in enumerate(network.newBulletCoords):
		helper.opponentBullets[count].uuid=bulletCoords[0]


		canvas.coords(helper.opponentBullets[count].id,(bulletCoords[1],bulletCoords[2],10+bulletCoords[1],10+bulletCoords[2]))


def restartfn(doSendMsg):
	print 'restarting!'

	gfxInit()
	scoreboardInit()
	if doSendMsg:
		sendRestartMsg()


#copy globals to other modules
network.lowerFrame=lowerFrame
network.root=root
network.updateOpponent=updateOpponent
network.updateBullets=updateBullets

helper.objects=objects
helper.canvas=canvas
helper.root=root
helper.updateLivesLabel=scoreboard.updateLivesLabel
helper.restartfn=restartfn

scoreboard.upperFrame=upperFrame
scoreboard.root=root

def update():

	if helper.player.lives<=0:
		print "Out of lives!"
		sendLoseMsg()
		if tkMessageBox.askyesno("You lost!", "Play again?"):			
			restartfn(False)
			network.doRestart=False
			
			# Schedule this function again
			root.after(10,update)
		else:
			exit()

		return

	if scoreboard.otherScoreLabelVar.get()!=network.newOtherScore:
		scoreboard.otherScoreLabelVar.set(network.newOtherScore)

	#if threading udp server got restart packet, restart
	if network.doRestart:
		restartfn(False)
		network.doRestart=False

		# Schedule this function again
		root.after(10,update)
		return

	if network.iWon:
		print 'you killed the opponent!'
		if tkMessageBox.askyesno("You won!", "Play again?"):			
			restartfn(False)
			network.iWon=False

			# Schedule this function again
			root.after(10,update)
		else:
			exit()
		return



	if network.OppStatusBoxVar.get()!=network.newStatusString:
		network.OppStatusBoxVar.set(network.newStatusString)
		network.OppStatusBox.config(fg=network.newStatusColor)
		

	if network.isConnected and  (time.time()-network.TimeSinceLastPacket)*1000>network.CONNECTIONTIMEOUT:
		print 'not connected any more'
		network.isConnected=False
		network.newStatusColor="red"
		network.newStatusString="Not Connected"
		network.OppStatusBoxVar.set("Not Connected")
		network.OppStatusBox.config(fg='red')
		
		
	#update speed
	deltaSpeed=[0,0]
	for key in helper.pressedKeys:
		if helper.pressedKeys[key]:
			newSpeed={"w":[0,-helper.CONTROLSENSITIVITY],"a":[-helper.CONTROLSENSITIVITY,0],"s":[0,helper.CONTROLSENSITIVITY],"d":[helper.CONTROLSENSITIVITY,0]}[key]
			deltaSpeed[0]+=newSpeed	[0]
			deltaSpeed[1]+=newSpeed	[1]

	helper.player.deltaX[0]+=deltaSpeed[0]
	helper.player.deltaX[1]+=deltaSpeed[1]


	for obj in objects:
		obj.update()

	bulletCoords=[]

	#make array of coords from bullets
	for count,bullet in enumerate(helper.bullets):

		# use the hex address of the bullet as uuid (id returns hex address)
		bulletCoords.append([id(helper.bullets[count])]+canvas.coords(bullet.id))


	#make all coords ints
	for count,item in enumerate(bulletCoords):
		bulletCoords[count][1]=int(bulletCoords[count][1])
		bulletCoords[count][2]=int(bulletCoords[count][2])


		

	#send coords of everything
	#order of this is importiant
	network.addToSend([int(i) for i in canvas.coords(helper.player.id)])
	network.addToSend(bulletCoords)
	network.addToSend(helper.bulletsToStopSending)
	network.addToSend(helper.player.lives)
	network.send()


	#loop through bullets opponent told you to delete
	for localBulletUuid in network.recievedBulletsToStopSending:
		for localbullet in helper.bullets:

			#if the recieved uuid matches a bullet
			if localBulletUuid==id(localbullet):

				#delete it from the screen
				canvas.delete(localbullet.id)

				#and the object lists
				helper.objects.remove(localbullet)
				helper.bullets.remove(localbullet)

	helper.bulletsToStopSending=[]

	#if there is no opponent, don't update Opponent and Opponent bullets
	if network.destIp:
		updateBullets()
		updateOpponent()
		
	# Schedule this function again
	root.after(10,update)



# ===== Key binding ===== #
# w,a,s,d -> move
# r -> restart
# ESC,q -> quit
# b -> debug
root.bind("<Key>", onKey)
root.bind("<Any-KeyRelease>", onKey)
canvas.bind("<Button-1>", onClick)

Button(lowerFrame, text="Restart",command=gfxInit).grid(row=1,column=0)

#start update loop
root.after(10,update)

# ===== Init functions ===== #
gfxInit()
networkInit()
scoreboardInit()

root.mainloop()
