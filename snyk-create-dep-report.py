import os
import snyk
import csv
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
import requests
import csv
from tqdm import tqdm


def write_csv(data_list, org_slug, proj_id, proj_name, report_type):
    # Write data to CSV file in dep_reports directory
    os.makedirs('dep_reports', exist_ok=True)
    with open(f'dep_reports/{org_slug}_{report_type}_Deps.csv', 'a', newline='') as csvfile:
        fieldnames = ['Organization', 'Project Name', 'Project ID', 'Project URL', 'Dependency',
                      'Current Version', 'License', 'Is Deprecated', 'Latest Version', 'Last Version Published']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        # Write header if file is empty
        csvfile.seek(0, os.SEEK_END)
        if csvfile.tell() == 0:
            writer.writeheader()

        # Write each dependency to CSV
        for dependency in data_list:
            deprecated = dependency.get('deprecated', 'N/A')
            version = dependency.get('version', 'N/A')
            latestVersion = dependency.get('latestVersion', 'N/A')
            latestVersionPublishedDate = dependency.get(
                'latestVersionPublishedDate', 'N/A')

            if len(dependency['licenses']) > 0:
                license = dependency['licenses'][0]['id']
            else:
                license = "N/A"

            writer.writerow({
                'Organization': org_slug,
                'Project Name': f"{proj_name}",
                'Project ID': f"{proj_id}",
                'Project URL': f"https://app.snyk.io/org/{org_slug}/project/{proj_id}/",
                'Dependency': dependency['name'],
                'Current Version': version,
                'License': license,
                'Is Deprecated': deprecated,
                'Latest Version': latestVersion,
                'Last Version Published': latestVersionPublishedDate
            })


def get_deps(driver, org_slug, proj_id,
             proj_snapshot, isTransitive, useDeprecatedFilter, isDeprecated):
    # Retrieve dependencies from the Snyk API
    page = 1
    dep_list = []
    if (useDeprecatedFilter):
        url = f'https://app.snyk.io/org/{org_slug}/project/{proj_id}/dependencies/{proj_snapshot}?page={page}&sortBy=name&sortDirection=ASC&deprecated={isDeprecated}&isTransitive={isTransitive}'
    else:
        url = f'https://app.snyk.io/org/{org_slug}/project/{proj_id}/dependencies/{proj_snapshot}?page={page}&sortBy=name&sortDirection=ASC&isTransitive={isTransitive}'

    while True:
        headers = {
            'accept': 'application/json',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/json',
            'origin': 'https://app.snyk.io',
            'priority': 'u=1, i',
            'referer': f'https://app.snyk.io/org/{org_slug}/project/{proj_id}/',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        }
        cookies = driver.get_cookies()
        snyk_cookies = {}
        for cookie in cookies:
            snyk_cookies[cookie['name']] = cookie['value']

        try:
            response = requests.get(url, headers=headers, cookies=snyk_cookies)
            response.raise_for_status()
            if response.status_code == 200:
                data = response.json()
                if len(data['dependencies']) > 0:
                    dep_list.extend(data['dependencies'])
                if data['maxPage'] > page:
                    page += 1
                else:
                    break
            else:
                print(
                    f"Failed to fetch data for page {page}. Status code: {response.status_code}")

        except requests.exceptions.HTTPError as err:
            print(f'HTTP ERROR: {err}')
            raise
        except Exception as e:
            print(f'ERROR: {e}')
            raise
    return dep_list


def get_poject_data(driver, isTransitive, useDeprecatedFilter,
                    isDeprecated):
    # Retrieve project data
    if isTransitive.lower() == 'false':
        report_type = "Direct"
    else:
        report_type = "Transitive"

    snyk_token = os.getenv('SNYK_TOKEN')
    if not snyk_token:
        raise ValueError(
            "Snyk API token is not provided. Set the SNYK_TOKEN environment variable.")

    client = snyk.SnykClient(token=snyk_token, tries=4,
                             delay=1, backoff=4, debug=False)

    orgs = client.organizations.all()
    num_orgs = len(orgs)
    # for org in orgs:
    for org in tqdm(orgs, desc='Organizations', unit='org', total=num_orgs):
        org_id = org.id
        org_slug = org.slug

        for proj in client.organizations.get(org_id).projects.all():
            dep_list = []
            proj_id = proj.id
            proj_name = proj.name

            if proj.type not in ["dockerfile", "sast", "k8sconfig", "linux", "apk", "deb"] and "config" not in proj.type:
                snapshot = proj._get_project_snapshot()
                proj_snapshot = snapshot.get('id')
                get_data = get_deps(driver, org_slug, proj_id,
                                    proj_snapshot, isTransitive, useDeprecatedFilter, isDeprecated)
                dep_list.extend(get_data)
                write_csv(dep_list, org_slug, proj_id, proj_name, report_type)


def main():
    # Variables for the type of deps you want
    isTransitive = "false"
    '''
    * If useDeprecatedFilter is True,
    *  then it will filter out dependencies based on the isDeprecated filter
    *
    * If useDeprecatedFilter is False,
    *   then it will include all direct or transitive dependencies
    '''
    useDeprecatedFilter = False
    isDeprecated = "false"

    # Set up Selenium
    driverPath = ChromeDriverManager().install()
    service = Service(executable_path=driverPath)
    driver = webdriver.Chrome(service=service)

    loginURL = 'https://app.snyk.io'

    print('Loading Snyk login page....')
    driver.get(loginURL)

    if 'app.snyk.io/login' in driver.current_url:
        print('Please Login to Snyk')
        WebDriverWait(driver, timeout=120).until(
            EC.url_contains('app.snyk.io/org/'))

        print(f'Press ENTER to get Snyk data: ')
        driver.minimize_window()
        input('>_ ')
        get_poject_data(driver, isTransitive, useDeprecatedFilter,
                        isDeprecated)


if __name__ == "__main__":
    main()
