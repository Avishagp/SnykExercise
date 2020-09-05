from flask import Flask
import requests
import json
import os
import time

app = Flask(__name__)


def translate_version_syntax(version):
    """
    Translate version number so it doesn't contain *, ^, ~, etc. Translation assumes lowest version number approved.
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

    # Translate version number (according to https://docs.npmjs.com/misc/semver).
    # Assume lowest version number approved.
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
        self.version = version
        self.deps = None
        self.discover_deps()

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
                    deps = [(name, ver) for name, ver in item["deps"]]
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
            for (pkg_name, pkg_ver), pkg_deps in cls.CACHE.items():
                cache.append({"name": pkg_name, "version": pkg_ver, "deps": pkg_deps})
            json.dump(cache, f)

    def add_dependencies(self, dependencies):
        """
        Add all dependencies to self.deps, creating a Package class instance if the dependency isn't in CACHE.
        :param dependencies: Dictionary of dependencies. Key is the dependency name, value is it's version/tag
        """
        for name, ver in dependencies.items():
            # Get the version number
            ver = translate_version_syntax(ver)
            pkg_id = (name, ver)

            # Create a new Package if dependency is not in the cache so that dependency discovering continues
            if pkg_id not in Package.CACHE:
                Package(name, ver)
            # Add Package instance to the dependencies list
            self.deps.append(pkg_id)

    def discover_deps(self):
        """
        Get all the package's dependencies and update self.deps
        """
        # No need to discover dependencies
        if self.deps is not None:
            return

        # Send a Get request to obtain all package's dependencies using URL format
        self.deps = []
        # The reason I add to cache here, is to handle cyclic dependencies
        Package.CACHE[(self.name, self.version)] = self.deps

        response = requests.get(f"https://registry.npmjs.org/{self.name}/{self.version}")
        pkg_info = response.json()

        # Dependencies appear in json under 'dependencies' OR under 'devDependencies'
        if 'dependencies' in pkg_info:
            self.add_dependencies(pkg_info['dependencies'])
        elif 'devDependencies' in pkg_info:
            self.add_dependencies(pkg_info['devDependencies'])


def get_tree(pkg, tree, discovered=None, depth=0):
    """
    Create dependency tree using DFS.
    :param pkg: (pkg_name, pkg_version) of the package to check dependencies for
    :param tree: string of the tree so far
    :param discovered: list containing all packages that have been checked already, used to avoid loops
    :param depth: number of dashes needed to be drawn (also the package's depth in the tree)
    :return: tree: string representing the tree
             printed_pkgs: list containing all packages that have been checked already, used to avoid loops
    """
    name, version = pkg
    if discovered is None:
        discovered = []
    dash = '─' * depth
    tree += f"│{dash}{name}({version})<br/>"
    discovered.append(pkg)

    for dep in Package.CACHE[pkg]:
        if dep not in discovered:  # To avoid loops
            tree, discovered = get_tree(dep, tree, discovered, depth + 1)

    return tree, discovered


@app.route('/<pkg_name>/<version>')
def present_dependencies(pkg_name, version):
    # Create package, get dependencies during creation and update cache
    pkg = Package(pkg_name, version)

    # update the cache with the resolved deps
    pkg.update_cache()

    # Create tree
    tree, _ = get_tree((pkg.name, pkg.version), f"Dependency Tree for {pkg_name}({version}):<br/><br/>")
    return tree


@app.route('/test/dependencies')
def test_dependencies():
    """
    Test if the dependencies of a certain package are found correctly
    :return: test message
    """
    pkg = Package("tap", "0.4.0")
    dependencies = [('inherits', '0.0.0'), ('yamlish', '0.0.0'), ('slide', '0.0.0'), ('runforcover', '0.0.2'),
                    ('nopt', '2.0.0'), ('mkdirp', '0.3.0'), ('difflet', '0.2.0'), ('deep-equal', '0.0.0'),
                    ('buffer-equal', '0.0.0'), ('glob', '3.1.14')]

    # Check if dependency list was discovered correctly
    if dependencies == pkg.deps:
        return "Dependencies test succeeded!"
    else:
        return "Dependencies test failed"


@app.route('/test/nodeps')
def test_no_dependencies():
    """
    Check if the program operates correctly with a package without dependencies.
    :return: test message
    """
    pkg = Package("inherits", "*")

    if len(pkg.deps) == 0:
        return "No dependencies test succeeded!"
    else:
        return "No dependencies test failed"


@app.route('/test/cache')
def test_cache():
    """
    Test if cache was correctly written to file.
    :return: test message
    """
    pkg = Package("tap", "0.4.0")
    pkg.update_cache()

    with open("cache.json") as f:
        # json: [{"name":"package_name", "version":"1.0", "deps":[("a","1.0")...]}...]
        cache = json.load(f)
        for pkg in cache:
            dep = (pkg["name"], pkg["version"])
            # Test json and CACHE uniformity
            if dep not in Package.CACHE:
                return "Cache test failed"
    return "Cache test succeeded!"


@app.route('/test/cachetime')
def test_cache_time():
    """
    Test package creation time after cache update.
    :return: test message
    """
    # Create package and check time
    before_pkg1 = time.time()
    pkg1 = Package("tap", "0.4.0")
    pkg1_time = time.time() - before_pkg1
    Package.update_cache()

    # Create same package and check time
    before_pkg2 = time.time()
    pkg2 = Package("tap", "0.4.0")
    pkg2_time = time.time() - before_pkg2

    if pkg2_time < pkg1_time:
        return f"Cache time test succeeded!<br/>Uncached time: {pkg1_time}<br/>Cached time: {pkg2_time}"
    else:
        return "Cache time test failed. Perhaps cache was full when you ran it?"


@app.route('/test/tree')
def test_tree():
    """
    Test tree correctness.
    :return: test message
    """
    pkg = Package("tap", "0.4.0")
    tree, _ = get_tree((pkg.name, pkg.version), f"Dependency Tree for {pkg.name}({pkg.version}):<br/><br/>")
    correct_tree = "Dependency Tree for tap(0.4.0):<br/><br/>│tap(0.4.0)<br/>│─inherits(0.0.0)<br/>│─yamlish(" \
                   "0.0.0)<br/>│─slide(0.0.0)<br/>│─runforcover(0.0.2)<br/>│──bunker(0.1.0)<br/>│───burrito(" \
                   "0.2.5)<br/>│────traverse(0.4.2)<br/>│────uglify-js(1.0.4)<br/>│─nopt(2.0.0)<br/>│──abbrev(" \
                   "1.0.0)<br/>│─mkdirp(0.3.0)<br/>│─difflet(0.2.0)<br/>│──traverse(0.6.0)<br/>│──charm(" \
                   "0.0.0)<br/>│──deep-equal(0.0.0)<br/>│─buffer-equal(0.0.0)<br/>│─glob(3.1.14)<br/>│──minimatch(" \
                   "0.2.0)<br/>│───lru-cache(1.0.5)<br/>│──graceful-fs(1.1.2)<br/>│───fast-list(" \
                   "1.0.0)<br/>│──inherits(1.0.0)<br/>"
    if correct_tree == tree:
        return "Tree test succeeded!"
    else:
        return "Tree test failed!"


@app.route('/sanitytest')
def test():
    """
    Sanity test that calls all tests.
    :return:
    """
    test_message = test_dependencies() + "<br/>"
    test_message += test_no_dependencies() + "<br/>"
    test_message += test_cache() + "<br/>"
    test_message += test_cache_time() + "<br/>"
    test_message += test_tree()
    return test_message


if __name__ == '__main__':
    app.run()
