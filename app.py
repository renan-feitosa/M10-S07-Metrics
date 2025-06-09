from fastapi import FastAPI, Request
from prometheus_client import Counter, Histogram, start_http_server, generate_latest, CONTENT_TYPE_LATEST, Gauge
from time import time

app = FastAPI()

# Métricas Prometheus
REQUEST_LATENCY = Histogram(
    "http_server_request_duration_seconds",
    "Duração das requisições HTTP",
    ["http_request_method", "http_route"]
)

HTTP_ACTIVE_REQUESTS = Gauge(
    "http_server_active_requests",
    "Número de requisições HTTP ativas no momento",
    ["http_request_method", "http_route"]
)

PRODUCT_SOLD = Counter(
    "contoso_product_sold_total",
    "Quantidade de produtos vendidos",
    ["product_name"]
)

start_http_server(8001)

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    method = request.method
    route = request.url.path

    HTTP_ACTIVE_REQUESTS.labels(method, route).inc()

    start_time = time()
    process_time = time() - start_time
    
    try: 
        response = await call_next(request)
        return response
    finally:
        process_time = time() - start_time
        REQUEST_LATENCY.labels(method, route).observe(process_time)
        HTTP_ACTIVE_REQUESTS.labels(method, route).dec()

@app.get("/")
async def read_root():
    return {"message": "Hello OpenTelemetry!"}

@app.post("/complete-sale")
async def complete_sale(product_name: str, quantity: int):
    PRODUCT_SOLD.labels(product_name).inc(quantity)
    return {"message": f"{quantity} unidades de {product_name} vendidas."}

@app.get("/metrics")
async def metrics():
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}
