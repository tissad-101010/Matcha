CREATE UNIQUE INDEX IF NOT EXISTS notifications_message_received_unique
    ON notifications (message_id)
    WHERE type = 'message_received';
