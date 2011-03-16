import re
import xmlrpclib
from urllib import urlopen

try:
    import simplejson as json
except ImportError:
    import json

API_TARGET = "https://sourceforge.net/api"

class SourceforgeError(Exception):
    """An error occurred when making a request to the Sourceforge API"""

class SourceforgeHandler(BaseHandler):
    title = "Sourceforge"
    url = "https://sourceforge.net"
    repo_regex = r'https://sourceforge.com/[\w\-\_]+/([\w\-\_]+)/{0,1}'
    slug_regex = r'https://sourceforge.com/[\w\-\_]+/([\w\-\_]+)/{0,1}'

    '''
    def _name_from_pypi_home_page(home_page):
        name1 = project_name1_RE.search(home_page)
        if name1:
            name1 = name1.group(1)
        name2 = project_name2_RE.search(home_page)
        if name2:
            name2 = name2.group(1)
            if name2 == 'www':
                name2 = None
        return name1 or name2
    '''

    def fetch_metadata(self, package):
        sourceforge = '';

        repo_name = package.repo_name()
        target = API_TARGET + "/projects/name/" + repo_name
        if not target.endswith("/"):
            target += "/"

        # sourceforge project API requires ending with /json/
        target += "json/"

        # open the target and read the content
        response = urlopen(target)
        response_text = response.read()

        # dejson the results
        try:
            data = json.loads(response_text)
        except jason.decoder.JSONDecodeError:
            raise SourceforgeError("unexpected response from sourceforge.net %d: %r" % (
                                   response.status, response_text))

        # sourceforge has both developers and maintainers in a list
        participants = data.get("developers").append(data.get("maintainers"))
        package.participants = [p['name'] for p in participants]

        package.repo_description = data.get("description")

        project_name = _name_from_pypi_home_page(package.pypi_home_page)
        # dejsonify the results
        try:
            sf_package_data = _get_project_data(project_name)
        except json.decoder.JSONDecodeError:
            message = "%s had a JSONDecodeError while loading %s" % (package.title,
                                                                     package_json_path)
            warn(message)
            return package
        package.repo_watchers = len(sf_package_data.get('maintainers', [])) + len(sf_package_data.get('developers', [])) 
        package.repo_description = sf_package_data.get('description', '')
        # TODO - remove the line below and use repo_url as your foundation    
        package.repo_url = _get_repo_url(sf_package_data)
        package.repo_forks = None

        return package

    def _get_project_data(project_name):
        if project_name == None:
            return None
        project_json_path = 'http://sourceforge.net/api/project/name/%s/json/' % project_name
        # open the target and read the content
        response = urlopen(project_json_path)
        response = response.read()
        # dejsonify the results
        try:
            project_data = json.loads(response)['Project']
        except KeyError:  # project does not exist
            project_data = None
        except ValueError:  # likely invalid chars in json file
            project_data = None
        return project_data


    def _get_repo_url(package_data):
        # Sourceforge API does not have Hg, Bzr, or Git support
        if 'SVNRepository' in package_data:
            return package_data['SVNRepository'].get('location', '')
        elif 'CVSRepository' in package_data:
            return package_data['CVSRepository'].get('anon-root', '')
        else:
            return ''
