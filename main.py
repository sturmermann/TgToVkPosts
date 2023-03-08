from pyrogram import Client
from pyrogram import types, filters
import requests, logging, atexit, json, os, asyncio, random

with open("settings.json", "r") as settings:
    settings = json.load(settings)

CHANNEL_ID = settings["CHANNEL_ID"]
CHANNEL_ID_COMMENTS = settings["CHANNEL_ID_COMMENTS"]
VK_GROUP_ID = settings["VK_GROUP_ID"]
VK_USERTOKEN = settings["VK_USERTOKEN"]
VK_USERTOKEN_ANSWER = settings["VK_USERTOKEN_ANSWER"]
API_ID = settings["API_ID"]
API_HASH = settings["API_HASH"]
BLACK_LIST = settings["BLACK_LIST"]

k = settings["commentSettings"]
howOftenMin = k["howOftenMin"]
howOftenMax = k["howOftenMax"]
firstMessageMin = k["firstMessageMin"]
firstMessageMax = k["firstMessageMax"]
secondMessageMin = k["secondMessageMin"]
secondMessageMax = k["secondMessageMax"]
questions = k["questions"]
answers = k["answers"]
accs = settings["accs"]

weReciviedFirstPhoto = 0
posts = 1

app = Client(
    "mainAccount",
    api_id=API_ID,
    api_hash=API_HASH
)

logging.basicConfig(
    filename='bot.log',
    level=logging.INFO,
    format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)

logging.info("программа стартует")
@atexit.register
def exitHan():
    logging.info("программа завершила работу")
    with open("valid.txt", "w") as output:
        output.write(str(accs))
    

def uploadPic(peer_id, picNames):
    a = requests.get("https://api.vk.com/method/photos.getWallUploadServer?access_token={}&v=5.131".format(VK_USERTOKEN)).json()
    logging.info(a)
    photoes = ""
    for i in picNames:
        logging.info(i)
        b = requests.post(a['response']['upload_url'], files={'photo': open(i, 'rb')}).json()
        logging.info(b)
        c = requests.get( "https://api.vk.com/method/photos.saveWallPhoto?photo={}&server={}&hash={}&access_token={}&v=5.131".format(b['photo'],b['server'],b['hash'], VK_USERTOKEN) ).json()
        logging.info(c)
        d = "photo{}_{}".format(c["response"][0]["owner_id"], c["response"][0]["id"])
        photoes += f"{d},"
    return photoes

async def commentsTheater(post_id, ex = 0):
    global posts
    if not ex:
        posts-=1
        if posts > 0: 
            return
        posts = random.randint(howOftenMin, howOftenMax)
        await asyncio.sleep(random.randint(firstMessageMin, firstMessageMax))
    ppl = accs[random.randint(0, len(accs)-1)]
    msg = random.randint(0, len(questions)-1)
    msg_1 = questions[msg]
    k = requests.get( f"https://api.vk.com/method/wall.createComment?owner_id={VK_GROUP_ID}&post_id={post_id}&message={msg_1}&access_token={ppl}&v=5.131").json()
    if k.get("error", False):
        accs.remove(ppl)
        logging.error(k)
        logging.error(ppl)
        await commentsTheater(post_id, ex = 1)
        return 0
    logging.info(k)
    await asyncio.sleep(random.randint(secondMessageMin, secondMessageMax))
    k = k["response"]["comment_id"]
    msg_1 = answers[msg]
    k = requests.get( f"https://api.vk.com/method/wall.createComment?owner_id={VK_GROUP_ID}&post_id={post_id}&message={msg_1}&access_token={VK_USERTOKEN_ANSWER}&reply_to_comment={k}&v=5.131").json()
    logging.info(k)


@app.on_message(filters.channel & filters.text)
async def onlyText(client, message):
    global weReciviedFirstPhoto
    yes = False
    for i in CHANNEL_ID.keys():
        if message.chat.id == int(i):
            yes = True
    if yes == False:
        return
    logging.info(f"Получено новое сообщение с ID {message.id} text: {message.text[:40]}")
    nowText = message.text
    topic_id = CHANNEL_ID[str(message.chat.id)]
    for i in BLACK_LIST:
        if i in nowText.lower():
            logging.info("Запрещенные слова")
            return
    k = requests.get(f"https://api.vk.com/method/wall.post?owner_id={VK_GROUP_ID}&from_group={1}&topic_id={topic_id}&message={nowText}&access_token={VK_USERTOKEN}&v=5.131").json()
    logging.info(k)
    if message.chat.id in CHANNEL_ID_COMMENTS:
        await commentsTheater(k["response"]["post_id"])

@app.on_message(filters.channel & filters.photo)
async def withPhotoes(client, message):
    global weReciviedFirstPhoto
    yes = False
    for i in CHANNEL_ID.keys():
        if message.chat.id == int(i):
            yes = True
    if yes == False:
        return
    logging.info(f"Получено новое сообщение с ID {message.id} фотокарточки")
    if message.caption:
        nowText = message.caption
    else:
        nowText = ""
    logging.info(f"С текстом: {nowText}")
    for i in BLACK_LIST:
        if i in nowText.lower():
            logging.info("Запрещенные слова")
            return
    topic_id = CHANNEL_ID[str(message.chat.id)]
    if not weReciviedFirstPhoto:
        for file in os.listdir(os.fsencode("photoes/")):
            filename = os.fsdecode(file)
            os.remove(f"photoes/{filename}")
    else:
        await asyncio.sleep(2)
    await app.download_media(message, "photoes/")
    if not weReciviedFirstPhoto:
        weReciviedFirstPhoto = 1
        pictures = []
        await asyncio.sleep(20)
        a1 = True
        while a1 == True:
            a2 = True
            for file in os.listdir(os.fsencode("photoes/")):
                filename = os.fsdecode(file)
                if (filename[-4:] == "temp"):
                    a2 = False
                    await asyncio.sleep(2)
                    break
            if a2 == False:
                continue
            a1 = False
        for file in os.listdir(os.fsencode("photoes/")):
            filename = os.fsdecode(file)
            logging.info(filename)
            pictures.append(f"photoes/{filename}")
        att = uploadPic(VK_GROUP_ID, pictures)
        for file in os.listdir(os.fsencode("photoes/")):
            filename = os.fsdecode(file)
            os.remove(f"photoes/{filename}")
        logging.info(att)
        k = requests.get(f"https://api.vk.com/method/wall.post?owner_id={VK_GROUP_ID}&topic_id={topic_id}&from_group={1}&message={nowText}&attachments={att}&access_token={VK_USERTOKEN}&v=5.131").json()
        logging.info(k)
        weReciviedFirstPhoto = 0
        if message.chat.id in CHANNEL_ID_COMMENTS:
            await commentsTheater(k["response"]["post_id"])
            
app.run()
