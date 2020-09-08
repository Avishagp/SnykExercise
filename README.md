# SnykExercise

## Usage
Displaly a dependency tree for a given npmjs package.
Run with `FLASK_APP=app.py python3 -m flask run`.<br/>
You can also browse to: http://127.0.0.1:5000/pkg_name/pkg_version. For example: http://127.0.0.1:5000/tap/0.4.0.

## Tests
Browse to http://127.0.0.1:5000/sanitytest to perform all sanity tests. Those include:
* http://127.0.0.1:5000/test/dependencies - Test if the dependencies of a certain package are found correctly
* http://127.0.0.1:5000/test/nodeps - Test if the program operates correctly with a package without dependencies.
* http://127.0.0.1:5000/test/cache - Test if cache was correctly written to file.
* http://127.0.0.1:5000/test/cachetime - Test package creation time after cache update.
* http://127.0.0.1:5000/test/tree - Test tree correctness.
