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

def fetch_arxiv_articles(search_query, max_results=1):
    """Fetch Arxiv articles based on the search query."""
    base_url = 'http://export.arxiv.org/api/query?'
    query = f'search_query={search_query}&start=0&max_results={max_results}&sortBy=submittedDate&sortOrder=descending'
    try:
        feed = feedparser.parse(base_url + query)
    except Exception as e:
        print(f"Error fetching Arxiv articles: {e}")
        return None    
    entries = [{'id': entry.id, 'title': entry.title, 'summary': entry.summary, 'link': entry.link} for entry in feed.entries]
    return entries

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

async def check_and_notify(hour, minute) -> None:
    """Check for new articles and notify"""
    # Function to check and notify new articles
    articles = fetch_arxiv_articles('hackathons')
    #articles = [{'id': '1', 'title': 'Hackathons', 'summary': 'Hackathons are fun', 'link': 'https://arxiv.org'}] # sample article while waiting for enough time to pass due to arxiv query rates
    notifier = DesktopNotifier(app_name="Sample App")
    stop_event = asyncio.Event()

    await wait_until_time(hour,minute)  # Wait until [time] before proceeding

    for article in articles:
        await notifier.send(
            title="New Arxiv Article on Hackathons",
            message=f"Title: {article['title']}\nLink: {article['link']}",
            urgency=Urgency.Normal,
            on_clicked=lambda: (webbrowser.open_new_tab(article['link'])),
            on_dismissed=lambda: print("Notification dismissed"),
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
    try:
        asyncio.run(check_and_notify(16, 39))
    except KeyboardInterrupt:
        # Handle KeyboardInterrupt gracefully on Windows.
        pass