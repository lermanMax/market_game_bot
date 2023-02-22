import schedule
import threading
import time


def run_continuously(interval=1):
    """Continuously run, while executing pending jobs at each
    elapsed time interval.
    @return cease_continuous_run: threading. Event which can
    be set to cease continuous run. Please note that it is
    *intended behavior that run_continuously() does not run
    missed jobs*. For example, if you've registered a job that
    should run every minute and you set a continuous run
    interval of one hour then your job won't be run 60 times
    at each interval but only once.
    """
    cease_continuous_run = threading.Event()

    class ScheduleThread(threading.Thread):
        @classmethod
        def run(cls):
            while not cease_continuous_run.is_set():
                schedule.run_pending()
                time.sleep(interval)

    continuous_thread = ScheduleThread()
    continuous_thread.start()
    return cease_continuous_run


def background_job():
    print('Hello from the background thread')


# def job():
#     print("I'm working...")

# # Start the background thread
# stop_run_continuously = run_continuously(interval=2)

# # Do some other things...
# schedule.every(2).seconds.do(background_job)
# for i in range(10):
#     time.sleep(1)
#     print(i)
# job_sc = schedule.every(3).seconds.do(job)
# for i in range(10):
#     time.sleep(1)
#     print(i)
# schedule.cancel_job(job_sc)
# for i in range(10):
#     time.sleep(1)
#     print(i)

# # Stop the background thread
# stop_run_continuously.set()


# schedule.every().minutes.do(job)
# schedule.every().day.at("17:22").do(job)

# while True:
#     schedule.run_pending()
#     time.sleep(20)
