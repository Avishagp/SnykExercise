from flask import Flask
import requests
import json

app = Flask(__name__)


def translate_version_syntax(version):
    """
    Translate version number so it doesn't contain *, ^, ~, etc. Translation assumes lowest version number.
    :param version: current version number
    :return: numeric version number
    """
    # Check if version contains any letters other than x (might be a tag and not a version number)
    if any(c.isalpha() and c != 'x' and c != 'X' for c in version):
        return version

    # Handle cases where a space appears
    version = version.split()
    version = version[0]

    # Extend version number (for instance, 1.1 would be extended to 1.1.0)
    if len(version.split('.')) < 3:
        split_version = version.split('.')
        split_version += ['0'] * (3 - len(split_version))
        sep = '.'
        version = sep.join(split_version)

    # Translate version number (according to https://docs.npmjs.com/misc/semver)
    # 1.x.0 --> 1.0.0
    # 1.1.* --> 1.1.0
    # ^1.2.3 := >=1.2.3 <2.0.0
    # ~1.0.0 >=1.0.0 <2.0.0 (Same as 1.x)
    version = version.replace('x', '0')
    version = version.replace('X', '0')
    version = version.replace('*', '0')
    version = version.lstrip('~^<=> ')
    return version


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
        self.version = str(version)
        self.deps = None
        Package.CACHE[self.name + self.version] = self  # Add package to cache
        self.discover_deps()

    def add_dependencies(self, dependencies):
        """
        Add all dependencies to self.deps, creating a Package class instance if the dependency isn't in CACHE.
        :param dependencies: Dictionary of dependencies. Key is the dependency name, value is it's version/tag
        """
        for name, ver in dependencies.items():
            # Get the version number
            ver = translate_version_syntax(ver)
            pkg_name = name + ver

            # Either get the package instance from the cache or create a new one
            if pkg_name not in Package.CACHE:
                pkg = Package(name, ver)
            else:
                pkg = Package.CACHE[pkg_name]
            # Add Package instance to the dependencies list
            self.deps.append(pkg)

    def discover_deps(self):
        """
        Get all the package's dependencies and update self.deps
        """
        # No need to discover dependencies
        if self.deps:
            return

        # Send a Get request to obtain all package's dependencies using URL format
        self.deps = []
        response = requests.get(f"https://registry.npmjs.org/{self.name}/{self.version}")
        pkg_info = response.json()

        # Dependencies appear in json under 'dependencies' OR under 'devDependencies'
        if 'dependencies' in pkg_info:
            self.add_dependencies(pkg_info['dependencies'])
        elif 'devDependencies' in pkg_info:
            self.add_dependencies(pkg_info['devDependencies'])


def print_tree(pkg, printed_pkgs, dash_num):
    dash = '-' * dash_num
    print(f"{dash}{pkg.name}({pkg.version})")
    printed_pkgs.append(pkg)

    if pkg.deps:
        for dep in pkg.deps:
            if dep not in printed_pkgs:
                printed_pkgs = print_tree(dep, printed_pkgs, dash_num + 1)

    return printed_pkgs


#
# Gets a string package name and a version string.
#
@app.route('/<pkg_name>/<version>')
def present_dependencies(pkg_name, version):
    pkg = Package(pkg_name, version)
    print("done. Starting tree!")
    print_tree(pkg, [], 0)
    print("end of tree!")


    # print("\nPrinting dependencies:\n")
    # for dep in pkg.deps:
    #     print(dep.name + " " + pkg.version)
    # print("\nPrinting Cache:\n")
    # for name, instance in pkg.CACHE.items():
    #     print(name)
    #     print(instance.name)
    #     print(instance.version)
    return 'OK'


if __name__ == '__main__':
    app.run()
