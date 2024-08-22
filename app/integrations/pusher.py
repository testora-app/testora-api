""" Wraps functionality for notifying users via push notifications """

import json
import logging
import uuid

from onesignal_sdk.client import Client
from onesignal_sdk.error import OneSignalHTTPError as ApiException
from globals import (
    ONE_SIGNAL_APP_ID,
    ONE_SIGNAL_REST_API_KEY,
)


from typing import List


class PushNotificationsService:
    """Wraps functionality for sending push notifications"""

    def notify_devices(self, title, content, device_ids: List, metadata=None, sender=None):
        """
        Send push notification via OneSignal API.

        Arguments:
            title {str} -- The title of the notification
            content {str} -- The body of the notification

        Keyword Arguments:
            device_ids -- The devices to send the notification.
                Example:  [device_id_1, device_id_2, ...]
            metadata {dict} -- Extra data to be sent with the notification
        """

        if not device_ids:
            logging.info(f'no device ids were provided')
            pass

        for device_id in device_ids:
            one_signal_client = self.__init_client()

            valid_device_ids = []
            for device_id in device_ids:
                try:
                    uuid.UUID(device_id)
                    valid_device_ids.append(device_id)
                except ValueError:
                    pass

            notification_data = {
                "contents": {"en": content},
                "headings": {"en": title},
                "include_player_ids": valid_device_ids,
            }

            if metadata:
                notification_data["data"] = metadata

            self.__send_notification(one_signal_client, notification_data)

    def notify_topic_subscribers(
        self, title, content, topics, metadata=None, sender=None
    ):
        """
        Send message to devices that are subscribed to topics.

        Arguments:
            title {str} -- The title of the notification
            content {str} -- The body of the notification

        Keyword Arguments:
            topics {dict} -- The topics to send the notification to, categorized by recipient_category.
                Example: {'STAFF': [topic_x278, topic_x455, ...], 'GUARDIANS': [topic_3XXX, topic_0hj3, ...]}
            metadata {dict} -- Extra data to be sent with the notification
        """
        for device_category, topic_names in topics.items():
            if not topic_names:
                logging.info(
                    "No OneSignal topic names provided for category: %s",
                    device_category,
                )
                continue

            one_signal_client = self.__init_client(device_category)

            notification_data = {
                "contents": {"en": content},
                "headings": {"en": title},
                "included_segments": topic_names,
            }

            if metadata:
                notification_data["data"] = metadata

            self.__send_notification(one_signal_client, notification_data)

    def __send_notification(self, one_signal_client: Client, notification_data):
        """
        Perform the actual action of sending the notification.

        Returns:
            bool -- True if the message was sent successfully
        """
        print("\n")
        print("*" * 40)
        print("OneSignal PUSH Notification")
        logging.info(json.dumps(notification_data, indent=4))
        print("*" * 40)
        print("\n")

        # if not is_in_development_environment():
        try:
            response = one_signal_client.send_notification(notification_data)
            logging.info("OneSignal Response: %s", response)
        except ApiException as e:
            logging.error("Failed to send OneSignal push notification: %s", e.message)
            return False

        return True

    @staticmethod
    def __init_client():
        """
        Initialize OneSignal API client based on the category.

        :param category: ['STAFF' | 'GUARDIAN']
        :return: OneSignal client
        """
        client = Client(
            app_id=ONE_SIGNAL_APP_ID,
            rest_api_key=ONE_SIGNAL_REST_API_KEY
        )
        return client


pusher = PushNotificationsService()