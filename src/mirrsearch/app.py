from flask import Flask, render_template, request

def create_app():
    app = Flask(__name__)

    @app.route("/")
    def home():
        return render_template('index.html')

    
    def hello_world():
        return "<p>Hello, World!</p>"
	
    @app.route("/search/")
    def search():
        search_input = request.args.get('str')
        return ["Test", "Dummy", search_input]


    return app


if __name__ == '__main__':
    app = create_app()
    app.run(port=8000, debug=True)

