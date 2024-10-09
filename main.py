from urllib.parse import quote
import asyncio
import feedparser
import platform
import signal
import webbrowser
from datetime import datetime, timedelta
from desktop_notifier import DEFAULT_SOUND, DesktopNotifier, Urgency

# Integrate with Core Foundation event loop on macOS to allow receiving callbacks.
if platform.system() == "Darwin":
    from rubicon.objc.eventloop import EventLoopPolicy

    asyncio.set_event_loop_policy(EventLoopPolicy())

def get_papers(topic, start, max_results):
    """ Get papers from arXiv based on query. """
    feed_url = f"http://export.arxiv.org/api/query?search_query=all:{topic}&start={start}&max_results={max_results}&sortBy=lastUpdatedDate&sortOrder=descending"
    try:
        feed = feedparser.parse(feed_url)
        entries = [{'id': entry.id, 'title': entry.title} for entry in feed.entries]
        return entries
    except Exception as e:
        print(f"Error: {e}")
        return []

async def wait_until_time(hour=9, minute=0, second=0):
    """Wait until a specific time of the day."""
    now = datetime.now()
    target_time = now.replace(hour=hour, minute=minute, second=second, microsecond=0)
    
    # If it's already past [time] today, schedule for the next day.
    if now > target_time:
        target_time += timedelta(days=1)
    
    # Calculate the number of seconds until [time]
    time_to_wait = (target_time - now).total_seconds()
    
    print(f"Waiting {time_to_wait / 3600:.2f} hours until [time]...")
    await asyncio.sleep(time_to_wait)

async def check_and_notify(topic, start = 0, max_results = 5, hour = 9, minute = 0, second = 0):
    """Check for new articles and notify"""
    notifier = DesktopNotifier(app_name="arXiv Notifier")
    stop_event = asyncio.Event()

    await wait_until_time(hour, minute, second)  # Wait until [time] before proceeding
    articles = get_papers(topic, start, max_results)
    for article in articles:
        await notifier.send(
            title=f"Title: {article['title']}",
            message=f"Link: {article['id']}",
            urgency=Urgency.Normal,
            on_clicked=lambda: (webbrowser.open_new_tab(article['id'])),
            sound=DEFAULT_SOUND,
        )

    await stop_event.wait()
    print("Notification clicked, stopping the script.")

    # Run the event loop forever to respond to user interactions with the notification.
    event = asyncio.Event()

    if platform.system() != "Windows":
        # Handle SIGINT and SIGTERM gracefully on Unix.
        loop = asyncio.get_running_loop()
        loop.add_signal_handler(signal.SIGINT, event.set)
        loop.add_signal_handler(signal.SIGTERM, event.set)

    await event.wait()


if __name__ == "__main__":
    # do param security checks
    topic = quote("machine learning")
    hour = 17
    minute = 30
    second = 0
    try:
        asyncio.run(check_and_notify(topic, hour, minute, second))
    except KeyboardInterrupt:
        # Handle KeyboardInterrupt gracefully on Windows
        pass