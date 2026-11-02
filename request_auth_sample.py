import json
import os.path
import time
from datetime import datetime
from uplink import Consumer, get, returns, put, post, Body, Query
import jwt
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))  # current directory をそろえるためのおまじない

token_path = "account/token.jwt"  # token 配置場所。 fbRealtimeDB/account 以下に token が自動配置される
request_path = "account/request.json"  # アカウント情報配置場所。fbRealtimeDB/account/request.json にアカウント情報記入のこと。
googleapiID = "https://identitytoolkit.googleapis.com/"  # google API の URL

# 下記は各自で変更のこと
webAPIKey = "AIzaSyBoDpu_bFWWpDwzQseHsO7Id4K4Y1K22EU"  # firebase project の web API key
base_url = "https://cloud25x-d6862-default-rtdb.firebaseio.com/"  # realtime DB の URL


class AuthService(Consumer):
    @returns.json()
    @post("v1/accounts:signInWithPassword")
    def get(self, key: Query("key"), auth_request: Body):
        """Auth request"""


class UserDBService(Consumer):  # samples from uplink quickstart page
    """A Python Client for the users entries in realtime DB."""

    @returns.json()
    @get("/protected/users/{uid}.json")
    def get(self, uid, token: Query("auth")):
        """Get a user entry specified by id."""

    @returns.json()
    @put("/protected/users/{uid}.json")
    def put(self, uid, user: Body, token: Query("auth")):
        """Put a user entry with the specified id."""


class QuestionService(Consumer):
    """Questions in realtime DB"""

    @returns.json()
    @post("/questions.json")
    def post(self, question: Body, token: Query("auth")):
        """Post a new question"""

    @returns.json()
    @get("/questions.json")
    def list(self, token: Query("auth")):
        """Get question list"""

class AnswerService(Consumer):
    """Answers in realtime DB"""

    @returns.json()
    @post("/answers/{question_id}.json")
    def post(self, question_id, answer: Body, token: Query("auth")):
        """Post an answer"""


class TokenManager:
    token: str = None
    decoded: dict = None

    def send_auth_request(self):
        auth_service = AuthService(base_url=googleapiID)
        with open(request_path) as file_in:
            request = json.load(file_in)
        res = auth_service.get(webAPIKey, request)
        self.token = res["idToken"]
        self.decoded = jwt.decode(self.token, options={"verify_signature": False})
        print("Received Token:", self.token)
        with open(token_path, 'w') as token_out:
            token_out.write(self.token)
        print("Expire: ", datetime.fromtimestamp(self.decoded["exp"]))

    def get_token(self):
        if self.token is None and os.path.isfile(token_path):
            with open(token_path) as token_in:
                self.token = token_in.read()
            self.decoded = jwt.decode(self.token, options={"verify_signature": False})
        if self.token is None or (self.decoded["exp"] < time.time()):
            self.send_auth_request()
        return self.token

    def get_token_user(self):
        if self.token is None:
            self.get_token()
        return self.decoded["user_id"]

def post_question(title, description):
    manager = TokenManager()
    token = manager.get_token()
    uid = manager.get_token_user()

    service = QuestionService(base_url=base_url)

    # 既存の質問一覧を取得
    existing = service.list(token)

    if existing is None:
        display_no = 1
    else:
        display_no = max(q.get("displayNo", 0) for q in existing.values()) + 1

    question = {
        "displayNo": display_no,   # ← 追加
        "title": title,
        "description": description,
        "sender": uid,
        "createdAt": int(time.time())
    }

    res = service.post(json.dumps(question), token)
    print(f"質問を投稿しました（質問番号: {display_no}）")



def list_questions():
    manager = TokenManager()
    token = manager.get_token()

    service = QuestionService(base_url=base_url)
    res = service.list(token)

    if res is None:
        print("まだ質問がありません")
        return

    # displayNo順に並べる
    questions = sorted(
        res.items(),
        key=lambda x: x[1].get("displayNo", 0)
    )

    for qid, q in questions:
        print(f"[{q['displayNo']}] {q['title']}")


def get_question(display_no):
    manager = TokenManager()
    token = manager.get_token()

    service = QuestionService(base_url=base_url)
    res = service.list(token)

    if res is None:
        return None

    for qid, q in res.items():
        if q.get("displayNo") == display_no:
            return qid

    return None


def post_answer(question_id, text):
    manager = TokenManager()
    token = manager.get_token()
    uid = manager.get_token_user()

    service = AnswerService(base_url=base_url)

    answer = {
        "sender": uid,
        "text": text,
        "createdAt": int(time.time())
    }

    res = service.post(question_id, json.dumps(answer), token)
    print("answer posted:", res)

def list_answers(question_id):
    manager = TokenManager()
    token = manager.get_token()

    service = AnswerService(base_url=base_url)
    res = service.list(question_id, token)

    if res is None:
        print("まだ回答がありません")
        return

    print(f"質問ID {question_id} の回答一覧:")
    for aid, a in res.items():
        created = datetime.fromtimestamp(a["createdAt"])
        print(f"- [{aid}] {a['text']} (by {a['sender']}, {created})")

def request_sample():
    user_db = UserDBService(base_url=base_url)
    manager = TokenManager()
    token = manager.get_token()
    uid = manager.get_token_user()

    print("::", token, "::", uid, "::")

    user = {
        "name": "神戸ぱいそん",
        "nickname": "ニックネーム"
    }
    put_response = user_db.put(uid, json.dumps(user), token)
    print("put response", put_response)

    get_response = user_db.get(uid, token)
    print("get response", get_response)

request_sample()

while True:
    n = input("どの操作をしますか？ (0: アンケート一覧表示, 1: アンケート投稿, 2: 回答投稿, 3: 回答一覧表示, 9: 終了)\n")

    if n == "0":
        list_questions()
    elif n == "1":
        title = input("質問タイトル: ")
        desc = input("質問内容: ")
        post_question(title, desc)


    elif n == "2":

        no = int(input("質問番号: "))

        qid = get_question(no)

        if qid is None:
            print("その質問番号は存在しません")

            continue

        text = input("回答内容: ")

        post_answer(qid, text)


    elif n == "3":

        no = int(input("質問番号: "))

        qid = get_question(no)

        if qid is None:
            print("その質問番号は存在しません")

            continue

        list_answers(qid)

    elif n == "9":
        break
