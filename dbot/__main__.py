import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.oauth2 import SpotifyOAuth
import os
import discord
from discord.ext import commands
from discord import app_commands
import requests
import uuid
from mutagen.mp3 import MP3
import asyncio
import queue
import requests
import base64
import json

client_id = os.environ["SPOTIFY_CLIENT_ID"]
client_secret = os.environ["SPOTIFY_CLIENT_SECRET"]
refresh_token = os.environ["SPOTIFY_REFLESH_TOKEN"]
credentials = base64.b64encode(f'{client_id}:{client_secret}'.encode('utf-8')).decode('utf-8') # クライアントIDとクライアントシークレットをBase64エンコード
response = requests.post(
            'https://accounts.spotify.com/api/token',
            headers={
                'Authorization': f'Basic {credentials}',
            },
            data={
                'refresh_token': refresh_token,
                'grant_type': 'refresh_token',
            },
)

# レスポンスから新しいアクセストークンを取得
access_token = response.json()["access_token"]
sp = spotipy.Spotify(access_token)

def get_token():
        # グローバル変数を宣言（これやらないと書き換えられない）
        global access_token     # こいつは将来的に環境変数で管理したほうが楽そう
        global sp
        # ヘッダーにクライアントIDとシークレットIDをBase64エンコードしたやつ
        # パラメータはSpotifyのURL叩いて手に入ったCodeを使用した下記コマンドで手に入れる
        # curl --data "code=手に入れたコード" --data "client_id=クライアントID" --data "client_secret=クライアントシークレット" --data "redirect_uri=設定したURL" --data "grant_type=authorization_code" https://accounts.spotify.com/api/token
        response = requests.post(
            'https://accounts.spotify.com/api/token',
            headers={
                'Authorization': f'Basic {credentials}',
            },
            data={
                'refresh_token': refresh_token,
                'grant_type': 'refresh_token',
            },
        )

        # レスポンスから新しいアクセストークンを取得
        access_token = response.json()["access_token"]
        sp = spotipy.Spotify(access_token) # 新規取得したアクセストークンで再ログイン

play_queue = queue.Queue()
audio_name = 'music_name'
locate_str = 'JP'

my_id = os.environ["SPOTIFY_CLIENT_ID"]
my_secret = os.environ["SPOTIFY_CLIENT_SECRET"]
TOKEN = os.environ["BOT_TOKEN"]
APPLICATION_ID = os.environ["APPLICATION_ID"]
scope = 'user-read-playback-state,playlist-read-private,user-modify-playback-state'

client = discord.Client(intents = discord.Intents.all())
intents = discord.Intents.default()
intents.message_content = True
tree = app_commands.CommandTree(client)



def Spotify_Search(Search_query,mode):
    global locate_str
    get_token()
    track_info = sp.search(q=f'{Search_query}', limit=1, offset=0, type='track', market=f'{locate_str}') #sp.search(search_str)
    if mode == 1:
        lz_uri = track_info['tracks']
        lz_uri = lz_uri['items']
        lz_uri = lz_uri[0]
        lz_uri = lz_uri['preview_url']
        return lz_uri
    elif mode == 2:
        #URLの取得
        url = track_info['tracks']
        url = url['items']
        url = url[0]
        url = url['external_urls']
        url = url['spotify']
        return url
    elif mode == 3:
        lz_name = track_info['tracks']
        lz_name = lz_name['items']
        lz_name = lz_name[0]
        lz_name = lz_name['name']
        return lz_name
    else:
        pass

def mutagen_length(path):
    try:
        audio = MP3(path)
        length = audio.info.length
        return length
    except:
        return None

async def play_next(guild,Discordclient):
    # 再生キューから次の曲を取得
    if not play_queue.empty():
        filename, audio_name = play_queue.get()
        guild.voice_client.play(discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(f'./music/{filename}.mp3'),volume=0.2), after=lambda e: asyncio.run_coroutine_threadsafe(play_next(guild,Discordclient), client.loop))
        try:
            audio_name = Spotify_Search(audio_name,3)
        finally:
            pass
        await Discordclient(activity = discord.Activity(name=str(f"🎵 {audio_name}"), type=2))
        return audio_name
    else:
        await Discordclient(activity = discord.CustomActivity(name=str('まだ何も再生されていません'), type=1))


@client.event
async def on_ready():
    # この関数はBotの起動準備が終わった際に呼び出されます
    print('{0.user}'.format(client) ,"がログインしました",flush=True)
    await client.change_presence(activity = discord.CustomActivity(name=str('まだ何も再生されていません'), type=1))
    await tree.sync()#スラッシュコマンドを同期

# VCに誰もいなくなった時の処理
@client.event
async def on_voice_state_update(member, before, after):
    if before.channel is not None:
        if len(before.channel.members) == 1 and before.channel.members[0] == client.user:
            await before.channel.members[0].move_to(None)  

    
@tree.command(name="help",description="Botの説明を表示します。")
async def test_command(interaction: discord.Interaction):
        embed = discord.Embed(title="使用方法",description="基本的にはこのBotではコマンドを使用する必要はありません。")
        embed.add_field(name='概要', inline=False ,value='')
        embed.add_field(name='「@BMA 曲名」と送信すると、自動であなたがいるVCに参加し、指定の曲名の音楽を再生します。', value='')
        embed.add_field(name='コマンド', inline=False ,value='')
        embed.add_field(name='`/bye`', value='VCから退出させます（VCに人がいなくなったときに勝手に退出するので、普段は使用する必要はありません。）')
        embed.add_field(name='`/help`', value='Botの説明を表示します。')
        embed.add_field(name='`&url`', value='リクエストを送信したメッセージに対してリプライを行うと、再生した楽曲の詳細について教えてくれます。')
        embed.add_field(name='`/skip`', value='次の曲にスキップします。')
        await interaction.response.send_message(embed=embed,ephemeral=True)

@tree.command(name="skip",description="次の曲にスキップします。")
async def test_command(interaction: discord.Interaction):
    if interaction.guild.voice_client is None:
        await interaction.response.send_message('現在何も再生されていません！')
        return
    if interaction.guild.voice_client.is_playing():
        if not play_queue.empty():
            interaction.guild.voice_client.stop()
            audio_name = await play_next(interaction.guild,client.change_presence)
            await interaction.response.send_message('スキップします')
            await client.change_presence(activity = discord.Activity(name=str(f"🎵 {audio_name}"), type=2))
        else:
            await interaction.response.send_message('次の曲はありません')
    else:
        await interaction.response.send_message('現在何も再生されていません！')

@tree.command(name="bye",description="VCから退出させます（VCに人がいなくなったときに勝手に退出するので、普段は使用する必要はありません。）")
async def test_command(interaction: discord.Interaction):
    if interaction.guild.voice_client is None:
        await interaction.response.send_message("退出済みです")
        return

    # 切断する
    await interaction.guild.voice_client.disconnect()
    await interaction.response.send_message("VCを退出します")
    return

    

@client.event
async def on_message_delete(message):
    if message.guild.voice_client is None:
        return
    if f'<@{APPLICATION_ID}>' in message.content:
        if message.guild.voice_client.is_playing():
                message.guild.voice_client.stop()
                await message.channel.send(content='リクエストメッセージが削除されたため、再生を停止しました！',delete_after=5)
                if not play_queue.empty():
                    await play_next(message.guild,client.change_presence)

@client.event
async def on_message(message):
    # メッセージの送信者がbotだった場合は無視する
    if message.author.bot:
        return
    # リクエストメッセージにリプライしたらその曲のＵＲＬ取得するよ
    if message.author != client and message.content == '&url':
        msg = None
        # リプライ元のメッセージを取得。取得に失敗した場合はリプライをしていないため、使い方のアドバイスを返す
        try:
            msg = await message.channel.fetch_message(message.reference.message_id)
        finally:
            if msg == None:
                embed = discord.Embed(title="このコマンドは、リクエストメッセージにリプライして使用する必要があります！",description="リクエストメッセージとは、「@BMA 曲名」というフォーマットのメッセージのことです。",color=0xff0000)
                await message.reply(embed=embed)
                return
        # ベータのBMAに対するURLコマンドは無視
        if "<@1194471332558147614>" in msg.content :
            return

        if not f'<@{APPLICATION_ID}>' in msg.content:
            embed = discord.Embed(title="このコマンドは、リクエストメッセージにリプライして使用する必要があります！",description="リクエストメッセージとは、「@BMA 曲名」というフォーマットのメッセージのことです。",color=0xff0000)
            await message.reply(embed=embed)
            return
        elif f'<@{APPLICATION_ID}>' in msg.content:
            query_words = msg.content.replace(f'<@{APPLICATION_ID}> ','').replace(f'<@{APPLICATION_ID}>','')
            SpotifyOpenURL = Spotify_Search(query_words,2)
            await message.reply(f'{SpotifyOpenURL}')
            return
        else:
            embed = discord.Embed(title="このコマンドは、リクエストメッセージにリプライして使用する必要があります！",description="リクエストメッセージとは、「@BMA 曲名」というフォーマットのメッセージのことです。",color=0xff0000)
            await message.reply(embed=embed)
            return

    # 音声再生
    if f'<@{APPLICATION_ID}>' in message.content:
        audio_name = message.content.replace(f'<@{APPLICATION_ID}> ','').replace(f'<@{APPLICATION_ID}>','')
        if audio_name.replace(' ','') == '':
            await message.reply('こんにちは！使い方を知りたい場合は、`/help`コマンドを実行してください！')
            return
        if message.author.voice is None:
            await message.reply("先にVCに参加してください")
            return
        elif message.guild.voice_client is None:
            await message.author.voice.channel.connect() # ボイスチャンネルに接続する
        elif message.guild.voice_client:
            await message.guild.voice_client.move_to(message.author.voice.channel)
        else:
            await message.reply("VCに参加できません")
            return
        music_url = Spotify_Search(audio_name,1)

        if music_url == None:
            await message.reply(f'「{audio_name}」という曲は見つかりませんでした...\nアーティスト名などを含めてリクエストすると見つかるかもしれません！')
            return
        responce = requests.get(music_url)
        filename = uuid.uuid4()
        with open(f'./music/{filename}.mp3','wb') as file:
            file.write(responce.content)
        
        # 再生キューに追加
        play_queue.put((filename,audio_name))

        # 再生中でなければ音楽を再生
        if not message.guild.voice_client.is_playing():
            await play_next(message.guild,client.change_presence)

# クライアントインスタンスを開始
client.run(TOKEN)
