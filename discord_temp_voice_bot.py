"""
디스코드 임시 음성방 봇
------------------------------------------------
기능
1. /임시음성방생성  : 명령어를 입력한 채팅방 바로 아래(같은 카테고리)에
                     "임시-음성방" 이라는 음성 채널을 생성
2. 유저가 "임시-음성방"에 입장하면 즉시
   "{유저 닉네임}의 음성방" 이라는 개인 음성 채널이 생성되고 그 유저가 그 채널로 이동됨
   - 권한은 "임시-음성방"의 권한을 그대로 복사
   - 단, 생성자(방장)는 무조건 manage_channels 권한을 추가로 받아
     본인 방의 "이름 변경"이 가능함 (오버라이트 이름 우클릭 -> 채널 편집 -> 이름 변경)
3. 개인 음성방이 비면 자동으로 삭제 (필요 없으면 아래 on_voice_state_update의
   해당 블록을 지우면 됩니다)

설치
    pip install -U discord.py python-dotenv

실행 전 준비
    1) https://discord.com/developers/applications 에서 봇 생성
    2) Bot 탭에서 다음 Privileged Gateway Intents 켜기
       - SERVER MEMBERS INTENT
       - (VOICE 관련은 별도 토글 없음, 기본 제공)
    3) OAuth2 > URL Generator 에서
       scope: bot, applications.commands
       권한: Manage Channels, Move Members, View Channels, Connect
       로 초대 링크 생성 후 서버에 봇 초대
    4) 처음 한 번 python discord_temp_voice_bot.py 를 실행하면
       같은 폴더에 .env 파일이 자동으로 생성됩니다.
       .env 파일을 열어서 DISCORD_BOT_TOKEN=여기에토큰 형태로 실제 토큰을 넣고 저장한 뒤
       다시 python discord_temp_voice_bot.py 실행
"""

import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")

# .env 파일이 없으면 템플릿을 자동으로 생성
if not os.path.exists(ENV_PATH):
    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.write("DISCORD_BOT_TOKEN=여기에_봇_토큰_붙여넣기\n")
    raise SystemExit(
        f".env 파일이 없어서 새로 만들었습니다: {ENV_PATH}\n"
        "그 파일을 열어서 DISCORD_BOT_TOKEN= 뒤에 실제 봇 토큰을 붙여넣은 뒤 다시 실행하세요."
    )

load_dotenv(ENV_PATH)

TEMP_CHANNEL_NAME = "임시-음성방"

intents = discord.Intents.default()
intents.voice_states = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# 길드별로 생성된 "임시-음성방" 채널 ID 캐시 {guild_id: channel_id}
temp_channel_ids: dict[int, int] = {}
# 봇이 만든 개인 음성방 추적 {channel_id: owner_id}
personal_channels: dict[int, int] = {}


@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"슬래시 명령어 {len(synced)}개 동기화 완료")
    except Exception as e:
        print(f"명령어 동기화 실패: {e}")
    print(f"{bot.user} 로 로그인했습니다.")


@bot.tree.command(name="임시음성방생성", description="이 채팅방 아래에 임시 음성방을 생성합니다.")
async def create_temp_channel(interaction: discord.Interaction):
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message("서버 안에서만 사용할 수 있어요.", ephemeral=True)
        return

    invoking_channel = interaction.channel
    category = getattr(invoking_channel, "category", None)

    # 같은 카테고리에 이미 임시 음성방이 있으면 재사용 안내
    existing = discord.utils.get(guild.voice_channels, name=TEMP_CHANNEL_NAME, category=category)
    if existing:
        temp_channel_ids[guild.id] = existing.id
        await interaction.response.send_message(
            f"이미 {existing.mention} 채널이 있어요! 그 방에 입장하면 개인 음성방이 만들어져요.",
            ephemeral=True,
        )
        return

    # 명령어를 입력한 채팅방 바로 아래에 배치
    position = getattr(invoking_channel, "position", None)
    position = position + 1 if position is not None else None

    new_channel = await guild.create_voice_channel(
        name=TEMP_CHANNEL_NAME,
        category=category,
        position=position,
        reason=f"{interaction.user} 님이 임시 음성방 생성",
    )

    temp_channel_ids[guild.id] = new_channel.id

    await interaction.response.send_message(
        f"{new_channel.mention} 채널을 만들었어요! 입장하면 자동으로 개인 음성방이 생성돼요.",
        ephemeral=True,
    )


@bot.event
async def on_voice_state_update(
    member: discord.Member,
    before: discord.VoiceState,
    after: discord.VoiceState,
):
    guild = member.guild

    # 1) "임시-음성방"에 입장한 경우 -> 개인 음성방 생성 후 이동
    if after.channel is not None:
        temp_channel = guild.get_channel(temp_channel_ids.get(guild.id, 0))
        if temp_channel is None:
            # 봇 재시작 등으로 캐시가 없을 때 이름으로 재탐색
            temp_channel = discord.utils.get(guild.voice_channels, name=TEMP_CHANNEL_NAME)
            if temp_channel:
                temp_channel_ids[guild.id] = temp_channel.id

        if temp_channel and after.channel.id == temp_channel.id:
            await make_personal_channel(member, temp_channel)

    # 2) 개인 음성방에서 모든 인원이 나가면 자동 삭제
    if before.channel is not None and before.channel.id in personal_channels:
        if len(before.channel.members) == 0:
            try:
                await before.channel.delete(reason="개인 음성방이 비어 자동 삭제")
            except discord.NotFound:
                pass
            personal_channels.pop(before.channel.id, None)


async def make_personal_channel(member: discord.Member, temp_channel: discord.VoiceChannel):
    guild = member.guild

    # 임시 음성방의 권한을 그대로 복사
    overwrites = dict(temp_channel.overwrites)

    # 생성자(방장)는 무조건 manage_channels 권한 추가 -> 본인 방 이름 변경 가능
    owner_overwrite = overwrites.get(member, discord.PermissionOverwrite())
    owner_overwrite.manage_channels = True
    overwrites[member] = owner_overwrite

    new_channel = await guild.create_voice_channel(
        name=f"{member.display_name}의 음성방",
        category=temp_channel.category,
        overwrites=overwrites,
        reason=f"{member} 님의 개인 음성방 생성",
    )

    personal_channels[new_channel.id] = member.id

    try:
        await member.move_to(new_channel, reason="개인 음성방으로 이동")
    except discord.HTTPException:
        # 유저가 이미 다른 곳으로 이동했거나 권한 문제 등
        pass


if __name__ == "__main__":
    TOKEN = os.environ.get("DISCORD_BOT_TOKEN")

    if not TOKEN or TOKEN == "여기에_봇_토큰_붙여넣기":
        raise SystemExit(
            f".env 파일의 DISCORD_BOT_TOKEN 값이 비어있습니다.\n"
            f"{ENV_PATH} 파일을 열어서 실제 봇 토큰을 입력한 뒤 다시 실행하세요."
        )

    bot.run(TOKEN)
