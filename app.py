from flask import Flask
app = Flask(__name__)


@app.route('/<pkg_name>')
def present_dependencies(pkg_name):
    pass
    # Get the entire set of dependencies and present them in a tree view


if __name__ == '__main__':
    app.run()
