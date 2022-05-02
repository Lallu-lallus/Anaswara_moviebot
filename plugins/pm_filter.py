#Kanged From @TroJanZheX
import asyncio
import re
import ast
import pytz
import datetime
import os

from telegraph import upload_file
from pyrogram.errors.exceptions.bad_request_400 import MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty
from Script import script
import pyrogram
from database.connections_mdb import active_connection, all_connections, delete_connection, if_active, make_active, make_inactive
from info import ADMINS, AUTH_CHANNEL, AUTH_USERS, CUSTOM_FILE_CAPTION, AUTH_GROUPS, P_TTI_SHOW_OFF, IMDB, SINGLE_BUTTON, SPELL_CHECK_REPLY, IMDB_TEMPLATE
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram import Client, filters
from pyrogram.errors import FloodWait, UserIsBlocked, MessageNotModified, PeerIdInvalid
from utils import get_size, is_subscribed, get_poster, search_gagala, temp
from database.users_chats_db import db
from database.ia_filterdb import Media, get_file_details, get_search_results
from database.filters_mdb import(
   del_all,
   find_filter,
   get_filters,
)
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

BUTTONS = {}
SPELL_CHECK = {}
FILTER_MODE = {}
SPELL_MODE = True

SPELL_TXT = """⭕Hey ||{mention}||

⭕Couldn't find any results for {query}, Do you searched for this movie ?

⭕Title: {title}
⭕Genre: {genres}
⭕Year: {year}
⭕Rating: {rating}
"""


now = datetime.datetime.now()
tz = pytz.timezone('asia/kolkata')
your_now = now.astimezone(tz)
hour = your_now.hour
if 0 <= hour <12:
    lallus = "Gᴏᴏᴅ ᴍᴏʀɴɪɴɢ"
elif 12 <= hour <15:
    lallus = 'Gᴏᴏᴅ ᴀꜰᴛᴇʀɴᴏᴏɴ'
elif 15 <= hour <20:
    lallus = 'Gᴏᴏᴅ ᴇᴠᴇɴɪɴɢ'
else:
    lallus = 'Gᴏᴏᴅ ɴɪɢʜᴛ'

@Client.on_message(filters.group & filters.text & ~filters.edited & filters.incoming)
async def give_filter(client,message):
    k = await manual_filters(client, message)
    if k == False:
        await auto_filter(client, message)   

# Sticker ID
@Client.on_message(
    filters.private
    & ~filters.forwarded
    & ~filters.command(["start", "about", "help", "id"])
)
async def stickers(bot, msg):
    if msg.sticker:
        await msg.reply(f"This Sticker's ID is⚠️ `{msg.sticker.file_id}`", quote=True)

@Client.on_message(filters.photo & filters.private)
async def telegraph_upload(client, message):
    
    if not await db.is_user_exist(update.from_user.id):
	    await db.add_user(update.from_user.id)
    
    text = await update.reply_text(
        text="<code>Downloading to My Server ...</code>",
        disable_web_page_preview=True
    )
    media = await update.download()
    
    await text.edit_text(
        text="<code>Downloading Completed. Now I am Uploading to telegra.ph Link ...</code>",
        disable_web_page_preview=True
    )
    
    try:
        response = upload_file(media)
    except Exception as error:
        print(error)
        await text.edit_text(
            text=f"Error :- {error}",
            disable_web_page_preview=True
        )
        return
    
    try:
        os.remove(media)
    except Exception as error:
        print(error)
        return
    
    await text.edit_text(
        text=f"<b>Link :-</b> <code>https://telegra.ph{response[0]}</code>\n\n<b>Join :-</b> @FayasNoushad",
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(text="Open Link", url=f"https://telegra.ph{response[0]}"),
                    InlineKeyboardButton(text="Share Link", url=f"https://telegram.me/share/url?url=https://telegra.ph{response[0]}")
                ],
                [InlineKeyboardButton(text="⚙ Join Updates Channel ⚙", url="https://telegram.me/FayasNoushad")]
            ]
        )
    )    

@Client.on_message(filters.command('copy'))
async def copy_msg(client, message):
    userid = message.from_user.id if message.from_user else None
    if not userid:
        return await message.reply(f"You are anonymous admin. Use /connect {message.chat.id} in PM")
    chat_type = message.chat.type

    if chat_type == "private":
        grpid = await active_connection(str(userid))
        if grpid is not None:
            grp_id = grpid
            try:
                chat = await client.get_chat(grpid)
                title = chat.title
            except:
                await message.reply_text("Make sure I'm present in your group!!", quote=True)
                return
        else:
            await message.reply_text("I'm not connected to any groups!", quote=True)
            return

    elif chat_type in ["group", "supergroup"]:
        grp_id = message.chat.id
        title = message.chat.title

    else:
        return

    st = await client.get_chat_member(grp_id, userid)
    if (
            st.status != "administrator"
            and st.status != "creator"
            and str(userid) not in ADMINS
    ):
        return

    if not message.reply_to_message:
        await message.reply("Reply to any messsge to copy")
        return
    msg=message.reply_to_message
    try:
        await msg.copy(grp_id)
        await message.reply("Message Copied to your group Successfully")
    except Exception as e:
        print(e)

@Client.on_message(filters.command('autofilter'))
async def fil_mod(client, message):
      mode_on = ["yes", "on", "true"]
      mode_of = ["no", "off", "false"]

      try:
         args = message.text.split(None, 1)[1].lower()
      except:
         return await message.reply("Command is incomplete.")

      m = await message.reply("Processing...")

      if args in mode_on:
          FILTER_MODE[str(message.chat.id)] = "True"
          await m.edit("Auto filter enabled for this chat")

      elif args in mode_of:
          FILTER_MODE[str(message.chat.id)] = "False"
          await m.edit("Auto filter disabled for this chat")
      else:
          await m.edit("Use: `/autofilter on` or `/autofilter off`")

@Client.on_callback_query(filters.regex(r"^next"))
async def next_page(bot, query):

    ident, req, key, offset = query.data.split("_")
    if int(req) not in [query.from_user.id, 0]:
        return await query.answer("oKda", show_alert=True)
    try:
        offset = int(offset)
    except:
        offset = 0
    search = BUTTONS.get(key)
    if not search:
        await query.answer("You are using one of my old messages, please send the request again.",show_alert=True)
        return

    files, n_offset, total = await get_search_results(search, offset=offset, filter=True)
    try:
        n_offset = int(n_offset)
    except:
        n_offset = 0

    if not files:
        return
    if SINGLE_BUTTON:
        btn = [
            [
                InlineKeyboardButton(
                    text=f"🚀[{get_size(file.file_size)}] {file.file_name}", callback_data=f'files#{file.file_id}'
                ),
            ]
            for file in files
        ]

    else:
        btn = [
            [
                InlineKeyboardButton(
                    text=f"{file.file_name}", callback_data=f'files#{file.file_id}'
                ),
                InlineKeyboardButton(
                    text=f"{get_size(file.file_size)}",
                    callback_data=f'files_#{file.file_id}',
                ),
            ]
            for file in files
        ]

    btn.insert(0, 
        [
            InlineKeyboardButton(f'🔮 {search} 🔮', 'dupe')
        ]
    )
    btn.insert(1,
        [
            InlineKeyboardButton(f'📁 Files: {len(files)}', 'dupe'),
            InlineKeyboardButton(f'💫 Tips', 'tips')
        ]
    )

    if 0 < offset <= 10:
        off_set = 0
    elif offset == 0:
        off_set = None
    else:
        off_set = offset - 10
    if n_offset == 0:
        btn.append(
            [InlineKeyboardButton("⏪ BACK", callback_data=f"next_{req}_{key}_{off_set}"), InlineKeyboardButton(f"📃 Pages {round(int(offset)/10)+1} / {round(total/10)}", callback_data="pages")]
        )
    elif off_set is None:
        btn.append([InlineKeyboardButton(f"🗓 {round(int(offset)/10)+1} / {round(total/10)}", callback_data="pages"), InlineKeyboardButton("NEXT ⏩", callback_data=f"next_{req}_{key}_{n_offset}")])
    else:
        btn.append(
            [
                InlineKeyboardButton("⏪ BACK", callback_data=f"next_{req}_{key}_{off_set}"),
                InlineKeyboardButton(f"🗓 {round(int(offset)/10)+1} / {round(total/10)}", callback_data="pages"),
                InlineKeyboardButton("NEXT ⏩", callback_data=f"next_{req}_{key}_{n_offset}")
            ],
        )
    try:
        await query.edit_message_reply_markup( 
            reply_markup=InlineKeyboardMarkup(btn)
        )
    except MessageNotModified:
        pass
    await query.answer()

@Client.on_callback_query(filters.regex(r"^spolling"))
async def advantage_spoll_choker(bot, query):
    _, user, movie_ = query.data.split('#')
    if int(user) != 0 and query.from_user.id != int(user):
        return await query.answer("okDa", show_alert=True)
    if movie_  == "close_spellcheck":
        return await query.message.delete()
    movies = SPELL_CHECK.get(query.message.reply_to_message.message_id)
    if not movies:
        return await query.answer("You are clicking on an old button which is expired.", show_alert=True)
    movie = movies[(int(movie_))]
    await query.answer('Checking for Movie in database...')
    k = await manual_filters(bot, query.message, text=movie)
    if k==False:
        files, offset, total_results = await get_search_results(movie, offset=0, filter=True)
        if files:
            k = (movie, files, offset, total_results)
            await auto_filter(bot, query, k)
        else:
            k = await query.message.edit('This Movie Not Found In DataBase')
            await asyncio.sleep(10)
            await k.delete()


@Client.on_callback_query()
async def cb_handler(client: Client, query: CallbackQuery):
    if query.data == "close_data":
        await query.message.delete()
    elif query.data == "delallconfirm":
        userid = query.from_user.id
        chat_type = query.message.chat.type

        if chat_type == "private":
            grpid  = await active_connection(str(userid))
            if grpid is not None:
                grp_id = grpid
                try:
                    chat = await client.get_chat(grpid)
                    title = chat.title
                except:
                    await query.message.edit_text("Make sure I'm present in your group!!", quote=True)
                    return
            else:
                await query.message.edit_text(
                    "I'm not connected to any groups!\nCheck /connections or connect to any groups",
                    quote=True
                )
                return

        elif chat_type in ["group", "supergroup"]:
            grp_id = query.message.chat.id
            title = query.message.chat.title

        else:
            return

        st = await client.get_chat_member(grp_id, userid)
        if (st.status == "creator") or (str(userid) in ADMINS):    
            await del_all(query.message, grp_id, title)
        else:
            await query.answer("You need to be Group Owner or an Auth User to do that!",show_alert=True)

    elif query.data == "delallcancel":
        userid = query.from_user.id
        chat_type = query.message.chat.type

        if chat_type == "private":
            await query.message.reply_to_message.delete()
            await query.message.delete()

        elif chat_type in ["group", "supergroup"]:
            grp_id = query.message.chat.id
            st = await client.get_chat_member(grp_id, userid)
            if (st.status == "creator") or (str(userid) in ADMINS):
                await query.message.delete()
                try:
                    await query.message.reply_to_message.delete()
                except:
                    pass
            else:
                await query.answer("Thats not for you!!",show_alert=True)


    elif "groupcb" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]
        
        act = query.data.split(":")[2]
        hr = await client.get_chat(int(group_id))
        title = hr.title
        user_id = query.from_user.id

        if act == "":
            stat = "CONNECT"
            cb = "connectcb"
        else:
            stat = "DISCONNECT"
            cb = "disconnect"

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{stat}", callback_data=f"{cb}:{group_id}"),
                InlineKeyboardButton("DELETE", callback_data=f"deletecb:{group_id}")],
            [InlineKeyboardButton("BACK", callback_data="backcb")]
        ])

        await query.message.edit_text(
            f"Group Name : **{title}**\nGroup ID : `{group_id}`",
            reply_markup=keyboard,
            parse_mode="md"
        )
        return

    elif "connectcb" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]

        hr = await client.get_chat(int(group_id))

        title = hr.title

        user_id = query.from_user.id

        mkact = await make_active(str(user_id), str(group_id))

        if mkact:
            await query.message.edit_text(
                f"Connected to **{title}**",
                parse_mode="md"
            )
        else:
            await query.message.edit_text('Some error occured!!', parse_mode="md")
        return

    elif "disconnect" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]

        hr = await client.get_chat(int(group_id))

        title = hr.title
        user_id = query.from_user.id

        mkinact = await make_inactive(str(user_id))

        if mkinact:
            await query.message.edit_text(
                f"Disconnected from **{title}**",
                parse_mode="md"
            )
        else:
            await query.message.edit_text(
                f"Some error occured!!",
                parse_mode="md"
            )
        return
    elif "deletecb" in query.data:
        await query.answer()

        user_id = query.from_user.id
        group_id = query.data.split(":")[1]

        delcon = await delete_connection(str(user_id), str(group_id))

        if delcon:
            await query.message.edit_text(
                "Successfully deleted connection"
            )
        else:
            await query.message.edit_text(
                f"Some error occured!!",
                parse_mode="md"
            )
        return
    elif query.data == "backcb":
        await query.answer()

        userid = query.from_user.id

        groupids = await all_connections(str(userid))
        if groupids is None:
            await query.message.edit_text(
                "There are no active connections!! Connect to some groups first.",
            )
            return
        buttons = []
        for groupid in groupids:
            try:
                ttl = await client.get_chat(int(groupid))
                title = ttl.title
                active = await if_active(str(userid), str(groupid))
                act = " - ACTIVE" if active else ""
                buttons.append(
                    [
                        InlineKeyboardButton(
                            text=f"{title}{act}", callback_data=f"groupcb:{groupid}:{act}"
                        )
                    ]
                )
            except:
                pass
        if buttons:
            await query.message.edit_text(
                "Your connected group details ;\n\n",
                reply_markup=InlineKeyboardMarkup(buttons)
            )

    elif "alertmessage" in query.data:
        grp_id = query.message.chat.id
        i = query.data.split(":")[1]
        keyword = query.data.split(":")[2]
        reply_text, btn, alerts, fileid = await find_filter(grp_id, keyword)
        if alerts is not None:
            alerts = ast.literal_eval(alerts)
            alert = alerts[int(i)]
            alert = alert.replace("\\n", "\n").replace("\\t", "\t")
            await query.answer(alert,show_alert=True)

    if query.data.startswith("file"):
        FILE_CHANNEL_ID = int(-1001602436134)
        ident, file_id = query.data.split("#")
        files_ = await get_file_details(file_id)
        if not files_:
            return await query.answer('No such file exist.')
        files = files_[0]
        title = files.file_name
        size=get_size(files.file_size)
        f_caption=files.caption
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption=CUSTOM_FILE_CAPTION.format(file_name=title, file_size=size, file_caption=f_caption)
            except Exception as e:
                logger.exception(e)
            f_caption=f_caption
        if f_caption is None:
            f_caption = f"{files.file_name}"
            
        try:
            if AUTH_CHANNEL and not await is_subscribed(client, query):
                await query.answer(url=f"https://t.me/{temp.U_NAME}?start={file_id}")
                return
            elif P_TTI_SHOW_OFF:
                await query.answer(url=f"https://t.me/{temp.U_NAME}?start={file_id}")
                return
            else:
                send_file = await client.send_cached_media(
                    chat_id=FILE_CHANNEL_ID,
                    file_id=file_id,
                    caption=f_caption
                    )
                btn = [[
                    InlineKeyboardButton("♻️DOWNLOAD♻️", callback_data='send_file.link')
                    ],[
                    InlineKeyboardButton("🔰JOIN CHANNEL🔰", url='https://t.me/+mFIQaT9QxC1mMDI1')
                ]]
                reply_markup = InlineKeyboardMarkup(btn)
                bb = await query.message.reply_text(
                    text = f"Hi click the below link and download the movies🍿\n\nERROR? Click the join channel button and try again \n\n{send_file.link}",
                    reply_markup = reply_markup
                )
                await asyncio.sleep(300)
                await send_file.delete()
                await bb.delete()
        except UserIsBlocked:
            await query.answer('Unblock the bot mahn !',show_alert = True)
        except PeerIdInvalid:
            await query.answer(url=f"https://t.me/{temp.U_NAME}?start={file_id}")
        except Exception as e:
            await query.answer(url=f"https://t.me/{temp.U_NAME}?start={file_id}")

    elif query.data.startswith("checksub"):
        if AUTH_CHANNEL and not await is_subscribed(client, query):
            await query.answer("I Like Your Smartness, But Don't Be Oversmart 😒",show_alert=True)
            return
        ident, file_id = query.data.split("#")
        files_ = await get_file_details(file_id)
        if not files_:
            return await query.answer('No such file exist.')
        files = files_[0]
        title = files.file_name
        size=get_size(files.file_size)
        f_caption=files.caption
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption=CUSTOM_FILE_CAPTION.format(m = query.from_user.mention,lallus = lallus,file_name=title, file_size=size, file_caption=f_caption)
            except Exception as e:
                logger.exception(e)
                f_caption=f_caption
        if f_caption is None:
            f_caption = f"{title}"
        await query.answer()
        await client.send_cached_media(
            chat_id=query.from_user.id,
            file_id=file_id,
            caption=f_caption
            )

    elif query.data == "pages":
        await query.answer()
    elif query.data == "start":
        await query.message.delete()
        buttons = [[
            InlineKeyboardButton('𝐀𝐝𝐝 𝐌𝐞 𝐓𝐨 𝐔𝐫 𝐆𝐫𝐩', url='https://t.me/anaswaramovie_bot?startgroup=true')
            ],[
            InlineKeyboardButton('𝐇𝐞𝐥𝐩', callback_data='help'),
            InlineKeyboardButton('𝐒𝐞𝐚𝐫𝐜𝐡', switch_inline_query_current_chat='')
            ],[
            InlineKeyboardButton('𝐀𝐛𝐨𝐮𝐭', callback_data='about')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.send_sticker(
            sticker="CAACAgIAAxkBAAIJ6WJmRdMcYdG3RGUVlrhN-kioFmQcAALOFwAC6Y7gSUi1pSJ_Okp9HgQ",
            chat_id=query.message.chat.id,
            reply_markup=reply_markup
            #parse_mode='html'
        )
    elif query.data == "func":
        await query.message.delete()
        buttons = [[
            InlineKeyboardButton('  ᴀᴅᴍɪɴ  ', callback_data='admin'),
            InlineKeyboardButton('  ᴄᴏɴɴᴇᴄᴛ  ', callback_data='coct'),
            InlineKeyboardButton('  ғɪʟᴛᴇʀs  ', callback_data='auto_manual')
            ],[
            InlineKeyboardButton('  ɢᴛʀᴀɴs  ', callback_data='gtrans'),
            InlineKeyboardButton('  ɪɴғᴏ  ', callback_data='info'),
            InlineKeyboardButton('  ᴘᴀsᴛᴇ  ', callback_data='paste')
            ],[
            InlineKeyboardButton(' ☜ ↼_↼𝘽𝙖𝙘𝙠 ', callback_data='help'),
            InlineKeyboardButton(' ғᴏɴᴛ', callback_data='font'),
            InlineKeyboardButton(' 𝙉𝙚𝙭𝙩☞ﾟヮﾟ☞', callback_data='s')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.send_message(
            text=script.HELP_TXT.format(query.from_user.mention),
            chat_id=query.message.chat.id,
            reply_markup=reply_markup,
           # parse_mode='html'
        )
    elif query.data == "s":
        buttons = [[
            InlineKeyboardButton('  ᴘᴜʀɢᴇ  ', callback_data='purge'),
            InlineKeyboardButton('  ʀᴇsᴛʀɪᴄᴛ  ', callback_data='restric'),
            InlineKeyboardButton('  sᴇᴀʀᴄʜ  ', callback_data='search')
            ],[
            InlineKeyboardButton('  ᴛᴇʟᴇɢʀᴀᴘʜ  ', callback_data='tgraph'),
            InlineKeyboardButton('  ᴡʜᴏɪs  ', callback_data='whois'),
            InlineKeyboardButton('  ғᴜɴ  ', callback_data='fun')
            ],[
            InlineKeyboardButton(' ☜ ↼_↼𝘽𝙖𝙘𝙠 ', callback_data='func'),
            InlineKeyboardButton(' 𝐜𝐚𝐫𝐛𝐨𝐧 ', callback_data='carbon'),
            InlineKeyboardButton(' 𝙉𝙚𝙭𝙩☞ﾟヮﾟ☞', callback_data='p')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.HELP_TXT.format(query.from_user.mention),
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "p":
        buttons = [[
            InlineKeyboardButton('  ᴀʟɪᴠᴇ  ', callback_data='alive'),
            InlineKeyboardButton('  sᴏɴɢ  ', callback_data='song'),
            InlineKeyboardButton('  ᴊsᴏɴ  ', callback_data='json')
            ],[
            InlineKeyboardButton('  ᴘɪɴ  ', callback_data='pin'),
            InlineKeyboardButton('  ᴄᴏʀᴏɴᴀ  ', callback_data='corona'),
            InlineKeyboardButton('  sᴛɪᴄᴋᴇʀɪᴅ  ', callback_data='stickerid')
            ],[
            InlineKeyboardButton(' ☜ ↼_↼𝘽𝙖𝙘𝙠 ', callback_data='func'),
            InlineKeyboardButton(' 𝙉𝙚𝙭𝙩☞ﾟヮﾟ☞', callback_data='func')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.HELP_TXT.format(query.from_user.mention),
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "help":
        await query.message.delete()
        buttons= [[
            InlineKeyboardButton('𝐌𝐚𝐧𝐮𝐞𝐥 𝐅𝐢𝐥𝐭𝐞𝐫', callback_data= 'manualfilter'),
            InlineKeyboardButton('𝐀𝐮𝐭𝐨 𝐅𝐢𝐥𝐭𝐞𝐫', callback_data= 'autofilter')
            ],[
            InlineKeyboardButton('𝐇𝐞𝐥𝐩 𝐅𝐮𝐧𝐜𝐭𝐢𝐨𝐧𝐬', callback_data= 'func')
            ],[
            InlineKeyboardButton('𝐁𝐚𝐜𝐤', callback_data= 'start')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.send_sticker(
            sticker="CAACAgIAAxkBAAIJ6WJmRdMcYdG3RGUVlrhN-kioFmQcAALOFwAC6Y7gSUi1pSJ_Okp9HgQ",
            chat_id=query.message.chat.id,
            reply_markup=reply_markup,
            # parse_mode='html'
        )
    elif query.data == "about":
        await query.message.delete()
        buttons= [[
            InlineKeyboardButton('𝐬𝐭𝐚𝐭𝐮𝐬', callback_data='stats'),
            InlineKeyboardButton('𝐬𝐨𝐮𝐫𝐜𝐞', callback_data='source')
            ],[
            InlineKeyboardButton('𝐁𝐚𝐜𝐤', callback_data='start'),
            InlineKeyboardButton('𝐂𝐥𝐨𝐬𝐞', callback_data='close_data')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.send_message(
            text=script.ABOUT_TXT.format(query.from_user.mention),
            chat_id=query.message.chat.id,
            reply_markup=reply_markup,
            disable_web_page_preview=True,
            parse_mode='html'
        )
    elif query.data == "alive":
        await query.message.delete()
        buttons = [[
            InlineKeyboardButton('ʙᴀᴄᴋ', callback_data='help')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.send_message(
            text=script.ALIVE_TXT.format(query.from_user.mention),
            chat_id=query.message.chat.id,
            reply_markup=reply_markup,
            disable_web_page_preview=True,
            parse_mode='html'
        )
    elif query.data == "font":
        await query.message.delete()
        buttons = [[
            InlineKeyboardButton('ʙᴀᴄᴋ', callback_data='help')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.send_message(
            text=script.FONT_TXT.format(query.from_user.mention),
            chat_id=query.message.chat.id,
            reply_markup=reply_markup,
            disable_web_page_preview=True,
            parse_mode='html'
        )
    elif query.data == "carbon":
        await query.message.delete()
        buttons = [[
            InlineKeyboardButton('ʙᴀᴄᴋ', callback_data='help')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.send_message(
            text=script.CARBON_TXT.format(query.from_user.mention),
            chat_id=query.message.chat.id,
            reply_markup=reply_markup,
            disable_web_page_preview=True,
            parse_mode='html'
        )
    elif query.data == "whois":
        await query.message.delete()
        buttons = [[
            InlineKeyboardButton('ʙᴀᴄᴋ', callback_data='help')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.send_message(
            text=script.WHOIS_TXT.format(query.from_user.mention),
            chat_id=query.message.chat.id,
            reply_markup=reply_markup,
            disable_web_page_preview=True,
            parse_mode='html'
        )
    elif query.data == "source":
        await query.message.delete()
        buttons = [[
            InlineKeyboardButton('« Back', callback_data='about')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.send_message(
            text=script.SOURCE_TXT.format(query.from_user.mention),
            chat_id=query.message.chat.id,
            reply_markup=reply_markup,
            disable_web_page_preview=True,
            parse_mode='html'
        )
    elif query.data == "corona":
        await query.message.delete()
        buttons = [[
            InlineKeyboardButton('ʙᴀᴄᴋ', callback_data='help')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.send_message(
            text=script.CORONA_TXT.format(query.from_user.mention),
            chat_id=query.message.chat.id,
            reply_markup=reply_markup,
            disable_web_page_preview=True,
            parse_mode='html'
        )
    elif query.data == "reason":
        buttons = [[
            InlineKeyboardButton('𝐉𝐨𝐢𝐧 𝐂𝐡𝐚𝐧𝐧𝐞𝐥', url='https://t.me/cml_links2')
            ],[
            InlineKeyboardButton('𝐜𝐥𝐨𝐬𝐞', callback_data='close')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.send_message(
            text=script.REASON_TXT.format(query.from_user.mention),
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data == "stickerid":
        await query.message.delete()
        buttons = [[
            InlineKeyboardButton('ʙᴀᴄᴋ', callback_data='help')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.send_message(
            text=script.STICKER_TXT.format(query.from_user.mention),
            chat_id=query.message.chat.id,
            reply_markup=reply_markup,
            disable_web_page_preview=True,
            parse_mode='html'
        )
    elif query.data == "song":
        await query.message.delete()
        buttons = [[
            InlineKeyboardButton('ʙᴀᴄᴋ', callback_data='help')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.send_message(
            text=script.SONG_TXT.format(query.from_user.mention),
            chat_id=query.message.chat.id,
            reply_markup=reply_markup,
            disable_web_page_preview=True,
            parse_mode='html'
        )
    elif query.data == "manualfilter":
        await query.message.delete()
        buttons = [[
            InlineKeyboardButton('« Back', callback_data='auto_manual'),
            InlineKeyboardButton('Buttons »', callback_data='button')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.send_message(
            text=script.MANUALFILTER_TXT.format(query.from_user.mention),
            chat_id=query.message.chat.id,
            reply_markup=reply_markup,
            disable_web_page_preview=True,
            parse_mode='html'
        )
    elif query.data == "json":
        await query.message.delete()
        buttons = [[ 
            InlineKeyboardButton('ʙᴀᴄᴋ', callback_data='help')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.send_message(
            text=script.JSON_TXT.format(query.from_user.mention),
            chat_id=query.message.chat.id,
            reply_markup=reply_markup,
            disable_web_page_preview=True,
            parse_mode='html'
        )
    elif query.data == "pin":
        await query.message.delete()
        buttons = [[
            InlineKeyboardButton('ʙᴀᴄᴋ', callback_data='help')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.send_message(
            text=script.PIN_TXT.format(query.from_user.mention),
            chat_id=query.message.chat.id,
            reply_markup=reply_markup,
            disable_web_page_preview=True,
            parse_mode='html'
        )
    elif query.data == "button":
        await query.message.delete()
        buttons = [[
            InlineKeyboardButton('« Back', callback_data='manualfilter')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.send_message(
            text=script.BUTTON_TXT.format(query.from_user.mention),
            chat_id=query.message.chat.id,
            reply_markup=reply_markup,
            disable_web_page_preview=True,
            parse_mode='html'
        )
    elif query.data == "autofilter":
        await query.message.delete()
        buttons = [[
            InlineKeyboardButton('« Back', callback_data='auto_manual')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.send_message(
            text=script.AUTOFILTER_TXT.format(query.from_user.mention),
            chat_id=query.message.chat.id,
            reply_markup=reply_markup,
            disable_web_page_preview=True,
            parse_mode='html'
        )
    elif query.data == "auto_manual":
        await query.message.delete()
        buttons = [[
            InlineKeyboardButton('auto', callback_data='autofilter'),
            InlineKeyboardButton('manual', callback_data='manualfilter')
            ],[
            InlineKeyboardButton('« Back', callback_data='help'),
            InlineKeyboardButton('Close ✗', callback_data='close_data')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.send_message(
            text=script.AUTO_MANUEL_TXT.format(query.from_user.mention),
            chat_id=query.message.chat.id,
            reply_markup=reply_markup,
            disable_web_page_preview=True,
            parse_mode='html'
        )
    elif query.data == "fun":
        await query.message.delete()
        buttons = [[
            InlineKeyboardButton('ʙᴀᴄᴋ', callback_data='func')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.send_message(
            text=script.FUN_TXT.format(query.from_user.mention),
            chat_id=query.message.chat.id,
            reply_markup=reply_markup,
            disable_web_page_preview=True,
            parse_mode='html'
        )
    elif query.data == "coct":
        await query.message.delete()
        buttons = [[
            InlineKeyboardButton('« Back', callback_data='help')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.send_message(
            text=script.CONNCTION_TXT.format(query.from_user.mention),
            chat_id=query.message.chat.id,
            reply_markup=reply_markup,
            disable_web_page_preview=True,
            parse_mode='html'
        )
    elif query.data == "paste":
        await query.message.delete()
        buttons = [[
            InlineKeyboardButton('« Back', callback_data='help'),
            InlineKeyboardButton('Close ✗', callback_data='close_data')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.send_message(
            text=script.PASTE_TXT.format(query.from_user.mention),
            chat_id=query.message.chat.id,
            reply_markup=reply_markup,
            disable_web_page_preview=True,
            parse_mode='html'
        )
    elif query.data == "tgraph":
        await query.message.delete()
        buttons = [[
            InlineKeyboardButton('« Back', callback_data='help')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.send_message(
            text=script.TGRAPH_TXT.format(query.from_user.mention),
            chat_id=query.message.chat.id,
            reply_markup=reply_markup,
            disable_web_page_preview=True,
            parse_mode='html'
        )
    elif query.data == "info":
        await query.message.delete()
        buttons = [[
            InlineKeyboardButton('« Back', callback_data='help')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.send_message(
            text=script.INFO_TXT.format(query.from_user.mention),
            chat_id=query.message.chat.id,
            reply_markup=reply_markup,
            disable_web_page_preview=True,
            parse_mode='html'
        )
    elif query.data == "search":
        await query.message.delete()
        buttons = [[
            InlineKeyboardButton('« Back', callback_data='help')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.send_message(
            text=script.SEARCH_TXT.format(query.from_user.mention),
            chat_id=query.message.chat.id,
            reply_markup=reply_markup,
            disable_web_page_preview=True,
            parse_mode='html'
        )
    elif query.data == "gtrans":
        await query.message.delete()
        buttons = [[
            InlineKeyboardButton('« Back', callback_data='help'),
            InlineKeyboardButton('lang codes', url='https://cloud.google.com/translate/docs/languages')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.send_message(
            text=script.GTRANS_TXT.format(query.from_user.mention),
            chat_id=query.message.chat.id,
            reply_markup=reply_markup,
            disable_web_page_preview=True,
            parse_mode='html'
        )
    elif query.data == "admin":
        await query.message.delete()
        buttons = [[
            InlineKeyboardButton('« Back', callback_data='help')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.send_message(
            text=script.ADMIN_TXT.format(query.from_user.mention),
            chat_id=query.message.chat.id,
            reply_markup=reply_markup,
            disable_web_page_preview=True,
            parse_mode='html'
        )
    elif query.data == "zombies":
        await query.message.delete()
        buttons = [[
            InlineKeyboardButton('« Back', callback_data='help')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.send_message(
            text=script.ZOMBIES_TXT.format(query.from_user.mention),
            chat_id=query.message.chat.id,
            reply_markup=reply_markup,
            disable_web_page_preview=True,
            parse_mode='html'
        )
    elif query.data == "purge":
        await query.message.delete()
        buttons = [[
            InlineKeyboardButton('« Back', callback_data='help')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.send_message(
            text=script.PURGE_TXT.format(query.from_user.mention),
            chat_id=query.message.chat.id,
            reply_markup=reply_markup,
            disable_web_page_preview=True,
            parse_mode='html'
        )
    elif query.data == "restric":
        await query.message.delete()
        buttons = [[
            InlineKeyboardButton('« Back', callback_data='help')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.send_message(
            text=script.RESTRIC_TXT.format(query.from_user.mention),
            chat_id=query.message.chat.id,
            reply_markup=reply_markup,
            disable_web_page_preview=True,
            parse_mode='html'
        )
    elif query.data == "stats":
        await query.message.delete()
        buttons = [[
            InlineKeyboardButton('« Back', callback_data='about'),
            InlineKeyboardButton('Refresh ⧖', callback_data='rfrsh')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        m=await query.message.reply_text("▣▢▢")
        n=await m.edit("▣▣▢")
        o=await n.edit("▣▣▣")
        await asyncio.sleep(1)
        await o.delete()
        total = await Media.count_documents()
        users = await db.total_users_count()
        chats = await db.total_chat_count()
        monsize = await db.get_db_size()
        free = 536870912 - monsize
        monsize = get_size(monsize)
        free = get_size(free)
        await query.message.edit_text(
            text=script.STATUS_TXT.format(total, users, chats, monsize, free),
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            parse_mode='html'
        )


    elif query.data == "rfrsh":
        await query.answer("Fetching MongoDb DataBase")
        buttons = [[
            InlineKeyboardButton('« Back', callback_data='about'),
            InlineKeyboardButton('Refresh ⧖', callback_data='rfrsh')
        ]]
    

async def auto_filter(client, msg, spoll=False):
    if not spoll:
        message = msg
        if re.findall("((^\/|^,|^!|^\.|^[\U0001F600-\U000E007F]).*)", message.text):
            return
        if 2 < len(message.text) < 100:
            search = message.text
            files, offset, total_results = await get_search_results(search.lower(), offset=0, filter=True)
            if not files:
                if SPELL_MODE:  
                    reply = search.replace(" ", "+")
                    reply_markup = InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔮IMDB🔮", url=f"https://imdb.com/find?q={reply}"),
                        InlineKeyboardButton("🪐 Reason", callback_data="reason")
                    ]])
                    imdb=await get_poster(search)
                    if imdb and imdb.get('poster'):
                        del3 = await message.reply_photo(photo=imdb.get('poster'), caption=SPELL_TXT.format(mention=message.from_user.mention, query=search, title=imdb.get('title'), genres=imdb.get('genres'), year=imdb.get('year'), rating=imdb.get('rating'), short=imdb.get('short_info'), url=imdb['url']), reply_markup=reply_markup) 
                        asyncio.sleep(600)
                        del3.delete()
                        message.delete()
                        return
                    else:
                        return
                else:
                    return
        else:
            return
    else:
        message = msg.message.reply_to_message # msg will be callback query
        search, files, offset, total_results = spoll
    if SINGLE_BUTTON:
        btn = [
            [
                InlineKeyboardButton(
                    text=f"[{get_size(file.file_size)}] {file.file_name}", callback_data=f'files#{file.file_id}'
                ),
            ]
            for file in files
        ]
    else:
        btn = [
            [
                InlineKeyboardButton(
                    text=f"{file.file_name}",
                    callback_data=f'files#{file.file_id}',
                ),
                InlineKeyboardButton(
                    text=f"{get_size(file.file_size)}",
                    callback_data=f'files_#{file.file_id}',
                ),
            ]
            for file in files
        ]

    if offset != "":
        key = f"{message.chat.id}-{message.message_id}"
        BUTTONS[key] = search
        req = message.from_user.id if message.from_user else 0
        btn.append(
            [InlineKeyboardButton(text=f"🗓 1/{round(int(total_results)/10)}",callback_data="pages"), InlineKeyboardButton(text="NEXT ⏩",callback_data=f"next_{req}_{key}_{offset}")]
        )
    else:
        btn.append(
            [InlineKeyboardButton(text="🗓 1/1",callback_data="pages")]
        )
    imdb = await get_poster(search, file=(files[0]).file_name) if IMDB else None
    if imdb:
        cap = IMDB_TEMPLATE.format(
            query = search, 
            title = imdb['title'], 
            votes = imdb['votes'], 
            aka = imdb["aka"],
            seasons = imdb["seasons"],
            box_office = imdb['box_office'], 
            localized_title = imdb['localized_title'],
            kind = imdb['kind'], 
            imdb_id = imdb["imdb_id"], 
            cast = imdb["cast"], 
            runtime = imdb["runtime"], 
            countries = imdb["countries"],
            certificates = imdb["certificates"], 
            languages = imdb["languages"],
            director = imdb["director"], 
            writer = imdb["writer"], 
            producer = imdb["producer"], 
            composer = imdb["composer"], 
            cinematographer = imdb["cinematographer"], 
            music_team = imdb["music_team"], 
            distributors = imdb["distributors"],
            release_date = imdb['release_date'], 
            year = imdb['year'],
            genres = imdb['genres'], 
            poster = imdb['poster'],
            plot = imdb['plot'],
            rating = imdb['rating'], 
            url = imdb['url'],
            **locals()
        )
    else:
        cap = f"Here is what i found for your query {search}"
    if imdb and imdb.get('poster'):
        try:
            dell = await message.reply_photo(photo=imdb.get('poster'), caption=cap, reply_markup=InlineKeyboardMarkup(btn))
            await asyncio.sleep(600)
            await dell.edit(f"⚙️ Filter For {search} Closed 🗑️")
        except (MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty):
            pic = imdb.get('poster')
            poster = pic.replace('.jpg', "._V1_UX360.jpg")
            del = await message.reply_photo(photo=poster, caption=cap, reply_markup=InlineKeyboardMarkup(btn))
            await asyncio.sleep(600)
            await del.edit(f"⚙️ Filter For {search} Closed 🗑️")
        except Exception as e:
            logger.exception(e)
            del1 = await message.reply_text(cap, reply_markup=InlineKeyboardMarkup(btn))
            await asyncio.sleep(600)
            await del1.edit(f"⚙️ Filter For {search} Closed 🗑️")
    else:
        del2 = await message.reply_text(cap, reply_markup=InlineKeyboardMarkup(btn))
         await asyncio.sleep(600)
         await del2.edit(f"⚙️ Filter For {search} Closed 🗑️")
    if spoll:
        await msg.message.delete()
      
async def manual_filters(client, message, text=False):
    group_id = message.chat.id
    name = text or message.text
    reply_id = message.reply_to_message.message_id if message.reply_to_message else message.message_id
    keywords = await get_filters(group_id)
    for keyword in reversed(sorted(keywords, key=len)):
        pattern = r"( |^|[^\w])" + re.escape(keyword) + r"( |$|[^\w])"
        if re.search(pattern, name, flags=re.IGNORECASE):
            reply_text, btn, alert, fileid = await find_filter(group_id, keyword)

            if reply_text:
                reply_text = reply_text.replace("\\n", "\n").replace("\\t", "\t")

            if btn is not None:
                try:
                    if fileid == "None":
                        if btn == "[]":
                            await client.send_message(group_id, reply_text, disable_web_page_preview=True)
                        else:
                            button = eval(btn)
                            await client.send_message(
                                group_id, 
                                reply_text,
                                disable_web_page_preview=True,
                                reply_markup=InlineKeyboardMarkup(button),
                                reply_to_message_id = reply_id
                            )
                    elif btn == "[]":
                        await client.send_cached_media(
                            group_id,
                            fileid,
                            caption=reply_text or "",
                            reply_to_message_id = reply_id
                        )
                    else:
                        button = eval(btn) 
                        await message.reply_cached_media(
                            fileid,
                            caption=reply_text or "",
                            reply_markup=InlineKeyboardMarkup(button),
                            reply_to_message_id = reply_id
                        )
                except Exception as e:
                    logger.exception(e)
                break
    else:
        return False
