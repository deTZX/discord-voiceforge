# VoiceForge

임시 음성방에 입장하면 자동으로 개인 음성방이 생성되는 디스코드 슬래시 명령어 기반 음성 봇입니다.

## 1. 필수 라이브러리 설치

터미널에서 아래 명령어를 입력하여 디스코드 라이브러리와 환경변수 패키지를 한 번에 설치합니다.

```
pip install -U discord.py python-dotenv
```

## 2. 디스코드 개발자 포털 설정

1. [Discord Developer Portal](https://discord.com/developers/applications)에서 본인의 봇 애플리케이션을 선택합니다.
2. 왼쪽 **Bot** 메뉴로 이동합니다.
3. **Privileged Gateway Intents** 항목에서 **SERVER MEMBERS INTENT**를 켜고(ON) 저장합니다.
4. 봇 초대 링크 생성 및 권한 설정 (필수)
   왼쪽 **OAuth2 → URL Generator**로 이동합니다.
   Scopes에서 `bot`과 `applications.commands`를 체크합니다.
   아래에 생기는 Bot Permissions에서 다음 권한을 반드시 체크합니다.
   - **Manage Channels** (채널 관리)
   - **Move Members** (멤버 이동)
   - **View Channels** (채널 보기)
   - **Connect** (연결하기)

## 3. 토큰 설정 및 실행

1. 처음 한 번 `python discord_temp_voice_bot.py`를 실행하면 같은 폴더에 `.env` 파일이 자동으로 생성됩니다.
2. 생성된 `.env` 파일을 열어 `DISCORD_BOT_TOKEN=` 뒤에 본인의 봇 토큰을 입력합니다.
3. 파일을 다시 실행합니다.

```
python discord_temp_voice_bot.py
```

## 🎮 사용 방법

봇이 서버에 정상적으로 로그인되면 자동으로 슬래시 명령어가 동기화됩니다. 채팅창에 `/`를 입력하여 사용하세요.

- `/임시음성방생성` : 명령어를 입력한 채팅방 바로 아래에 `임시-음성방` 채널을 생성합니다.
- 이후 누군가 `임시-음성방`에 입장하면 자동으로 `{닉네임}의 음성방`이 생성되고 그 방으로 이동됩니다.
- 개인 음성방의 권한은 임시 음성방과 동일하게 적용됩니다.
- 하지만 개인 음성방의 방장은 언제든 채널 이름을 변경할 수 있습니다.
- 개인 음성방에 아무도 남지 않으면 자동으로 삭제됩니다.
