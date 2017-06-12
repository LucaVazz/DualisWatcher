from email.utils import make_msgid
from string import Template

from bs4 import BeautifulSoup
from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from pygments.lexers.html import HtmlLexer

from dualis_connector.results_handler import extract_course_name_from_result_page
from version_recorder import CollectionOfDiffIds

# for the following template strings, viewer discretion is advised.
 # No, I personally don't want to write them with these ugly table layouts and inline styles.
 # But the mail clients leave me no other choice...

main_wrapper = Template('''
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">    
    <html xmlns="http://www.w3.org/1999/xhtml">
    <head></head>
    <body style="padding: 17px; background-color: #efefef; font-family: 'Segoe UI', 'Calibri', 'Lucida Grande', Arial, sans-serif;">
        <div style="background-color: #fefefe; border: 1px solid #dfdede;">
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

diff_added_box = Template('''
    <div style="margin-top: 17px; margin-bottom: 7px; padding: 15px;">
        <table style="width: 100%;">
            <tbody><tr>
                <td style="width: 17px; color: #7d878d; font-size: 17px; font-family: 'Segoe UI', 'Calibri', 'Lucida Grande', Arial, sans-serif;">
                    +
                </td>
                <td style="width: auto; color: #7d878d; font-size: 20px; font-family: 'Segoe UI', 'Calibri', 'Lucida Grande', Arial, sans-serif;">
                    ${course_name}
                </td>
                <td style="width: 170px; font-align: center">
                    <a style="border: 1px solid #e2001a; border-radius: 3px; padding: 3px; padding-left: 5px; padding-right: 7px; color: #e2001a; text-decoration: none !important;" 
                        target="_blank"   
                        href="https://dualis.dhbw.de/scripts/mgrqcgi?APPNAME=CampusNet&PRGNAME=RESULTDETAILS&ARGUMENTS=-N${token},-N000307,-N${course_id}">
                        <span style="text-decoration: none !important; font-family: 'Segoe UI', 'Calibri', 'Lucida Grande', Arial, sans-serif;">komplett anzeigen »</span>
                    </a>
                </td>
            </tr></tbody>
        </table>
    </div>
''')

diff_deleted_box = Template('''
    <div style="margin-top: 17px; margin-bottom: 7px; padding: 15px;">
        <table style="width: 100%;">
            <tbody><tr>
                <td style="width: 17px; color: #7d878d; font-size: 17px; font-family: 'Segoe UI', 'Calibri', 'Lucida Grande', Arial, sans-serif;">
                    ‒
                </td>
                <td style="width: auto; color: #7d878d; font-size: 20px; font-family: 'Segoe UI', 'Calibri', 'Lucida Grande', Arial, sans-serif;">
                    ${course_name}
                </td>
                <td style="width: 170px; font-align: center">
                </td>
            </tr></tbody>
        </table>
    </div>
''')

diff_modified_box = Template('''
    <div style="margin-top: 17px; margin-bottom: 7px; padding: 15px;">
        <table style="width: 100%;">
            <tbody><tr>
                <td style="width: 17px; color: #7d878d; font-size: 17px; font-family: 'Segoe UI', 'Calibri', 'Lucida Grande', Arial, sans-serif;">
                    ≠
                </td>
                <td style="width: auto; color: #7d878d; font-size: 20px; font-family: 'Segoe UI', 'Calibri', 'Lucida Grande', Arial, sans-serif;">
                    ${course_name}
                </td>
                <td style="width: 170px; font-align: center">
                    <a style="border: 1px solid #e2001a; border-radius: 3px; padding: 3px; padding-left: 5px; padding-right: 7px; color: #e2001a; text-decoration: none !important;" 
                        target="_blank"   
                        href="https://dualis.dhbw.de/scripts/mgrqcgi?APPNAME=CampusNet&PRGNAME=RESULTDETAILS&ARGUMENTS=-N${token},-N000307,-N${course_id}">
                        <span style="text-decoration: none !important; font-family: 'Segoe UI', 'Calibri', 'Lucida Grande', Arial, sans-serif;">komplett anzeigen »</span>
                    </a>
                </td>
            </tr></tbody>
        </table>
        <table style="margin-top: 10px; background: #272822">
            <tr>
                <td>
                    ${code_content}
                </td>
            </tr>
        </table>
    </div>
''')


def _format_code(html_code):
    # syntax highlighting:
    code_highlighted = highlight(html_code, HtmlLexer(), HtmlFormatter(style='monokai', noclasses=True))
    # add formatting for diff-markers
    common_diff_style = ' margin-right: 3px; padding-right: 7px; padding-left: 7px;'
    code_formatted = code_highlighted \
        .replace('[-', '<span style="background: #71332c;' + common_diff_style + '">') \
        .replace('-]', '</span>') \
        .replace('{+', '<span style="background: #2e4d28;' + common_diff_style + '">') \
        .replace('+}', '</span>')

    code_wrapped = '<div style="color: #efefef; margin: 3px; margin-left: 17px;line-height: 150%%;">%s</div>'\
                   %(code_formatted)

    return code_wrapped

def _finish_with_main_wrapper(content: str, introduction: str):
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


def create_full_diff_mail(changes: CollectionOfDiffIds, results: {str : (str, str)}, token: str):
    content = ''

    for added_element_id in changes.added:
        content += diff_added_box.substitute(
            course_id=added_element_id, course_name=results[added_element_id][1], token=token
        )

    for deleted_element_id in changes.deleted:
        deleted_name = extract_course_name_from_result_page(
            BeautifulSoup(changes.deleted[deleted_element_id], 'html.parser')
        )

        content += diff_deleted_box.substitute(
            course_id=deleted_element_id, course_name=deleted_name
        )

    for modified_element_id in changes.modified:
        inner_diffs = ''
        inner_diffs_fragments = changes.modified[modified_element_id]
        for fragment in inner_diffs_fragments:
            inner_diffs += _format_code(fragment)

        content += diff_modified_box.substitute(
            course_id=modified_element_id, course_name=results[modified_element_id][1],
            code_content=inner_diffs, token=token
        )

    full_content = _finish_with_main_wrapper(
        content, 'Es wurden Änderungen an %s Modulen festgestellt:' % (changes.diff_count)
    )

    return full_content

def create_full_welcome_mail():
    content = info_message_box.substitute(text='Hurra, es funktioniert \\o/')

    full_content = _finish_with_main_wrapper(content, 'Willkommen! Test Test...')

    return full_content

def create_full_error_mail(details):
    content = error_message_box.substitute(details=details)

    full_content = _finish_with_main_wrapper(content, 'Bei der Ausführung ist der folgende Fehler aufgetreten:')

    return full_content
