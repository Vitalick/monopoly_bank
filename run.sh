pydantic2ts --module ./models_interfaces/models.py --output ./models_interfaces/interfaces.ts
uvicorn serv.main:app --reload --reload-dir=serv