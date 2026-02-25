import os
from flask import Flask, request, jsonify, send_from_directory
from mirrsearch.internal_logic import InternalLogic


def create_app(db_layer=None):
    # This is needed due to templates being 2 levels up from this file causing flask not to see it.
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    static_dir = os.path.join(project_root, 'static')

    flask_app = Flask(__name__, static_folder=static_dir, static_url_path='/static')

    @flask_app.route("/")
    def home():
        return send_from_directory(static_dir, "index.html")

    @flask_app.route("/search/")
    def search():
        search_input = request.args.get('str')
        filter_param = request.args.get('filter')
        agency_param = request.args.get('agency')
        if search_input is None:
            search_input = "example_query"
        logic = InternalLogic("sample_database", db_layer=db_layer)
        return jsonify(logic.search(search_input, filter_param, agency_param))

    return flask_app

app = create_app()

if __name__ == '__main__':
    app.run(port=80, debug=True)
    