from flask import Flask
from flask import request

app = Flask(__name__)


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def proxy(path):
    # Get the values from the header
    sp_id = request.headers['SERVICE-PROVIDER']
    user_token = request.headers['X-AUTH-TOKEN']

    # TODO: Get SAML2 from Keystone
    # TODO: Use K2K to get a scoped token for the SP
    # TODO: Analyze the service catalog in the token
    # TODO: Decide which endpoint to forward the request

    # TODO: Switch the token from the request
    # TODO: Remove the SP_ID from the request

    # TODO: Forward the request to the SP, to the same path received
    # TODO: Return the received response
    response = ''
    return response

if __name__ == "__main__":
    app.run(port=5001)