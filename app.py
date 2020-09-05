from flask import Flask
import requests
import json
import os

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
        dictionary CACHE - Holds data of all packages: set of package name and version to a list of it's dependencies.
    """
    CACHE = None  # {("package_name","package_version") : [("package_name","package_version")...]}

    def __init__(self, name, version):
        """
        :param name: Package's name
        :param version: Package's version/tag
        """
        Package._init_cache()
        self.name = name
        self.version = str(version)
        self.deps = None
        self.discover_deps()
        Package.CACHE[(self.name, self.version)] = self.deps  # Add package to cache

    @classmethod
    def _init_cache(cls):
        """
        Either create or load cache json file to CACHE class member
        """
        if cls.CACHE is not None:
            return
        try:
            with open("cache.json") as f:
                # Load the cache file to a dictionary class member
                # json: [{"name":"package_name", "version":"1.0", "deps":[("a","1.0")...]}...]
                # CACHE: {("package_name","package_version") : [("package_name","package_version")...]}
                cache = json.load(f)
                cls.CACHE = {}
                for item in cache:
                    # json converts tuples to lists so the dependency list needs to be converted back
                    deps = [(i[0], i[1]) for i in item["deps"]]
                    # Add to class member cache
                    cls.CACHE[(item["name"], item["version"])] = deps

        except FileNotFoundError:
            cls.CACHE = {}
        except json.JSONDecodeError:
            cls.CACHE = {}
            # cache json is bad, remove it
            os.remove("cache.json")

    @classmethod
    def update_cache(cls):
        """
        Update cache json file using CACHE class member
        """
        with open("cache.json", 'w') as f:
            cache = []
            # Write the cache dictionary to a json file:
            # json: [{"name":"package_name", "version":"1.0", "deps":[("a","1.0")...]}...]
            # CACHE: {("package_name","package_version") : [("package_name","package_version")...]}
            for pkg_name, pkg_deps in cls.CACHE.items():
                cache.append({"name": pkg_name[0], "version": pkg_name[1], "deps": pkg_deps})
            json.dump(cache, f)

    def add_dependencies(self, dependencies):
        """
        Add all dependencies to self.deps, creating a Package class instance if the dependency isn't in CACHE.
        :param dependencies: Dictionary of dependencies. Key is the dependency name, value is it's version/tag
        """
        for name, ver in dependencies.items():
            # Get the version number
            ver = translate_version_syntax(ver)
            pkg_name = (name, ver)

            # Create a new Package if dependency is not in the cache so that dependency discovering continues
            if pkg_name not in Package.CACHE:
                Package(name, ver)
            # Add Package instance to the dependencies list
            self.deps.append(pkg_name)

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


def get_tree(pkg, printed_pkgs, dash_num, tree, CACHE):
    """
    Create dependency tree.
    :param pkg: (pkg_name, pkg_version) of the package to check dependencies for
    :param printed_pkgs: a list containing all packages that have been checked already, used to avoid loops
    :param dash_num: number of dashes needed to be drawn (also the package's depth in the tree)
    :param tree: string of the tree so far
    :param CACHE: holds data on all packages and dependencies
    :return:
    """
    dash = '─' * dash_num
    tree += f"│{dash}{pkg[0]}({pkg[1]})<br/>"
    printed_pkgs.append(pkg)

    if CACHE[pkg]:  # Are there any dependencies?
        for dep in CACHE[pkg]:
            if dep not in printed_pkgs:  # To avoid loops
                tree, printed_pkgs = get_tree(dep, printed_pkgs, dash_num + 1, tree, CACHE)

    return tree, printed_pkgs


@app.route('/<pkg_name>/<version>')
def present_dependencies(pkg_name, version):
    # Create package, get dependencies during creation and update cache
    pkg = Package(pkg_name, version)
    pkg.update_cache()

    # Create tree
    print("done. Starting tree!")
    tree = get_tree((pkg.name, pkg.version), [], 0, f"Dependency Tree for {pkg_name}({version}):<br/><br/>", Package.CACHE)
    print("end of tree!")
    return tree[0]


if __name__ == '__main__':
    app.run()
