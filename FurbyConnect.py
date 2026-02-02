import asyncio
import random
from FurbyCommands import directCommands
from bleak import BleakScanner,BleakClient
from Moods import MoodActions,MoodTypes

debug=True # always send the same command
debug_command=[39,2,3,3] #"let's give little guy a hand"

# characteristic used to send commands
command_characteristic = "dab91383-b5a1-e29c-b041-bcd562613bde"


class Furby(BleakClient):

	def __init__(self,device,characteristic=command_characteristic):
		self.device=device
		super().__init__(device,pair=True)

		self.characteristic=characteristic

		# does this work?
		#asyncio.ensure_future(self.connect())

	def __del__(self):
		# cannot use await here
		if self.is_connected:
			asyncio.ensure_future(self.disconnect())

	async def check_is_connected(self):
		if not self.is_connected:
			print(f"{self.device.address} is not connected, trying now.")
			await self.connect()

	async def send_msg(self,msg:bytearray):
		print(f"sending {msg} to {self.address}")
		await self.check_is_connected()
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

furbies={} # clients by address

# since python 3.6 keys are maintained in order of insertion
# so we can do this_colour=antenna_colours.keys()[index] to select
# a colour name
antenna_colours={
	"red":[255,0,0],
	"green":[0,255,0],
	"blue":[0,0,255],
}


lenCommands=len(directCommands)

#stop_event = asyncio.Event()

async def main():
	print("main")

	next_antenna_colour_index=0

	while True:
		print("Scanning")
		devices=await BleakScanner.discover()

		for dev in devices:

			if dev.name is not None:
				if not dev.address in furbies and dev.name.startswith("Furby"):
					print(f"Found a Furby '{dev.name}' @ {dev.address}")
					furbies[dev.address] = Furby(dev) # a paired client
					await furbies[dev.address].connect() # cannot be done in __init__

		if len(furbies)>0:
			print("Send a random message to each Furby, if any have been discovered")
			# send a random message to each furby
			print(f"I found {len(furbies)} furbies")
			for furby in furbies:
				try:
					if not debug:
						msg_num = random.randint(0, lenCommands)
						msg = directCommands[msg_num]
					else:
						# send a fixed command so we can tell if it is obeyed
						# this results in furby repeating the command intermingled with
						# random stuff
						msg = debug_command

					await furbies[furby].send_command(msg)

					colour_name=list(antenna_colours.keys())[next_antenna_colour_index]

					# set Furby Mood
					mood_type=MoodTypes.excited
					await furbies[furby].set_mood(mood_type,50)


				except Exception as e:
					print(f"EXCEPTION : >{e}<")

		# select the next antenna colour
		next_antenna_colour_index+= 1
		next_antenna_colour_index = next_antenna_colour_index % len(antenna_colours.keys())

		#if len(furbies)<=2:
		#	await asyncio.sleep(5) # may not be needed with multiple furbies

if __name__ == "__main__":
	try:
		asyncio.run(main())
		print("asyncio.run finished")

	except KeyboardInterrupt:
		print("\nScan interrupted by user.")
