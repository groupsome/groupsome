import telepot
from .models import Feedback
from django.utils.translation import ugettext as _


class Command():
    required_role = None
    hide_in_keyboard = False
    
    def __init__(self, user, group, msg, bot, cache, message_handler):
        self.user = user
        self.group = group
        self.msg = msg
        self.bot = bot
        self.cache = cache
        self.message_handler = message_handler
        
        content_type, chat_type, chat_id = telepot.glance(msg)
        self.content_type = content_type
        self.chat_type = chat_type
        self.chat_id = chat_id
    
    def validate(self):
        return True
    
    def handle(self):
        pass
    
    def reply(self, message, private=False, reply_markup=None, add_keyboard=False, direct_reply=False):
        reply_to = None
        recipient = self.chat_id
        
        if private:
            recipient = self.user.telegram_id
        
        if add_keyboard and self.group:
            reply_markup = self.message_handler.get_public_keyboard()
        elif add_keyboard:
            reply_markup = self.message_handler.get_private_keyboard()
        
        if direct_reply:
            reply_to = self.msg["message_id"]

        self.bot.sendMessage(recipient, message, reply_markup=reply_markup, reply_to_message_id=reply_to)

    @property
    def text(self):
        return self.msg["text"]

    @property
    def args(self):
        return self.msg["text"].split(" ")[1:]


class StatefulCommand():
    key = None
    
    def handle(self):
        self.handle_initial_state()
    
    def handle_initial_state(self):
        pass
    
    def handle_state(self, state):
        handler = getattr(self, "handle_state_" + str(state))
        handler()
    
    def get_state_key(self):
        return str(self.user.telegram_id) + self.key
    
    def get_state(self):
        return self.cache.get(self.get_state_key())
    
    def set_state(self, state):
        self.cache.set(self.get_state_key(), state, 5 * 60)
    
    def reset_state(self):
        self.cache.delete(self.get_state_key())


class FeedbackCommand(StatefulCommand, Command):
    key = "_state_feedback"
    
    def handle_initial_state(self):
        self.reply(_("Please give us your feedback!"))
        self.set_state(1)
    
    def handle_state_1(self):
        if len(self.text) > 1000:
            return self.reply(_("Your feedback is too long!\nPlease stay within 1000 chars"), private=True)
        
        feedback = Feedback.create_and_save(feedback=self.text, user=self.user.user)
        self.reply(_("Thank you! We always want to improve our service."), direct_reply=True)
        self.reset_state()


class HelpCommand(Command):
    def handle(self):
        if self.group:
            self.reply(_("This is the groupsome Telegram bot, you can use the following commands."), add_keyboard=True,
                       direct_reply=True)
        else:
            self.reply(_("This is the groupsome Telegram bot, you can use the following commands. More features are "
                         "available in a group chat."), add_keyboard=True)
            

class CancelCommand(Command):
    def handle(self):
        for command, klass in self.message_handler.private_commands.items():
            if issubclass(klass, StatefulCommand):
                self.cache.delete(str(self.user.telegram_id) + klass.key)
        for command, klass in self.message_handler.public_commands.items():
            if issubclass(klass, StatefulCommand):
                self.cache.delete(str(self.user.telegram_id) + klass.key)
        self.cache.delete(str(self.user.telegram_id) + "_event")
        self.cache.delete(str(self.user.telegram_id) + "_survey")
        self.cache.delete(str(self.user.telegram_id) + "_survey_options")
        self.reply(_("Cancelled"))
