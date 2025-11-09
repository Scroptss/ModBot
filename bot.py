from datetime import datetime, timezone, timedelta
from urllib.request import urlopen
from pymongo import MongoClient
from termcolor import colored
from libs import iFunny
from libs.iFunny import User
from libs.iFunny import Chat
from libs.antispam import MessageRateLimiter
import requests
import json
import asyncio
import time
import math
import itertools
import random


ratelimiter = MessageRateLimiter()
client = MongoClient()
user_db = client.iFunny.users
chat_db = client.iFunny.chats
link_db = client.iFunny.link
email = "modbotnew@scropts.me" # The iFunny account your bot will run on. 
password = "" # Input your account's password
region = "United States"  # or "Brazil" for Brazilian chat servers.
prefix = "/" # Choose a symbol your bot will respond to. Examples: / . , ! $ > 
developers = ["660328cff4c8ab3c26086f4a", "5506eb31454fd0754e8b456f"] # Butterbeer; Dank


bot = iFunny.Bot(email, password, region, prefix, developers)
basicauth = bot.basic
bearer = bot.bearer


##### Common Functions #####


def cprint(*args, end_each=" ", end_all=""):

	dt = str(datetime.fromtimestamp(int(time.time())))
	print(colored(dt, "white"), end=end_each)

	for i in args:
		print(colored(str(i[0]), i[1].lower()), end=end_each)

	print(end_all)


def paginate(data: list, page: int = 1, limit: int = 5):
	max_page = math.ceil(len(data)/limit)
	page = min(max(int(page), 1), max_page)
	chunk = data[(page-1)*limit:page*limit]
	return chunk, page, max_page


def days_to_str(t):
	
	now = int(time.time())
	return str(int((now - t) / 86400))


async def updateChatData(ctx,chat,data):
	
	res = chat_db.replace_one({"_id":chat.id},data)

	if res.acknowledged:
		cprint(("Updated Chat Data ","cyan"), (chat.id, "yellow"))


async def updateChatDataByID(chat_id,data):
	
	res = chat_db.replace_one({"_id":chat_id},data)

	if res.acknowledged:
		cprint(("Updated Chat Data ","cyan"), (chat_id, "yellow"))


async def updateUserData(ctx,user,data):

	
	res = user_db.replace_one({"_id":user.id},data)

	if res.acknowledged:
		cprint(("Updated User Data ","cyan"), (user.nick,"green"))


async def updateLinkData(data):

	res = link_db.replace_one({"_id":"chat_link"},data)

	if res.acknowledged:
		cprint(("Updated Linking Data ","cyan"))


async def createChatData(ctx,chat):

	members = await chat.members()
	ops = []
	mems = []
	owner = {"id":"<error>","nick":"<error>"}
	admins = []

	for member in members:
		mems.append({"id":member.id,"nick":member.nick,"joined":int(time.time())})
		match member.role:
			case 0:
				if member.id == bot.user_id:
					#admins.append("")
					await chat.send(f"A rare error has occured, and I cannot determine the chat owner.")
					continue
				owner = {"id":member.id,"nick":member.nick}
			case 1:
				ops.append({"id":member.id,"nick":member.nick})
			case 2:
				continue

	data = {"_id":chat.id,"is_operator":False,"title":chat.title,"cover":chat.cover,"type":chat.type,"total_members":len(mems),"days":0,"antispam":"warn","demote":True,"lockdown":False,"no_pfp":False,"welcome":"","rules":"","linked":"","notes":[],"owner":owner,"admins":admins,"moderators":[],"vips":[],"ops":ops,"whitelist":[],"bans":{},"members":mems}
	res = chat_db.insert_one(data)

	if res.acknowledged:
		cprint(("Created Chat Data", "cyan"), (chat.id,"yellow"))

	return data


async def delChatData(ctx,chat):
	res = None

	data = chat_db.find_one({"_id":chat.id})
	if data:
		res = chat_db.delete_one(data)

	if res:
		cprint((f"Deleted Chat Data", "red"), (chat.id, "yellow"))


async def createUserData(ctx,user):

	user = await ctx.user_by_id(user.id)

	data = {"_id":user.id,"nick":user.og_nick,"met_me":int(time.time()),"chat_bans":[],"profile_bans":[],"past_names":[user.og_nick],"rank":0,"days":user.meme_experience.get("days",0)}
	res = user_db.insert_one(data)

	if res.acknowledged:
		cprint((f"Created User Data ","cyan"), (user.nick,"green"))

	return data


async def createLinkData():

	data = {"_id":"chat_link","codes":{},"chats":{}}
	res = link_db.insert_one(data)

	if res.acknowledged:
		cprint((f"Created Linking Data ","cyan"))

	return data


async def getChatData(ctx,chat):

	if chat.type == 1: return {}

	data = chat_db.find_one({"_id":chat.id})

	if not data:
		data = await createChatData(ctx,chat)

	return data


async def getChatDataByID(chat_id):

	data = chat_db.find_one({"_id":chat_id})

	if not data: return {}

	return data


async def getUserData(ctx,user):

	data = user_db.find_one({"_id":user.id})

	if not data:
		data = await createUserData(ctx,user)
	
	return data


async def getLinkData():

	data = link_db.find_one({"_id":"chat_link"})

	if not data:
		data = await createLinkData()

	return data


async def encode_special(string):

	args_list = string.split(" ")
	chosen = args_list.pop(0)
	msg = ""
	for i in args_list:
		msg += f"{i} "
	msg = msg[:len(msg)-1]
	
	norm = "AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz123456789_"
		
	fonts = [
		"𝗔𝗮𝗕𝗯𝗖𝗰𝗗𝗱𝗘𝗲𝗙𝗳𝗚𝗴𝗛𝗵𝗜𝗶𝗝𝗷𝗞𝗸𝗟𝗹𝗠𝗺𝗡𝗻𝗢𝗼𝗣𝗽𝗤𝗾𝗥𝗿𝗦𝘀𝗧𝘁𝗨𝘂𝗩𝘃𝗪𝘄𝗫𝘅𝗬𝘆𝗭𝘇𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵_",
		"𝘈𝘢𝘉𝘣𝘊𝘤𝘋𝘥𝘌𝘦𝘍𝘧𝘎𝘨𝘏𝘩𝘐𝘪𝘑𝘫𝘒𝘬𝘓𝘭𝘔𝘮𝘕𝘯𝘖𝘰𝘗𝘱𝘘𝘲𝘙𝘳𝘚𝘴𝘛𝘵𝘜𝘶𝘝𝘷𝘞𝘸𝘟𝘹𝘠𝘺𝘡𝘻123456789_",
		"𝘼𝙖𝘽𝙗𝘾𝙘𝘿𝙙𝙀𝙚𝙁𝙛𝙂𝙜𝙃𝙝𝙄𝙞𝙅𝙟𝙆𝙠𝙇𝙡𝙈𝙢𝙉𝙣𝙊𝙤𝙋𝙥𝙌𝙦𝙍𝙧𝙎𝙨𝙏𝙩𝙐𝙪𝙑𝙫𝙒𝙬𝙓𝙭𝙔𝙮𝙕𝙯123456789_",
		"𝔄𝔞𝔅𝔟ℭ𝔠𝔇𝔡𝔈𝔢𝔉𝔣𝔊𝔤ℌ𝔥ℑ𝔦𝔍𝔧𝔎𝔨𝔏𝔩𝔐𝔪𝔑𝔫𝔒𝔬𝔓𝔭𝔔𝔮ℜ𝔯𝔖𝔰𝔗𝔱𝔘𝔲𝔙𝔳𝔚𝔴𝔛𝔵𝔜𝔶ℨ𝔷123456789_",
		"𝕬𝖆𝕭𝖇𝕮𝖈𝕯𝖉𝕰𝖊𝕱𝖋𝕲𝖌𝕳𝖍𝕴𝖎𝕵𝖏𝕶𝖐𝕷𝖑𝕸𝖒𝕹𝖓𝕺𝖔𝕻𝖕𝕼𝖖𝕽𝖗𝕾𝖘𝕿𝖙𝖀𝖚𝖁𝖛𝖂𝖜𝖃𝖝𝖄𝖞𝖅𝖟123456789_",
		"𝒜𝒶𝐵𝒷𝒞𝒸𝒟𝒹𝐸𝑒𝐹𝒻𝒢𝑔𝐻𝒽𝐼𝒾𝒥𝒿𝒦𝓀𝐿𝓁𝑀𝓂𝒩𝓃𝒪𝑜𝒫𝓅𝒬𝓆𝑅𝓇𝒮𝓈𝒯𝓉𝒰𝓊𝒱𝓋𝒲𝓌𝒳𝓍𝒴𝓎𝒵𝓏𝟣𝟤𝟥𝟦𝟧𝟨𝟩𝟪𝟫_",
		"𝓐𝓪𝓑𝓫𝓒𝓬𝓓𝓭𝓔𝓮𝓕𝓯𝓖𝓰𝓗𝓱𝓘𝓲𝓙𝓳𝓚𝓴𝓛𝓵𝓜𝓶𝓝𝓷𝓞𝓸𝓟𝓹𝓠𝓺𝓡𝓻𝓢𝓼𝓣𝓽𝓤𝓾𝓥𝓿𝓦𝔀𝓧𝔁𝓨𝔂𝓩𝔃123456789_",
		"𝕒α𝔟Ｂｃ𝒸ｄ𝐝𝒆ε𝓕Ƒ𝐠𝑔𝐡𝒽𝕚Ｉⓙ𝐣ķᵏĹⓛ๓Ⓜ𝐧𝓃ｏⓞƤƤ𝐐𝓠ℝⓡŜˢţ𝐓ᵘ𝓾𝓥Ｖⓦｗ𝔵᙭Ⓨ𝐲ℤℤ❶２３４➄６７➇９_",
		"🄰🄰🄱🄱🄲🄲🄳🄳🄴🄴🄵🄵🄶🄶🄷🄷🄸🄸🄹🄹🄺🄺🄻🄻🄼🄼🄽🄽🄾🄾🄿🄿🅀🅀🅁🅁🅂🅂🅃🅃🅄🅄🅅🅅🅆🅆🅇🅇🅈🅈🅉🅉123456789_",
		"🅰🅰🅱🅱🅲🅲🅳🅳🅴🅴🅵🅵🅶🅶🅷🅷🅸🅸🅹🅹🅺🅺🅻🅻🅼🅼🅽🅽🅾🅾🅿🅿🆀🆀🆁🆁🆂🆂🆃🆃🆄🆄🆅🆅🆆🆆🆇🆇🆈🆈🆉🆉123456789_",
		"ⒶⓐⒷⓑⒸⓒⒹⓓⒺⓔⒻⓕⒼⓖⒽⓗⒾⓘⒿⓙⓀⓚⓁⓛⓂⓜⓃⓝⓄⓞⓅⓟⓆⓠⓇⓡⓈⓢⓉⓣⓊⓤⓋⓥⓌⓦⓍⓧⓎⓨⓏⓩ①②③④⑤⑥⑦⑧⑨_",
		"ＡａＢｂＣｃＤｄＥｅＦｆＧｇＨｈＩｉＪｊＫｋＬｌＭｍＮｎＯｏＰｐＱｑＲｒＳｓＴｔＵｕＶｖＷｗＸｘＹｙＺｚ１２３４５６７８９_",
		"𝔸𝕒𝔹𝕓ℂ𝕔𝔻𝕕𝔼𝕖𝔽𝕗𝔾𝕘ℍ𝕙𝕀𝕚𝕁𝕛𝕂𝕜𝕃𝕝𝕄𝕞ℕ𝕟𝕆𝕠ℙ𝕡ℚ𝕢ℝ𝕣𝕊𝕤𝕋𝕥𝕌𝕦𝕍𝕧𝕎𝕨𝕏𝕩𝕐𝕪ℤ𝕫𝟙𝟚𝟛𝟜𝟝𝟞𝟟𝟠𝟡_"
	]
	
	final = ""
	f = [r"%bold",r"%italic",r"%italic_bold",r"%gothic",r"%gothic_bold",r"%fancy",r"%fancy_bold",r"%funky",r"%boxed",r"%emoji",r"%bubble",r"%smooth",r"%outline"]
	if not chosen or chosen.lower() not in f:
		return string
	the_font = fonts[f.index(chosen.lower())]
	
	for char in msg:
		if char not in norm:
			final += char
			continue
	
		encoded_char = the_font[norm.index(char)]
		final += encoded_char
		
	return final


async def shouldKick(ctx,data,user_id):

	user = await ctx.user_by_id(user_id)
	kick = False

	if data["lockdown"]: kick = True

	if data["no_pfp"] and not user.pfp: kick = True

	if data["bans"]:
		kick = True
		if data["bans"][user_id]["type"] == "temp":
			if int(time.time()) > data["bans"][user_id]["release"]:
				del data["bans"][user_id]
				await updateChatData(ctx,ctx.chat,data)
				kick = False				

	if user.meme_experience.get("days") < data["days"]:
		kick = True

	return kick


##### Admin Commands #####


@bot.command(help_category="moderation",help_message="Admin a user in your chat! Admins are able to do the following:\n\nRemove moderators\nKick & Ban users\nEdit chat info (name, cover)\nSet chat statuses (Lockdown, Mute, No PFP, Rank)\nTalk during mute periods\n\nAdmin permissions should only given to members you trust. 🔒")
async def admin(ctx,username=None,*args):
	chat = ctx.chat
	author = ctx.message.author
	message = ctx.message

	if chat.type == 1:
		return

	if not username: return await chat.send("Input a username.")

	user = await ctx.user(username)
	if not user: return await chat.send("That user doesn't exist!")

	if user.id == bot.user_id:

		if chat.role != 0:
			if not message.payload.get("local_id"):
				return await chat.send("I have detected that you are on an Android device, Follow these directions to get started:\nhttps://ifunny.co/picture/AOkbS4zHB")
			elif "-" in message.payload["local_id"]:
				return await chat.send("I have detected that you are on an IOS device, Follow these directions to get started:\nhttps://ifunny.co/picture/bLrQa4zHB")
			else:
				return await chat.send("I could not detect what device you are using, Try these instructions: https://ifunny.co/picture/AOkbS4zHB")
			
		else: return await chat.send("I am already set as admin.")

	if chat.role != 0:
		return await chat.send(f"I am not set as admin of this chat. For more information, type \"{ctx.bot.prefix}admin {ctx.bot.username}\"")

	data = await getChatData(ctx,chat)

	if author.id != data["owner"]["id"]:
		return await chat.send(f"Only {data['owner']['nick']} can modify admins!")
	
	if user.id in data["admins"]:
		return await chat.send(f"{user.nick} is already an admin!")
	
	if user.id in data["moderators"]:
		return await chat.send("You must un-mod this user before promoting them to admin!")
	
	if user.id in data["vips"]:
		return await chat.send(f"You must un-VIP this user before promoting them to admin!")

	data["admins"].append(user.id)
	await updateChatData(ctx,chat,data)
	return await chat.send(f"Successfully promoted {user.nick} to admin! 🎉")


@bot.command(help_category="moderation",help_message="Demotes an admin back to user! Only the chat owner can edit the admin list.")
async def unadmin(ctx,username=None,*args):
	chat = ctx.chat
	author = ctx.message.author

	if chat.type == 1:
		return

	if not username: return await chat.send("Input a username.")

	user = await ctx.user(username)
	if not user: return await chat.send("That user doesn't exist!")

	if chat.role != 0:
		return await chat.send(f"I am not set as admin of this chat. For more information, type \"{ctx.bot.prefix}admin {ctx.bot.username}\"")
	
	data = await getChatData(ctx,chat)

	if user.id == bot.user_id and chat.role == 0:
		if author.id == data["owner"]["id"] or author.id in developers:
			await chat.send("Giving ownership back to you...")
			data["is_operator"] = False
			await asyncio.sleep(.5)
			await bot.buff.send_ifunny_ws(json.dumps([48,bot.buff.ifunny_ws_counter,{},"co.fun.chat.leave_chat",[],{"admin":f"{author.id}","chat_name":f"{chat.id}"}]))
			await asyncio.sleep(.5)
			await chat.invite(await ctx.user(bot.user_id))

		else: return await chat.send(f"Only {data['owner']['nick']} can take ownership of this chat!")

	if author.id != data["owner"]["id"]:
		return await chat.send(f"Only {data['owner']['nick']} can modify admins!")
	
	if user.id not in data["admins"] and user.id != bot.user_id:
		return await chat.send(f"{user.nick} wasn't an admin in to begin with!")
	
	if user.id in data["admins"]:
		data["admins"].remove(user.id)

	await updateChatData(ctx,chat,data)
	return await chat.send(f"{user.nick} was demoted to member.")


@bot.command(help_category="moderation",help_message="Add a moderator to your chat! Mods are able to do the following:\n\nKick users\nTalk during mute periods\n\nOnly the chat owner can add moderators, but admins are able to remove mods.")
async def mod(ctx,username=None,*args):
	chat = ctx.chat
	author = ctx.message.author

	if chat.type == 1:
		return

	if not username: return await chat.send("Input a username.")

	user = await ctx.user(username)
	if not user: return await chat.send("That user doesn't exist!")

	if user.id == bot.user_id:
		return await chat.send("I cannot be set as a moderator!")

	if chat.role != 0:
		return await chat.send(f"I am not set as admin of this chat. For more information, type \"{ctx.bot.prefix}admin {ctx.bot.username}\"")

	data = await getChatData(ctx,chat)

	if author.id != data["owner"]["id"]:
		return await chat.send(f"Only {data['owner']['nick']} can edit moderators!")
	
	if user.id in data["moderators"]:
		return await chat.send(f"{user.nick} is already a moderator!")
	
	if user.id in data["admins"]:
		return await chat.send("You must un-admin this user before promoting them to moderator!")
	
	if user.id in data["vips"]:
		return await chat.send(f"You must un-VIP this user before promoting them to moderator!")

	data["moderators"].append(user.id)
	await updateChatData(ctx,chat,data)
	return await chat.send(f"Successfully promoted {user.nick} to moderator! 🎉")


@bot.command(help_category="moderation",help_message="Demotes a moderator back to user! Only admins and the owner can remove moderators.")
async def unmod(ctx,username=None,*args):
	chat = ctx.chat
	author = ctx.message.author

	if chat.type == 1:
		return

	if not username: return await chat.send("Input a username.")

	user = await ctx.user(username)
	if not user: return await chat.send("That user doesn't exist!")

	if chat.role != 0:
		return await chat.send(f"I am not set as admin of this chat. For more information, type \"{ctx.bot.prefix}admin {ctx.bot.username}\"")
	
	data = await getChatData(ctx,chat)

	#if author.id != data["owner"]["id"]:
	#	return await chat.send(f"Only {data['owner']['nick']} can edit moderators!")
	
	if user.id == bot.user_id:
		return await chat.send("I'm not a moderator, silly")
	
	if user.id not in data["moderators"] and user.id != bot.user_id:
		return await chat.send(f"{user.nick} wasn't a moderator in to begin with!")
	
	if user.id in data["moderators"]:
		data["moderators"].remove(user.id)

	await updateChatData(ctx,chat,data)
	return await chat.send(f"{user.nick} was demoted to member.")


@bot.command(help_category="moderation",help_message="Set a user as a VIP! VIP status can only be assigned and revoked by the chat owner. This exclusive role grants mute immunity and protection from being kicked or removed by admins or moderators.")
async def vip(ctx,username=None,*args):
	chat = ctx.chat
	author = ctx.message.author
	message = ctx.message

	if chat.type == 1:
		return

	if not username: return await chat.send("Input a username.")

	user = await ctx.user(username)
	if not user: return await chat.send("That user doesn't exist!")

	if user.id == bot.user_id and chat.role != 0: return await chat.send("<3")

	if user.id == bot.user_id and chat.role == 0: return await chat.send("I'm already a VIP")

	if chat.role != 0:
		return await chat.send(f"I am not set as admin of this chat. For more information, type \"{ctx.bot.prefix}admin {ctx.bot.username}\"")
	
	data = await getChatData(ctx,chat)

	if author.id != data["owner"]["id"]:
		return await chat.send(f"Only {data['owner']['nick']} can modify VIPs!")
	
	if user.id in data["vips"]:
		return await chat.send(f"{user.nick} is already a VIP!")
	
	if user.id in data["moderators"] or user.id in data["admins"]:
		return await chat.send("You must demote this user before promoting them to VIP!")

	data["vips"].append(user.id)
	await updateChatData(ctx,chat,data)
	return await chat.send(f"Successfully promoted {user.nick} to VIP! 🎉")


@bot.command(help_category="moderation",help_message="Demotes a VIP back to user! Only admins and the owner can remove VIPs.")
async def unvip(ctx,username=None,*args):
	chat = ctx.chat
	author = ctx.message.author

	if chat.type == 1:
		return

	if not username: return await chat.send("Input a username.")

	user = await ctx.user(username)
	if not user: return await chat.send("That user doesn't exist!")

	if chat.role != 0:
		return await chat.send(f"I am not set as admin of this chat. For more information, type \"{ctx.bot.prefix}admin {ctx.bot.username}\"")
	
	data = await getChatData(ctx,chat)

	if author.id != data["owner"]["id"]:
		return await chat.send(f"Only {data['owner']['nick']} can modify VIPs!")
	
	if user.id not in data["vips"] and user.id != bot.user_id:
		return await chat.send(f"{user.nick} wasn't a VIP in to begin with!")
	
	if user.id in data["vips"]:
		data["vips"].remove(user.id)

	await updateChatData(ctx,chat,data)
	return await chat.send(f"{user.nick} was demoted to member.")


@bot.command(help_category="moderation",help_message="Removes a user from the chat.")
async def kick(ctx,*args):
	chat = ctx.chat
	message = ctx.message.args.replace("\n"," ").split(" ")

	if chat.type == 1:
		return

	if not args:
		return await chat.send("Input a username or ID.")
	
	data = await getChatData(ctx,chat)
	author = ctx.message.author

	if author.id not in data["admins"] and author.id not in data["moderators"]:
		return await chat.send("You are neither an admin or moderator for this chat!")
	
	members = await chat.members()
	msg = ""

	for username in message:
		user = None		

		for member in members:				
			if member.nick.lower() != username.lower():
				continue
			if member.nick.lower() == username.lower():
				user = member
				break
		if not user:
			msg += f"🔍 couldnt find {username}\n"
			continue

		if user.id in data["admins"]:
			msg += f"❌ I cannot kick {user.nick} as they are an admin.\n"
			continue

		if user.id in data["moderators"]:
			msg += f"❌ I cannot kick {user.nick} as they are a mod.\n"
			continue

		if user.id in data["vips"]:
			msg += f"❌ I cannot kick {user.nick} as they are a VIP\n"
			continue

		msg += f"✅ {user.nick} was kicked\n"

		if user.id in data["members"]:
			data.remove(user.id)

		await chat.kick(user)
		
	await updateChatData(ctx,chat,data)
	return await chat.send(msg)


# Timeout (temp-ban)


@bot.command(help_category="moderation",help_message="Ban a user from your chat")
async def ban(ctx,*args):
	chat = ctx.chat
	message = ctx.message.args.replace("\n"," ").split(" ")

	if chat.type == 1:
		return
	
	if not args:
		return await chat.send("Input a username or ID.")

	data = await getChatData(ctx,chat)
	author = ctx.message.author

	if author.id not in data["admins"] and author.id not in data["moderators"]:
		return await chat.send("You are neither an admin or moderator!")
	
	moderator = author.id in data["moderators"]
		
	members = await chat.members()
	msg = ""

	for username in message:
		user = await ctx.user(username)		

		if not user:
			for member in members:				
				if member.nick.lower() != username.lower():
					continue
				if member.nick.lower() == username.lower():
					user = member
					break
			if not user:
				msg += f"🔍 couldnt find {username}\n"
				continue

		if user.id in data["admins"]:
			msg += f"❌ I cannot ban {user.nick} as they are an admin.\n"
			continue

		if user.id in data["vips"]:
			msg += f"❌ I cannot ban {user.nick} as they are a VIP\n"
			continue

		if user.id in data["moderators"]:
			msg += f"❌ I cannot ban {user.nick} as they are a mod.\n"
			continue

		if not data["bans"].get(user.id):
			if moderator:
				data["bans"][user.id] = {"type":"temp","release":int(time.time()) + 86400,"nick":user.nick,"ban_by":{"nick":author.nick,"id":author.id}}
				msg += f"✅ {user.nick} was temp-banned for 1d\n"

			else: data["bans"][user.id] = {"type":"perm","nick":user.nick,"ban_by":{"nick":author.nick,"id":author.id}}
			msg += f"✅ {user.nick} was banned\n"

		else: msg += f"✅ {user.nick} already banned"				

		if user.id in data["members"]:
			data.remove(user.id)

		await chat.kick(user)
	
	await updateChatData(ctx,chat,data)
	return await chat.send(msg)


@bot.command(help_category="moderation",help_message="Unbans a user from the chat")
async def unban(ctx,username=None,*args):
	chat = ctx.chat
	author = ctx.message.author
	data = await getChatData(ctx,chat)

	if ctx.chat.type == 1:
		return

	if author.id not in data["admins"]:
		return await chat.send("You are not an admin!.")
		
	if not username:
		return await chat.send("Input a user to unban")
	
	user = await ctx.user(username)
	if not user:
		return await chat.send("That user doesn't exist!")
	
	if user.id not in data["bans"]:
		return await chat.send("That user isnt banned to begin with.")
	
	del data["bans"][user.id]

	await updateChatData(ctx,chat,data)

	return await chat.send(f"{user.nick} has been forgiven")


@bot.command(help_category="moderation",help_message=f"Removes inactive users from the chat. Excludes admins and mods.\n\nUsage: {prefix}purge 2")
async def purge(ctx,days=1,*args):
	chat = ctx.chat
	author = ctx.message.author
	data = await getChatData(ctx,chat)

	if ctx.chat.type == 1:
		return await chat.send("This is a DM, not a group chat.")

	if chat.role != 0:
		return await chat.send(f"I am not set as the admin for this chat. For help on setting me admin type {prefix}admin {ctx.bot.username}")

	if author.id != data["owner"]["id"]:
		return await chat.send("Only the owner can run this command!")
	
	if not days.isdigit():
		return await chat.send("Specify an amount of days")
	
	days_in_seconds = 86400
	if int(days) < 1:
		return
	if int(days) > 1:
		days_in_seconds = 86400*int(days)
	timenow = int(time.time())
	cutoff = timenow - int(days_in_seconds)

	members = await chat.members()

	members_to_remove = []

	for member in members:
		if member.status == 0: continue
		
		if (member.status // 1000) < cutoff:
			if member.id not in data["admins"] and member.id not in data["moderators"] and member.id not in data["vips"]:
				members_to_remove.append({"id":member.id,"nick":member.nick})

	if not members_to_remove:
		return await chat.send(f"There are no members who have been inactive for {days} days")

	cancels = ["stop","no","cancel"]

	await chat.send(f"This will kick {len(members_to_remove)} members from the chat. To view the members, say \"View\", otherwise say \"Confirm\" to kick these members or \"Cancel\" to stop the purge.")

	try:
		while message := await chat.input(type=iFunny.Message,timeout=30):
			if isinstance(message, iFunny.Message):
				if message.author.id == author.id:

					if message.text.lower() == "view":
						msg = "Members to kick:\n\n"
						for member in members_to_remove:
							msg += member["nick"]
						await chat.send(msg)
						continue

					if message.text.lower() == "confirm":
						await chat.send("Removing members...")
						await asyncio.sleep(1)
						for member in members_to_remove:
							await chat.kick(member["id"])
						await chat.send("Purge complete!")

					if message.text.lower() in cancels:
						return await chat.send("The purge was cancelled.")

	except:
		return await chat.send("The purge was cancelled due to inactivity.")


@bot.command(help_category="moderation",help_message="Makes the chat go into lockdown mode. To disable, run the command again.")
async def lockdown(ctx,*args):
	chat = ctx.chat
	author = ctx.message.author

	if ctx.chat.type == 1:
		return await chat.send("This is a DM, not a group chat.")

	if chat.bot_role != 0:
		return await chat.send("I am not admin of the chat!")
	
	data = await getChatData(ctx,chat)
	
	if author.id not in data["admins"]:
		return await chat.send("You are not an admin.")
	
	if data["lockdown"] == True:
		data["lockdown"] = False
		await chat.send("Lockdown has been disabled")
	else:
		data["lockdown"] = True
		await chat.send("Lockdown has been enabled, anybody who joins the chat will be kicked.")

	await updateChatData(ctx,chat,data)


@bot.command(help_category="moderation",help_message="Toggle whether or not users with no Profile Pics can join the chat.")
async def nopfp(ctx,*args):
	chat = ctx.chat
	author = ctx.message.author

	if ctx.chat.type == 1:
		return await chat.send("This is a DM, not a group chat.")

	if chat.bot_role != 0:
		return await chat.send("I am not admin of the chat!")
	
	data = await getChatData(ctx,chat)
	
	if author.id not in data["admins"]:
		return await chat.send("You are not an admin.")
	
	if data["no_pfp"] == True:
		data["no_pfp"] = False
		await chat.send("Automatic kicking of users with no profile pic has been disabled")
	else:
		data["no_pfp"] = True
		await chat.send("NoPFP has been enabled, anybody who joins the chat without a profile picture will be kicked.")

	await updateChatData(ctx,chat,data)


@bot.command(help_category="moderation",help_message="Mute the chat so only admins can talk. Only works for public chats.")
async def mute(ctx,*args):
	chat = ctx.chat
	data = await getChatData(ctx,chat)
	author = ctx.message.author

	if author.id not in data["admins"]:
		return await chat.send("This is an admin only command")
	
	if chat.type != 3:
		return await chat.send("This feature only works for public chats.")
	
	operators = []
	members = await chat.members()
	for member in members:
		if member.role == 1 and member.id != data["owner"]["id"]:
			operators.append(member.id)	

	await chat.send("Muting the chat... Only admins, VIPs, and moderators will be able to send messages")

	if operators != []:
		await bot.buff.send_ifunny_ws(json.dumps([48,bot.buff.ifunny_ws_counter,{},"co.fun.chat.unregister_operators",[],{"chat_name":f"{chat.id}","operator_ids":operators}]))
		operators.clear()

	users = []
	for mod in data["moderators"]:
		users.append(mod)
	for admin in data["admins"]:
		users.append(admin)
	for vip in data["vips"]:
		users.append(vip)

	await asyncio.sleep(1)
	await bot.buff.send_ifunny_ws(json.dumps([48,bot.buff.ifunny_ws_counter,{},"co.fun.chat.register_operators",[],{"chat_name":f"{chat.id}","operator_ids":users}]))
	await asyncio.sleep(1)
	await bot.buff.send_ifunny_ws(json.dumps([48,bot.buff.ifunny_ws_counter,{},"co.fun.chat.freeze_chat",[],{"chat_name":f"{chat.id}"}]))
	return await chat.send("Chat has been muted")


@bot.command(help_category="moderation",help_message="Unmutes a chat from a previous mute. Only works for public chats.")
async def unmute(ctx,*args):
	chat = ctx.chat
	author = ctx.message.author
	data = await getChatData(ctx,chat)

	if author.id not in data["admins"] and author.id != data["owner"]["id"]:
		return await chat.send("This is an admin only command")
	
	if chat.type != 3:
		return await chat.send("This feature only works for public chats.")
	
	operators = []
	members = await chat.members()

	for member in members:
		if member.role == 1 and member.id != data["owner"]["id"]:
			operators.append(member.id)

	await bot.buff.send_ifunny_ws(json.dumps([48,bot.buff.ifunny_ws_counter,{},"co.fun.chat.unfreeze_chat",[],{"chat_name":f"{chat.id}"}]))

	if operators != []:
		await bot.buff.send_ifunny_ws(json.dumps([48,bot.buff.ifunny_ws_counter,{},"co.fun.chat.unregister_operators",[],{"chat_name":str(chat.id),"operator_ids":operators}]))

	return await chat.send("Chat has been un-muted")


@bot.command(help_category="moderation",help_message=f"Set the antispam mode. Toggles between:\n\nOff\nWarn\nKick\nBan\n\nusage: {prefix}antispam warn")
async def antispam(ctx,mode=None,*args):
	chat = ctx.chat
	author = ctx.message.author
	data = await getChatData(ctx,chat)

	if ctx.chat.type == 1:
		return await chat.send("This is a DM, not a group chat.")

	if author.id not in data["admins"]:
		return await chat.send("You are not an admin of this chat!")

	if not mode:
		return await chat.send(f"Please specify between the following modes:\n\nOff\nWarn\nKick\nBan\n\nEx: {prefix}antispam Off")
	
	if mode.lower() not in ["off","warn","kick","ban"]:
		return await chat.send(f"Please specify between the following modes:\n\nOff\nWarn\nKick\nBan\n\nEx: {prefix}antispam Off")
	
	msg = ""
	data["antispam"] = mode.lower()

	match mode.lower():
		case "off":
			msg += "Antispam was turned off."
		case "warn":
			msg += "Antispam was set to warn users"
		case "kick":
			msg += "Antispam was set to kick users"
		case "ban":
			msg += "Antispam was set to ban users"
	
	await updateChatData(ctx,chat,data)
	return await chat.send(msg)


@bot.command(help_category="moderation",help_message=f"Set a day minimun requirement for users to be able to join your chat.\n\nEx: {prefix}joindays 10", aliases=["mindays"])
async def joindays(ctx,days=1,*args):
	chat = ctx.chat
	author = ctx.message.author
	data = await getChatData(ctx,chat)

	if ctx.chat.type == 1:
		return await chat.send("This is a DM, not a group chat.")

	if author.id not in data["admins"]:
		return await chat.send("You are not an admin for this chat!")
	
	if not days:
		return await chat.send(f"Specify the minimun amount of days a user must have before being able to join.\n\nEx: {prefix}joindays 10")
	
	if not days:
		return await chat.send("Input a number of days")

	if not days.isdigit():
		return await chat.send("Specify a number of days.")
	
	data["days"] = int(days)
	await updateChatData(ctx,chat,data)
	return await chat.send(f"Users with less than {days} days will be kicked upon entering the chat.")


@bot.command(help_category="moderation",help_message=f"Toggle the feature to demote a member from moderator / admin if they decide to leave the chat.\n\nEx: {prefix}demote on")
async def demote(ctx,toggle = None,*args):
	chat = ctx.chat
	author = ctx.message.author
	data = await getChatData(ctx,chat)

	if ctx.chat.type == 1:
		return await chat.send("This is a DM, not a group chat.")

	if author.id != data["owner"]["id"]:
		return await chat.send(f"Only {data['owner']['nick']} can toggle this setting!")
	
	if not toggle:
		if data["demote"]: return await chat.send("Demoting is currently turned on.")
		return await chat.send("Demoting is currently disabled.")
	
	if toggle.lower() not in ["on","off"]:
		return await chat.send("Please specify either On or Off.")
	
	if toggle.lower() == "on":
		data["demote"] = True
	else:
		data["demote"] = False

	await updateChatData(ctx,chat,data)
	return await chat.send(f"Demoting departing moderation members has been turned {toggle.lower()}.")


##### Chat Customization #####


@bot.command(aliases=["setcover"],help_category="customization",help_message=f"Change the Chat's Profile pic\n\nUsage: {prefix}setpfp (image link)\n\nSupports direct image links from the internet, an image sent after running the command, or iFunny post links")
async def setpfp(ctx,link=None,*args):
	chat = ctx.chat
	chat_id = chat.id
	author = ctx.message.author
	data = await getChatData(ctx,chat)

	if chat.type == 1:
		return
	
	if author.id != data['owner']['id']:
		return await chat.send("Only the owner can edit this!")

	if not link and chat.type != 2: return await chat.send("I require an image link to set the pfp to")

	if chat.type == 2 and not link:
		await chat.send("Send an image or GIF to set.")
		while image := await chat.input(type=iFunny.File):
			if isinstance(image, iFunny.File):
				if image.author.id != author.id:
					await chat.send("Not you!")
					continue
				if image.type not in ["img","gif"]:
					return await chat.send("File received was not an image or GIF")
				link = image.url
				break

	if chat.type == 3:
		if "https://ifunny.co" not in link and "https://ifunnyx.co" not in link and author.id != data["owner"]["id"]:
			return await chat.send("Admins can only be set to an iFunny post link!")
		
	if "https://ifunny.co" in link or "https://ifunnyx.co" in link:
		link = link.split("/")[4]
		content_id = link.split("?s=")[0]

		header = {
			'Host': 'api.ifunny.mobi',
			'Applicationstate': '1',
			"Accept": "video/mp4, image/jpeg",
			'Accept-Encoding': 'gzip, deflate, br',
			'Ifunny-Project-Id': 'iFunny',
			'User-Agent': 'iFunny/8.41.11(24194) iPhone/16.3.1 (Apple; iPhone12,5)',
			'Authorization': 'Basic '+ bot.basic,
			'Accept-Language': 'en-us'}
		
		url = f"https://api.ifunny.mobi/v4/content/{content_id}"
		print(url)

		req = requests.get(url,headers=header).json()

		if req["status"] == 404:
			return await chat.send("That content either got banned or doesnt exist.")
		
		link = req["data"]["url"]

	await bot.buff.send_ifunny_ws(json.dumps([48,bot.buff.ifunny_ws_counter,{},"co.fun.chat.edit_chat",[],{"unset":[],"set":{"title":f"{chat.title}","cover":f"{link}"},
	"chat_name":f"{chat_id}"}]))
			
	data["cover"] = link
	await updateChatData(ctx,chat,data)
	return await chat.send("Cover has been set!")


@bot.command(help_category="customization",help_message="Set the chat name\n\nUsage:\n/setname Chat Name Here\n\nYou can also select a font!\n\nFont usage:\n/setname %font Chat Name Here\n\nAvailable Fonts:\n%bold : 𝗛𝗲𝗹𝗹𝗼\n%italic : 𝘏𝘦𝘭𝘭𝘰\n%italic_bold : 𝙃𝙚𝙡𝙡𝙤\n%gothic : ℌ𝔢𝔩𝔩𝔬\n%gothic_bold : 𝕳𝖊𝖑𝖑𝖔\n%fancy : 𝐻𝑒𝓁𝓁𝑜\n%fancy_bold : 𝓗𝓮𝓵𝓵𝓸\n%funky : ⒽέĻŁᵒ\n%boxed : 🄷🄴🄻🄻🄾\n%emoji : 🅷🅴🅻🅻🅾\n%bubble : Ⓗⓔⓛⓛⓞ\n%smooth : Ｈｅｌｌｏ\n%outline : ℍ𝕖𝕝𝕝𝕠",aliases=["settitle"])
async def setname(ctx,*args):
	chat = ctx.chat
	chat_id = chat.id
	author = ctx.message.author
	data = await getChatData(ctx,chat)

	if chat.type == 1:
		return

	if author.id != data['owner']['id']:
		return await chat.send("Only the owner can edit this!")
	
	if not args:
		return await chat.send("Specify a title to set.")
		
	title = ctx.message.args

	font_list = [r"%bold",r"%italic",r"%italic_bold",r"%gothic",r"%gothic_bold",r"%fancy",r"%fancy_bold",r"%funky",r"%boxed",r"%emoji",r"%bubble",r"%smooth",r"%outline"]

	if args:
		if args[0].lower() in font_list:
			title = await encode_special(ctx.message.args)

	data["title"] = title
	await updateChatData(ctx,chat,data)
	await bot.buff.send_ifunny_ws(json.dumps([48,bot.buff.ifunny_ws_counter,{},"co.fun.chat.edit_chat",[],{"unset":[],"chat_name":f"{chat_id}","set":{"title":f"{title}"}}]))
	return await chat.send("Chat name has been updated")


@bot.command(help_category="customization",help_message="Set the chat description! Only available for public chats.\n\nUsage:\n/setdesc Chat Description Here\n\nYou can also select a font!\n\nFont usage:\n/setdesc %font Chat Description Here\n\nAvailable Fonts:\n%bold : 𝗛𝗲𝗹𝗹𝗼\n%italic : 𝘏𝘦𝘭𝘭𝘰\n%italic_bold : 𝙃𝙚𝙡𝙡𝙤\n%gothic : ℌ𝔢𝔩𝔩𝔬\n%gothic_bold : 𝕳𝖊𝖑𝖑𝖔\n%fancy : 𝐻𝑒𝓁𝓁𝑜\n%fancy_bold : 𝓗𝓮𝓵𝓵𝓸\n%funky : ⒽέĻŁᵒ\n%boxed : 🄷🄴🄻🄻🄾\n%emoji : 🅷🅴🅻🅻🅾\n%bubble : Ⓗⓔⓛⓛⓞ\n%smooth : Ｈｅｌｌｏ\n%outline : ℍ𝕖𝕝𝕝𝕠",aliases=["setdesc"])
async def setdescription(ctx,*args):
	chat = ctx.chat
	chat_id = chat.id
	author = ctx.message.author
	data = await getChatData(ctx,chat)

	if chat.type != 3:
		return await chat.send("This only works for public chats!")

	if author.id not in data["admins"]:
		return await chat.send("You are not an admin of this chat!")
	
	if not args:
		return await chat.send("Specify a description to set.")
		
	description = ctx.message.args

	font_list = [r"%bold",r"%italic",r"%italic_bold",r"%gothic",r"%gothic_bold",r"%fancy",r"%fancy_bold",r"%funky",r"%boxed",r"%emoji",r"%bubble",r"%smooth",r"%outline"]

	if args:
		if args[0].lower() in font_list:
			description = await encode_special(ctx.message.args)

	data["description"] = description
	await updateChatData(ctx,chat,data)
	await bot.buff.send_ifunny_ws(json.dumps([48,bot.buff.ifunny_ws_counter,{},"co.fun.chat.edit_chat",[],{"unset":[],"chat_name":f"{chat_id}","set":{"description":f"{description}"}}]))
	return await chat.send("Chat description has been updated")


@bot.command(help_category="customization",help_message="Set the welcome message to say when users join the chat! Run the command by itself to clear the welcome message. You can substitute \"%user\" for the joinee's username")
async def setwelcome(ctx,*args):
	chat = ctx.chat
	author = ctx.message.author
	data = await getChatData(ctx,chat)

	if ctx.chat.type == 1:
		return await chat.send("This is a DM, not a group chat.")

	if author.id not in data["admins"]:
		return await chat.send("You are not an admin of this chat!")
	
	if not args:
		data["welcome"] = ""
		await updateChatData(ctx,chat,data)
		return await chat.send("Clearing the welcome message...")
	
	data["welcome"] = ctx.message.args
	await updateChatData(ctx,chat,data)
	return await chat.send(f"I will now welcome new members with the following:\n\n{ctx.message.args}")


@bot.command(help_category="customization",help_message="Set a custom rule list for your chat. Run the command by itself to clear the current rule set.")
async def setrules(ctx,*args):
	chat = ctx.chat
	author = ctx.message.author
	data = await getChatData(ctx,chat)

	if ctx.chat.type == 1:
		return await chat.send("This is a DM, not a group chat.")

	if author.id not in data["admins"]:
		return await chat.send("You are not an admin of this chat!")
	
	if not args:
		data["rules"] = ""
		await updateChatData(ctx,chat,data)
		return await chat.send("Clearing the rules...")
	
	data["rules"] = ctx.message.args
	await updateChatData(ctx,chat,data)
	return await chat.send(f"The rules have been updated. Say {prefix}rules to view them")

def generateCode(paramInt=5):
	intRange = range(1, paramInt+1)
	arrayList = []
	for i in intRange:
		arrayList.append(random.choice("abcdefghjkmnpqrstuvwxyz23456789"))
	strn = ''.join(arrayList)
	return strn

@bot.command(help_category="customization",help_message="Link this chat to another. I will send you a code in our dms, then ask you to send that code in the chat you want to link.")
async def link(ctx,code="",*args):
	chat = ctx.chat
	if chat.type == 1: return await chat.send("Linking can only be done in group chats!")
	if chat.role != 0: return await chat.send(f"I am not set as admin of this chat. For more information, type \"{ctx.bot.prefix}admin {ctx.bot.username}\"")
	author = ctx.message.author
	data = await getChatData(ctx,chat)
	code = code.lower()

	if data['owner']['id'] != author.id:
		return await chat.send("Only the chat owner can link this chat.")
	
	link = data.get("linked",{})

	# If link already exists, ask to run unlink.
	if link != {}:
		chat2 = await bot.get_chat(link['id'])
		if not chat2:
			return await chat.send(f"This chat is already linked to another chat, however I was unable to get it's information. If it has been deleted and you would like to remove this link, type {bot.prefix}unlink")
		return await chat.send(f"This chat is already linked to the following chat:\n\n({chat2.title})\n\nTo unlink this chat, type {bot.prefix}unlink")

	link_data = await getLinkData()
	linked_chat = link_data["codes"].get(code,{})
	# If code, and user is owner in both chats, save linked data.
	if code and len(code) == 5:
		
		firstChat = linked_chat["from"]
		chat2 = await bot.get_chat(firstChat)
		chat2.id = firstChat
		chat2_data = await getChatDataByID(chat2.id)

		if not linked_chat:
			return await chat.send("That code is invalid.")
		
		if linked_chat['owner']['id'] != author.id:
			return await chat.send("You are not the one I supplied the code to!")
		
		if linked_chat["from"] == chat.id:
			return await chat.send("That code won't work here.")
		
		if chat2_data["owner"]["id"] != author.id:
			return await chat.send("You are not the owner of this chat!")
		
		#if valid - save linked chat IDs to each chat file
		
		await chat2.send(f"This chat is now linked to {chat.title}! Say {prefix}join to be invited!")

		data['linked'] = {"id":firstChat}
		await updateChatData(ctx,chat,data)

		chat2_data["linked"] = {"id":chat.id}
		await updateChatDataByID(chat2.id,chat2_data)

		link_data["chats"].pop(firstChat)
		link_data["codes"].pop(code)
		await updateLinkData(link_data)
		return await chat.send("Successfully linked!")
	

	# If not code, and user is owner, and chat not currently linked, generate code - add to codes - and send code to user DMs.

	if oldCode := link_data["chats"].get(chat.id):
		await author.send(f"The following code will link {chat.title}\n\nType it in the chat you would like to link to.")
		await author.send(f"{bot.prefix}link {oldCode.upper()}")
		return await chat.send("This chat already has a link code. I have sent it to our DMs.")

	while True:
		code = generateCode().lower()
		if not link_data.get(code): break

	link_data["codes"].update({code:{"from":chat.id, "owner":{"id":author.id,"name":author.nick}}})
	link_data["chats"].update({chat.id:code})
	await updateLinkData(link_data)
	await author.send(f"The following code will link {chat.title}\n\nType it in the chat you would like to link to.")
	await author.send(f"{bot.prefix}link {code.upper()}")
	return await chat.send("I have sent a code to our DMs. Input the code in another chat to complete the linking process.")


##### Tool Commands #####


@bot.command(help_category="tools",help_message="Join the linked chat.")
async def join(ctx,*args):
	chat = ctx.chat
	author = ctx.message.author

	if chat.type == 1: return

	if chat.role != 0:
		return await chat.send(f"I am not set as admin of this chat. For more information, type \"{ctx.bot.prefix}admin {ctx.bot.username}\"")

	data = await getChatData(ctx,chat)
	link = data.get("linked",{})

	if not link:
		data["linked"] = {}
		await updateChatData(ctx,chat,data)
		if data['owner']['id'] == author.id:
			return await chat.send(f"This chat isn't linked to another chat!\n\nType {bot.prefix}link to start the linking process.")
		return await chat.send("This chat isn't linked to another chat!")
		

	chat2 = await bot.get_chat(link['id'])
	
	if not chat2:
		return await chat.send("An error occured, linked chat doesnt exist!")
	
	chat2.id = link['id']

	await chat2.invite(ctx.message.author)
	return await chat.send("Invited!")


@bot.command(help_category="tools",help_message=f"Take notes! Adds whatever you type to the chat's notes file!\n\nSay {prefix}notes to view the file.")
async def note(ctx,*args):
	chat = ctx.chat
	author = ctx.message.author
	data = await getChatData(ctx,chat)

	if not args:
		return await chat.send("Input a note to write!")

	data["notes"].append({"id":author.id,"nick":author.nick,"note":ctx.message.args[:100].replace("\n","")})

	await updateChatData(ctx,chat,data)
	return await chat.send("Recorded! 📝")


@bot.command(help_category="tools",help_message=f"Read the chat's notes! Read the next page by typing the page number. Ex: {prefix}notes 2\n\nSay {prefix}note to write to the file.")
async def notes(ctx,page = "",*args):
	chat = ctx.chat
	data = await getChatData(ctx,chat)

	if not page.isdigit():
		page = 1
	page = int(page)
	
	notes = data["notes"]

	chunk, page, max_page = paginate(notes,page)
	msg = f"Page {page}/{max_page} of notes:\n\n"

	for note in chunk:
		msg += f"{note['note']} - {note['nick']}\n\n"		

	return await chat.send(msg)


@bot.command(help_category="tools",help_message="Show the current members and the time they joined this chat")
async def members(ctx,page = "",*args):
	chat = ctx.chat
	data = await getChatData(ctx,chat)
	members = data["members"]

	print(len(members))

	if not page.isdigit():
		page = 1
	
	chunk, page, max_page = paginate(members,page,limit=20)
	msg = f"Page ({page}/{max_page})\n\n"

	for member in chunk:

		if chat.role == 0:

			if member["id"] in data["admins"]:
				if member["id"] == data["owner"]["id"]:
					msg+= "⭐ "
				else: msg += "🔷 "

			elif member["id"] in data["moderators"]:
				msg += "🔶 "

			elif member["id"] in data["vips"]:
				msg += "🏅 "
		
		msg += f"{member['nick']} - {days_to_str(member['joined'])}d\n"

	return await chat.send(msg)


@bot.command(help_category="tools",help_message="Show the chat's rules")
async def rules(ctx,*args):
	chat = ctx.chat
	data = await getChatData(ctx,chat)

	if ctx.chat.type == 1:
		return await chat.send("This is a DM, not a group chat.")

	if not data["rules"]:
		return await chat.send(f"There are no rules set. An admin can set rules by using the {prefix}setrules command")

	return await chat.send(data["rules"])


@bot.command(help_category="tools",help_message="View Current admins in this chat")
async def admins(ctx,*args):
	chat = ctx.chat
	data = await getChatData(ctx,chat)
	members = await chat.members()

	if ctx.chat.type == 1:
		return await chat.send("This is a DM, not a group chat.")

	admins = []
	moderators = []
	vips = []

	for admin in data["admins"]:
		for member in members:
			if member.id == admin and member.id != data["owner"]["id"]:
				admins.append(member.nick)

	for mod in data["moderators"]:
		for member in members:
			if member.id == mod and member.id != data["owner"]["id"]:
				moderators.append(member.nick)

	for mod in data["vips"]:
		for member in members:
			if member.id == mod and member.id != data["owner"]["id"]:
				vips.append(member.nick)

	msg = f"Owner:\n{data['owner']['nick']}\n\n"

	if admins:
		msg += f"Admins:\n"
	else:
		msg += f"There are no admins set. Set an admin by saying {ctx.bot.prefix}admin (username).\n"	

	for name in admins:
		msg += f"{name}\n"

	if moderators:
		msg+= f"\nMods:\n"
	else:
		msg += "\nThere are no mods set.\n"

	for name in moderators:
		msg += f"{name}\n"

	if vips:
		msg += "\nVIPs:\n"
	else:
		msg += "\nThere are no VIPs set.\n"

	for vip in vips:
		msg += f"{vip}\n"
	
	return await chat.send(msg)


@bot.command(help_category="tools",help_message="See all users banned from the chat. Use \"bans <page>\" to view other pages",aliases=["sb"])
async def bans(ctx,page="",*args):
	chat = ctx.chat

	if chat.type == 1:
		return
	
	data = await getChatData(ctx,chat)

	if not page.isdigit():
		page = 1
	page = int(page)

	bans = []

	for k, v in data["bans"].items():
		bans.append(v)

	chunk, page, max_page = paginate(bans,page,20)
	msg = f"🅿 = Permanent, 🆃 = Timeout\nBans page {page}/{max_page}\n\n"

	for user in chunk:
		banType = user['type']
		emoji = "🆃"
		if banType == "perm": emoji = "🅿"
		msg += f"{emoji} {user['nick']}\n"

	return await chat.send(msg)	


@bot.command(help_category="tools",help_message="See if a certain user is banned from the chat. Useful for large ban lists.",aliases=["sb"])
async def searchbans(ctx,username=None,*args):
	chat = ctx.chat

	if chat.type == 1:
		return

	if not username:
		return await chat.send("Input a username")
	
	data = await getChatData(ctx,chat)

	user = await ctx.user(username)
	if not user:
		return await chat.send("I couldn't find that user!")
	
	if data["bans"].get(user.id):
		return await chat.send(f"✅ {user.nick} is banned.")
	else:
		return await chat.send(f"❌ {user.nick} is not banned")


@bot.command(help_category="tools",help_message="Search for a user")
async def user(ctx,*args):
	chat = ctx.chat

	if not ctx.message.args:
		return await chat.send("Specify a username.")
	
	user = await ctx.user(args[0])

	if not user:
		return await chat.send("That user doesn't exist.")
	
	return await chat.send(f"https://ifunny.co/user/{user.og_nick.lower()}")


@bot.command(help_category="tools",help_message="Sends the user ID of an account's name")
async def id(ctx,*args):
	chat = ctx.chat

	if not ctx.message.args:
		return await chat.send("Specify a username.")
	
	user = await ctx.user(args[0])
	
	if not user:
		return await chat.send("That user doesn't exist.")
	
	return await chat.send(user.id)

					
@bot.command(help_category="tools",help_message="Sends the account's name of a user ID")
async def whois(ctx,*args):
	chat = ctx.chat	

	user = await ctx.user(args[0])	

	if not user:
		return await chat.send("This is not a user ID")
	
	return await chat.send(f"Username: {user.original_nick}\n\nhttps://ifunny.co/user/{user.original_nick}")


@bot.command(help_category="tools",help_message="Invites a user to the chat!",aliases=["summon","inv","add"])
async def invite(ctx,username=None,*args):
	chat = ctx.chat
	data = await getChatData(ctx,chat)
	author = ctx.message.author

	if not username:
		return

	if chat.type == 1:
		return await chat.send("You cant invite users to a dm.")
	
	user = await ctx.user(username)
	if not user:
		return await chat.send("That user doesnt exist")	
	
	if await chat.has_member(user):
		return await chat.send("That user is already in the chat")
	
	
	if chat.role == 0:
		if await shouldKick(ctx,data,user.id):

			if user.id in data["bans"]:
				if author.id in data["admins"]:
					if user.id not in data["whitelist"]:
						data["whitelist"].append(user.id)
						
				else: return await chat.send("That user is banned from this chat.")

			if data["lockdown"]:
				if author.id in data["admins"]:
					if user.id not in data["whitelist"]:
						data["whitelist"].append(user.id)

				else: return await chat.send("This chat is in a lockdown!")

			if data["no_pfp"] and not user.pfp:
				if author.id in data["admins"]:
					if user.id not in data["whitelist"]:
						data["whitelist"].append(user.id)

				else: return await chat.send("This chat has NoPFP enabled, and that user would be kicked upon joining!")
			
			if data["days"] > user.meme_experience.get("days"):
				if author.id in data["admins"]:
					if user.id not in data["whitelist"]:
						data["whitelist"].append(user.id)

				else: return await chat.send("That user's days is lower than the chat minimum")

			await updateChatData(ctx,chat,data)

	match await chat.check_invite(author,user):
		case 0:
			await chat.invite(user)
			return await chat.send("Invited!")
		case 1:
			return await chat.send("I cannot invite that user as their DMs are closed.")
		case 2:
			return await chat.send("I cannot invite that user as they are not friends with you.")


@bot.command(help_category="tools",help_message="Find the current online members of a chat!",aliases=["online"])
async def expose(ctx,*args):
	chat = ctx.chat
	data = await getChatData(ctx,chat)
	
	if chat.type == 1:
		return

	members = await chat.members()
	msg = "Users online:\n\n"

	for member in members:
		if member.status != 0:
			continue

		if chat.role == 0:

			if member.id in data["admins"]:
				if member.id == data["owner"]["id"]:
					msg += "⭐ "
				else: msg += "🔷 "

			if member.id in data["moderators"]:
				msg += "🔶 "

			if member.id in data["vips"]:
				msg += "🏅 "

		
		msg += f"{member.nick}\n"

	return await chat.send(msg)


@bot.command(hide_help=True)
async def chatid(ctx, *args):
	chat = ctx.chat
	await chat.send(ctx.chat.id)


@bot.command(hide_help=True, developer=True, aliases = ["bl"])
async def blacklist(ctx, *args):
	chat = ctx.chat

	if args:
		user = await ctx.user(args[0])
		if not user:
			return await chat.send("Input a valid username")		
		ctx.bot.blacklist(user)
		return await chat.send(f"{user.nick} has been blacklisted")
	
	return await chat.send(f"There are {len(ctx.bot.blacklist())} Blacklisted Users")


@bot.command(hide_help=True, developer=True, aliases = ["wl"])
async def whitelist(ctx, *args):
	chat = ctx.chat

	if args:
		user = await ctx.user(args[0])
		if not user:
			return await chat.send("Input a valid username")
		ctx.bot.whitelist(user)
		return await chat.send(f"{user.nick} has been whitelisted")


@bot.command(help_category="tools",help_message="Displays the chat's pfp")
async def chatpfp(ctx,*args):
	chat = ctx.chat
	cover = ctx.chat.cover

	if ctx.chat.type == 1:
		return await chat.send("This is a DM, not a group chat.")

	if not cover:
		return await chat.send("This chat doesnt have a cover!")
	
	cover = urlopen(cover)

	try:
		await chat.upload(cover)
	except Exception as e:
		return await chat.send(f"Error uploading image\n\n{e}")


@bot.command(hide_help=True)
async def ping(ctx,*args):
	ping = ctx.message.ping
	uptime = bot.seconds_to_str(int(time.time()) - bot.buff.start_time)
	return await ctx.chat.send(f"Pong! {ping}ms\n\nUptime: {uptime}")


@bot.command(hide_help=True,developer=True)
async def color(ctx,color=str,*args):
	chat = ctx.chat
	color = color.replace("#","")

	if len(color) != 6:
		return await chat.send("Invalid color code")

	headers = {
		"Host": "api.ifunny.mobi",
		"Content-Type": "application/json; charset=utf-8",
		"Accept": "video/mp4, image/jpeg",
		"Authorization": "Bearer " + bot.bearer,
		"Accept-Encoding": "gzip, deflate, br",
		"Accept-Language": "en_US",
		"Applicationstate": "1",
		"Content-Length": "18",
		"Ifunny-Project-Id": "iFunny",
		"User-Agent": "iFunny/8.41.11(24194) iPhone/16.3.1 (Apple; iPhone12,5)"
	}

	data = {'color':color}

	r = requests.patch(f"https://api.ifunny.mobi/v4/users/{bot.user_id}/nick_color",headers=headers,json=data)

	if r.status_code != 200:
		return await chat.send(f"An error has occured:\n\n{r.text}")

	return await chat.send("Done :)")


@bot.command(help_message="Send a message to me if you need help!")
async def support(ctx,*args):
	chat = ctx.chat
	author = ctx.author

	if not args: return await chat.send("Input a message to send!")

	webhook = "https://discord.com/api/webhooks/1219375108490268784/hj6p2bqngTtVFpO3lbwe0Sp4PAsMcG3vGcFIzPLHQdEgv7gSfX8nx1MNp25VdjWXmwAo"
	pfp = author.pfp
	
	if pfp:
		pfp = pfp.replace("quality:90","quality:100")
	else:
		pfp = "https://scropts.me/files/default_user.jpg"

	cover = ""

	if chat.type == 1:
		cover = pfp
	
	else:
		cover = chat.cover
		if not cover:
			cover = "https://scropts.me/files/default_cover.jpg"

	chatType = ""
	msg = ctx.message.args.replace("http","url: ").replace("\n"," ")

	match chat.type:
		case 1:
			chatType = "DM"
		case 2:
			chatType = "Private"
		case 3:
			chatType = "Public"
		case _:
			chatType = "IDK tbh"
	

	data = {
		"content": "<@&1219423565577850900>",
		"embeds": [{
			"title": "Support Message",
			"description": f"[Chatlink](https://ifunny.co/c/{chat.id})",
			"color": None,
			"fields": [
				{
				"name":"Title",
				"value": chat.title
				},
				{
				"name":"ID",
				"value": chat.id
				},
				{
				"name":"Type",
				"value": chatType
				},
			  	{
				"name":"Message",
				"value": msg
				}],
			"author": {
				"name": ctx.author.nick,
				"url": f"https://ifunny.co/user/{ctx.author.nick}",
				"icon_url": pfp
				},
			"timestamp": str(datetime.now(tz=timezone(timedelta(hours=-6))).isoformat()),
			"thumbnail": {
				"url": cover
				}}],
		"attachments": []
		}

	res = requests.post(webhook, json=data)

	if res.status_code == 204:
		return await chat.send("Successfully sent support message!")
	
	return await chat.send("There was an error sending that message...")


##### Events #####


# When a user is kicked
@bot.event()
async def user_kick(ctx):
	chat = ctx.chat
	user = ctx.user
	data = await getChatData(ctx,chat)

	for member in data["members"]:
		if user.id == member["id"]:
			data["members"].remove(member)

	if chat.role == 0 and chat.type != 1:
		if user.id not in data["admins"] and user.id not in data["moderators"]:
			if ratelimiter.check(user.id,chat.id):
				if data["antispam"] == "kick":
					await chat.send(f"{user.nick} was kicked for spam")
				if data["antispam"] == "ban":
					await chat.send(f"{user.nick} was banned for spam")

	await updateChatData(ctx,chat,data)
	cprint((f"{ctx.user.nick} was kicked from {ctx.chat.title}", "cyan"), (f"({ctx.chat.id})", "green"))


# When a user leaves
@bot.event()
async def user_leave(ctx):
	chat = ctx.chat
	user = ctx.user
	members = await chat.members()
	data = await getChatData(ctx,chat)

	# if an admin / moderator leaves the chat, they will also revoke their admin status
	if data["demote"]:

		if user.id in data["admins"] and user.id != data["owner"]["id"]:
			await chat.send(f"{user.nick} has lost their admin role, as demoting is currently turned on.\n\nTo turn off demotions, type {bot.prefix}demote off")
			data["admins"].remove(user.id)

		if user.id in data["moderators"]:
			await chat.send(f"{user.nick} has lost their moderator role, as demoting is currently turned on.\n\nTo turn off demotions, type {bot.prefix}demote off")
			data["moderators"].remove(user.id)

		if user.id in data["vips"]:
			await chat.send(f"{user.nick} has lost their VIP role, as demoting is currently turned on.\n\nTo turn off demotions, type {bot.prefix}demote off")
			data["vips"].remove(user.id)

	for member in data["members"]:
		if user.id == member["id"]:
			data["members"].remove(member)

	is_op = data.get("is_operator",False)
	
	if chat.role == 0 and user.id == data["owner"]["id"]:
		await asyncio.sleep(.5)
		await chat.invite(user)
		if is_op == False: await chat.send(f"Your chat is now being operated by {bot.username}. Now you can:\n\nAdd admins with {bot.prefix}admin\n\nAdd moderators with {bot.prefix}mod\n\nAdd VIPs with {bot.prefix}vip\n\nRemove members with {bot.prefix}kick\n\nAnd more! For more moderation commands, type {bot.prefix}help moderation\n\nFor chat customization type {bot.prefix}help customization\n\nYou can always regain ownership with {bot.prefix}unadmin {bot.username}")
		data["is_operator"] = True
		if user.id not in data["admins"]:
			data["admins"].append(user.id)

	for member in members:
		if member.role == 0 and member.id != bot.user_id:
			data["owner"] = {"id":member.id,"nick":member.nick}

	await updateChatData(ctx,chat,data)
	cprint((f"{ctx.user.nick} has left {ctx.chat.title} ", "cyan"), (f"({ctx.chat.id})", "green"))


# When a user joins
@bot.event()
async def user_join(ctx):
	chat = ctx.chat
	user = ctx.user
	data = await getChatData(ctx,chat)
	#user_data = await getUserData(ctx,user)
	kick = await shouldKick(ctx,data,user.id)
	
	if user.id in data["whitelist"] and kick == True:
		await chat.send(f"Not kicking {user.nick} as they were invited by an admin")
		data["whitelist"].remove(user.id)
		kick = False

	if kick: await chat.kick(user)

	data["members"].append({"id":user.id,"nick":user.nick,"joined":int(time.time())})

	if user.id == data["owner"]["id"]:
		if user.id not in data["admins"]:
			data["admins"].append(data["owner"]["id"])
		await chat.register_operator(user)

	if data["welcome"]:
		await chat.send(data["welcome"].replace("%user",user.nick))

	members = await chat.members()
	for member in members:
		if member.role == 0 and member.id != bot.user_id:
			data["owner"] = {"id":member.id,"nick":member.nick}

	await updateChatData(ctx,chat,data)
	cprint((f"{ctx.user.nick} has joined {ctx.chat.title} ", "cyan"), (f"({ctx.chat.id})", "green"))


# When a user sends an image, gif, or video attachment
@bot.event()
async def on_file(ctx):
	#await ctx.chat.send(ctx.message.url)
	cprint((f"{ctx.author.nick} sent an attachment in {ctx.chat.title}", "cyan"), (f"({ctx.chat.id})", "green"))


# When a user sends a message
@bot.event()
async def on_message(ctx):
	chat = ctx.chat
	message = ctx.message.args.replace("\n"," ")
	author = ctx.message.author

	if chat.type == 1:
		return cprint((f"{chat.title}", "cyan"),(f"{chat.id}","green"),(f"{author.nick}", "magenta"),(f"{message}", "blue"))

	data = await getChatData(ctx,chat)

	if data["title"] != chat.title:
		data["title"] = chat.title
		await updateChatData(ctx,chat,data)

	# If we have control over the chat
	if chat.role == 0 and chat.type != 1:

		# Antispam
		if author.id not in data["admins"] and author.id not in data["moderators"]:
			ratelimiter.log(author.id,chat.id)
			if ratelimiter.check(author.id,chat.id):
				match data["antispam"]:
					case "off": pass
					case "warn": await chat.send(f"{author.nick} should stop spamming...")
					case "kick": await chat.kick(author)
					case "ban": 
						await chat.kick(author)
						if author.id not in data["bans"]:
							data["bans"].append(author.id)
							await updateChatData(ctx,chat,data)

	cprint((f"{chat.title}", "cyan"),(f"{chat.id}","green"),(f"{author.nick}", "magenta"),(f"{message}", "blue"))


# When the bot gets invited to / joins a chat
@bot.event()
async def on_join(ctx):
	chat = ctx.chat

	if chat.type == 1:
		return
	
	data = await getChatData(ctx,chat)	

	members = await chat.members()

	for member in members:
		if member.role == 0 and member.id != bot.user_id:
			data["owner"] = {"id":member.id,"nick":member.nick}
			await updateChatData(ctx,chat,data)
	
	if chat.inviter:
		if chat.inviter.id != bot.user_id:
			await chat.send(f"{ctx.chat.inviter.nick} invited me! \nType {ctx.bot.prefix}help for info.")


# When the bot gets removed from a chat
@bot.event()
async def on_kick(ctx):
	chat = ctx.chat

	cprint((f"Removed From Chat", "magenta"),(chat.id, "yellow"))
	await delChatData(ctx,chat)

# Start the bot
if __name__ == "__main__":
	bot.run() 