from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_socketio import emit
from models import db, Notification
from app import socketio  

notifications_bp = Blueprint("notifications_bp", __name__)

# Send real-time notifications to a user
def send_notification(user_id, message):
    notification = Notification(user_id=user_id, message=message)
    db.session.add(notification)
    db.session.commit()
    
    # Emit a real-time event
    socketio.emit(f"notification_{user_id}", {"message": message}, to=user_id)

# Create a new notification
@notifications_bp.route("/notifications", methods=["POST"])
@jwt_required()
def create_notification():
    data = request.get_json()
    user_id = get_jwt_identity()  # Get the logged-in user ID
    message = data.get("message", "")

    if not message:
        return jsonify({"error": "Message is required"}), 400

    send_notification(user_id, message)  # Save and emit notification

    return jsonify({"success": "Notification sent"}), 201

# Get all notifications for the logged-in user
@notifications_bp.route("/notifications", methods=["GET"])
@jwt_required()
def get_notifications():
    user_id = get_jwt_identity()
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 5, type=int)
    notifications = Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "notifications": [
            {"id": n.id, "message": n.message, "is_read": n.is_read, "created_at": n.created_at}
            for n in notifications.items
        ],
        "total_pages": notifications.pages,
        "current_page": notifications.page
    })

# Mark a notification as read
@notifications_bp.route("/notifications/<int:notification_id>/read", methods=["PUT"])
@jwt_required()
def mark_as_read(notification_id):
    notification = Notification.query.get(notification_id)
    
    if not notification:
        return jsonify({"error": "Notification not found"}), 404

    notification.is_read = True
    db.session.commit()

    return jsonify({"success": "Notification marked as read"}), 200


# Delete a notification
@notifications_bp.route("/notifications/<int:notification_id>", methods=["DELETE"])
@jwt_required()
def delete_notification(notification_id):
    user_id = get_jwt_identity()  # Get the logged-in user ID

    # Find the notification
    notification = Notification.query.get(notification_id)
    
    if not notification:
        return jsonify({"error": "Notification not found"}), 404

    # Ensure the user owns the notification
    if notification.user_id != user_id:
        return jsonify({"error": "Unauthorized to delete this notification"}), 403

    # Delete the notification
    db.session.delete(notification)
    db.session.commit()

    return jsonify({"message": "Notification deleted successfully"}), 200

