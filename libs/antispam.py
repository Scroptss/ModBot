import time

class MessageRateLimiter:
    def __init__(self):
        self.message_logs = {}

    def check(self, user_id, channel_id, window = 15, max = 10):

        current_time = time.time()
        window_start_time = current_time - window

        # Clean up old message logs
        self._clean_old_logs(current_time, window)

        # Get message log for the user and channel
        user_channel_logs = self.message_logs.setdefault(user_id, {}).setdefault(channel_id, [])

        # Count the number of messages within the time window for the given user and channel
        count = sum(1 for timestamp in user_channel_logs if timestamp >= window_start_time)

        return count >= max

    def log(self, user_id, channel_id):
        current_time = time.time()
        user_channel_logs = self.message_logs.setdefault(user_id, {}).setdefault(channel_id, [])
        user_channel_logs.append(current_time)

    def _clean_old_logs(self, current_time, window):

        for user_id, user_logs in self.message_logs.items():
            for channel_id, timestamps in user_logs.items():
                self.message_logs[user_id][channel_id] = [t for t in timestamps if current_time - t <= window]
