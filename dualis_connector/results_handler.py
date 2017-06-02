from dualis_connector.request_helper import RequestHelper


class ResultsHandler:
    def __init__(self, request_helper: RequestHelper):
        self.request_helper = request_helper

    def fetch_semesters(self):
        page = self.request_helper.get_ressource('COURSERESULTS')

        results = []
        semester_entries = page.find('select', id='semester').findAll('option')
        for entry in semester_entries:
            semester_id = entry.attrs['value']
            results.append(semester_id)

        return results

    def fetch_courses(self, semester_id: str):
        page = self.request_helper.get_ressource('COURSERESULTS', semester_id)

        results = []
        course_entries = page.find('table', class_='nb list').find('tbody').findAll('tr')
        #                                 ^ because class is a reserved Python-keyword
        course_entries_without_gpa = course_entries[:-1]
        for entry in course_entries_without_gpa:
            # we need to extract the course id from the link to open the view
            link_raw = entry.find('a').attrs['href']
            link_arguments_raw = link_raw.split('ARGUMENTS=')[1]
            link_arguments = link_arguments_raw.split(',')
            course_id = link_arguments[2][len('-N'):] # drop the '-N' prefix
            results.append(course_id)

        return results

    def fetch_result(self, course_id: str):
        page = self.request_helper.get_ressource('RESULTDETAILS', course_id)
        return page