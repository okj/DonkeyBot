import discord
from discord.ext import tasks, commands
from .Server import Server

from tinydb import TinyDB, where
from tinydb.operations import set

import datetime
from datetime import date
from random import seed
from random import choice
import time

class FunCog(commands.Cog, Server):

    def __init__(self, client):
        self.client = client
        self.events = TinyDB('database/events.json')
        self.users = TinyDB('database/users.json')

        Server.__init__(self)

        self.noon = datetime.datetime.now().replace(hour=12, minute=0, second=0, microsecond=0)

        lastCoolGuy = self.events.get(where('name') == 'coolguy')['last']
        self.lastCoolGuy = datetime.datetime.strptime(lastCoolGuy.replace("-",""), "%Y%m%d").date()

        self.activeUsers = self.events.get(where('name') == 'coolguy')['activeUsers']

        self.CheckBirthday.start()
    
    @tasks.loop(hours=24)
    async def CheckBirthday(self):

        userBirthdays = self.users.search(where('birthday').exists())

        for user in userBirthdays:
            if (user['birthday'] == str(datetime.datetime.now().date())):
                general = self.client.get_guild(self.server).get_channel(self.generalChannel)
                await general.send("**Happy Birthday <@" + str(user['id']) + ">!** :birthday: :tada:")

    @commands.Cog.listener()
    async def on_message(self, message):

        #Temp remove messages with content in drawing arena
        if (message.channel.id == 750753280694550539 and message.content != ""):
            await message.delete()
        
        member = message.author

        #Add non-staff to list of active users
        if (not member.bot and (str(member.id) not in self.activeUsers and not member.guild_permissions.manage_messages)):
            self.activeUsers.append(str(member.id))
            self.events.update(set('activeUsers', self.activeUsers), where('name') == 'coolguy')

        #Cool guy raffle once a day
        now = datetime.datetime.now()
        if (now > self.noon and (date.today() > self.lastCoolGuy)):

            #Set date
            self.lastCoolGuy = date.today()
            self.events.update(set('last', str(self.lastCoolGuy)), where('name') == 'coolguy')

            coolGuyRole = message.guild.get_role(self.coolGuyRole)

            #Remove last cool guy(s)
            coolGuys = [] if coolGuyRole.members is None else coolGuyRole.members
            for coolGuy in coolGuys:
                await coolGuy.remove_roles(coolGuyRole)

            #New cool guys
            found = False
            while (not found):
                selection = choice(self.activeUsers)
                if message.guild.get_member(int(selection)) != None:
                    found = True
            winner = message.guild.get_member(int(selection))
            await winner.add_roles(coolGuyRole)

            found = False
            while (not found):
                selection = choice(message.guild.members)
                if (selection != winner):
                    await selection.add_roles(coolGuyRole)
                    found = True
            
            general = message.guild.get_channel(self.generalChannel)
            await general.send(winner.mention + " and " + selection.mention + " won the cool guy raffle! ")

            #Reset active users
            self.activeUsers = []
            self.events.update(set('activeUsers', self.activeUsers), where('name') == 'coolguy')

def setup(client):
    client.add_cog(FunCog(client))