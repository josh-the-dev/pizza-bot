import os
import random
import lib.winner_repository as winner_repository
from datetime import datetime, time
from collections import Counter
from twitchio.ext import commands
from dotenv import load_dotenv

load_dotenv('.env.local')


class Bot(commands.Bot):

    def __init__(self):
        super().__init__(token=os.getenv('TWITCH_TOKEN'),
                         prefix='!', initial_channels=[os.getenv('TWITCH_CHANNEL_NAME')])

        self.raffle_queue = []
        self.arena_queue = []
        self.arena_rotation = ["itsWiiland"]
        self.arena_entrants = ["itsWiiland"]
        self.is_raffle_open = False
        self.win_streak = 0
        self.scoreboard = {"itsWiiland": 0}

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

    def add_to_arena(self, user):
        if len(self.arena_rotation) == 4:
            self.arena_queue.append(user)
        else:
            self.arena_rotation.append(user)
            self.add_to_scoreboard(user)

    def add_to_scoreboard(self, user):
        if user not in self.scoreboard:
            self.scoreboard[user] = 0

    def is_first(self, winning_user):
        highest_score = self.get_highest_score_without_winner(winning_user)
        return highest_score <= self.scoreboard[winning_user]

    def get_highest_score_without_winner(self, winning_user):
        scoreboard_minus_winner = self.get_scoreboard_minus_winner(winning_user)
        return max(scoreboard_minus_winner.values())

    def get_scoreboard_minus_winner(self, winning_user):
        scoreboard_minus_winner = dict(self.scoreboard)
        scoreboard_minus_winner.pop(winning_user, None)
        return scoreboard_minus_winner

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
    async def status(self, ctx: commands.Context):
        user = ctx.author.name
        if self.is_raffle_open:
            await ctx.send(f'The raffle is open {user}!')
        else:
            await ctx.send(f'The raffle is not open {user}!')

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
        if len(self.arena_rotation) == 4 and len(self.arena_queue) == 2:
            await ctx.send(f'The arena is full!')
            return

        random_user = random.choice(self.raffle_queue)

        self.add_to_arena(random_user)
        self.raffle_queue.remove(random_user)
        await ctx.send(f'{random_user} has been selected!')

    @commands.command()
    async def add(self, ctx: commands.Context):
        is_privileged_user = self.check_user_privilege(ctx.message)
        if not is_privileged_user:
            return
        split_message = ctx.message.content.split()
        user_to_add = split_message[1]

        if user_to_add in self.arena_rotation or user_to_add in self.arena_queue:
            await ctx.send(f'{user_to_add} is already in the arena!')
            return
        if len(self.arena_rotation) == 4 and len(self.arena_queue) == 2:
            await ctx.send(f'The arena is full!')
            return

        self.add_to_arena(user_to_add)
        await ctx.send(f'{user_to_add} added to the arena!')

    @commands.command()
    async def remove(self, ctx: commands.Context):
        is_privileged_user = self.check_user_privilege(ctx.message)
        if not is_privileged_user:
            return
        split_message = ctx.message.content.split()
        user_to_remove = split_message[1]

        if user_to_remove not in self.arena_rotation or user_to_remove not in self.arena_queue:
            await ctx.send(f'{user_to_remove} is not in the arena!')
            return
        if user_to_remove is self.arena_rotation[0]:
            self.win_streak = 0
        if user_to_remove in self.arena_queue:
            self.arena_queue.remove(user_to_remove)
        else:
            # in arena rotation, so we have to bump people up.
            self.arena_rotation.remove(user_to_remove)
            if len(self.arena_queue) > 0:
                user_to_invite = self.arena_queue.pop(0)
                self.arena_rotation.append(user_to_invite)
                self.add_to_scoreboard(user_to_invite)

        await ctx.send(f'{user_to_remove} removed from the arena!')

    @commands.command()
    async def win(self, ctx: commands.Context):
        is_privileged_user = self.check_user_privilege(ctx.message)

        if not is_privileged_user:
            return

        await self.win_points(ctx, 1)

    @commands.command()
    async def win3stock(self, ctx: commands.Context):
        is_privileged_user = self.check_user_privilege(ctx.message)

        if not is_privileged_user:
            return

        await self.win_points(ctx, 3)

    async def win_points(self, ctx: commands.Context, points: int):
        winning_user = self.arena_rotation[0]
        losing_user = self.arena_rotation[1]
        self.win_streak += 1

        if self.is_first(winning_user):
            points = 1

        self.scoreboard[winning_user] += points
        is_losing_user_channel_owner = self.check_is_channel_owner_by_name(
            losing_user)
        # If there are any people in the arena queue, we need to move them to the arena rotation
        # And the loser moves to the arena queue and removed from the arena rotation
        # If the loser is the channel owner, they move to the back of the arena rotation
        if is_losing_user_channel_owner:
            self.arena_rotation.append(self.arena_rotation.pop(1))
            print(self.arena_rotation)

        else:
            if len(self.arena_queue) > 0:
                user_to_invite = self.arena_queue.pop(0)
                self.arena_rotation.remove(losing_user)
                self.arena_rotation.append(user_to_invite)
                self.arena_queue.append(losing_user)
                self.add_to_scoreboard(user_to_invite)
                await ctx.send(f'@{user_to_invite} please join the arena!')
                await ctx.send(f'@{losing_user} please leave the arena!')
                print(self.arena_rotation)
            else:
                self.arena_rotation.append(self.arena_rotation.pop(1))
                print(self.arena_rotation)
        if self.win_streak == 3:
            is_winning_user_channel_owner = self.check_is_channel_owner_by_name(
                winning_user)

            if is_winning_user_channel_owner:
                self.arena_rotation.append(self.arena_rotation.pop(0))
                await ctx.send(f'@{winning_user} has a win streak of 3! Back of the queue you go !')
                print(self.arena_rotation)
            else:
                if len(self.arena_queue) > 0:
                    user_to_invite = self.arena_queue.pop(0)
                    self.arena_rotation.append(user_to_invite)
                    self.arena_rotation.remove(winning_user)
                    self.arena_queue.append(winning_user)
                    await ctx.send(f'@{winning_user} has a win streak of 3! Please leave the arena!')
                    await ctx.send(f'@{user_to_invite} please join the arena!')
                    print(self.arena_rotation)
                else:
                    self.arena_rotation.append(self.arena_rotation.pop(0))
                    print(self.arena_rotation)

            self.win_streak = 0

    @commands.command()
    async def lose(self, ctx: commands.Context):
        is_privileged_user = self.check_user_privilege(ctx.message)

        if not is_privileged_user:
            return

        await self.lose_points(ctx, 1)

    @commands.command()
    async def lose3stock(self, ctx: commands.Context):
        is_privileged_user = self.check_user_privilege(ctx.message)

        if not is_privileged_user:
            return

        await self.lose_points(ctx, 3)

    async def lose_points(self, ctx, points: int):
        losing_user = self.arena_rotation[0]
        winning_user = self.arena_rotation[1]

        if self.is_first(winning_user):
            points = 1

        # Remove the losing user from the arena entrants
        is_losing_user_channel_owner = self.check_is_channel_owner_by_name(
            losing_user)
        if is_losing_user_channel_owner:
            self.arena_rotation.append(self.arena_rotation.pop(0))
            await ctx.send(f'@{losing_user} go to the back of the queue!')
            print(self.arena_rotation)
        else:
            if len(self.arena_queue) > 0:
                user_to_invite = self.arena_queue.pop(0)
                self.arena_rotation.remove(losing_user)
                self.arena_rotation.append(user_to_invite)
                self.arena_queue.append(losing_user)
                self.add_to_scoreboard(user_to_invite)
                await ctx.send(f'@{user_to_invite} please join the arena!')
                await ctx.send(f'@{losing_user} please leave the arena!')
                print(self.arena_rotation)
            else:
                self.arena_rotation.append(self.arena_rotation.pop(0))
                print(self.arena_rotation)
        self.win_streak = 1
        self.scoreboard[winning_user] += points

    @commands.command()
    async def list(self, ctx: commands.Context):
        await ctx.send(f'The arena list is the following: {", ".join(self.arena_rotation)}')
        await ctx.send(f'The people outside the arena are: {", ".join(self.arena_queue)}')

    @commands.command()
    async def raffle(self, ctx: commands.Context):
        await ctx.send(f'The raffle list is the following: {", ".join(self.raffle_queue)}')

    @commands.command()
    async def scoreboard(self, ctx: commands.Context):
        scores = [f'{key}: {value}' for key, value in
                  {k: v for k, v in sorted(self.scoreboard.items(), key=lambda item: item[1], reverse=True)}.items()]
        await ctx.send(f'The score is the following: {", ".join(scores)}')

    @commands.command()
    async def winner(self, ctx: commands.Context):
        is_privileged_user = self.check_user_privilege(ctx.message)
        if not is_privileged_user:
            return
        split_message = ctx.message.content.split()
        winner = split_message[1]

        winner_repository.save(dict(name=winner, date=datetime.combine(datetime.now(), time.min)))
        await ctx.send(f'{winner} wins today\'s Pizza Stream!')

    @commands.command()
    async def winners(self, ctx: commands.Context):
        winners = winner_repository.find_all()
        winner_names = list(map(lambda x: x['name'], winners))
        winner_by_wins = Counter(winner_names)
        scores = [f'{key}: {value}x' for key, value in
                  {k: v for k, v in sorted(winner_by_wins.items(), key=lambda item: item[1], reverse=True)}.items()]
        await ctx.send(f'The pizza stream winners are the following: {", ".join(scores)}')


bot = Bot()
bot.run()
