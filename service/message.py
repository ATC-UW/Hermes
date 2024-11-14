from fastapi.responses import JSONResponse

OK = 200
BAD_REQUEST = 400
NOT_FOUND = 404
INTERNAL_SERVER_ERROR = 500

class Message:
    def __init__(self, message, error=False, detail=None, result=None, status=200):
        self.message = message
        self.error = error
        self.status = status
        self.detail = detail
        self.result = result

    def __str__(self):
        return self.message

    def __repr__(self):
        return self.message
    
    def json(self):
        if(self.error):
            return JSONResponse({"error": self.message, "detail": self.detail, "status": self.status})
        return JSONResponse({"message": self.message, "result": self.result, "status": self.status})