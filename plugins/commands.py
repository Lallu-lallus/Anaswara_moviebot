import os
import logging
import random
import asyncio
from Script import script
from pyrogram import Client, filters
from pyrogram.errors.exceptions.bad_request_400 import ChatAdminRequired
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from database.ia_filterdb import Media, get_file_details
from database.users_chats_db import db
from info import CHANNELS, ADMINS, AUTH_CHANNEL, CUSTOM_FILE_CAPTION, LOG_CHANNEL, PICS
from utils import get_size, is_subscribed, temp

logger = logging.getLogger(__name__)

MY_PIC = ["CAACAgIAAxkBAAIJzWJmRB8BlK9Hr1fmr5L3YjcTybemAAJUFgAC0HtBSfy5WNnzRlYoHgQ",
          "CAACAgIAAxkBAAIJz2JmRFB6q5QB-nzskiRu4a6OQtYFAAJEGQACCOHZSVKp6_XqghKoHgQ",
          "CAACAgIAAxkBAAIJ0WJmRGW06tWK38t6FehI8zjvAqwwAAJ0GQAC_cTJSSusPcMW_Z-lHgQ",
          "CAACAgIAAxkBAAIJ02JmRHnHrRNCDRKkN30I-9MnLdFjAAIpGAACE__ZSRXGCIP-uUsZHgQ",
          "CAACAgIAAxkBAAIJ1WJmRPSMtNovBAI4OEaYRblMjuz2AAKrGAACnK7YSSsNbIPRhqCrHgQ",
          "CAACAgIAAxkBAAIJ12JmRQgU5dFJ1zlWw9AcojUygNZEAAIxGAACHKzgSa63hlzSvPYgHgQ",
          "CAACAgIAAxkBAAIJ2WJmRSi0lUZYK5ulASqHbbIvoJ9kAAKOFQACJU3BSY8WTX7r0TbzHgQ",
          "CAACAgIAAxkBAAIJ22JmRT2kVdjTiDfQTqWR0FwfUUZCAALmFwAC8_aBSdRvya1MnMXRHgQ",
          "CAACAgIAAxkBAAIJ3WJmRVOgbK-HSXUS5RRieWMiJ9EPAALgFgAC8uXhSepcBaMKpvocHgQ",
          "CAACAgIAAxkBAAIJ32JmRW64ipODcXaqLVemUvBU5phAAALOGwACO3SBSoTI8zjsBQGuHgQ",
          "CAACAgIAAxkBAAIJ4WJmRYCJd5g4eAJUtHUeorF_oTzAAAJcGgACS4PZSWp63xHDwoUyHgQ",
          "CAACAgIAAxkBAAIJ42JmRZgUvdyWbPwToNDk9A8fH-sMAAI_GAACjI7JSb1MrpohVVXQHgQ",
          "CAACAgIAAxkBAAIJ5WJmRbRMj7QgvJxPkJx6pZWKxWY0AAL2GgACTrcRSeXI9W89ePowHgQ",
          "CAACAgIAAxkBAAIJ52JmRcTNw4xzyMYtOiW-D4AutbeFAAJkGAAC8bUQSZjj826eUmRrHgQ",
          "CAACAgIAAxkBAAIJ6WJmRdMcYdG3RGUVlrhN-kioFmQcAALOFwAC6Y7gSUi1pSJ_Okp9HgQ",
          "CAACAgIAAxkBAAIJ62JmReh47ERAAqaVelJuetpeL_R0AAL6FQACgb8QSU-cnfCjPKF6HgQ',
          "CAACAgIAAxkBAAIJ7WJmRfm-XGIRuxmHaGdllyP_ct7YAAL0EwACB3UQSTqMZ6ks08xgHgQ",
          "CAACAgIAAxkBAAIJ72JmRhACf4L7MkiInlGIAAHG5UnWYAAC9hoAAk63EUnlyPVvPXj6MB4E",
          "CAACAgIAAxkBAAIJ8WJmRjoosRbHcQIvXttKxdiX35LYAAK6FQACmOXASWDPbIbSEH5gHgQ",
          "CAACAgIAAxkBAAIJ82JmRoJKkiUwmGpS095Y8iZQXw_MAAJxAwACfvLFDJE5cyEs3k8bHgQ"
]     

@Client.on_message(filters.command("start"))
async def start(client, message):
    if message.chat.type in ['group', 'supergroup']:
        buttons = [
            [
                InlineKeyboardButton('𝚄𝙿𝙳𝙰𝚃𝙴𝚂', url='https://t.me/annaben_updates')
            ],
            [
                InlineKeyboardButton('𝙷𝙴𝙻𝙿', url=f"https://t.me/{temp.U_NAME}?start=help"),
            ]
            ]
        reply_markup = InlineKeyboardMarkup(buttons)
        await message.reply(script.START_TXT.format(message.from_user.mention if message.from_user else message.chat.title, temp.U_NAME, temp.B_NAME), reply_markup=reply_markup)
        await asyncio.sleep(2) # 😢 https://github.com/EvamariaTG/EvaMaria/blob/master/plugins/p_ttishow.py#L17 😬 wait a bit, before checking.
        if not await db.get_chat(message.chat.id):
            total=await client.get_chat_members_count(message.chat.id)
            await client.send_message(LOG_CHANNEL, script.LOG_TEXT_G.format(message.chat.title, message.chat.id, total, "Unknown"))       
            await db.add_chat(message.chat.id, message.chat.title)
        return 
    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id, message.from_user.first_name)
        await client.send_message(LOG_CHANNEL, script.LOG_TEXT_P.format(message.from_user.id, message.from_user.mention))
    if len(message.command) != 2:
        buttons = [[
            InlineKeyboardButton('𝐀𝐝𝐝 𝐌𝐞 𝐓𝐨 𝐔𝐫 𝐆𝐫𝐩', url='https://t.me/anaswaramovie_bot?startgroup=true')
            ],[
            InlineKeyboardButton('𝐇𝐞𝐥𝐩', callback_data='help'),
            InlineKeyboardButton('𝐒𝐞𝐚𝐫𝐜𝐡', switch_inline_query_current_chat='')
            ],[
            InlineKeyboardButton('𝐀𝐛𝐨𝐮𝐭', callback_data='about')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
         await bot.reply_sticker(
             sticker=random.choice(MY_PIC),
           # caption=script.START_TXT.format(message.from_user.mention, temp.U_NAME, temp.B_NAME),
            reply_markup=reply_markup
            #parse_mode='html'
        )
        return
    if AUTH_CHANNEL and not await is_subscribed(client, message):
        try:
            invite_link = await client.create_chat_invite_link(int(AUTH_CHANNEL))
        except ChatAdminRequired:
            logger.error("Make sure Bot is admin in Forcesub channel")
            return
        btn = [
            [
                InlineKeyboardButton(
                    "🤖 Join Updates Channel", url=invite_link.invite_link
                )
            ]
        ]

        if message.command[1] != "subscribe":
            btn.append([InlineKeyboardButton("𝚃𝚁𝚈 𝙰𝙶𝙰𝙸𝙽", callback_data=f"checksub#{message.command[1]}")])
        await client.send_message(
            chat_id=message.from_user.id,
            text="**Please Join My Updates Channel to use this Bot!**",
            reply_markup=InlineKeyboardMarkup(btn),
            parse_mode="markdown"
            )
        return
    if len(message.command) ==2 and message.command[1] in ["subscribe", "error", "okay", "help"]:
        buttons = [[
            InlineKeyboardButton('𝐀𝐝𝐝 𝐌𝐞 𝐓𝐨 𝐔𝐫 𝐆𝐫𝐩', url='https://t.me/anaswaramovie_bot?startgroup=true')
            ],[
            InlineKeyboardButton('𝐇𝐞𝐥𝐩', callback_data='help'),
            InlineKeyboardButton('𝐒𝐞𝐚𝐫𝐜𝐡', switch_inline_query_current_chat='')
            ],[
            InlineKeyboardButton('𝐀𝐛𝐨𝐮𝐭', callback_data='about')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
         await bot.reply_sticker(
             sticker=random.choice(MY_PIC),
           # caption=script.START_TXT.format(message.from_user.mention, temp.U_NAME, temp.B_NAME),
            reply_markup=reply_markup
            #parse_mode='html'
        )
        return
    file_id = message.command[1]
    files_ = await get_file_details(file_id)
    if not files_:
        return await message.reply('No such file exist.')
    files = files_[0]
    title = files.file_name
    size=get_size(files.file_size)
    f_caption=files.caption
    if CUSTOM_FILE_CAPTION:
        try:
            f_caption=CUSTOM_FILE_CAPTION.format(file_name=title, file_size=size, file_caption=f_caption)
        except Exception as e:
            print(e)
            f_caption=f_caption
    if f_caption is None:
        f_caption = f"{files.file_name}"
    await client.send_cached_media(
        chat_id=message.from_user.id,
        file_id=file_id,
        caption=f_caption,
        )
                    

@Client.on_message(filters.command('channel') & filters.user(ADMINS))
async def channel_info(bot, message):
           
    """Send basic information of channel"""
    if isinstance(CHANNELS, (int, str)):
        channels = [CHANNELS]
    elif isinstance(CHANNELS, list):
        channels = CHANNELS
    else:
        raise ValueError("Unexpected type of CHANNELS")

    text = '📑 **Indexed channels/groups**\n'
    for channel in channels:
        chat = await bot.get_chat(channel)
        if chat.username:
            text += '\n@' + chat.username
        else:
            text += '\n' + chat.title or chat.first_name

    text += f'\n\n**Total:** {len(CHANNELS)}'

    if len(text) < 4096:
        await message.reply(text)
    else:
        file = 'Indexed channels.txt'
        with open(file, 'w') as f:
            f.write(text)
        await message.reply_document(file)
        os.remove(file)


@Client.on_message(filters.command('logs') & filters.user(ADMINS))
async def log_file(bot, message):
    """Send log file"""
    try:
        await message.reply_document('TelegramBot.log')
    except Exception as e:
        await message.reply(str(e))

@Client.on_message(filters.command('delete') & filters.user(ADMINS))
async def delete(bot, message):
    """Delete file from database"""
    reply = message.reply_to_message
    if reply and reply.media:
        msg = await message.reply("Processing...⏳", quote=True)
    else:
        await message.reply('Reply to file with /delete which you want to delete', quote=True)
        return

    for file_type in ("document", "video", "audio"):
        media = getattr(reply, file_type, None)
        if media is not None:
            break
    else:
        await msg.edit('This is not supported file format')
        return

    result = await Media.collection.delete_one({
        'file_name': media.file_name,
        'file_size': media.file_size,
        'mime_type': media.mime_type
    })
    if result.deleted_count:
        await msg.edit('File is successfully deleted from database')
    else:
        await msg.edit('File not found in database')


@Client.on_message(filters.command('deleteall') & filters.user(ADMINS))
async def delete_all_index(bot, message):
    await message.reply_text(
        'This will delete all indexed files.\nDo you want to continue??',
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="YES", callback_data="autofilter_delete"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="CANCEL", callback_data="close_data"
                    )
                ],
            ]
        ),
        quote=True,
    )


@Client.on_callback_query(filters.regex(r'^autofilter_delete'))
async def delete_all_index_confirm(bot, message):
    await Media.collection.drop()
    await message.answer()
    await message.message.edit('Succesfully Deleted All The Indexed Files.')

