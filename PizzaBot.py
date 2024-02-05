import twitchio


class MyBot(twitchio.Client):
    def __init__(self, username, token, channel):
        super().__init__(username=username,
                         token=token, initial_channels=[channel])
        self.queue = []

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
bot_username = 'your_bot_username'
bot_token = 'your_bot_oauth_token'
channel_name = 'your_channel_name'

bot = MyBot(bot_username, bot_token, channel_name)
bot.run()
