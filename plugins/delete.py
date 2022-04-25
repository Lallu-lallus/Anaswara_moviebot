import asyncio
from pyrogram import Client, filters
from pyrogram.types import (
	Message
	)
	
@Client.on_message(filters.command("del"))
async def del_msg(app, message: Message):
	if message.chat.type == "private":
		return await message.reply_to_message.delete()
	if message.chat.type == ["supergroup", "channel"]:
		chat_id = message.chat.id
		user_id = message.from_user.id if message.from_user else message.sender_chat.id
		reply = message.reply_to_message
		reply_id = reply.from_user.id if reply.from_user else reply.sender_chat.id
		
		if reply:
			user = await app.get_chat_member(chat_id, user_id)
			admin = ["administrator", "creator"]
			if user.status not in admin:
				await app.send_message(
					chat_id,
					text="Who the hell are you",
					reply_to_message=reply)
					
			else:
				try:
					await app.reply.delete()
					await app.send_message(
						"I've deleted the message"
						)
					await asyncio.sleep(5)
				except Exception as e:
					print(e)
					await message.reply(f"Failed to delete the message {e}")
		
		
		else:
			await message.reply(
				"Please reply a to a message"
				)
				
				
	else: 
		await message.reply("This command is not for you")
      

      	
