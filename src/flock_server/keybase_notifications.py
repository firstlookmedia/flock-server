import json
from datetime import datetime
from elasticsearch_dsl import Index

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

    def _get_setting(self):
        # We must refresh the index before loading the settings for tests to pass -- this shouldn't be
        # necessary because _save_settings() refreshes it, but since the setting index is so small it
        # doesn't hurt
        Index('setting').refresh()

        results = Setting.search().query('match', key='keybase_notifications').execute()
        if len(results) == 0:
            # There are no keybase settings, so default everything to on
            default_settings = self._get_default_settings()
            setting = Setting(key='keybase_notifications', value=json.dumps(default_settings))
            setting.save()
            return setting

        setting = results[0]
        return setting

    def _load_settings(self):
        setting = self._get_setting()
        try:
            notification_settings = json.loads(setting.value)

            # Make sure they have all of the right notifications
            update = False
            for notification in self.notifications:
                if notification not in notification_settings:
                    notification_settings[notification] = True
                    update = True
            to_del = []
            for notification in notification_settings:
                if notification not in self.notifications:
                    to_del.append(notification)
                    update = True
            for notification in to_del:
                del notification_settings[notification]
            if update:
                setting.update(value=json.dumps(notification_settings))
                setting.save()

            return notification_settings
        except:
            # Failed json decoding, so update the settings to the defaults
            default_settings = self._get_default_settings()
            setting.update(value=json.dumps(default_settings))
            setting.save()
            return default_settings

    def _save_settings(self, notification_settings):
        setting = self._get_setting()
        setting.update(value=json.dumps(notification_settings))
        setting.save()
        Index('setting').refresh()

    def _is_enabled(self, notification):
        if notification not in self.notifications:
            return False

        notification_settings = self._load_settings()
        if notification in notification_settings:
            return notification_settings[notification]
        else:
            # This notification is not in the settings, set it to true
            notification_settings[notification] = True
            self._save_settings(notification_settings)
            return True

    def get_enabled_state(self):
        return self._load_settings()

    def enable(self, notification):
        notification_settings = self._load_settings()
        if notification in notification_settings:
            if not notification_settings[notification]:
                notification_settings[notification] = True
                self._save_settings(notification_settings)

    def disable(self, notification):
        notification_settings = self._load_settings()
        if notification in notification_settings:
            if notification_settings[notification]:
                notification_settings[notification] = False
                self._save_settings(notification_settings)

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