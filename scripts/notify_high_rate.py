#!/usr/bin/python3

import argparse
import base64
import requests
import smtplib
import ssl

from email.mime.text import MIMEText
from lxml import etree


STATUS_URL_FORMAT = 'http://{}/meas.xml'
STATUS_CACHE = '/opt/var/lib/overmind/.ratechage'


class FetchError(Exception):
    """Errors fetching Wattrouter status"""
    pass


def notify(smtp: str, recipients: list, subject: str, content: str):
    with open(smtp, 'r') as pwf:
        smtp_data = base64.b64decode(pwf.read())
    smtp_addr, smtp_port, sender, password = smtp_data.split(':')

    msg = MIMEText(content)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ', '.join(recipients)

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_addr, smtp_port, context=context) as srv:
        srv.login(sender, password)
        srv.sendmail(sender, recipients, msg.as_string())


def get_current_wattrouter_state(address: str, root_element: str = 'meas') -> etree.Element:
    try:
        req = requests.get(STATUS_URL_FORMAT.format(address))
    except requests.exceptions.ConnectionError:
        raise FetchError('Wattrouter not reachable on {}'.format(address))
    
    doc = etree.XML(req.content)
    root = doc.find(root_element)
    if not root:
        raise FetchError('Did not find root element ({}) in response'.format(root_element))
    return doc


def rate_state(address: str, rate_element: str = 'ILT', root_element: str = 'meas') -> int:
    state = get_current_wattrouter_state(address, root_element=root_element)

    low_rate = state.find(rate_element)
    if not low_rate:
        raise FetchError('Did not find rate element ({}) in response'.format(rate_element))
    
    try:
        result = int(low_rate.text)
    except ValueError:
        raise FetchError('Unexpected value of rate: {}'.format(low_rate.text))
    return result


def main():
    parser = argparse.ArgumentParser(
        prog = 'notify_high_rate',
        description = 'Reports change of rate level')
    parser.add_argument('-w', '--wattrouter', default='192.168.0.10')
    parser.add_argument('-s', '--smtp', default='/opt/etc/overmind/.notification')
    parser.add_argument('-r', '--recipient', action="extend", nargs="+", type=str)
    parser.add_argument('-u', '--subject', default='[overmind] Změna tarifu')
    parser.add_argument('-t', '--template', default='Byla zaznamenána změna tarifu ceny elektrické energie na: \{\}')
    parser.add_argument('--hr', default='VT')
    parser.add_argument('--lr', default='NT')
    args = parser.parse_args()
    
    try:
        curr_rate = rate_state(args.wattrouter)
        with open(STATUS_CACHE, 'r') as cache:
            last_rate = int(cache.read())
        with open(STATUS_CACHE, 'w') as cache:
            cache.write(curr_rate)
    except FetchError as ex:
        notify(args.smtp, args.recipient, args.subject, 'Failed to fetch state: {}'.format(str(ex)))
    except OSError as ex:
        notify(args.smtp, args.recipient, args.subject, 'Failed to cache state: {}'.format(str(ex)))

    if curr_rate == last_rate:
        return
    if last_rate < curr_rate:
        notify(args.smtp, args.recipient, args.subject, args.template.format(args.lr))
    if last_rate > curr_rate:
        notify(args.smtp, args.recipient, args.subject, args.template.format(args.hr))

    
if __name__ == '__main__':
    main()

    

