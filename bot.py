import discord
from discord import app_commands
from discord.ext import commands
import os
import json
import asyncio
from pathlib import Path
from dotenv import load_dotenv

from analyzer.deobfuscator import LuauDeobfuscator
from analyzer.report import generate_pdf_report
from dashboard.app import run_dashboard

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_CONFIG_FILE = "channel_config.json"

def load_channel_config():
    if Path(CHANNEL_CONFIG_FILE).exists():
        with open(CHANNEL_CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_channel_config(config):
    with open(CHANNEL_CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

channel_config = load_channel_config()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree


@bot.event
async def on_ready():
    print(f"Bot logged in as {bot.user} (ID: {bot.user.id})")
    try:
        synced = await tree.sync()
        print(f"Synced {len(synced)} slash command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")


@tree.command(name="set", description="このチャンネルをLuau解析チャンネルとして設定します")
@app_commands.checks.has_permissions(administrator=True)
async def set_channel(interaction: discord.Interaction):
    guild_id = str(interaction.guild_id)
    channel_id = interaction.channel_id
    channel_config[guild_id] = channel_id
    save_channel_config(channel_config)
    embed = discord.Embed(
        title="✅ チャンネル設定完了",
        description=f"<#{channel_id}> をLuau解析チャンネルとして設定しました。\nこのチャンネルに `.lua` または `.txt` ファイルを送信すると解析が実行されます。",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed)


@tree.command(name="status", description="現在設定されている解析チャンネルを確認します")
async def status(interaction: discord.Interaction):
    guild_id = str(interaction.guild_id)
    if guild_id in channel_config:
        ch_id = channel_config[guild_id]
        embed = discord.Embed(
            title="📋 解析チャンネル情報",
            description=f"現在の解析チャンネル: <#{ch_id}>",
            color=discord.Color.blue()
        )
    else:
        embed = discord.Embed(
            title="⚠️ 未設定",
            description="`/set` コマンドで解析チャンネルを設定してください。",
            color=discord.Color.orange()
        )
    await interaction.response.send_message(embed=embed)


@tree.command(name="unset", description="解析チャンネルの設定を解除します")
@app_commands.checks.has_permissions(administrator=True)
async def unset_channel(interaction: discord.Interaction):
    guild_id = str(interaction.guild_id)
    if guild_id in channel_config:
        del channel_config[guild_id]
        save_channel_config(channel_config)
        embed = discord.Embed(
            title="🗑️ 設定解除完了",
            description="解析チャンネルの設定を解除しました。",
            color=discord.Color.red()
        )
    else:
        embed = discord.Embed(
            title="⚠️ 未設定",
            description="解析チャンネルは設定されていません。",
            color=discord.Color.orange()
        )
    await interaction.response.send_message(embed=embed)


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    guild_id = str(message.guild.id) if message.guild else None
    if not guild_id:
        return

    if guild_id not in channel_config:
        return

    if message.channel.id != channel_config[guild_id]:
        return

    if not message.attachments:
        return

    for attachment in message.attachments:
        if not (attachment.filename.endswith(".lua") or attachment.filename.endswith(".txt")):
            continue

        processing_msg = await message.reply(
            embed=discord.Embed(
                title="⏳ 解析中...",
                description=f"`{attachment.filename}` を解析しています。しばらくお待ちください。",
                color=discord.Color.yellow()
            )
        )

        try:
            code_bytes = await attachment.read()
            code = code_bytes.decode("utf-8", errors="replace")

            deobfuscator = LuauDeobfuscator(code, attachment.filename)
            result = await deobfuscator.analyze()

            score_color = (
                discord.Color.green() if result["obfuscation_score"] < 30
                else discord.Color.orange() if result["obfuscation_score"] < 70
                else discord.Color.red()
            )

            embed = discord.Embed(
                title="🔍 Luau 解析レポート",
                color=score_color
            )
            embed.add_field(
                name="📁 ファイル名",
                value=f"`{attachment.filename}`",
                inline=True
            )
            embed.add_field(
                name="🔒 難読化スコア",
                value=f"`{result['obfuscation_score']}/100`",
                inline=True
            )
            embed.add_field(
                name="📊 解析サマリー",
                value=result["summary"],
                inline=False
            )

            checks = [
                ("GUI ツリー生成", result["checks"]["gui_tree"]),
                ("ScreenGui 解析", result["checks"]["screen_gui"]),
                ("RemoteEvent 解析", result["checks"]["remote_event"]),
                ("ModuleScript 解析", result["checks"]["module_script"]),
                ("loadstring 先取得", result["checks"]["loadstring"]),
                ("require 解析", result["checks"]["require"]),
                ("AST 変換", result["checks"]["ast"]),
                ("StyLua 自動整形", result["checks"]["stylua"]),
            ]
            checks_text = "\n".join(
                f"{'✅' if v else '❌'} {k}" for k, v in checks
            )
            embed.add_field(name="🧩 解析チェック項目", value=checks_text, inline=False)

            if result.get("ai_report"):
                ai_text = result["ai_report"]
                if len(ai_text) > 1024:
                    ai_text = ai_text[:1020] + "..."
                embed.add_field(name="🤖 AI 解析レポート", value=ai_text, inline=False)

            files_to_send = []

            readable_code = result.get("readable_code", "")
            if readable_code:
                readable_filename = attachment.filename.replace(".txt", ".lua")
                if not readable_filename.endswith(".lua"):
                    readable_filename += "_readable.lua"
                else:
                    readable_filename = readable_filename.replace(".lua", "_readable.lua")

                readable_bytes = readable_code.encode("utf-8")
                files_to_send.append(
                    discord.File(
                        fp=__import__("io").BytesIO(readable_bytes),
                        filename=readable_filename
                    )
                )

            pdf_path = generate_pdf_report(result, attachment.filename)
            if pdf_path and Path(pdf_path).exists():
                files_to_send.append(discord.File(fp=pdf_path, filename="report.pdf"))

            await processing_msg.delete()
            await message.reply(embed=embed, files=files_to_send)

        except Exception as e:
            await processing_msg.edit(
                embed=discord.Embed(
                    title="❌ 解析エラー",
                    description=f"解析中にエラーが発生しました:\n```{str(e)}```",
                    color=discord.Color.red()
                )
            )
            print(f"Error analyzing {attachment.filename}: {e}")

    await bot.process_commands(message)


async def main():
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, run_dashboard)
    await bot.start(DISCORD_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
