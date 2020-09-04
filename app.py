from flask import Flask
import requests
import json

app = Flask(__name__)


#
# Gets a list of string. Each string represents a dependency.
# Resturns TODO
#
def create_tree(dependencies):
    return 0


#
# Gets a dictionary that contains all data about a package.
# Returns a list of all dependencies.
#
def get_dependencies(pkg_info):
    dependencies = []
    if 'dependencies' in pkg_info:
        dependencies.extend(pkg_info['dependencies'])
    elif 'devDependencies' in pkg_info:
        dependencies.extend(pkg_info['devDependencies'])

    return dependencies


#
# Gets a string package name and an optional version string.
# Returns TODO
#
@app.route('/present/<pkg_name>/<version>')
@app.route('/present/<pkg_name>')
def present_dependencies(pkg_name, version=None):
    # Send a Get request using package name
    if version:
        response = requests.get("https://registry.npmjs.org/" + str(pkg_name) + "/" + str(version))
    else:
        response = requests.get("https://registry.npmjs.org/" + str(pkg_name))

    # Get the entire set of dependencies
    dependencies = get_dependencies(response.json())
    print(dependencies)
    # Get a tree string for presentation
    tree = create_tree(dependencies)

    # Present the tree!


if __name__ == '__main__':
    app.run()
