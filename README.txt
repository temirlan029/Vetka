===== Discord-бот: Приватные ветки =====

1. Установи Python 3.10+ (https://python.org)

2. Установи зависимости:
   pip install -r requirements.txt

3. Открой файл .env и впиши токен бота и ID ролей:
   BOT_TOKEN=твой_токен
   ROLE_IDS=id1,id2,id3  (через запятую, можно добавлять новые)

4. Убедись, что у бота включены интенты:
   - В Discord Developer Portal -> Bot -> Privileged Gateway Intents
   - Включи: SERVER MEMBERS INTENT и MESSAGE CONTENT INTENT

5. Права бота (при приглашении на сервер):
   - Manage Threads
   - Create Private Threads
   - Send Messages
   - Send Messages in Threads
   - Use Application Commands (slash-команды)
   - Mention Everyone (чтобы бот мог тегать роли)

6. Запуск:
   python bot.py

7. На сервере напиши /setup в нужном канале.
   Появится сообщение с кнопкой "Создать приватную ветку".

8. При нажатии на кнопку:
   - Создается приватная ветка "ветка-[имя]"
   - В ветку добавляется автор
   - Бот упоминает роли Dep.Owner и High
