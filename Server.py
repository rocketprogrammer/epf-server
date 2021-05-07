from aiohttp import web
from hashlib import md5
import asyncio, logging, psycopg2, bcrypt, json

# Setup logging for web requests.
logging.basicConfig(level = logging.INFO)

# Load our configuration.
data = open('credentials.json').read()
credentials = json.loads(data)

# Grab our database information.
host = credentials['Host']

database = credentials['Database']
username = credentials['Username']
password = credentials['Password']

# Connect to our PostgreSQL database.
conn = psycopg2.connect(host = host, database = database, user = username, password = password)
cur = conn.cursor()

class Crypto:

    @staticmethod
    def hash(undigested):
        if type(undigested) == str:
            undigested = undigested.encode('utf-8')
        elif type(undigested) == int:
            undigested = str(undigested).encode('utf-8')
        return md5(undigested).hexdigest()

    @staticmethod
    def encryptPassword(password, digest = True):
        if digest:
            password = Crypto.hash(password)

        swappedHash = password[16:32] + password[0:16]
        return swappedHash

    @staticmethod
    def getLoginHash(password, rndk):
        key = Crypto.encryptPassword(password, False)
        key += rndk
        key += 'Y(02.>\'H}t":E1'

        loginHash = Crypto.encryptPassword(key)

        return loginHash

class RequestTypes:
    MAIN_SCREEN = 1
    UPLOAD_COINS = 2
    ONLINE_POLL = 3
    POLL_SELECT = 4
    NEWSLETTER = 5
    MISSION_DOWNLOAD = 7
    ACCOUNT_VALIDATION = 8
    DOWNLOAD_NEWSLETTER = 9

async def handleSubmit(request):
    #print(request.method, request.path, request.query, request.headers)
    args = await request.post()
    #print('args', args)

    requestId = int(args.get('RequestID'))
    print('requestId', requestId)

    if requestId in (RequestTypes.ACCOUNT_VALIDATION, RequestTypes.UPLOAD_COINS):
        username = args.get('UserName').decode().lower()
        password = args.get('Password').decode()

    if requestId == RequestTypes.UPLOAD_COINS:
        amount = int(args.get('Amount'))

        cur.execute("""SELECT coins FROM penguin WHERE username = %(username)s""", {'username': username})
        curAmount = cur.fetchall()[0][0]

        if curAmount < 0:
            return web.Response()

        curAmount += amount

        cur.execute("""UPDATE penguin SET coins = %(curAmount)s WHERE username = %(username)s""", {'curAmount': curAmount, 'username': username})
        conn.commit()

        return web.Response(text = '001')

    elif requestId == RequestTypes.ONLINE_POLL:
        return web.Response(text = 'Test Poll')

    elif requestId == RequestTypes.POLL_SELECT:
        pollSelection = args.get('PollSelection').decode()
        return web.Response(text = '25%')

    elif requestId in (RequestTypes.NEWSLETTER, RequestTypes.DOWNLOAD_NEWSLETTER):
        return web.Response(text = 'Test!')

    elif requestId == RequestTypes.ACCOUNT_VALIDATION:
        cur.execute("""SELECT password FROM penguin WHERE username = %(username)s""", {'username': username})
        dbPassword = cur.fetchall()[0][0]

        password = Crypto.hash(password).upper()
        password = Crypto.getLoginHash(password, rndk = 'houdini')

        if not bcrypt.checkpw(password.encode(), dbPassword.encode()):
            return web.Response()
        else:
            return web.Response(text = '001')

    return web.Response()

async def initializeService():
    app = web.Application()
    app.router.add_post('/submit_uk.php', handleSubmit)
    return app

loop = asyncio.get_event_loop()
app = loop.run_until_complete(initializeService())
web.run_app(app, host = '0.0.0.0', port = 80)