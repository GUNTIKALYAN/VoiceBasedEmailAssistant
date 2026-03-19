# # class ConversationState:

# #     def __init__(self):
# #         self.reset()

# #     def reset(self):

# #         self.user_pin = "1234"
# #         # language
# #         self.session_language = "en-IN"

# #         # logged in user email
# #         self.user_email = None


# #         # inbox features
# #         self.email_list = []
# #         self.current_email_index = None
# #         self.awaiting_email_selection = False
# #         self.current_email = None

# #         # SEND MAIL AGENT STATES

# #         # activate send mail flow
# #         self.send_mail_mode = False

# #         # steps in flow
# #         self.awaiting_recipient = False
# #         self.awaiting_subject = False
# #         self.awaiting_intent = False

# #         # generated email confirmation
# #         self.awaiting_confirmation = False

# #         # security pin verification
# #         self.awaiting_pin = False

# #         # data storage
# #         self.recipient = None
# #         self.subject = None
# #         self.intent_line = None
# #         self.generated_email = None


# # assistant_state = ConversationState()


# class ConversationState:

#     def __init__(self):
#         self.user_email = None
#         self.username = None
#         self.session_language = "en-IN"

#     def reset(self):

#         # Security
#         self.user_pin = "1234"

#         # Language
#         self.session_language = "en-IN"

#         # Logged-in user email
#         # self.user_email = None
#         # self.username = None

#         # ── Inbox / read flow ──────────────────────────────────────────
#         self.email_list = []
#         self.current_email_index = None
#         self.awaiting_email_selection = False   # True while waiting for user to say a number
#         self.current_email = None               # Full email dict {sender, subject, body}

#         # ── Send / reply mail flow ─────────────────────────────────────
#         self.send_mail_mode = False             # True while inside send-mail conversation

#         # Step flags (only one should be True at a time)
#         self.awaiting_recipient = False
#         self.awaiting_recipient_confirmation = False
#         self.awaiting_subject = False
#         self.awaiting_intent = False
#         self.awaiting_confirmation = False
#         self.awaiting_pin = False
#         self.awaiting_pin_confimation = False
#         self.temp_pin = None
#         self.awaiting_email = False
#         self.awaiting_pin_creation = False
        



#         # Captured data
#         self.recipient = None
#         self.subject = None
#         self.intent_line = None
#         self.generated_email = None


# # Singleton used across the entire app
# assistant_state = ConversationState()

class ConversationState:

    def __init__(self):
        self.reset()

    def reset(self):

        # ─────────────────────────────────────────
        # USER / SESSION
        # ─────────────────────────────────────────
        self.user_email = None
        self.username = None
        self.session_language = "en-IN"
        self.auth_mode = None   # "new_user", "login"

        # ─────────────────────────────────────────
        # AUTH FLOW (VOICE LOGIN)
        # ─────────────────────────────────────────
        self.awaiting_email = False
        self.awaiting_pin = False
        self.awaiting_pin_creation = False
        self.awaiting_pin_confirmation = False
        self.temp_pin = None

        # ─────────────────────────────────────────
        # INBOX / READ FLOW
        # ─────────────────────────────────────────
        self.email_list = []
        self.current_email_index = None
        self.awaiting_email_selection = False
        self.current_email = None

        # ─────────────────────────────────────────
        # SEND MAIL FLOW
        # ─────────────────────────────────────────
        self.send_mail_mode = False

        self.awaiting_recipient = False
        self.awaiting_recipient_confirmation = False
        self.awaiting_subject = False
        self.awaiting_intent = False
        self.awaiting_confirmation = False

        # ─────────────────────────────────────────
        # EMAIL DATA
        # ─────────────────────────────────────────
        self.recipient = None
        self.subject = None
        self.intent_line = None
        self.generated_email = None


# Singleton
assistant_state = ConversationState()