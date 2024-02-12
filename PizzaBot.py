import os
import random
from twitchio.ext import commands
from dotenv import load_dotenv

load_dotenv('.env.local')


class Bot(commands.Bot):

    def __init__(self):
        super().__init__(token=os.getenv('TWITCH_TOKEN'),
                         prefix='!', initial_channels=[os.getenv('TWITCH_CHANNEL_NAME')])

        self.raffle_queue = []
        self.arena_rotation = ["itsWiiland"]
        self.is_raffle_open = False

    async def event_ready(self):
        print(f'Logged in as | {self.nick}')
        print(f'User id is | {self.user_id}')

    async def event_message(self, message):
        # Messages with echo set to True are messages sent by the bot
        if message.echo:
            return

        print(message.content)

        # Since we have commands and are overriding the default `event_message`
        # We must let the bot know we want to handle and invoke our commands...
        await self.handle_commands(message)

    def check_user_privilege(self, message):
        user = message.author.name.lower()
        is_moderator = 'moderator' in message.author._tags.get('badges', '')
        # Check if the message sender is the channel owner
        is_channel_owner = user == message.channel.name.lower()
        is_privileged_user = is_moderator or is_channel_owner
        return is_privileged_user

    @commands.command()
    async def open(self, ctx: commands.Context):
        is_privileged_user = self.check_user_privilege(ctx.message)

        if is_privileged_user and not self.is_raffle_open:
            self.is_raffle_open = True
            await ctx.send(f'The raffle is now open!')
        elif not is_privileged_user:
            await ctx.send(f'Sorry you cannot do that!')
        else:
            await ctx.send(f'The raffle is already open!')

    @commands.command()
    async def close(self, ctx: commands.Context):
        is_privileged_user = self.check_user_privilege(ctx.message)

        if is_privileged_user and self.is_raffle_open:
            self.is_raffle_open = False
            await ctx.send(f'The raffle is now closed!')
        elif not is_privileged_user:
            await ctx.send(f'Sorry you cannot do that!')
        else:
            await ctx.send(f'The raffle is already closed!')

    @commands.command()
    async def join(self, ctx: commands.Context):
        user = ctx.author.name

        if not self.is_raffle_open:
            await ctx.send(f'The raffle is not open {user}!')
            return

        elif user in self.raffle_queue:
            await ctx.send(f'{ctx.author.name} is already in the raffle')
            return

        self.raffle_queue.append(user)
        await ctx.send(f'{ctx.author.name} is added to the raffle!')

    @commands.command()
    async def pick(self, ctx: commands.Context):

        if not self.is_raffle_open:
            await ctx.send(f'The raffle is not open!')
            return
        if len(self.raffle_queue) == 0:
            await ctx.send(f'The raffle is empty!')
            return

        random_user = random.choice(self.raffle_queue)
        self.arena_rotation.append(random_user)
        self.raffle_queue.remove(random_user)
        await ctx.send(f'{random_user} has been selected!')


bot = Bot()
bot.run()
