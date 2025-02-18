from telegram.error import BadRequest

class HaruBot:
    def __init__(self):
        self.generator = HaruGenerator()
        self.config = Config()
        self.last_request = 0

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        username = update.effective_user.first_name
        response = self._safe_generate("Привет", username)
        await self._send_response(update, response)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        current_time = time.time()
        if current_time - self.last_request < 5:
            return
            
        self.last_request = current_time
        user_message = update.message.text
        username = update.effective_user.first_name
        response = self._safe_generate(user_message, username)
        await self._send_response(update, response)

    async def _send_response(self, update, text):
        parts = self._split_response(text)
        for part in parts:
            try:
                await update.message.reply_text(part)
            except BadRequest as e:
                logger.error(f"Ошибка отправки сообщения: {str(e)}")
                # Попробуем отправить сообщение в личный чат
                try:
                    await context.bot.send_message(
                        chat_id=update.effective_user.id,
                        text="Кажется, я не могу писать в этом чате... Напиши мне в личку!"
                    )
                except Exception as e:
                    logger.error(f"Ошибка отправки в личный чат: {str(e)}")
            time.sleep(random.uniform(*self.config.RESPONSE_DELAY))

    def _split_response(self, text):
        return [text[i:i+300] for i in range(0, len(text), 300)][:3]
