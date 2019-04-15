# coding=utf-8

from email.utils import make_msgid
from string import Template
import re

from bs4 import BeautifulSoup
from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from pygments.lexers.html import HtmlLexer

from dualis_connector.results_handler import extract_course_name_from_result_page
from version_recorder import CollectionOfChanges

"""
Encapsulates the formatting of the various notification-mails.
"""

# for the following template strings, viewer discretion is advised.
# No, I personally don't want to write them with these ugly table layouts and inline styles.
# But the mail clients leave me no other choice...

main_wrapper = Template('''
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
    <html xmlns="http://www.w3.org/1999/xhtml">
    <head></head>
    <body style="padding: 17px; background-color: #fefefe; font-family: 'Segoe UI', 'Calibri', 'Lucida Grande', Arial, sans-serif;">
        <div style="background-color: #ffffff; border: 1px solid #dfdede;">
            <table border-spacing="0" cellspacing="0" cellpadding="0" border="0" style="margin-bottom: 17px; width: 100%; border-spacing: 0;">
                <tbody><tr>
                    <td style="vertical-align: middle; width: 400px; padding: 0; margin: 0;">
                        <img src="cid:${header_cid}" style="height: 70px;"/>
                    </td>
                    <td style="vertical-align: middle; width: auto; padding: 0; margin: 0;">
                        <img src="cid:${extender_cid}" style="height: 70px; width: 100%;"/>
                    </td>
                </tr></tbody>
            </table>

            <div style="margin: 20px; margin-bottom: 0;">
                <p>${introduction_text}</p>

                ${content}
            </div>
        </div>
    </body>
</html>
''')

error_message_box = Template('''
    <table style="width: 100%; background-color: #ff3860; color: #fff; margin-bottom: 15px;">
        <tr>
            <td style="font-family: 'Segoe UI', 'Calibri', 'Lucida Grande', Arial, sans-serif; padding: 15px; padding-top: 7px; padding-bottom: 7px;">
                    ${details}
            </td>
        </tr>
    </table>
''')

info_message_box = Template('''
    <table style="width: 100%; background-color: #23d160; color: #fff; margin-bottom: 15px; padding: 10px;">
        <tr>
            <td style="font-family: 'Segoe UI', 'Calibri', 'Lucida Grande', Arial, sans-serif; padding: 15px; padding-top: 7px; padding-bottom: 7px;">
                <p>
                    ${text}
                </p>
            </td>
        </tr>
    </table>
''')

diff_dualis_main_box = Template('''
    <table style="width: 100%;">
        <thead style="heigth: 0"><tr>
            <td style="width: 17px"/>
            <td style="width: auto"/>
        </tr></thead>
        <tbody>
            ${content}
            
            <tr style="height: 50px">
                <td colspan="2">
                    <a style="border: 1px solid #e2001a; border-radius: 3px; padding: 3px; padding-left: 5px; padding-right: 7px; color: #e2001a; text-decoration: none !important;"
                        target="_blank"
                        href="https://dualis.dhbw.de/scripts/mgrqispi.dll?APPNAME=CampusNet&PRGNAME=EXTERNALPAGES&ARGUMENTS=-N000000000000001,-N000324,-Awelcome">
                                <span style="text-decoration: none !important; font-family: 'Segoe UI', 'Calibri', 'Lucida Grande', Arial, sans-serif;">Dualis öffnen »</span>
                    </a>
                </td>
            </tr>
        </tbody>
    </table>
''')

diff_dualis_added_box = Template('''
    <tr>
        <td style="padding-bottom: 24px; color: #7d878d; font-size: 17px; font-family: 'Segoe UI', 'Calibri', 'Lucida Grande', Arial, sans-serif;">
            +
        </td>
        <td style="padding-bottom: 24px; color: #7d878d; font-size: 20px; font-family: 'Segoe UI', 'Calibri', 'Lucida Grande', Arial, sans-serif;">
            ${course_name}
        </td>
    </tr>
''')

diff_dualis_deleted_box = Template('''
    <tr>
        <td style="padding-bottom: 24px; color: #7d878d; font-size: 17px; font-family: 'Segoe UI', 'Calibri', 'Lucida Grande', Arial, sans-serif;">
            ‒
        </td>
        <td style="padding-bottom: 24px; color: #7d878d; font-size: 20px; font-family: 'Segoe UI', 'Calibri', 'Lucida Grande', Arial, sans-serif;">
            ${course_name}
        </td>
    </tr>
''')

diff_dualis_modified_box = Template('''
    <tr>
        <td style="color: #7d878d; font-size: 17px; font-family: 'Segoe UI', 'Calibri', 'Lucida Grande', Arial, sans-serif;">
            ≠
        </td>
        <td style="color: #7d878d; font-size: 20px; font-family: 'Segoe UI', 'Calibri', 'Lucida Grande', Arial, sans-serif;">
            ${course_name}
        </td>
    </tr>
    <tr>
        <td colspan="2" style="padding-bottom: 10px;">
            <table>
                <tbody>
                    <tr>
                        <td style="background: #272822">
                            ${code_content}
                        </td>
                    </tr>
                </tbody>
            </table>
        </td>
    </tr>
''')

diff_schedule_modified_box = Template('''
    <div style="margin-bottom: 7px; padding: 15px;">
        <table style="margin-top: 10px; background: #272822">
            <tr>
                <td>
                    ${code_content}
                </td>
            </tr>
        </table>
        <table style="padding-top: 14px; padding-left: 7px;">
            <tr><td>
                <a style="border: 1px solid #e2001a; border-radius: 3px; padding: 3px; padding-left: 5px; padding-right: 7px; color: #e2001a; text-decoration: none !important;"
                    target="_blank"
                    href="http://vorlesungsplan.dhbw-mannheim.de/index.php?action=view&gid=3067001&uid=${uid}">
                    <span style="text-decoration: none !important; font-family: 'Segoe UI', 'Calibri', 'Lucida Grande', Arial, sans-serif;">Kalendar öffnen »</span>
                </a>
            </td></tr>
        </table>
    </div>
''')


def _format_code(html_code):
    # syntax highlighting:
    code_highlighted = highlight(html_code, HtmlLexer(), HtmlFormatter(style='monokai', noclasses=True))
    # add formatting for diff-markers:
    common_diff_style = ' margin-right: 3px; padding-right: 7px; padding-left: 7px;'
    code_formatted = code_highlighted \
        .replace('[-', '<span style="background: #71332c;' + common_diff_style + '">') \
        .replace('-]', '</span>') \
        .replace('{+', '<span style="background: #2e4d28;' + common_diff_style + '">') \
        .replace('+}', '</span>')

    # wrap in general layout:
    code_wrapped = '<div style="color: #efefef; margin: 3px; margin-left: 17px;line-height: 150%%;">%s</div>'\
                   %(code_formatted)

    return code_wrapped

def _finish_with_main_wrapper(content: str, introduction: str) -> (str, {str : str}):
    # cids link the attatched media-files to be displayed inline
    header_cid = make_msgid()
    extender_cid = make_msgid()

    full_content = main_wrapper.substitute(
        content=content, introduction_text=introduction,
        header_cid=header_cid[1:-1], extender_cid=extender_cid[1:-1]
    )

    cids_and_filenames = {}
    cids_and_filenames.update({header_cid : 'header.png'})
    cids_and_filenames.update({extender_cid: 'header_extender.png'})

    return (full_content, cids_and_filenames)


def _redact_grades(content):
    return re.sub(r'\d{1,3},\d{1,2}', '<span style="color:#a49aad; font-style:italic; font-weight:bold;">Note</span>', content)

def create_full_dualis_diff_mail(changes: CollectionOfChanges, course_names: {str, str}) -> (str, {str : str}):
    inner_diff_content = ''

    for added_element_id in changes.added:
        inner_diff_content += diff_dualis_added_box.substitute(
            course_id=added_element_id, course_name=course_names[added_element_id]
        )

    for deleted_element_id in changes.deleted:
        deleted_name = extract_course_name_from_result_page(
            BeautifulSoup(changes.deleted[deleted_element_id], 'html.parser')
        )

        inner_diff_content += diff_dualis_deleted_box.substitute(
            course_id=deleted_element_id, course_name=deleted_name
        )

    for modified_element_id in changes.modified:
        inner_diffs = ''
        inner_diffs_fragments = changes.modified[modified_element_id]
        for fragment in inner_diffs_fragments:
            inner_diffs += _format_code(fragment)

        inner_diff_content += diff_dualis_modified_box.substitute(
            course_id=modified_element_id, course_name=course_names[modified_element_id],
            code_content=inner_diffs
        )

    inner_diff_content = _redact_grades(inner_diff_content)

    full_diff_content = diff_dualis_main_box.substitute(
        content=inner_diff_content
    )

    count = changes.diff_count

    full_content = _finish_with_main_wrapper(
        full_diff_content,
        'Es wurden Änderungen an %s Modulen festgestellt:'%(count) if count > 1 else\
            'Am folgenden Modul würde Veränderung festgestellt:'
    )

    return full_content

def _format_special_ical(code):
    # Make Timestamps a bit more readable:
    # i.e.: 20170402T1337   ->   02.04.2017 13:37
    #       \1  \2\3 \4\5        \3 \2 \1   \4 \5
    code = re.sub(r':(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})', r':\3.\2.\1 \4:\5', code)

    # Increase readability further with more spacing:
    code = code\
            .replace('UID:',      '<b>UID: </b>', )\
            .replace('LOCATION:', '<b>LOCATION: </b>', )\
            .replace('SUMMARY:',  '<b>SUMMARY: </b>', )\
            .replace('DTSTART:',  '<b>DTSTART: </b>', )\
            .replace('DTEND:',    '<b>DTEND: </b>', )\
            .replace('DTSTAMP:',  '<b>DTSTAMP: </b>', )\
            .replace('@', ' @ ')\
            .replace('BEGIN:VEVENT', '\nBEGIN:VEVENT')

    return code

def create_full_schedule_diff_mail(changes: [str], uid: str) -> (str, {str : str}):
    content = ''

    inner_diffs = ''
    for fragment in changes:
        inner_diffs += _format_special_ical(_format_code(fragment))

    content += diff_schedule_modified_box.substitute(
        code_content=inner_diffs, uid=uid
    )

    full_content = _finish_with_main_wrapper(
        content,
        'Es wurden die folgenden %s Änderungen festgestellt:' % (len(changes) - 1) if len(changes) > 1 else\
            'Es wurde die folgende Änderung festgestellt:'
    )

    return full_content

def create_full_welcome_mail() -> (str, {str : str}):
    content = info_message_box.substitute(text='Hurra, es funktioniert \\o/')

    full_content = _finish_with_main_wrapper(content, 'Willkommen! Test Test...')

    return full_content

def create_full_error_mail(details) -> (str, {str : str}):
    content = error_message_box.substitute(details=details)

    full_content = _finish_with_main_wrapper(content, 'Bei der Ausführung ist der folgende Fehler aufgetreten:')

    return full_content
