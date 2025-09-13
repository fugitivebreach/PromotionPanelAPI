from flask import Flask, request, jsonify
import requests
import os
from datetime import datetime
import json
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
API_KEY = "ARROWSPROMOTIONAPI2025-2026APIAPIAPIAPIAPIROYALGUARDROYALGUARDPROMOTIONPANEL"
ROBLOX_COOKIE = os.getenv('ROBLOX_COOKIE')
GROUP_ID = 9429240

# In-memory storage for promotion requests (in production, use a database)
promotion_requests = {}

def verify_api_key(provided_key):
    """Verify the API key"""
    return provided_key == API_KEY

def get_csrf_token():
    """Get CSRF token from ROBLOX"""
    headers = {
        'Cookie': f'.ROBLOSECURITY={ROBLOX_COOKIE}',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.post('https://auth.roblox.com/v2/logout', headers=headers)
        return response.headers.get('x-csrf-token')
    except Exception as e:
        logger.error(f"Failed to get CSRF token: {e}")
        return None

def get_user_info(user_id):
    """Get user information from ROBLOX"""
    try:
        response = requests.get(f'https://users.roblox.com/v1/users/{user_id}')
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        logger.error(f"Failed to get user info for {user_id}: {e}")
        return None

def get_user_rank_in_group(user_id, group_id):
    """Get user's rank in a specific group"""
    try:
        response = requests.get(f'https://groups.roblox.com/v2/users/{user_id}/groups/roles')
        if response.status_code == 200:
            data = response.json()
            for group in data.get('data', []):
                if group.get('group', {}).get('id') == group_id:
                    return group.get('role', {}).get('rank', 0)
        return 0
    except Exception as e:
        logger.error(f"Failed to get user rank for {user_id} in group {group_id}: {e}")
        return 0

def promote_user_in_group(user_id, rank_id):
    """Promote user in ROBLOX group"""
    csrf_token = get_csrf_token()
    if not csrf_token:
        return False, "Failed to get CSRF token"
    
    headers = {
        'Cookie': f'.ROBLOSECURITY={ROBLOX_COOKIE}',
        'X-CSRF-TOKEN': csrf_token,
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    data = {
        'roleId': rank_id
    }
    
    try:
        response = requests.patch(
            f'https://groups.roblox.com/v1/groups/{GROUP_ID}/users/{user_id}',
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            return True, "User promoted successfully"
        else:
            return False, f"Failed to promote user: {response.status_code} - {response.text}"
    except Exception as e:
        logger.error(f"Failed to promote user {user_id}: {e}")
        return False, f"Exception occurred: {str(e)}"

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat()})

@app.route('/submit_promotion', methods=['POST'])
def submit_promotion():
    """Submit a promotion request for approval"""
    # Verify API key
    api_key = request.headers.get('X-API-Key')
    if not verify_api_key(api_key):
        return jsonify({"error": "Invalid API key"}), 401
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400
    
    required_fields = ['target_user_id', 'target_rank_id', 'requester_user_id', 'event']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    # Generate unique request ID
    request_id = f"{data['target_user_id']}_{data['target_rank_id']}_{int(datetime.utcnow().timestamp())}"
    
    # Get user information
    target_user = get_user_info(data['target_user_id'])
    requester_user = get_user_info(data['requester_user_id'])
    
    if not target_user or not requester_user:
        return jsonify({"error": "Failed to get user information"}), 400
    
    # Store promotion request
    promotion_requests[request_id] = {
        'id': request_id,
        'target_user_id': data['target_user_id'],
        'target_username': target_user.get('name', 'Unknown'),
        'target_rank_id': data['target_rank_id'],
        'requester_user_id': data['requester_user_id'],
        'requester_username': requester_user.get('name', 'Unknown'),
        'event': data['event'],
        'status': 'pending',
        'created_at': datetime.utcnow().isoformat(),
        'processed_at': None,
        'processed_by': None
    }
    
    logger.info(f"Promotion request submitted: {request_id}")
    
    return jsonify({
        "success": True,
        "request_id": request_id,
        "message": "Promotion request submitted for approval"
    })

@app.route('/get_pending_promotions', methods=['GET'])
def get_pending_promotions():
    """Get all pending promotion requests"""
    # Verify API key
    api_key = request.headers.get('X-API-Key')
    if not verify_api_key(api_key):
        return jsonify({"error": "Invalid API key"}), 401
    
    pending_requests = [req for req in promotion_requests.values() if req['status'] == 'pending']
    
    return jsonify({
        "success": True,
        "pending_requests": pending_requests,
        "count": len(pending_requests)
    })

@app.route('/approve_promotion/<request_id>', methods=['POST'])
def approve_promotion(request_id):
    """Approve a promotion request"""
    # Verify API key
    api_key = request.headers.get('X-API-Key')
    if not verify_api_key(api_key):
        return jsonify({"error": "Invalid API key"}), 401
    
    if request_id not in promotion_requests:
        return jsonify({"error": "Promotion request not found"}), 404
    
    request_data = promotion_requests[request_id]
    if request_data['status'] != 'pending':
        return jsonify({"error": "Promotion request is not pending"}), 400
    
    data = request.get_json() or {}
    approver_user_id = data.get('approver_user_id', 'system')
    
    # Attempt to promote the user
    success, message = promote_user_in_group(
        request_data['target_user_id'],
        request_data['target_rank_id']
    )
    
    # Update request status
    request_data['status'] = 'approved' if success else 'failed'
    request_data['processed_at'] = datetime.utcnow().isoformat()
    request_data['processed_by'] = approver_user_id
    request_data['result_message'] = message
    
    logger.info(f"Promotion request {request_id} {'approved' if success else 'failed'}: {message}")
    
    return jsonify({
        "success": success,
        "message": message,
        "request": request_data
    })

@app.route('/reject_promotion/<request_id>', methods=['POST'])
def reject_promotion(request_id):
    """Reject a promotion request"""
    # Verify API key
    api_key = request.headers.get('X-API-Key')
    if not verify_api_key(api_key):
        return jsonify({"error": "Invalid API key"}), 401
    
    if request_id not in promotion_requests:
        return jsonify({"error": "Promotion request not found"}), 404
    
    request_data = promotion_requests[request_id]
    if request_data['status'] != 'pending':
        return jsonify({"error": "Promotion request is not pending"}), 400
    
    data = request.get_json() or {}
    rejector_user_id = data.get('rejector_user_id', 'system')
    rejection_reason = data.get('reason', 'No reason provided')
    
    # Update request status
    request_data['status'] = 'rejected'
    request_data['processed_at'] = datetime.utcnow().isoformat()
    request_data['processed_by'] = rejector_user_id
    request_data['result_message'] = f"Rejected: {rejection_reason}"
    
    logger.info(f"Promotion request {request_id} rejected by {rejector_user_id}: {rejection_reason}")
    
    return jsonify({
        "success": True,
        "message": "Promotion request rejected",
        "request": request_data
    })

@app.route('/get_request_status/<request_id>', methods=['GET'])
def get_request_status(request_id):
    """Get the status of a specific promotion request"""
    # Verify API key
    api_key = request.headers.get('X-API-Key')
    if not verify_api_key(api_key):
        return jsonify({"error": "Invalid API key"}), 401
    
    if request_id not in promotion_requests:
        return jsonify({"error": "Promotion request not found"}), 404
    
    return jsonify({
        "success": True,
        "request": promotion_requests[request_id]
    })

@app.route('/direct_promote', methods=['POST'])
def direct_promote():
    """Directly promote a user (for high-ranking users)"""
    # Verify API key
    api_key = request.headers.get('X-API-Key')
    if not verify_api_key(api_key):
        return jsonify({"error": "Invalid API key"}), 401
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400
    
    required_fields = ['target_user_id', 'target_rank_id', 'requester_user_id']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    # Attempt to promote the user directly
    success, message = promote_user_in_group(
        data['target_user_id'],
        data['target_rank_id']
    )
    
    logger.info(f"Direct promotion attempt for user {data['target_user_id']} by {data['requester_user_id']}: {'Success' if success else 'Failed'}")
    
    return jsonify({
        "success": success,
        "message": message
    })

if __name__ == '__main__':
    if not ROBLOX_COOKIE:
        logger.error("ROBLOX_COOKIE environment variable is not set!")
        exit(1)
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
