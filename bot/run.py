import democracy
import discord
import importlib

def run():
	"""
		Due to a potential failure of the discrod library, we often have to restart it for the bot to function.
		That is the sole purpose of this program, to restart the bot whenever there is an exception caused by
		discord. It has worked so far, but it would be better to investigate what is causing the bug. More 
		details are avaiable in "democracy.py" TODO name the function that has more details.
	"""

	while True:

		try:

			print("Restarting")
			
			importlib.reload(discord)
			importlib.reload(democracy)
			
			democracy.Democracybot.initialize()
		
		except KeyboardInterrupt as e:

			return

		except Exception as e:  # TODO limit error handling to only Discord related exceptions. Which implies finding and recording the exact exception. Consider logging them outside fo "nohup" to make them clearer.

			print("Exception caught")
			print(type(e))
			print(e)

if __name__ == '__main__':

	run()

