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