## This file is part of himibot.
# For other plugins and more information, please visit:
# https://github.com/doodlehuang/himibot

from nonebot import get_plugin_config, CommandGroup
from nonebot.plugin import PluginMetadata
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot.adapters import Message
from himibot.plugins.keep_safe import is_banned

from .config import Config
from .metro import update_metro_data, list_stations
from .navigate import navigate_metro

__plugin_meta__ = PluginMetadata(
    name="inf-metro",
    description="",
    usage="",
    config=Config,
)

config = get_plugin_config(Config)
def safe_int_assert(value):
    try:
        assertion = int(value)
        return True
    except (ValueError, TypeError):
        return False
    
def soft_int_assert(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        return value
    
metro = CommandGroup('metro')
metro_help = metro.command('help')
metro_default = metro.command(tuple())
metro_update = metro.command('update', permission=SUPERUSER)
metro_liststations = metro.command('liststations', aliases={'metro ls'})

@metro_help.handle()
async def handle(bot, event):
    await metro_help.finish('DHW Inf 地铁导航工具 nonebot 版\n'
                            '导航：\n:metro <起点> <终点>\n'
                            '其中，起点和/或终点可以用坐标（x z），也可以用地铁站名\n'
                            '例如：\n:metro 100 100 临漪\n'
                            '列出所有地铁站名：\n:metro liststations/ls\n'
                            '更新站点数据（机器人管理员）：\n:metro update (url) \n'
                            '\n所有命令中，方括号内的内容表示必选参数，括号内的内容表示可选参数。')

@metro_default.handle()
async def handle(bot, event, args: Message = CommandArg()):
    args = args.extract_plain_text().split(' ')
    if event.message_type == 'group':
        if is_banned(event.group_id):
            return
    if not args:
        await metro_default.finish('请提供起点和终点坐标或站名。')
    await metro_default.finish(navigate_metro(*args))

@metro_update.handle()
async def handle(bot, event, args: Message = CommandArg()):
    if event.message_type == 'group':
        if is_banned(event.group_id):
            return
    if args:
        url = args.extract_plain_text()
        await metro_update.finish(update_metro_data(url))
    else:
        await metro_update.finish(update_metro_data())

@metro_liststations.handle()
async def handle(bot, event):
    if event.message_type == 'group':
        if is_banned(event.group_id):
            return
    await metro_liststations.finish(list_stations())