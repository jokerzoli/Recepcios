import discord
import math
import asyncio
import aiohttp
import json
import datetime
from discord.ext import commands
import traceback
import sqlite3
from urllib.parse import quote
from discord.ext.commands.cooldowns import BucketType
from time import gmtime, strftime


class voice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        conn = sqlite3.connect('voice.db')
        c = conn.cursor()
        guildID = member.guild.id
        c.execute("SELECT voiceChannelID FROM guild WHERE guildID = ?", (guildID,))
        voice=c.fetchone()
        if voice is None:
            pass
        else:
            voiceID = voice[0]
            try:
                if after.channel.id == voiceID:
                    c.execute("SELECT * FROM voiceChannel WHERE userID = ?", (member.id,))
                    cooldown=c.fetchone()
                    if cooldown is None:
                        pass
                    else:
                        await member.send("Túl gyorsan készítettél csatornákat, várj 15 másodpercet és próbáld újra!")
                        await asyncio.sleep(15)
                    c.execute("SELECT voiceCategoryID FROM guild WHERE guildID = ?", (guildID,))
                    voice=c.fetchone()
                    c.execute("SELECT channelName, channelLimit FROM userSettings WHERE userID = ?", (member.id,))
                    setting=c.fetchone()
                    c.execute("SELECT channelLimit FROM guildSettings WHERE guildID = ?", (guildID,))
                    guildSetting=c.fetchone()
                    if setting is None:
                        name = f"{member.name} csatornája"
                        if guildSetting is None:
                            limit = 0
                        else:
                            limit = guildSetting[0]
                    else:
                        if guildSetting is None:
                            name = setting[0]
                            limit = setting[1]
                        elif guildSetting is not None and setting[1] == 0:
                            name = setting[0]
                            limit = guildSetting[0]
                        else:
                            name = setting[0]
                            limit = setting[1]
                    categoryID = voice[0]
                    id = member.id
                    category = self.bot.get_channel(categoryID)
                    channel2 = await member.guild.create_voice_channel(name,category=category)
                    channelID = channel2.id
                    await member.move_to(channel2)
                    await channel2.set_permissions(self.bot.user, connect=True,read_messages=True)
                    await channel2.edit(name= name, user_limit = limit)
                    c.execute("INSERT INTO voiceChannel VALUES (?, ?)", (id,channelID))
                    conn.commit()
                    def check(a,b,c):
                        return len(channel2.members) == 0
                    await self.bot.wait_for('voice_state_update', check=check)
                    await channel2.delete()
                    await asyncio.sleep(3)
                    c.execute('DELETE FROM voiceChannel WHERE userID=?', (id,))
            except:
                pass
        conn.commit()
        conn.close()

    @commands.command()
    async def help(self, ctx):
        embed = discord.Embed(title="Magyarázat", description="",color=0x7289da)
        embed.set_author(name="Recepciós", icon_url="https://www.portas.co.hu/Content/img/leppo-312-round.png")
        embed.add_field(name=f'**Parancsok**', value=f'**Zárolhatod a csatornádat hogy más ne tudjon belépni:**\n`.voice lock`\n------------\n'
                        f'**A zárolt csatornát a következő paranccsal tudod feloldani:**\n`.voice unlock`\n------------\n'
                        f'**Megváltoztathatod a csatornád nevét:**\n`.voice name <name>`\n**Például:** `.voice name EU 5kd+`\n------------\n'
                        f'**Megváltoztathatod a korlátozást:**\n`.voice limit number`\n**Például:** `.voice limit 2`\n------------\n'
                        f'**Feljogosíthadsz valakit hogy tudjon csatlakozni a zárt csatornádhoz:**\n`.voice permit @person`\n**Például:** `.voice permit @Zozoo`\n------------\n'
                        f'**Megadhatod hogy ki legyen a kezelője a csatornádat miután kilépsz:**\n`.voice claim`\n**Például:** `.voice claim`\n------------\n'
                        f'**Eltávolíthatsz embereket, vagy megvonhatod a beszéd jogait a csatornádon:**\n`.voice reject @person`\n**Például:** `.voice reject @Zozoo`\n', inline='false')
        embed.set_footer(text='Bot fejlesztője: Sam#9452 / Fordította Zozoo')
        await ctx.channel.send(embed=embed)

    @commands.group()
    async def voice(self, ctx):
        pass

    @voice.command()
    async def setup(self, ctx):
        conn = sqlite3.connect('voice.db')
        c = conn.cursor()
        guildID = ctx.guild.id
        id = ctx.author.id
        if ctx.author.id == ctx.guild.owner.id or ctx.author.id == 554362230838132736:
            def check(m):
                return m.author.id == ctx.author.id
            await ctx.channel.send("**60 másodperced van hogy válaszolj a kérdésekre!**")
            await ctx.channel.send(f"**Adj meg egy kategória nevet amiben szeretnéd hogy ezek a csatornák legyenek(Pl. Hang csatornák)**")
            try:
                category = await self.bot.wait_for('message', check=check, timeout = 60.0)
            except asyncio.TimeoutError:
                await ctx.channel.send('Túl későn válaszoltál!')
            else:
                new_cat = await ctx.guild.create_category_channel(category.content)
                await ctx.channel.send('**Adj meg egy hangcsatorna nevet: (Pl. Hozz létre saját hangcsatornát)**')
                try:
                    channel = await self.bot.wait_for('message', check=check, timeout = 60.0)
                except asyncio.TimeoutError:
                    await ctx.channel.send('Túl későn válaszoltál!')
                else:
                    try:
                        channel = await ctx.guild.create_voice_channel(channel.content, category=new_cat)
                        c.execute("SELECT * FROM guild WHERE guildID = ? AND ownerID=?", (guildID, id))
                        voice=c.fetchone()
                        if voice is None:
                            c.execute ("INSERT INTO guild VALUES (?, ?, ?, ?)",(guildID,id,channel.id,new_cat.id))
                        else:
                            c.execute ("UPDATE guild SET guildID = ?, ownerID = ?, voiceChannelID = ?, voiceCategoryID = ? WHERE guildID = ?",(guildID,id,channel.id,new_cat.id, guildID))
                        await ctx.channel.send("**Készen vagy a beállításokkal, használatra kész!**")
                    except:
                        await ctx.channel.send("Nem megfelelő nevet adtál meg.\nHasználd újra a `.voice setup` parancsot!")
        else:
            await ctx.channel.send(f"{ctx.author.mention} Csak a szerver tulajdonosa állíthatja be a Bot-ot!")
        conn.commit()
        conn.close()

    @commands.command()
    async def setlimit(self, ctx, num):
        conn = sqlite3.connect('voice.db')
        c = conn.cursor()
        if ctx.author.id == ctx.guild.owner.id or ctx.author.id == 554362230838132736:
            c.execute("SELECT * FROM guildSettings WHERE guildID = ?", (ctx.guild.id,))
            voice=c.fetchone()
            if voice is None:
                c.execute("INSERT INTO guildSettings VALUES (?, ?, ?)", (ctx.guild.id,f"{ctx.author.name} csatornája",num))
            else:
                c.execute("UPDATE guildSettings SET channelLimit = ? WHERE guildID = ?", (num, ctx.guild.id))
            await ctx.send("Sikeresen megváltoztattad az csatorna limit alapbeállításait a szervereden!")
        else:
            await ctx.channel.send(f"{ctx.author.mention} Csak a szerver tulajdonosa állíthatja be a Bot-ot!")
        conn.commit()
        conn.close()

    @setup.error
    async def info_error(self, ctx, error):
        print(error)

    @voice.command()
    async def lock(self, ctx):
        conn = sqlite3.connect('voice.db')
        c = conn.cursor()
        id = ctx.author.id
        c.execute("SELECT voiceID FROM voiceChannel WHERE userID = ?", (id,))
        voice=c.fetchone()
        if voice is None:
            await ctx.channel.send(f"{ctx.author.mention} Nem rendelkezel csatornával.")
        else:
            channelID = voice[0]
            role = discord.utils.get(ctx.guild.roles, name='@everyone')
            channel = self.bot.get_channel(channelID)
            await channel.set_permissions(role, connect=False,read_messages=True)
            await ctx.channel.send(f'{ctx.author.mention} Hang csatorna zárolva! 🔒')
        conn.commit()
        conn.close()

    @voice.command()
    async def unlock(self, ctx):
        conn = sqlite3.connect('voice.db')
        c = conn.cursor()
        id = ctx.author.id
        c.execute("SELECT voiceID FROM voiceChannel WHERE userID = ?", (id,))
        voice=c.fetchone()
        if voice is None:
            await ctx.channel.send(f"{ctx.author.mention} Nem rendelkezel csatornával.")
        else:
            channelID = voice[0]
            role = discord.utils.get(ctx.guild.roles, name='@everyone')
            channel = self.bot.get_channel(channelID)
            await channel.set_permissions(role, connect=True,read_messages=True)
            await ctx.channel.send(f'{ctx.author.mention} Hang csatorna feloldva! 🔓')
        conn.commit()
        conn.close()

    @voice.command(aliases=["allow"])
    async def permit(self, ctx, member : discord.Member):
        conn = sqlite3.connect('voice.db')
        c = conn.cursor()
        id = ctx.author.id
        c.execute("SELECT voiceID FROM voiceChannel WHERE userID = ?", (id,))
        voice=c.fetchone()
        if voice is None:
            await ctx.channel.send(f"{ctx.author.mention} Nem rendelkezel csatornával.")
        else:
            channelID = voice[0]
            channel = self.bot.get_channel(channelID)
            await channel.set_permissions(member, connect=True)
            await ctx.channel.send(f'{ctx.author.mention} feljogosította {member.name} -t hogy belépjen a csatornájára. ✅')
        conn.commit()
        conn.close()

    @voice.command(aliases=["deny"])
    async def reject(self, ctx, member : discord.Member):
        conn = sqlite3.connect('voice.db')
        c = conn.cursor()
        id = ctx.author.id
        guildID = ctx.guild.id
        c.execute("SELECT voiceID FROM voiceChannel WHERE userID = ?", (id,))
        voice=c.fetchone()
        if voice is None:
            await ctx.channel.send(f"{ctx.author.mention} Nem rendelkezel csatornával.")
        else:
            channelID = voice[0]
            channel = self.bot.get_channel(channelID)
            for members in channel.members:
                if members.id == member.id:
                    c.execute("SELECT voiceChannelID FROM guild WHERE guildID = ?", (guildID,))
                    voice=c.fetchone()
                    channel2 = self.bot.get_channel(voice[0])
                    await member.move_to(channel2)
            await channel.set_permissions(member, connect=False,read_messages=True)
            await ctx.channel.send(f'{ctx.author.mention} letiltotta {member.name} -t a csatornájáról. ❌')
        conn.commit()
        conn.close()



    @voice.command()
    async def limit(self, ctx, limit):
        conn = sqlite3.connect('voice.db')
        c = conn.cursor()
        id = ctx.author.id
        c.execute("SELECT voiceID FROM voiceChannel WHERE userID = ?", (id,))
        voice=c.fetchone()
        if voice is None:
            await ctx.channel.send(f"{ctx.author.mention} Nem rendelkezel csatornával.")
        else:
            channelID = voice[0]
            channel = self.bot.get_channel(channelID)
            await channel.edit(user_limit = limit)
            await ctx.channel.send(f'{ctx.author.mention} Csatorna limit beállítva '+ '{}!'.format(limit))
            c.execute("SELECT channelName FROM userSettings WHERE userID = ?", (id,))
            voice=c.fetchone()
            if voice is None:
                c.execute("INSERT INTO userSettings VALUES (?, ?, ?)", (id,f'{ctx.author.name}',limit))
            else:
                c.execute("UPDATE userSettings SET channelLimit = ? WHERE userID = ?", (limit, id))
        conn.commit()
        conn.close()


    @voice.command()
    async def name(self, ctx,*, name):
        conn = sqlite3.connect('voice.db')
        c = conn.cursor()
        id = ctx.author.id
        c.execute("SELECT voiceID FROM voiceChannel WHERE userID = ?", (id,))
        voice=c.fetchone()
        if voice is None:
            await ctx.channel.send(f"{ctx.author.mention} Nem rendelkezel csatornával.")
        else:
            channelID = voice[0]
            channel = self.bot.get_channel(channelID)
            await channel.edit(name = name)
            await ctx.channel.send(f'{ctx.author.mention} a csatornád neve mostantól: '+ '{}!'.format(name))
            c.execute("SELECT channelName FROM userSettings WHERE userID = ?", (id,))
            voice=c.fetchone()
            if voice is None:
                c.execute("INSERT INTO userSettings VALUES (?, ?, ?)", (id,name,0))
            else:
                c.execute("UPDATE userSettings SET channelName = ? WHERE userID = ?", (name, id))
        conn.commit()
        conn.close()

    @voice.command()
    async def claim(self, ctx):
        x = False
        conn = sqlite3.connect('voice.db')
        c = conn.cursor()
        channel = ctx.author.voice.channel
        if channel == None:
            await ctx.channel.send(f"{ctx.author.mention} Nem vagy hangcsatornában.")
        else:
            id = ctx.author.id
            c.execute("SELECT userID FROM voiceChannel WHERE voiceID = ?", (channel.id,))
            voice=c.fetchone()
            if voice is None:
                await ctx.channel.send(f"{ctx.author.mention} Nem a tiéd a csatorna!")
            else:
                for data in channel.members:
                    if data.id == voice[0]:
                        owner = ctx.guild.get_member(voice [0])
                        await ctx.channel.send(f"{ctx.author.mention} , a csatorna tulajdonosa: {owner.mention}!")
                        x = True
                if x == False:
                    await ctx.channel.send(f"{ctx.author.mention} Mostantól Te vagy a csatorna tulajdonosa!")
                    c.execute("UPDATE voiceChannel SET userID = ? WHERE voiceID = ?", (id, channel.id))
            conn.commit()
            conn.close()


def setup(bot):
    bot.add_cog(voice(bot))
