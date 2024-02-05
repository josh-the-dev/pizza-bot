import twitchio
import os
from dotenv import load_dotenv

load_dotenv()


class MyBot(twitchio.Client):
    def __init__(self, token, channel):
        super().__init__(token=token, initial_channels=[channel])
        self.channel = channel
        self.raffle_queue = []
        self.arena_queue = []

    async def event_message(self, message):
        # Check if the message is a command
        if message.content.startswith('!add'):
            user = message.author.name
            self.queue.append(user)
            await message.channel.send(f'{user} has been added to the queue.')

        elif message.content.startswith('!remove'):
            user = message.author.name
            if user in self.queue:
                self.queue.remove(user)
                await message.channel.send(f'{user} has been removed from the queue.')
            else:
                await message.channel.send(f'{user}, you are not in the queue.')


# Replace these with your bot's credentials
bot_token = os.getenv('TWITCH_BOT_TOKEN')
channel_name = os.getenv('TWITCH_CHANNEL_NAME')

bot = MyBot(bot_token, channel_name)
bot.run()
