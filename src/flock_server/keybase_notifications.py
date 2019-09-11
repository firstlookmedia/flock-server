import json
from datetime import datetime

from .elasticsearch import es, User, Setting, KeybaseNotification


class KeybaseNotifications:
    def __init__(self):
        self.notifications = {
            "user_registered": "A user has registered with the server",
            "user_already_exists": "A user tried to register with an existing username (they might be trying to re-setup their Flock Agent; if so delete the existing user so they can finish registering)",
            "reverse_shell": "A reverse shell was detected"
            #"launchd": "A new launch daemon was installed",
            #"startup_items": "A new startup item was installed"
        }
        self.warnings = ["reverse_shell"]

    def _get_default_settings(self):
        default_settings = {}
        for notification in self.notifications:
            default_settings[notification] = True
        return default_settings

    def _is_enabled(self, notification):
        if notification not in self.notifications:
            return False

        # Load the keybase settings
        results = Setting.search().query('match', key='keybase_notifications').execute()
        if len(results) == 0:
            # There are no keybase settings, so default everything to on
            setting = Setting(key='keybase_notifications', value=json.dumps(self._get_default_settings()))
            setting.save()
            return True

        setting = results[0]
        try:
            notification_settings = json.loads(setting.value)
        except:
            # Failed json decoding, so update the settings to the defaults
            setting.update(value=json.dumps(self._get_default_settings()))
            setting.save()
            return True

        if notification in notification_settings:
            return notification_settings[notification]
        else:
            # This notification is not in the settings, set it to true
            notification_settings[notification] = True
            setting.update(value=json.dumps(notification_settings))
            setting.save()
            return True

    def add(self, notification, details):
        if self._is_enabled(notification):
            # Create a new keybase notification
            keybase_notification = KeybaseNotification(
                notification_type=notification,
                details=details,
                delivered=False,
                created_at=datetime.now()
            )
            keybase_notification.save()

    def format(self, notification, details):
        if notification in self.warnings:
            return "@here :warning: :rotating_light:{}:rotating_light::\n```\n{}\n```".format(self.notifications[notification], details)
        else:
            return "{}:\n```\n{}\n```".format(self.notifications[notification], details)