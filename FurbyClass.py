from bleak import BleakScanner,BleakClient,BleakError
import asyncio
import logging

debug_msgs=False

log=logging.getLogger("Furby") # basic config setup by user

# characteristic used to send commands and read responses
write_characteristic = "dab91383-b5a1-e29c-b041-bcd562613bde"
read_characteristic = "dab91382-b5a1-e29c-b041-bcd562613bde"

class Furby(BleakClient):

	def __init__(self,device,writeChar=write_characteristic,readChar=read_characteristic):
		self.device=device
		super().__init__(device,pair=True)

		# characteristic to use for talking to the Furby
		self.write_characteristic = writeChar
		self.read_characteristic = readChar

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
		try:
			if self.services.services:
				return True
		except:
			msg = f"Service Discovery has not been performed yet for {self.address}."
			print(msg)
			log.error(msg)
			return False

	async def send_msg(self,msg:bytearray):
		global debug_msgs

		if debug_msgs:
			print(f"sending {msg} to {self.address}")

		await self.check_is_connected()
		if not self.check_services_discovered():
			return
		await self.write_gatt_char(self.write_characteristic,msg,response=False)

	async def read_response(self):
		global log
		x=await self.read_gatt_char(self.read_characteristic)
		print("Read=",x)
		log.debug(f"Read response {x}")


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