import os
from flask import Flask, request, jsonify, send_from_directory
from mirrsearch.internal_logic import InternalLogic


def create_app(dist_dir=None):
    if dist_dir is None:
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        dist_dir = os.path.join(project_root, 'frontend', 'dist')

    flask_app = Flask(__name__, static_folder=dist_dir, static_url_path='')

    @flask_app.route("/")
    def home():
        return send_from_directory(dist_dir, "index.html")

    @flask_app.route("/search/")
    def search():
        search_input = request.args.get('str')
        document_type_param = request.args.get('document_type')
        agency_param = request.args.get('agency')
        cfr_part_param = request.args.get('cfr_part')

        if search_input is None:
            search_input = "example_query"

        logic = InternalLogic("sample_database")
        return jsonify(logic.search(search_input,
                                    document_type_param,
                                    agency_param,
                                    cfr_part_param))

    return flask_app

app = create_app()

if __name__ == '__main__':
    app.run(port=80, debug=True)
