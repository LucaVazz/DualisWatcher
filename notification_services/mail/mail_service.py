import logging
import traceback
from getpass import getpass

from notification_services.mail.mail_formater import create_full_welcome_mail, create_full_diff_mail, \
    create_full_error_mail
from notification_services.mail.mail_shooter import MailShooter
from notification_services.notification_service import NotificationService
from version_recorder import CollectionOfChanges


class MailService(NotificationService):
    def interactively_configure(self):
        do_mail_input = input('Do you want to activate Notifications via mail [y/n]?   ')
        while not (do_mail_input == 'y' or do_mail_input == 'n'):
            do_mail_input = input('Unrecognized input. Try again:   ')

        if do_mail_input == 'y':
            print('[The following Inputs are not validated!]')

            config_valid = False
            while not config_valid:
                sender = input('E-Mail-Address of the Sender:   ')
                server_host = input('Host of the SMTP-Server:   ')
                server_port = input('Port of the SMTP-Server:   ')
                username = input('Username for the SMTP-Server:   ')
                password = getpass('Password for the SMTP-Server [no output]:   ')
                target = input('E-Mail-Address of the Target:   ')

                print('Testing Mail-Config...')
                welcome_content = create_full_welcome_mail()
                mail_shooter = MailShooter(
                    sender, server_host, int(server_port), username, password
                )
                try:
                    mail_shooter.send(target, 'Hey!', welcome_content[0], welcome_content[1])
                except BaseException as e:
                    print('Error while sending the test mail: %s'%(str(e)))
                else:
                    input(
                        'Please check if you received the Welcome-Mail. If yes, confirm with Return.\n'
                        + 'If not, exit this program ([CTRL]+[C]) and try again later.'
                    )
                    config_valid = True

            mail_cfg = {
                'sender': sender,
                'server_host': server_host,
                'server_port': server_port,
                'username': username,
                'password': password,
                'target': target
            }

            self.config_helper.set_property('mail', mail_cfg)

    def notify_about_changes_in_results(self, changes: CollectionOfChanges, course_names: {str: str}, token: str) -> None:
        try:
            try:
                mail_cfg = self.config_helper.get_property('mail')
            except ValueError:
                logging.debug('Mail-Notifications not configured, skipping.')
                return

            logging.debug('Sending Notification via Mail...')
            mail_content = create_full_diff_mail(changes, course_names, token)

            mail_shooter = MailShooter(
                mail_cfg['sender'], mail_cfg['server_host'], int(mail_cfg['server_port']),
                mail_cfg['username'], mail_cfg['password']
            )
            mail_shooter.send(
                mail_cfg['target'],
                '%s neue Änderungen in den Modul-Ergebnissen!'%(changes.diff_count),
                mail_content[0], mail_content[1]
            )
        except:
            error_formatted = traceback.format_exc()
            logging.error('While sending notification:\n%s'%(error_formatted), extra={'exception':e})
            pass  # ignore the exception further up

    def notify_about_error(self, error_description: str):
        try:
            try:
                mail_cfg = self.config_helper.get_property('mail')
            except ValueError:
                logging.debug('Mail-Notifications not configured, skipping.')
                return

            logging.debug('Sending Error-Notification via Mail...')
            mail_content = create_full_error_mail(error_description)

            mail_shooter = MailShooter(
                mail_cfg['sender'], mail_cfg['server_host'], int(mail_cfg['server_port']),
                mail_cfg['username'], mail_cfg['password']
            )
            mail_shooter.send(
                mail_cfg['target'], 'Fehler!', mail_content[0], mail_content[1]
            )
        except:
            error_formatted = traceback.format_exc()
            logging.error('While sending notification:\n%s' % (error_formatted), extra={'exception':e})
            pass  # ignore the exception further up
