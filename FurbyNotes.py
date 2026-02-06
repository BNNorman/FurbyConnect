import asyncio
import random
from bleak import BleakScanner,BleakClient,BleakError
from FurbyMoods import MoodActions,MoodTypes
import logging
from FurbyClass import Furby

logging.basicConfig(filename="Furby.log",filemode="w",level=logging.DEBUG)
log=logging.getLogger("Furby")
log.info("Starting Furby scanner")

debug=True # always send the same command


debug_command=[39,2,3,3] #"let's give little guy a hand"
debug_mood=0


directCommands=[
[71, 0, 0, 0],	# "Do" ,
[71, 0, 0, 1],	# "Re" ,
[71, 0, 0, 2],	# "Mi" ,
[71, 0, 0, 3],	# "Fa" ,
[71, 0, 0, 4],	# "Sol" ,
[71, 0, 0, 5],	# "La" ,
[71, 0, 0, 6],	# "Ti" ,
[71, 0, 0, 7],	# "Do" ,
]

antenna_colours=[
	[255,0,0],
	[0,255,0],
	[0,0,255],
	[255,255,0],
	[0,255,255],
	[255,0,255],
	[255,255,0],
	[255,255,255]
	]

# used to terminate co-routines

stop_event = asyncio.Event()
running=True # terminates all coroutines if False


furbies={}  # clients by address
ignore={}	# other BLE devices to ignore

# since python 3.6 keys are maintained in order of insertion
# so we can do this_colour=antenna_colours.keys()[index] to select
# a colour name


async def stopper():
	# sets the running flag False to terminate everything
	global running,debug,log
	if debug:
		print("stopper is running")
	try:
		while running:
			await asyncio.sleep(1)
	except BleakError as e:
		msg=f"STOPPER BleakError EXCEPTION {e}"
		print(msg)
		log.exception(e)
		running=False

	except Exception as e:
		msg=f"STOPPER EXCEPTION {e}"
		print(msg)
		log.exception(e)
		running=False

async def callback(dev,data):
	global furbies,log
	if dev.address in ignore:
		return
	name=dev.name or "noname"
	#print(f"Callback got {name} @ {dev.address}")
	if name.startswith("Furby"):
		if dev.address not in furbies:
			print(f"Found a new Furby '{dev.name}' @ {dev.address}")
			furbies[dev.address] = Furby(dev)  # a paired client
			await furbies[dev.address].connect()  # cannot be done in __init__
	else:
		ignore[dev.address] = True

async def scanner():
	global running,debug,furbies,log
	if debug:
		print("scanner is running")

	this_scanner=BleakScanner(callback)

	while running:
		try:
			await this_scanner.start()
			await asyncio.sleep(5)
			await this_scanner.stop()

			if running:
				await asyncio.sleep(5)

		except BleakError as e:
			msg=f"SCANNER BLEAKERROR {e}"
			print(msg)
		except Exception as e:
			print("EXCEPTION {e}")

async def messenger():
	# sends messages to discovered furbies
	global running,debug,furbies

	if debug:
		print("messenger is running")

	step_idx=0 # there are 8 notes and 8 colours
	antenna_idx=0

	while running:
		if len(furbies)>0:

			# send a random message to each furby

			for this_furby in furbies:
				# note furbies[this_furby] is a BleakClient

				if furbies[this_furby].is_connected:
					try:
						await furbies[this_furby].send_command(directCommands[step_idx])
						if step_idx==0:
							await furbies[this_furby].set_antenna_colour(antenna_colours[antenna_idx])
							antenna_idx=(antenna_idx+1) % len(antenna_colours)

					except BleakError as e:
						log.exception(f"BlearError in messenger {e}")
					except Exception as e:
						# oddly this sometimes is is null
						print(f"MESSENGER EXCEPTION : >{e}<")
						log.exception(f"messenger exception {e}")

						# service discovery is performed during the connection phase
						# I have observed some lag despite awaiting the connect()
						if e == "Service Discovery has not been performed yet":
							print("Waiting for service discovery on ",furbies[this_furby].address)
						else:
							running=False # stop everything to investigate

			step_idx=(step_idx+1)%len(directCommands)

		await asyncio.sleep(.001)

	# loop has finished - tidy up
	# furbies tend to hang on to connections if not closed
	for this_furby in furbies:
		await furbies[this_furby].disconnect()

async def main():
	# run these co-routines concurrently
	await asyncio.gather(stopper(),messenger(),scanner())

	print("Main finished")

if __name__ == "__main__":
	try:
		asyncio.run(main())
		print("asyncio.run finished")

	except KeyboardInterrupt:
		print("\nInterrupted by user.")
	except Exception as e:
		print(f"MAIN EXCEPTION {e}")
		log.exception("main exception {e}")
