from flask import Flask, request

app = Flask(__name__)

@app.route('/callback/')
def callback():
    code = request.args.get('code')
    if code:
        return f"Authorization successful! Your code is: {code}", 200
    else:
        return "Authorization failed or no code received.", 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
