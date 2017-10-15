import discord
import asyncio

import sys, os, pickle
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--token", help="clients Discord token")
args = parser.parse_args()

token = args.token
DELAY = 900 #15 minutes

# Set CWD to script directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

class Bot(discord.Client):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.loop.create_task(self.get_discrims())

    async def get_discrims(self):
        await asyncio.sleep(10)
        print('Creating Discrim List...')
        while True:
            try:
                discrims = {}
                count = 0
                
                for user in self.get_all_members():
                    if user.discriminator in discrims and user.name not in discrims[user.discriminator]:
                        discrims[user.discriminator].append(user.name)
                    else:
                        discrims[user.discriminator] = [user.name]
                    count = count + 1
                    
                print(f'Processed {count} members from guilds.')

                for i in range(1,10000):
                    i_str = "{:04}".format(i)
                    if i_str not in discrims:
                        print(f"We are missing a user for discrim {i_str}")
                
                # Save our dict to binary file
                with open('discrims.pkl', 'wb') as f:
                    pickle.dump(discrims, f, pickle.HIGHEST_PROTOCOL)
                
            except Exception as e: 
                print('Failed! Exception Occured.')
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(exc_type, fname, exc_tb.tb_lineno)
                return
            
            await asyncio.sleep(DELAY)


bot = Bot()
bot.run(token, bot=False)