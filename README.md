# ArrowsPromotionAPI

A Flask-based API for managing ROBLOX group promotions, replacing the Trello integration with a direct API approach.

## Features

- **API Key Authentication**: Secure access using the API key `ARROWSPROMOTIONAPI2025-2026APIAPIAPIAPIAPIROYALGUARDROYALGUARDPROMOTIONPANEL`
- **ROBLOX Integration**: Direct integration with ROBLOX groups using cookies
- **Promotion Workflow**: Submit promotion requests for approval or direct promotion for high-ranking users
- **Request Management**: Track, approve, and reject promotion requests
- **Railway Deployment**: Ready for deployment on Railway platform

## API Endpoints

### Health Check
- `GET /health` - Check API status

### Promotion Management
- `POST /submit_promotion` - Submit a promotion request for approval
- `GET /get_pending_promotions` - Get all pending promotion requests
- `POST /approve_promotion/<request_id>` - Approve a promotion request
- `POST /reject_promotion/<request_id>` - Reject a promotion request
- `GET /get_request_status/<request_id>` - Get status of a specific request
- `POST /direct_promote` - Directly promote a user (for high-ranking users)

## Authentication

All endpoints (except `/health`) require the `X-API-Key` header with the value:
```
ARROWSPROMOTIONAPI2025-2026APIAPIAPIAPIAPIROYALGUARDROYALGUARDPROMOTIONPANEL
```

## Environment Variables

- `ROBLOX_COOKIE`: Your ROBLOX authentication cookie
- `PORT`: Port for the application (set automatically by Railway)

## Deployment on Railway

1. Create a new Railway project
2. Connect your repository
3. Set the `ROBLOX_COOKIE` environment variable
4. Deploy!

## Usage with Lua

The API is designed to work with the `promoteuser.lua` script, replacing the Trello integration with direct API calls.

### Example Request (Submit Promotion)
```json
POST /submit_promotion
Headers: X-API-Key: ARROWSPROMOTIONAPI2025-2026APIAPIAPIAPIAPIROYALGUARDROYALGUARDPROMOTIONPANEL
Body: {
  "target_user_id": 123456789,
  "target_rank_id": 50,
  "requester_user_id": 987654321,
  "event": "promotion"
}
```

### Example Request (Direct Promotion)
```json
POST /direct_promote
Headers: X-API-Key: ARROWSPROMOTIONAPI2025-2026APIAPIAPIAPIAPIROYALGUARDROYALGUARDPROMOTIONPANEL
Body: {
  "target_user_id": 123456789,
  "target_rank_id": 50,
  "requester_user_id": 987654321
}
```
