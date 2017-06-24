#!/usr/bin/env python

import hashlib
import sh

from IPython import embed
import requests
import rosdistro
from rosdistro.distribution_cache_generator import generate_distribution_cache
from rosinstall_generator.distro import (
    get_recursive_dependencies,
    generate_rosinstall
)

ROSDISTRO_URL = 'https://raw.githubusercontent.com/ros/rosdistro/master/index.yaml'


def main():
    rosdistro_index = rosdistro.get_index(ROSDISTRO_URL)

    cache = generate_distribution_cache(rosdistro_index, 'indigo')
    cached_distro = rosdistro.get_cached_distribution(rosdistro_index, 'indigo', cache=cache)

    root_packages = {'roscpp'}

    package_names = root_packages.union(
        get_recursive_dependencies(cached_distro, root_packages))

    print(f'Bundling {len(package_names)} packages')

    rosinstall_data = generate_rosinstall(
        cached_distro, package_names, flat=True, tar=True)

    remote_files = []

    for rosinstall_pkg in rosinstall_data:
        name = rosinstall_pkg['tar']['local-name']
        url = rosinstall_pkg['tar']['uri'].replace('.tar.gz', '.zip')
        print(name, url)

        # Fetch tarball to get its sha1sum
        r = requests.get(url)
        r.raise_for_status()
        sha1sum = hashlib.sha1(r.content).hexdigest()

        remote_files.append({
            'name': name,
            'url': url,
            'sha1': sha1sum,
        })

    sh.mkdir('-p', 'ros')

    with open('ros/BUCK', 'w') as out_f:
        for rf in remote_files:
            s = f"""remote_file(
  name = '{rf['name']}',
  url = '{rf['url']}',
  sha1 = '{rf['sha1']}'
)
"""
            out_f.write(s)        


if __name__ == '__main__':
    main()
