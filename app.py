from flask import Flask
import requests
import json

app = Flask(__name__)


class Package:
    CACHE = {}

    def __init__(self, name, version):
        self.name = name
        self.version = version
        self.deps = None
        Package.CACHE[self.name + self.version] = self

    def add_dependencies(self, dependencies):
        for name, ver in dependencies.items():
            # "my_dep": "^1.0.0"
            # "my_dep": "~1.0.0"
            ver = ver.lstrip(['^', '~'])
            pkg_name = name + ver

            # Either get the package instance from the cache or create a new one
            pkg = Package.CACHE.get(pkg_name, Package(name, ver))
            # Add Package instance to the dependencies list
            self.deps.append(pkg)

    def discover_deps(self):
        if self.deps is not None:
            return

        # Need to discover dependencies since it hasn't been done before
        self.deps = []
        response = requests.get(f"https://registry.npmjs.org/{self.name}/{self.version}")
        pkg_info = response.json()

        # dependencies appear in json under 'dependencies' OR under 'devDependencies'
        if 'dependencies' in pkg_info:
            self.add_dependencies(pkg_info['dependencies'])
        elif 'devDependencies' in pkg_info:
            self.add_dependencies(pkg_info['devDependencies'])


#
# Gets a list of strings. Each string represents a dependency.
# Resturns TODO
#
def create_tree(dependencies):
    return 0


#
# Gets a string package name and an optional version string.
# Returns TODO
# TODO get latest version number
#
@app.route('/present/<pkg_name>/<version>')
def present_dependencies(pkg_name, version):
    pass


if __name__ == '__main__':
    app.run()
