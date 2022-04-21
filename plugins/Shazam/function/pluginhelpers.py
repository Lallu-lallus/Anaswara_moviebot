import os
import asyncio
import math
import shlex
import sys
import time
import traceback
from functools import wraps
from typing import Callable, Coroutine, Dict, List, Tuple, Union
import aiohttp
from PIL import Image
from pyrogram import Client as pbot
from pyrogram.errors import FloodWait, MessageNotModified
from pyrogram.types import Chat, Message, User


async def fetch_audio(client, message):
    time.time()
    if not message.reply_to_message:
        await message.reply("Reply To A Video / Audio.")
        return
    warner_stark = message.reply_to_message
    if warner_stark.audio is None and warner_stark.video is None:
        await message.reply("`Format Not Supported`")
        return
    if warner_stark.video:
        lel = await message.reply("`Video Detected, Converting To Audio !`")
        warner_bros = await message.reply_to_message.download()
        stark_cmd = f"ffmpeg -i {warner_bros} -map 0:a riya.mp3"
        await runcmd(stark_cmd)
        final_warner = "riya.mp3"
    elif warner_stark.audio:
        final_warner = await message.reply_to_message.download()
    await lel.delete()
    return final_warner

async def edit_or_reply(message, text, parse_mode="md"):
    if message.from_user.id:
        if message.reply_to_message:
            kk = message.reply_to_message.message_id
            return await message.reply_text(
                text, reply_to_message_id=kk, parse_mode=parse_mode
            )
        return await message.reply_text(text, parse_mode=parse_mode)
    return await message.edit(text, parse_mode=parse_mode)


async def runcmd(cmd: str) -> Tuple[str, str, int, int]:
    """run command in terminal"""
    args = shlex.split(cmd)
    process = await asyncio.create_subprocess_exec(
        *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    return (
        stdout.decode("utf-8", "replace").strip(),
        stderr.decode("utf-8", "replace").strip(),
        process.returncode,
        process.pid,
    )

