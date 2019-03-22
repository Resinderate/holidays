from collections import defaultdict

import datetime
from datetime import timedelta

import holidays
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

uk_holidays = holidays.CountryHoliday("England")


def _get_creds():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return creds


def _is_weekend(date):
    return date.weekday() >= 5


def _get_time_taken_off(start, end):
    start = datetime.datetime.strptime(start, "%Y-%m-%d").date()
    end = datetime.datetime.strptime(end, "%Y-%m-%d").date()

    days_off = (end - start).days
    days_off_as_dates = [
        start + timedelta(days=i)
        for i in range(days_off)
    ]
    days_off_excluding_holidays = [
        day
        for day in days_off_as_dates
        if day not in uk_holidays and not _is_weekend(day)
    ]
    return len(days_off_excluding_holidays)


def _get_days_off_for_year(year):
    service = build('calendar', 'v3', credentials=_get_creds())

    start_period = datetime.datetime(year, 1, 1).isoformat() + 'Z'
    end_period = datetime.datetime(year, 12, 31).isoformat() + 'Z'
    events_result = service.events().list(
        calendarId='originmarkets.com_vqm4e3bdr3j3ar49acoj39331c@group.calendar.google.com',
        timeMin=start_period,
        timeMax=end_period,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    events = events_result.get('items', [])

    number_of_days_taken_off = defaultdict(int)
    reasons = defaultdict(list)
    if not events:
        print('No upcoming events found.')
    for event in events:
        creator = event["creator"]["email"]
        start = event['start'].get('date')
        end = event['end'].get('date')
        summary = event["summary"]
        if start is None or end is None:
            # print("This uses datetime, skipping.. ", event["start"], creator)
            continue

        days_off = _get_time_taken_off(start, end)
        number_of_days_taken_off[creator] += days_off
        reasons[creator].append(summary)

    print("Days taken off for ", year)
    for employee, days_taken in sorted(number_of_days_taken_off.items()):
        print(employee, "--", days_taken)


def main():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    _get_days_off_for_year(2017)
    _get_days_off_for_year(2018)
    _get_days_off_for_year(2019)


if __name__ == '__main__':
    main()
    # main_x()
