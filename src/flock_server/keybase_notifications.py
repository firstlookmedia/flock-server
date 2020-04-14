import json
from datetime import datetime
from elasticsearch_dsl import Index, Search

from .elasticsearch import es, User, Setting, KeybaseNotification


class KeybaseNotifications:
    def __init__(self):
        self.notifications = {
            # User registration
            "user_registered": {
                "type": "user",
                "desc": "A user has registered with the server",
            },
            "user_already_exists": {
                "type": "user",
                "desc": "A user tried to register with an existing username (they might be trying to re-setup their Flock Agent; if so delete the existing user so they can finish registering)",
            },
            # Flock logs
            "server_enabled": {
                "type": "flock",
                "desc": "A user has enabled the server",
            },
            "server_disabled": {
                "type": "flock",
                "desc": "A user has disabled the server",
            },
            "twigs_enabled": {"type": "flock", "desc": "A user has enabled twigs"},
            "twigs_disabled": {"type": "flock", "desc": "A user has disabled twigs"},
            # Osquery
            "reverse_shell": {
                "type": "osquery",
                "desc": "A reverse shell was detected",
            },
            "os_version": {"type": "osquery", "desc": "OS version has changed"},
            "safari_extensions": {
                "type": "osquery",
                "desc": "Opera extension has changed",
            },
            "opera_extensions": {
                "type": "osquery",
                "desc": "Opera extension has changed",
            },
            "chrome_extensions": {
                "type": "osquery",
                "desc": "Chrome extension has changed",
            },
            "firefox_addons": {"type": "osquery", "desc": "Firefox add-on has changed"},
            "launchd": {"type": "osquery", "desc": "Launch daemon has changed"},
            "startup_items": {"type": "osquery", "desc": "Startup item has changed"},
            "crontab": {"type": "osquery", "desc": "Cron job has changed"},
            "kextstat": {"type": "osquery", "desc": "Kernel extension has changed"},
            "installed_applications": {
                "type": "osquery",
                "desc": "Applications have changed",
            },
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
        Index("setting").refresh()

        results = Setting.search().query("match", key="keybase_notifications").execute()
        if len(results) == 0:
            # There are no keybase settings, so default everything to on
            default_settings = self._get_default_settings()
            setting = Setting(
                key="keybase_notifications", value=json.dumps(default_settings)
            )
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
        Index("setting").refresh()

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
        details_obj = json.dumps(details, indent=2)
        if self._is_enabled(notification):
            # Create a new keybase notification
            keybase_notification = KeybaseNotification(
                notification_type=notification,
                details=details_obj,
                delivered=False,
                created_at=datetime.now(),
            )
            keybase_notification.save()

    def format(self, notification, details):
        details_obj = json.loads(details)
        if self.notifications[notification]["type"] == "osquery":
            # osquery notifications
            if "type" in details_obj and details_obj["type"] == "summary":
                # Display a summary of how many of this type of change
                username = details_obj["username"]
                name = details_obj["name"]
                added_count = details_obj["added_count"]
                removed_count = details_obj["removed_count"]
                other_count = details_obj["other_count"]

                message = f"- Computer: **{name}** (`{username}`)"
                if added_count > 0:
                    message += f"\n- **{added_count}** added"
                if removed_count > 0:
                    message += f"\n- **{removed_count}** removed"
                if other_count > 0:
                    message += f"\n- **{other_count}** unknown action"
            else:
                # Display the details of a single change
                username = details_obj["hostIdentifier"]
                name = details_obj["user_name"]
                action = details_obj["action"]
                time = details_obj["calendarTime"]
                columns = json.dumps(details_obj["columns"], indent=2)

                message = f"- Computer: **{name}** (`{username}`)\n- Date: {time}\n- Action: {action}\n```\n{columns}```"

        else:
            # user and flock notifications
            message = f"```{json.dumps(details_obj, indent=2)}```"

        if notification in self.warnings:
            return f"@here **:warning: :rotating_light:{self.notifications[notification]['desc']}:rotating_light:**:\n{message}"
        else:
            return f"**{self.notifications[notification]['desc']}:**\n{message}"
