from waitress import serve
import reply

serve(reply.app, host='127.0.0.1', port=8000)
