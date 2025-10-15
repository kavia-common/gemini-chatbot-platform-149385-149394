from flask_smorest import Blueprint
from flask.views import MethodView

# PUBLIC_INTERFACE
blp = Blueprint("Health", "health", url_prefix="/", description="Health check routes")


@blp.route("/")
class HealthCheckRoot(MethodView):
    """Basic root health response for legacy checks."""
    def get(self):
        return {"message": "Healthy"}


# PUBLIC_INTERFACE
@blp.route("/healthz")
class HealthCheck(MethodView):
    """Kubernetes-style readiness/liveness probe endpoint."""
    def get(self):
        return {"status": "ok"}
