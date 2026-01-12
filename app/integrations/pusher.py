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

    def notify_devices(
        self, title, content, device_ids: List = None, emails: List = [], metadata=None, sender=None
    ):
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
            logging.info(f"no device ids were provided")
            return

        for device_id in device_ids:
            valid_device_ids = []
            for device_id in device_ids:
                try:
                    uuid.UUID(device_id)
                    valid_device_ids.append(device_id)
                except ValueError:
                    logging.warning(f"Invalid device ID: {device_id}")

        notification_data = {
            "contents": {"en": content},
            "headings": {"en": title},
            # "include_player_ids": valid_device_ids,
            "include_aliases": {"external_id": emails},
            "target_channel": "push",
        }

        if metadata:
            notification_data["data"] = metadata

        one_signal_client = self.__init_client()
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
                "app_id": ONE_SIGNAL_APP_ID,
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
        logging.info("\n")
        logging.info("*" * 40)
        logging.info("OneSignal PUSH Notification")
        logging.info(json.dumps(notification_data, indent=4))
        logging.info("*" * 40)
        logging.info("\n")

        # if not is_in_development_environment():
        try:
            response = one_signal_client.send_notification(notification_data)
            print("OneSignal Response: %s", response.body)
            print(response.http_response)
            print(response.status_code)
            logging.info("OneSignal Response: %s", response.body)
        except ApiException as e:
            print("Failed to send OneSignal push notification: %s", e.message)
            logging.error("Failed to send OneSignal push notification: %s", e.message)
            return False
        except Exception as e:
            print("Failed to send OneSignal push notification: %s", e)
            logging.error("Failed to send OneSignal push notification: %s", e)
            return False

        return True

    @staticmethod
    def __init_client():
        """
        Initialize OneSignal API client based on the category.

        :param category: ['STAFF' | 'GUARDIAN']
        :return: OneSignal client
        """
        client = Client(app_id=ONE_SIGNAL_APP_ID, rest_api_key=ONE_SIGNAL_REST_API_KEY)
        return client


pusher = PushNotificationsService()
