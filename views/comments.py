from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Comment, Task

comments_bp = Blueprint("comments_bp", __name__)

# Create a comment
@comments_bp.route("/tasks/<int:task_id>/comments", methods=["POST"])
@jwt_required()
def add_comment(task_id): 
    data = request.get_json()
    user_id = get_jwt_identity()
    content = data.get("content")

    # Check if task exists
    task = Task.query.get(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404

    # Validate comment content
    if not content or content.strip() == "":
        return jsonify({"error": "Comment cannot be empty"}), 400

    new_comment = Comment(task_id=task_id, user_id=user_id, content=content)
    db.session.add(new_comment)
    db.session.commit()

    return jsonify({
        "message": "Comment added successfully",
        "comment": {"id": new_comment.id, "content": new_comment.content}
    }), 201

# Get all comments for a task
@comments_bp.route("/tasks/<int:task_id>/comments", methods=["GET"])
@jwt_required()
def get_comments(task_id):
    task = Task.query.get(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404

    comments = Comment.query.filter_by(task_id=task_id).all()
    comments_list = [{"id": c.id, "content": c.content, "user_id": c.user_id} for c in comments]

    return jsonify({"comments": comments_list}), 200

# Update a comment (Partial Update)
@comments_bp.route("/comments/<int:comment_id>", methods=["PATCH"])
@jwt_required()
def update_comment(comment_id):
    data = request.get_json()
    user_id = get_jwt_identity()

    comment = Comment.query.get(comment_id)
    if not comment:
        return jsonify({"error": "Comment not found"}), 404

    if comment.user_id != user_id:
        return jsonify({"error": "Unauthorized to edit this comment"}), 403

    # Update only if content is provided
    if "content" in data and data["content"].strip():
        comment.content = data["content"]
        db.session.commit()
        return jsonify({"message": "Comment updated successfully", "comment": {"id": comment.id, "content": comment.content}}), 200

    return jsonify({"error": "No valid content provided"}), 400

# Delete a comment
@comments_bp.route("/comments/<int:comment_id>", methods=["DELETE"])
@jwt_required()
def delete_comment(comment_id):
    user_id = get_jwt_identity()

    comment = Comment.query.get(comment_id)
    if not comment:
        return jsonify({"error": "Comment not found"}), 404

    if comment.user_id != user_id:
        return jsonify({"error": "Unauthorized to delete this comment"}), 403

    db.session.delete(comment)
    db.session.commit()

    return jsonify({"message": "Comment deleted successfully"}), 200
