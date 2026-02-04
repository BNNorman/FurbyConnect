import asyncio
import random
from FurbyCommands import directCommands
from bleak import BleakScanner,BleakClient,BleakError
from FurbyMoods import MoodActions,MoodTypes
import logging

logging.basicConfig(filename="Furby.log",filemode="w",level=logging.DEBUG)
log=logging.getLogger("Furby")
log.info("Starting Furby scanner")

debug=True # always send the same command
debug_msgs=False

debug_command=[39,2,3,3] #"let's give little guy a hand"
debug_mood=0

# characteristic used to send commands
command_characteristic = "dab91383-b5a1-e29c-b041-bcd562613bde"

# used to terminate co-routines

stop_event = asyncio.Event()
running=True # terminates all coroutines if False

class Furby(BleakClient):

	def __init__(self,device,characteristic=command_characteristic):
		self.device=device
		super().__init__(device,pair=True)

		# characteristic to use for talking to the Furby
		self.characteristic=characteristic

	def __del__(self):
		# cannot use await here
		if self.is_connected:
			asyncio.ensure_future(self.disconnect())

	async def check_is_connected(self):
		global debug,log
		if not self.is_connected:

			if debug:
				msg=f"{self.address} is not connected, trying now."
				print(msg)
				log.error("msg")
			await self.connect()

	def check_services_discovered(self):
		if not self.services:
			msg=f"Service Discovery has not been performed yet for {self.address}."
			print(msg)
			log.error(msg)
			return False
		return True

	async def send_msg(self,msg:bytearray):
		global debug
		if debug_msgs:
			print(f"sending {msg} to {self.address}")

		await self.check_is_connected()
		if not self.check_services_discovered():
			return
		await self.write_gatt_char(self.characteristic,msg,response=False)

	async def set_antenna_colour(self,rgb:list):
		cmd = bytearray([0x14]+rgb)
		await self.send_msg(cmd)

	async def send_command(self,command:list):
		cmd = bytearray([0x13,0x00]+command)
		await self.send_msg(cmd)

	async def set_mood(self,mood_type:int,value:int):
		# set the mood value and starting value
		# mood_params [action,type,value]
		cmd=bytearray([0x24,0x1,mood_type,value])
		await self.send_msg(cmd)

	async def change_mood(self,mood_type: int, value: int):
		# increase mood value
		# mood_params [action,type,value]
		cmd = bytearray([0x24, 0x00, mood_type, value])
		await self.send_msg(cmd)

furbies={}  # clients by address
ignore={}	# other BLE devices to ignore

# since python 3.6 keys are maintained in order of insertion
# so we can do this_colour=antenna_colours.keys()[index] to select
# a colour name
antenna_colours={
	"red":[255,0,0],
	"green":[0,255,0],
	"blue":[0,0,255],
}

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

	next_antenna_colour_index=0

	while running:
		if len(furbies)>0:

			if debug:
				print("Sending a debug message to each Furby")

			# send a random message to each furby

			for this_furby in furbies:
				# note furbies[this_furby] is a BleakClient

				if debug:
					print(f"Sending a debug message to {furbies[this_furby].address}")

				if furbies[this_furby].is_connected:
					if debug:
						msg=f"messenger furby {furbies[this_furby].address} is connected"
						print(msg)
						log.debug(msg)
					try:
						# select a random or debug message
						if not debug:
							msg_num = random.randint(0, len(directCommands))
							msg = directCommands[msg_num]
						else:
							# send a fixed command so we can tell if it is obeyed
							# this results in furby repeating the command intermingled with
							# random stuff
							msg = debug_command

						await furbies[this_furby].send_command(msg)

						# set antenna colour (Cycles though all the colours)
						colour_name=list(antenna_colours.keys())[next_antenna_colour_index]
						await furbies[this_furby].set_antenna_colour(antenna_colours[colour_name])

						# set Furby Mood
						if not debug:
							mood_type=MoodTypes[random.randint(0,4)]
						else:
							mood_type=MoodTypes.excited
						# I'm guessing what the value is (range 0..255)?
						await furbies[this_furby].set_mood(mood_type,128)

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


		# select the next antenna colour
		next_antenna_colour_index+= 1
		next_antenna_colour_index = next_antenna_colour_index % len(antenna_colours.keys())
		await asyncio.sleep(.5)

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
