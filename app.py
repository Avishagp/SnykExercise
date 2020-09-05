from flask import Flask
import requests
import json

app = Flask(__name__)


class Package:
    """
    Members:
        string name - package's name
        string version - package's version or tag
        Package list deps - package's dependencies
    Class members:
        dictionary CACHE - Holds cache of all packages.
    """
    CACHE = {}  # {package_name+package_version : package_class_instance}

    def __init__(self, name, version):
        """
        :param name: Package's name
        :param version: Package's version/tag
        """
        self.name = name
        self.version = version
        self.deps = None
        Package.CACHE[self.name + self.version] = self  # Add package to cache

    def add_dependencies(self, dependencies):
        """
        Add all dependencies to self.deps, creating a Package class instance if the dependency isn't in CACHE.
        :param dependencies: Dictionary of dependencies. Key is the dependency name, value is it's version/tag
        """
        for name, ver in dependencies.items():
            # Get the version number - lose the ~/^
            # "my_dep": "^1.0.0"
            # "my_dep": "~1.0.0"
            ver = ver.lstrip(['^', '~'])
            pkg_name = name + ver

            # Either get the package instance from the cache or create a new one
            pkg = Package.CACHE.get(pkg_name, Package(name, ver))
            # Add Package instance to the dependencies list
            self.deps.append(pkg)

    def discover_deps(self):
        """
        Get all the package's dependencies and update self.deps
        """
        # Send a Get request to obtain all package's dependencies using URL format
        self.deps = []
        response = requests.get(f"https://registry.npmjs.org/{self.name}/{self.version}")
        pkg_info = response.json()

        # Dependencies appear in json under 'dependencies' OR under 'devDependencies'
        if 'dependencies' in pkg_info:
            self.add_dependencies(pkg_info['dependencies'])
        elif 'devDependencies' in pkg_info:
            self.add_dependencies(pkg_info['devDependencies'])


#
# Gets a list of strings. Each string represents a dependency.
# Resturns TODO
#
def create_tree(dependencies):
    return


#
# Gets a string package name and a version string.
# Returns TODO
#
@app.route('/<pkg_name>/<version>')
def present_dependencies(pkg_name, version):
    pkg = Package(pkg_name, version)
    pkg.discover_deps()
    print(pkg.deps, pkg.CACHE)


if __name__ == '__main__':
    app.run()
