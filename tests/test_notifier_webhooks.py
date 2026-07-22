"""
Tests unitaires pour la sécurisation et l'envoi des notifications Webhook (Slack, Discord) (tests/test_notifier_webhooks.py).
"""

import pytest
from unittest.mock import patch, MagicMock
from orchestrator.notifier import (
    obfuscate_url,
    send_slack_notification,
    send_discord_notification,
    NotificationManager
)


def test_obfuscate_url():
    url = "https://hooks.slack.domain/webhook/T000/B000/KEY123456789"
    masked = obfuscate_url(url)
    assert ".../*******" in masked
    assert "KEY123456789" not in masked


@patch("requests.post")
def test_send_slack_notification_success(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_post.return_value = mock_resp

    res = send_slack_notification("Test Message", "https://mock.slack.local/webhook")
    assert res is True
    mock_post.assert_called_once_with(
        "https://mock.slack.local/webhook",
        json={"text": "Test Message"},
        timeout=5
    )


@patch("requests.post")
def test_send_discord_notification_success(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 204
    mock_post.return_value = mock_resp

    res = send_discord_notification("Test Discord", "https://mock.discord.local/webhook")
    assert res is True
    mock_post.assert_called_once_with(
        "https://mock.discord.local/webhook",
        json={"content": "Test Discord"},
        timeout=5
    )


def test_send_slack_notification_no_url():
    assert send_slack_notification("Test", "") is False


@patch("urllib.request.urlopen")
def test_notification_manager(mock_urlopen):
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    manager = NotificationManager("https://mock.slack.local/webhook")
    res = manager.notify_job_start("job_12345", "Test Task")
    assert res is True
