from app import app, socketio
import routes

if __name__ == "__main__":
    # Run with SocketIO support for real-time features
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
