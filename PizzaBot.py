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
        self.arena_entrants = ["itsWiiland"]
        self.is_raffle_open = False
        self.win_streak = 0

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

    def check_is_channel_owner_by_message(self, message):
        user = message.author.name.lower()
        return user == message.channel.name.lower()

    def check_is_channel_owner_by_name(self, name):
        return name == os.getenv('TWITCH_CHANNEL_NAME')

    def check_user_privilege(self, message):
        user = message.author.name.lower()
        is_moderator = 'moderator' in message.author._tags.get('badges', '')
        # Check if the message sender is the channel owner
        is_channel_owner = self.check_is_channel_owner_by_message(message)
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
        is_privileged_user = self.check_user_privilege(ctx.message)
        if not is_privileged_user:
            return
        if self.is_raffle_open:
            await ctx.send(f'The raffle is not closed yet!')
            return
        if len(self.raffle_queue) == 0:
            await ctx.send(f'The raffle is empty!')
            return
        if len(self.arena_rotation) == 6:
            await ctx.send(f'The arena is full!')
            return
        random_user = random.choice(self.raffle_queue)
        self.arena_rotation.append(random_user)
        
        if len(self.arena_entrants) == 4:
            self.raffle_queue.remove(random_user)
            await ctx.send(f'{random_user} has been selected!')
            return
        
        self.arena_entrants.append(random_user)
        self.raffle_queue.remove(random_user)
        await ctx.send(f'{random_user} has been selected!')

    @commands.command()
    async def add(self, ctx: commands.Context):
        is_privileged_user = self.check_user_privilege(ctx.message)
        if not is_privileged_user:
            return
        split_message = ctx.message.content.split()
        user_to_add = split_message[1]

        if user_to_add in self.arena_rotation:
            await ctx.send(f'{user_to_add} is already in the arena!')
            return
        if len(self.arena_rotation) == 6:
            await ctx.send('The arena is already at 6 people!')
            return
        self.arena_rotation.append(user_to_add)
        await ctx.send(f'{user_to_add} added to the arena!')

    @commands.command()
    async def remove(self, ctx: commands.Context):
        is_privileged_user = self.check_user_privilege(ctx.message)
        if not is_privileged_user:
            return
        split_message = ctx.message.content.split()
        user_to_remove = split_message[1]

        if user_to_remove not in self.arena_rotation:
            await ctx.send(f'{user_to_remove} is not in the arena!')
            return
        if user_to_remove is self.arena_rotation[0]:
            self.win_streak = 0
        self.arena_rotation.remove(user_to_remove)
        await ctx.send(f'{user_to_remove} removed from the arena!')

    @commands.command()
    async def win(self, ctx: commands.Context):
        is_privileged_user = self.check_user_privilege(ctx.message)

        if not is_privileged_user:
            return

        winning_user = self.arena_rotation[0]
        losing_user = self.arena_rotation[1]
       
        self.win_streak += 1

        is_losing_user_channel_owner = self.check_is_channel_owner_by_name(
            losing_user)
        
        # If arena rotation is 5 people or more, invite the 5th person to the arena entrants list
    
        if len(self.arena_rotation) >= 5:
            if is_losing_user_channel_owner:
                # Move losing user to back of arena rotation
                self.arena_rotation.append(self.arena_rotation.pop(1))
                print(self.arena_entrants)
            else:
                # Check if channel owner is in position 5 or 6 in the arena rotation
                # If so add the 4th person in the arena rotation to the arena entrants
                # And move the channel owner to the back of the arena rotation

                user_to_invite = self.arena_rotation[4] 
                if self.check_is_channel_owner_by_name(self.arena_rotation[4]) or self.check_is_channel_owner_by_name(self.arena_rotation[5]):
                    user_to_invite = self.arena_rotation[3]

                print(user_to_invite)
                await ctx.send(f'@{losing_user} please leave the arena!')
                await ctx.send(f'@{user_to_invite} please join the arena!')

                # Remove the losing user from the arena entrants
                self.arena_entrants.remove(losing_user)

                # Add the user to the arena rotation
                self.arena_entrants.append(user_to_invite)

                # Move the losing user to the back of the arena rotation
                self.arena_rotation.append(self.arena_rotation.pop(1))

                print(self.arena_entrants)
                print(self.arena_rotation)

          
            if self.win_streak == 3:
                is_winning_user_channel_owner = self.check_is_channel_owner_by_name(
                    winning_user)
                
                if is_winning_user_channel_owner:
                    self.arena_rotation.append(self.arena_rotation.pop(0))
                    await ctx.send(f'@{winning_user} has a win streak of 3! Back of the queue you go !')
                    print(self.arena_entrants)
                else:
                    self.arena_entrants.remove(winning_user)
                    user_to_invite = self.arena_rotation[4] 
                    if self.check_is_channel_owner_by_name(self.arena_rotation[4]) or self.check_is_channel_owner_by_name(self.arena_rotation[5]):
                        user_to_invite = self.arena_rotation[3]
                    self.arena_rotation.append(self.arena_rotation.pop(0))
            
                    self.arena_entrants.append(user_to_invite)
                    await ctx.send(f'@{winning_user} has a win streak of 3! Please leave the arena!')
                    await ctx.send(f'@{user_to_invite} please join the arena!')
                self.win_streak = 0

    @commands.command()
    async def lose(self, ctx: commands.Context):
        is_privileged_user = self.check_user_privilege(ctx.message)

        if not is_privileged_user:
            return

        losing_user = self.arena_rotation[0]

        # Remove the losing user from the arena entrants
        

        if len(self.arena_rotation) >= 5:
            is_losing_user_channel_owner = self.check_is_channel_owner_by_name(
                losing_user)
            if not is_losing_user_channel_owner:
                self.arena_entrants.remove(losing_user)
                user_to_invite = self.arena_rotation[4]
                self.arena_entrants.append(user_to_invite)
                await ctx.send(f'@{user_to_invite} please join the arena!')
                await ctx.send(f'@{losing_user} please leave the arena!')
            else:
                await ctx.send(f'@{losing_user} go to the back of the queue!')

            self.arena_rotation.append(self.arena_rotation.pop(0))
        self.win_streak = 1

        print(self.arena_entrants)
        print(self.arena_rotation)

    @commands.command()
    async def list(self, ctx: commands.Context):
        await ctx.send(f'The arena list is the following: {", ".join(self.arena_rotation)}')

    @commands.command()
    async def raffle(self, ctx: commands.Context):
        await ctx.send(f'The raffle list is the following: {", ".join(self.raffle_queue)}')


bot = Bot()
bot.run()
